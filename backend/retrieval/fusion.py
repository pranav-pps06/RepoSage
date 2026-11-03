from typing import List, Dict
from collections import defaultdict

from retrieval.semantic_search import SemanticRetriever
from retrieval.keyword_search import KeywordSearch


class HybridRetriever:
    def __init__(
        self,
        semantic_top_k: int = 10,
        keyword_top_k: int = 10,
        final_top_k: int = 10,
        rrf_k: int = 60
    ):
        self.semantic_retriever = SemanticRetriever(top_k=semantic_top_k)
        self.keyword_search = KeywordSearch()

        self.semantic_top_k = semantic_top_k
        self.keyword_top_k = keyword_top_k
        self.final_top_k = final_top_k
        self.rrf_k = rrf_k

    def build_keyword_index(
        self,
        chunks: List[Dict],
        repository_id: str
    ) -> None:
        indexed_chunks = [
            {
                **chunk,
                "repository_id": repository_id
            }
            for chunk in chunks
        ]

        self.keyword_search.build_index(indexed_chunks)

    def reciprocal_rank_fusion(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict]
    ) -> List[Dict]:

        fused_results = {}

        retrieval_lists = [
            semantic_results,
            keyword_results
        ]

        for results in retrieval_lists:
            for rank, chunk in enumerate(results, start=1):

                chunk_id = chunk["chunk_id"]
                key = (
                    chunk.get("repository_id"),
                    chunk_id
                )

                if key not in fused_results:
                    fused_results[key] = {
                        **chunk,
                        "rrf_score": 0.0
                    }

                fused_results[key]["rrf_score"] += (
                    1.0 / (self.rrf_k + rank)
                )

        ranked_results = sorted(
            fused_results.values(),
            key=lambda item: item["rrf_score"],
            reverse=True
        )

        return ranked_results[:self.final_top_k]

    def retrieve(
        self,
        question: str,
        repository_id: str
    ) -> List[Dict]:

        semantic_results = self.semantic_retriever.retrieve(
            question=question,
            repository_id=repository_id,
            limit=self.semantic_top_k
        )

        keyword_results = self.keyword_search.search(
            query=question,
            repository_id=repository_id,
            top_k=self.keyword_top_k
        )

        fused_results = self.reciprocal_rank_fusion(
            semantic_results,
            keyword_results
        )

        return fused_results

    def close(self):
        self.semantic_retriever.close()


if __name__ == "__main__":

    sample_chunks = [
        {
            "chunk_id": "chunk_1",
            "file_path": "auth.py",
            "start_line": 1,
            "end_line": 20,
            "language": "python",
            "content": """
            def authenticate_user(username, password):
                user = database.get_user(username)
                return verify_password(password, user.password)
            """
        },
        {
            "chunk_id": "chunk_2",
            "file_path": "database.py",
            "start_line": 1,
            "end_line": 15,
            "language": "python",
            "content": """
            def get_user(username):
                return users.find_one({"username": username})
            """
        },
        {
            "chunk_id": "chunk_3",
            "file_path": "routes.py",
            "start_line": 1,
            "end_line": 25,
            "language": "python",
            "content": """
            @app.route("/login")
            def login():
                return authenticate_user(request.form["username"],
                                         request.form["password"])
            """
        }
    ]

    retriever = HybridRetriever()

    repository_id = "sample_repository"

    retriever.build_keyword_index(
        chunks=sample_chunks,
        repository_id=repository_id
    )

    keyword_results = retriever.keyword_search.search(
        query="How does user authentication work?",
        repository_id=repository_id,
        top_k=10
    )

    print("\nBM25 Results:")

    for result in keyword_results:
        print(
            result["file_path"],
            result["start_line"],
            result["end_line"],
            result["score"]
        )

    semantic_results = [
        {
            **sample_chunks[0],
            "repository_id": repository_id,
            "score": 0.90
        },
        {
            **sample_chunks[1],
            "repository_id": repository_id,
            "score": 0.80
        }
    ]

    fused_results = retriever.reciprocal_rank_fusion(
        semantic_results,
        keyword_results
    )

    print("\nHybrid Retrieval Results:")

    for result in fused_results:
        print(
            f"File: {result['file_path']}",
            f"Lines: {result['start_line']}-{result['end_line']}",
            f"RRF Score: {result['rrf_score']:.6f}"
        )

    retriever.close()