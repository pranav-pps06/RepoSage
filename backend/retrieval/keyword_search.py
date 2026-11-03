import re
from typing import List, Dict

from rank_bm25 import BM25Okapi


class KeywordSearch:

    def __init__(self):
        """
        Initialize BM25 keyword search.
        """

        self.chunks = []
        self.bm25 = None
        self.tokenized_corpus = []

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize code while preserving identifiers.

        Example:
        verifyToken -> verifytoken
        """

        # Split camelCase identifiers
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

        # Extract identifiers, numbers and keywords
        tokens = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*|\d+", text)

        return [token.lower() for token in tokens]

    def build_index(self, chunks: List[Dict]):
        """
        Build BM25 index from repository code chunks.
        """

        if not chunks:
            raise ValueError("No chunks provided to build BM25 index.")

        self.chunks = chunks

        self.tokenized_corpus = [
            self.tokenize(chunk["content"])
            for chunk in chunks
        ]

        self.bm25 = BM25Okapi(self.tokenized_corpus)

        print(f"BM25 index created with {len(chunks)} chunks.")

    def search(
        self,
        query: str,
        repository_id: str = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search indexed code chunks using BM25.
        """

        if self.bm25 is None:
            raise ValueError("BM25 index has not been created.")

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")

        query_tokens = self.tokenize(query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        results = []

        for index, score in enumerate(scores):

            chunk = self.chunks[index]

            # Repository-specific filtering
            if repository_id is not None:
                if chunk.get("repository_id") != repository_id:
                    continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "repository_id": chunk.get("repository_id"),
                "file_path": chunk["file_path"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "language": chunk["language"],
                "content": chunk["content"],
                "bm25_score": float(score)
            })

        # Sort by BM25 score in descending order
        results.sort(
            key=lambda item: item["bm25_score"],
            reverse=True
        )

        return results[:top_k]


if __name__ == "__main__":

    sample_chunks = [
        {
            "chunk_id": "chunk_1",
            "repository_id": "repo_123",
            "file_path": "backend/auth.py",
            "start_line": 10,
            "end_line": 30,
            "language": "python",
            "content": """
            def verifyToken(token):
                return jwt.decode(token, SECRET_KEY)
            """
        },
        {
            "chunk_id": "chunk_2",
            "repository_id": "repo_123",
            "file_path": "backend/login.py",
            "start_line": 5,
            "end_line": 25,
            "language": "python",
            "content": """
            def login_user(username, password):
                return authenticate(username, password)
            """
        },
        {
            "chunk_id": "chunk_3",
            "repository_id": "repo_456",
            "file_path": "backend/database.py",
            "start_line": 1,
            "end_line": 20,
            "language": "python",
            "content": """
            def connect_database():
                pass
            """
        }
    ]

    keyword_search = KeywordSearch()

    # Build BM25 index
    keyword_search.build_index(sample_chunks)

    # Search query
    query = "Where is verifyToken implemented?"

    results = keyword_search.search(
        query=query,
        repository_id="repo_123",
        top_k=10
    )

    print(f"\nQuery: {query}")

    for index, result in enumerate(results, start=1):

        print("\n" + "=" * 50)
        print(f"Result: {index}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"File: {result['file_path']}")
        print(
            f"Lines: {result['start_line']}-{result['end_line']}"
        )
        print(f"BM25 Score: {result['bm25_score']:.4f}")
        print("\nCode:")
        print(result["content"])