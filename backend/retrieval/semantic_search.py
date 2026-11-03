from typing import List, Dict

from embeddings.embedder import CodeEmbedder
from retrieval.vector_search import VectorSearch


class SemanticRetriever:

    def __init__(self, top_k: int = 10):
        """
        Initialize embedding model and Qdrant vector database.
        """

        self.embedder = CodeEmbedder(
            model_name="all-MiniLM-L6-v2"
        )

        self.vector_db = VectorSearch(
            embedding_dimension=384
        )

        self.top_k = top_k

    def retrieve(
        self,
        question: str,
        repository_id: str,
        limit: int = None
    ) -> List[Dict]:
        """
        Retrieve relevant source-code chunks using semantic search.
        """

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not repository_id:
            raise ValueError("Repository ID is required.")

        if limit is None:
            limit = self.top_k

        # Step 1: Convert question into an embedding
        query_embedding = self.embedder.generate_query_embedding(
            question
        )

        # Step 2: Search Qdrant with repository filtering
        results = self.vector_db.search(
            query_embedding=query_embedding,
            repository_id=repository_id,
            limit=limit
        )

        # Step 3: Return relevant chunks with metadata
        return results

    def close(self):
        self.vector_db.close()


if __name__ == "__main__":

    retriever = SemanticRetriever(top_k=10)

    question = "How does the application authenticate users?"

    repository_id = "test_repository_123"

    try:
        results = retriever.retrieve(
            question=question,
            repository_id=repository_id
        )

        print(f"\nQuestion: {question}")
        print(f"Retrieved chunks: {len(results)}")

        for index, result in enumerate(results, start=1):

            print(f"\n{'=' * 60}")
            print(f"Result {index}")
            print(f"File: {result['file_path']}")
            print(
                f"Lines: {result['start_line']}-{result['end_line']}"
            )
            print(f"Language: {result['language']}")
            print(f"Score: {result['score']:.4f}")

            print("\nSource Code:")
            print(result["content"])

    finally:
        retriever.close()