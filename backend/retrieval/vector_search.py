import uuid
from pathlib import Path
from typing import List, Dict, Optional

from qdrant_client import QdrantClient, models


class VectorSearch:

    def __init__(
        self,
        embedding_dimension: int = 384,
        collection_name: str = "repository_chunks"
    ):
        """
        Initialize Qdrant with persistent local storage.
        """

        self.embedding_dimension = embedding_dimension
        self.collection_name = collection_name

        storage_path = Path("data/qdrant_storage")
        storage_path.mkdir(parents=True, exist_ok=True)

        self.client = QdrantClient(
            path=str(storage_path)
        )

        self._create_collection()

    def _create_collection(self):
        """
        Create collection if it does not already exist.
        """

        if not self.client.collection_exists(self.collection_name):

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_dimension,
                    distance=models.Distance.COSINE
                )
            )

    def insert_chunks(
        self,
        chunks: List[Dict],
        embeddings,
        repository_id: str
    ):
        """
        Insert code chunks and their embeddings into Qdrant.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must match."
            )

        points = []

        for chunk, embedding in zip(chunks, embeddings):

            if len(embedding) != self.embedding_dimension:
                raise ValueError("Invalid embedding dimensions.")

            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "repository_id": repository_id,
                    "chunk_id": chunk["chunk_id"],
                    "file_path": chunk["file_path"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "language": chunk["language"],
                    "content": chunk["content"]
                }
            )

            points.append(point)

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )

        return len(points)

    def search(
        self,
        query_embedding,
        repository_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for similar code chunks within a specific repository.
        """

        if len(query_embedding) != self.embedding_dimension:
            raise ValueError("Invalid query embedding dimensions.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        if not repository_id:
            raise ValueError("Repository ID is required.")

        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="repository_id",
                        match=models.MatchValue(
                            value=repository_id
                        )
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )

        results = []

        for point in search_result.points:

            results.append({
                "score": point.score,
                "repository_id": point.payload["repository_id"],
                "chunk_id": point.payload["chunk_id"],
                "file_path": point.payload["file_path"],
                "start_line": point.payload["start_line"],
                "end_line": point.payload["end_line"],
                "language": point.payload["language"],
                "content": point.payload["content"]
            })

        return results

    def delete_repository(self, repository_id: str):
        """
        Delete all chunks belonging to a repository.
        """

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repository_id",
                            match=models.MatchValue(
                                value=repository_id
                            )
                        )
                    ]
                )
            ),
            wait=True
        )

    def close(self):
        """Close Qdrant client."""

        self.client.close()


if __name__ == "__main__":

    vector_db = VectorSearch(embedding_dimension=384)

    sample_chunks = [
        {
            "chunk_id": "chunk_1",
            "file_path": "backend/auth.py",
            "start_line": 10,
            "end_line": 20,
            "language": "python",
            "content": "def verify_token(req):\n    return validate(req)"
        }
    ]

    import numpy as np

    sample_embeddings = np.random.rand(1, 384).astype("float32")

    repository_id = "test_repository_123"

    inserted = vector_db.insert_chunks(
        chunks=sample_chunks,
        embeddings=sample_embeddings,
        repository_id=repository_id
    )

    print("Inserted points:", inserted)

    query_embedding = np.random.rand(384).astype("float32")

    results = vector_db.search(
        query_embedding=query_embedding,
        repository_id=repository_id,
        limit=5
    )

    for result in results:
        print(result)

    vector_db.close()