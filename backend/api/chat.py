import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import (
    GEMINI_API_KEY,
    SEMANTIC_TOP_K,
    KEYWORD_TOP_K,
    FUSION_TOP_K,
    RERANK_TOP_K
)
from database.storage import RepositoryStorage
from conversation.memory import ConversationMemory
from retrieval.vector_search import VectorSearch
from retrieval.semantic_search import SemanticRetriever
from retrieval.keyword_search import KeywordSearch
from retrieval.fusion import HybridRetriever
from retrieval.reranker import CodeReranker
from generation.answer_generator import AnswerGenerator
from generation.query_rewriter import QueryRewriter

router = APIRouter(prefix="/api/chat", tags=["chat"])

storage = RepositoryStorage()
memory = ConversationMemory()

# Cache BM25 instances per repository
_bm25_indices: Dict[str, KeywordSearch] = {}
_reranker_instance = None
_hybrid_retriever = None

def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever(
            semantic_top_k=SEMANTIC_TOP_K,
            keyword_top_k=KEYWORD_TOP_K,
            final_top_k=FUSION_TOP_K
        )
    return _hybrid_retriever

def get_reranker() -> Optional[CodeReranker]:
    global _reranker_instance
    if _reranker_instance is None:
        try:
            _reranker_instance = CodeReranker(top_k=RERANK_TOP_K)
        except Exception as e:
            print(f"[Warning] Failed to initialize reranker: {e}")
            _reranker_instance = None
    return _reranker_instance

def get_bm25_for_repo(repository_id: str) -> KeywordSearch:
    if repository_id not in _bm25_indices:
        # Re-use the existing client from hybrid retriever to avoid Windows file locks
        hybrid = get_hybrid_retriever()
        chunks = hybrid.semantic_retriever.vector_db.get_repository_chunks(repository_id)
        if not chunks:
            raise ValueError(f"No chunks found for repository {repository_id}")
        ks = KeywordSearch()
        ks.build_index(chunks)
        _bm25_indices[repository_id] = ks
    return _bm25_indices[repository_id]


class ChatRequest(BaseModel):
    repository_id: str
    message: str
    session_id: Optional[str] = None
    use_reranker: Optional[bool] = True

class Citation(BaseModel):
    chunk_id: str
    file_path: str
    start_line: int
    end_line: int

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation]
    retrieved_chunks_count: int


