from typing import List, Dict
from sentence_transformers import CrossEncoder


class CodeReranker:
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k: int = 5
    ):
        self.model = CrossEncoder(model_name)
        self.top_k = top_k

    def rerank(
        self,
        question: str,
        retrieved_chunks: List[Dict]
    ) -> List[Dict]:

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if not retrieved_chunks:
            return []

        pairs = [
            [
                question,
                chunk["content"]
            ]
            for chunk in retrieved_chunks
        ]

        scores = self.model.predict(
            pairs,
            batch_size=16,
            show_progress_bar=False
        )

        reranked_chunks = []

        for chunk, score in zip(retrieved_chunks, scores):
            reranked_chunks.append({
                **chunk,
                "rerank_score": float(score)
            })

        reranked_chunks.sort(
            key=lambda chunk: chunk["rerank_score"],
            reverse=True
        )

        return reranked_chunks[:self.top_k]


if __name__ == "__main__":

    question = "Explain the JWT authentication process."

    retrieved_chunks = [
        {
            "chunk_id": "chunk_1",
            "file_path": "controllers/login.py",
            "start_line": 10,
            "end_line": 30,
            "language": "python",
            "content": """
            def login(username, password):
                user = authenticate(username, password)
                token = jwt.encode({"user_id": user.id}, SECRET_KEY)
                return {"access_token": token}
            """
        },
        {
            "chunk_id": "chunk_2",
            "file_path": "controllers/register.py",
            "start_line": 5,
            "end_line": 25,
            "language": "python",
            "content": """
            def register(username, password):
                user = User(username=username, password=hash_password(password))
                database.add(user)
                return user
            """
        },
        {
            "chunk_id": "chunk_3",
            "file_path": "middleware/auth.py",
            "start_line": 1,
            "end_line": 25,
            "language": "python",
            "content": """
            def verify_token(token):
                try:
                    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                    return payload["user_id"]
                except jwt.InvalidTokenError:
                    raise UnauthorizedError()
            """
        },
        {
            "chunk_id": "chunk_4",
            "file_path": "components/dashboard.jsx",
            "start_line": 1,
            "end_line": 20,
            "language": "javascript",
            "content": """
            function Dashboard() {
                return <h1>Welcome to Dashboard</h1>;
            }
            """
        },
        {
            "chunk_id": "chunk_5",
            "file_path": "database/connection.py",
            "start_line": 1,
            "end_line": 20,
            "language": "python",
            "content": """
            def connect_database():
                return create_engine(DATABASE_URL)
            """
        }
    ]

    reranker = CodeReranker(top_k=5)

    results = reranker.rerank(
        question=question,
        retrieved_chunks=retrieved_chunks
    )

    print("\nReranked Results:\n")

    for rank, chunk in enumerate(results, start=1):
        print(f"Rank: {rank}")
        print(f"File: {chunk['file_path']}")
        print(
            f"Lines: {chunk['start_line']}-{chunk['end_line']}"
        )
        print(f"Rerank Score: {chunk['rerank_score']:.4f}")
        print("-" * 60)