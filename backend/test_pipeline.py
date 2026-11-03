from ingestion.github_loader import clone_repository
from ingestion.file_filter import filter_repository_files
from ingestion.chunker import chunk_repository_files
from embeddings.embedder import CodeEmbedder
from retrieval.vector_search import VectorSearch
from retrieval.semantic_search import SemanticRetriever


REPOSITORY_URL = "https://github.com/expressjs/express"

QUESTIONS = [
    "Where is the authentication logic implemented?",
    "Which files interact with the database?",
    "Where is the application configuration stored?",
    "Where is the login function defined?",
    "What does the main entry point do?"
]


def main():

    print("\n========== STEP 1: CLONE REPOSITORY ==========")

    repository = clone_repository(REPOSITORY_URL)

    repository_id = repository["repository_id"]
    repository_path = repository["repository_path"]

    print("Repository:", repository["repository_name"])
    print("Repository ID:", repository_id)
    print("Repository Path:", repository_path)

    print("\n========== STEP 2: FILTER FILES ==========")

    files = filter_repository_files(repository_path)

    print("Eligible files:", len(files))

    for file in files[:10]:
        print(file)

    print("\n========== STEP 3: GENERATE CHUNKS ==========")

    chunks = chunk_repository_files(
        file_paths=files,
        repository_path=repository_path,
        chunk_size=80,
        overlap=10
    )

    print("Total chunks generated:", len(chunks))

    print("\n========== STEP 4: GENERATE EMBEDDINGS ==========")

    embedder = CodeEmbedder(
        model_name="all-MiniLM-L6-v2"
    )

    embeddings = embedder.generate_embeddings(chunks)

    print("Embedding shape:", embeddings.shape)

    print("\n========== STEP 5: INSERT INTO QDRANT ==========")

    vector_db = VectorSearch(
        embedding_dimension=384
    )

    inserted = vector_db.insert_chunks(
        chunks=chunks,
        embeddings=embeddings,
        repository_id=repository_id
    )

    print("Total vectors inserted:", inserted)

    vector_db.close()

    print("\n========== STEP 6: TEST SEMANTIC RETRIEVAL ==========")

    retriever = SemanticRetriever(top_k=10)

    try:

        for question in QUESTIONS:

            print("\n" + "=" * 80)
            print("QUESTION:", question)
            print("=" * 80)

            results = retriever.retrieve(
                question=question,
                repository_id=repository_id,
                limit=10
            )

            if not results:
                print("No relevant chunks found.")
                continue

            for index, result in enumerate(results, start=1):

                print("\n" + "-" * 60)

                print(f"Result #{index}")

                print(f"Similarity Score: {result['score']:.4f}")

                print(f"File Path: {result['file_path']}")

                print(
                    f"Line Numbers: "
                    f"{result['start_line']}-{result['end_line']}"
                )

                print(f"Language: {result['language']}")

                print("\nSource Code:")
                print(result["content"])

    finally:
        retriever.close()

    print("\n========== PIPELINE TEST COMPLETED ==========")


if __name__ == "__main__":
    main()