@router.post("", response_model=ChatResponse)
def chat_with_codebase(request: ChatRequest):
    """
    Main RAG Question-Answering endpoint with:
    1. Conversational memory & query rewriting
    2. Hybrid Search (Semantic + BM25)
    3. Reciprocal Rank Fusion (RRF)
    4. Cross-Encoder Reranking
    5. Gemini LLM generation with strict citation validation
    """
    repo_id = request.repository_id
    question = request.message.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    repo = storage.get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    if repo["status"] != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not ready for querying (status: {repo['status']})."
        )

    # Manage session & conversational memory
    session_id = request.session_id
    if not session_id:
        session_id = memory.create_session(repository_id=repo_id)
    else:
        try:
            memory.validate_session(session_id, repository_id=repo_id)
        except Exception:
            session_id = memory.create_session(repository_id=repo_id, session_id=session_id)

    # Fetch recent conversation history
    history = memory.get_history(session_id=session_id, repository_id=repo_id, limit=6)

    # Query Rewriting for follow-up questions
    retrieval_query = question
    api_key_valid = GEMINI_API_KEY and GEMINI_API_KEY != "your_actual_gemini_api_key"

    if history and api_key_valid:
        try:
            rewriter = QueryRewriter()
            retrieval_query = rewriter.rewrite_question(question=question, history=history)
        except Exception as e:
            print(f"[Warning] Query rewriting failed: {e}")
            retrieval_query = question

    # Hybrid Retrieval (Semantic + BM25)
    hybrid = get_hybrid_retriever()

    # Step 1: Semantic search
    semantic_results = hybrid.semantic_retriever.retrieve(
        question=retrieval_query,
        repository_id=repo_id,
        limit=SEMANTIC_TOP_K
    )

    # Step 2: Keyword search (BM25)
    try:
        bm25_searcher = get_bm25_for_repo(repo_id)
        keyword_results = bm25_searcher.search(
            query=retrieval_query,
            repository_id=repo_id,
            top_k=KEYWORD_TOP_K
        )
    except Exception as e:
        print(f"[Warning] BM25 search failed: {e}")
        keyword_results = []

    # Step 3: Reciprocal Rank Fusion
    fused_chunks = hybrid.reciprocal_rank_fusion(
        semantic_results=semantic_results,
        keyword_results=keyword_results
    )

    # Step 4: Cross-Encoder Reranking
    final_chunks = fused_chunks
    if request.use_reranker and fused_chunks:
        reranker = get_reranker()
        if reranker:
            try:
                final_chunks = reranker.rerank(
                    question=retrieval_query,
                    retrieved_chunks=fused_chunks
                )
            except Exception as e:
                print(f"[Warning] Reranker failed: {e}")
                final_chunks = fused_chunks[:RERANK_TOP_K]

    # Save user message to memory
    memory.save_message(
        session_id=session_id,
        repository_id=repo_id,
        role="user",
        content=question
    )

    # Step 5: Generate Answer
    if not final_chunks:
        fallback_answer = "The answer cannot be determined from the retrieved code because no relevant files were found."
        memory.save_message(
            session_id=session_id,
            repository_id=repo_id,
            role="assistant",
            content=fallback_answer
        )
        return ChatResponse(
            session_id=session_id,
            answer=fallback_answer,
            citations=[],
            retrieved_chunks_count=0
        )

    if api_key_valid:
        try:
            generator = AnswerGenerator()
            generation_result = generator.generate_answer(
                question=question,
                retrieved_chunks=final_chunks
            )
            answer = generation_result.get("answer", "")
            raw_citations = generation_result.get("citations", [])
            citations = [
                Citation(
                    chunk_id=c.get("chunk_id", ""),
                    file_path=c.get("file_path", ""),
                    start_line=c.get("start_line", 1),
                    end_line=c.get("end_line", 1)
                )
                for c in raw_citations
            ]
        except Exception as e:
            # Fallback if Gemini quota or connection error occurs
            print(f"[Warning] Answer generator error: {e}")
            answer = f"Found {len(final_chunks)} relevant source code sections. (Note: LLM answer generation failed with error: {str(e)}). Please review the citations below to inspect the source code directly."
            citations = [
                Citation(
                    chunk_id=c.get("chunk_id", ""),
                    file_path=c.get("file_path", ""),
                    start_line=c.get("start_line", 1),
                    end_line=c.get("end_line", 1)
                )
                for c in final_chunks[:5]
            ]
    else:
        # If user hasn't set real Gemini API key yet, provide structured citation response
        answer = (
            "Retrieved matching source snippets successfully through Semantic + BM25 Hybrid Retrieval and RRF ranking. "
            "To generate natural language answers with Gemini, please provide a valid GEMINI_API_KEY in `backend/.env`."
        )
        citations = [
            Citation(
                chunk_id=c.get("chunk_id", ""),
                file_path=c.get("file_path", ""),
                start_line=c.get("start_line", 1),
                end_line=c.get("end_line", 1)
            )
            for c in final_chunks[:5]
        ]

    # Save assistant message to memory
    memory.save_message(
        session_id=session_id,
        repository_id=repo_id,
        role="assistant",
        content=answer
    )

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=citations,
        retrieved_chunks_count=len(final_chunks)
    )


@router.get("/history/{session_id}")
def get_session_history(session_id: str, repository_id: str, limit: int = 50):
    """Retrieve full conversation history for a session."""
    return memory.get_history(session_id=session_id, repository_id=repository_id, limit=limit)
