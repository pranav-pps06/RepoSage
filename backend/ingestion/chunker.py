import uuid
from pathlib import Path
from typing import List, Dict

CHUNK_SIZE = 80
CHUNK_OVERLAP = 10

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql"
}


def detect_language(file_path: str) -> str:
    """Identify programming language from file extension."""

    extension = Path(file_path).suffix.lower()

    return LANGUAGE_MAP.get(extension, "text")


def read_file(file_path: str) -> List[str]:
    """Read source file while preserving line structure."""

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readlines()

    except UnicodeDecodeError:
        return []

    except OSError:
        return []


def create_chunks(
    file_path: str,
    repository_path: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Dict]:
    """
    Convert a source file into overlapping line-based chunks.

    Each chunk contains:
        chunk_id
        file_path
        language
        start_line
        end_line
        content
    """

    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be between 0 and chunk_size.")

    file_path = Path(file_path).resolve()
    repository_path = Path(repository_path).resolve()

    try:
        relative_path = file_path.relative_to(repository_path)
    except ValueError:
        raise ValueError("File must be inside the repository directory.")

    lines = read_file(str(file_path))

    # Handle empty or unreadable files
    if not lines:
        return []

    language = detect_language(str(file_path))

    chunks = []

    start = 0
    total_lines = len(lines)

    while start < total_lines:

        end = min(start + chunk_size, total_lines)

        chunk_content = "".join(lines[start:end])

        chunk = {
            "chunk_id": str(uuid.uuid4()),
            "file_path": relative_path.as_posix(),
            "language": language,
            "start_line": start + 1,
            "end_line": end,
            "content": chunk_content
        }

        chunks.append(chunk)

        if end == total_lines:
            break

        start = end - overlap

    return chunks


def chunk_repository_files(
    file_paths: List[str],
    repository_path: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[Dict]:
    """
    Process all eligible repository files and return their chunks.
    """

    all_chunks = []

    for file_path in file_paths:

        try:
            file_chunks = create_chunks(
                file_path=file_path,
                repository_path=repository_path,
                chunk_size=chunk_size,
                overlap=overlap
            )

            all_chunks.extend(file_chunks)

        except (ValueError, OSError) as error:
            print(f"Skipping {file_path}: {error}")

    return all_chunks


if __name__ == "__main__":

    repository_path = "data/repositories/express"

    from ingestion.file_filter import filter_repository_files

    files = filter_repository_files(repository_path)

    chunks = chunk_repository_files(
        file_paths=files,
        repository_path=repository_path
    )

    print(f"Total files processed: {len(files)}")
    print(f"Total chunks generated: {len(chunks)}")

    for chunk in chunks[:3]:
        print("\n----------------------------")
        print(chunk)