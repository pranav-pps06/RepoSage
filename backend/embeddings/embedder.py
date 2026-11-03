from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class CodeEmbedder:

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Load the embedding model once.
        """

        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()

    def generate_embeddings(self, chunks: List[dict]) -> np.ndarray:
        """
        Generate embeddings for a list of code chunks.
        """

        if not chunks:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        texts = [chunk["content"] for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        if embeddings.shape[1] != self.embedding_dimension:
            raise ValueError("Embedding dimensions are inconsistent.")

        return embeddings

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a user query.
        Uses the same model as code chunk embeddings.
        """

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        embedding = self.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        if len(embedding) != self.embedding_dimension:
            raise ValueError("Embedding dimensions are inconsistent.")

        return embedding


if __name__ == "__main__":

    embedder = CodeEmbedder()

    sample_chunks = [
        {
            "chunk_id": "1",
            "content": "def verify_token(req):\n    return validate(req)"
        },
        {
            "chunk_id": "2",
            "content": "class User:\n    def __init__(self, name):\n        self.name = name"
        }
    ]

    embeddings = embedder.generate_embeddings(sample_chunks)

    print("Number of embeddings:", len(embeddings))
    print("Embedding dimensions:", embeddings.shape[1])

    query = "How is user authentication handled?"

    query_embedding = embedder.generate_query_embedding(query)

    print("Query embedding dimensions:", query_embedding.shape)