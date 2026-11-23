import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from config import (
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_DIMENSION,
    REPOSITORIES_DIR
)
from database.storage import RepositoryStorage
from ingestion.github_loader import clone_repository, validate_github_url
from ingestion.file_filter import filter_repository_files
from ingestion.chunker import chunk_repository_files
from embeddings.embedder import CodeEmbedder
from retrieval.vector_search import VectorSearch

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
storage = RepositoryStorage()

# Shared singletons for indexing to avoid reloading model continuously
_embedder_instance = None
_vector_db_instance = None

def get_embedder():
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = CodeEmbedder(model_name=EMBEDDING_MODEL_NAME)
    return _embedder_instance

def get_vector_db():
    global _vector_db_instance
    if _vector_db_instance is None:
        _vector_db_instance = VectorSearch(embedding_dimension=EMBEDDING_DIMENSION)
    return _vector_db_instance


class IndexRepositoryRequest(BaseModel):
    repository_url: str

class RepositoryResponse(BaseModel):
    repository_id: str
    repository_name: str
    repository_url: str
    status: str
    total_files: int
    total_chunks: int
    languages: List[str]
    error_message: Optional[str] = None
    created_at: str
    indexed_at: Optional[str] = None

class FileContentResponse(BaseModel):
    file_path: str
    content: str
    total_lines: int
    start_line: Optional[int] = None
    end_line: Optional[int] = None


def index_repository_task(repository_id: str, repo_url: str):
    """
    Background worker that runs the complete ingestion and indexing pipeline:
    Clone -> Filter -> Chunk -> Embed -> Insert in Qdrant -> Update Status
    """
    try:
        storage.update_status(repository_id, status="indexing")

        # Step 1: Clone (or re-use)
        repo_data = clone_repository(repo_url)
        repo_path = repo_data["repository_path"]

        # Step 2: Filter files
        files = filter_repository_files(repo_path)
        if not files:
            storage.update_status(
                repository_id,
                status="failed",
                error_message="No eligible source files found in repository."
            )
            return

        # Step 3: Chunk files
        chunks = chunk_repository_files(
            file_paths=files,
            repository_path=repo_path,
            chunk_size=DEFAULT_CHUNK_SIZE,
            overlap=DEFAULT_CHUNK_OVERLAP
        )

        if not chunks:
            storage.update_status(
                repository_id,
                status="failed",
                error_message="No valid chunks could be created from source files."
            )
            return

        # Detect languages & file stats
        languages = sorted(list({c.get("language") for c in chunks if c.get("language")}))
        files_info = []
        chunks_by_file = {}
        for c in chunks:
            fp = c.get("file_path", "")
            chunks_by_file[fp] = chunks_by_file.get(fp, 0) + 1
        for fp, count in chunks_by_file.items():
            lang = next((c.get("language") for c in chunks if c.get("file_path") == fp), "")
            files_info.append({"file_path": fp, "language": lang, "chunk_count": count})

        storage.save_indexed_files(repository_id, files_info)

        # Step 4: Embed
        embedder = get_embedder()
        embeddings = embedder.generate_embeddings(chunks)

        # Step 5: Insert into Qdrant
        vector_db = get_vector_db()
        # Clean any old points for this repo ID first
        vector_db.delete_repository(repository_id)
        vector_db.insert_chunks(
            chunks=chunks,
            embeddings=embeddings,
            repository_id=repository_id
        )

        # Step 6: Mark ready
        storage.update_status(
            repository_id=repository_id,
            status="ready",
            total_files=len(files),
            total_chunks=len(chunks),
            languages=languages
        )
    except Exception as e:
        storage.update_status(
            repository_id=repository_id,
            status="failed",
            error_message=str(e)
        )


@router.get("", response_model=List[RepositoryResponse])
def list_repositories():
    """List all tracked repositories."""
    return storage.list_repositories()


@router.post("/index", response_model=Dict[str, Any])
def index_repository(
    request: IndexRepositoryRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger cloning and indexing of a GitHub repository.
    """
    url = request.repository_url.strip()
    if not validate_github_url(url):
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL.")

    # Check if repository is already indexed or exists
    existing = storage.get_repository_by_url(url)
    if existing and existing["status"] in ("ready", "indexing"):
        return {
            "message": f"Repository already {existing['status']}",
            "repository": existing
        }

    # Extract name and prepare record
    parsed_path = url.rstrip("/").split("/")
    repo_name = parsed_path[-1].replace(".git", "") if parsed_path else "repo"
    import uuid
    repo_id = existing["repository_id"] if existing else str(uuid.uuid4())
    local_path = str(REPOSITORIES_DIR / f"{repo_name}_{repo_id}")

    repo_record = storage.create_repository(
        repository_id=repo_id,
        repository_name=repo_name,
        repository_url=url,
        local_path=local_path,
        status="indexing"
    )

    # Launch background indexing
    background_tasks.add_task(index_repository_task, repo_id, url)

    return {
        "message": "Repository indexing started",
        "repository": repo_record
    }


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository_details(repository_id: str):
    """Get repository metadata and indexing status."""
    repo = storage.get_repository(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return repo


@router.get("/{repository_id}/file", response_model=FileContentResponse)
def get_repository_file_content(
    repository_id: str,
    path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None
):
    """
    Fetch source code for the interactive code viewer.
    """
    repo = storage.get_repository(repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found.")

    local_path = Path(repo["local_path"])
    # Prevent directory traversal
    target_file = (local_path / path).resolve()
    if not str(target_file).startswith(str(local_path.resolve())):
        raise HTTPException(status_code=400, detail="Invalid file path.")

    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        content = "".join(lines)
        return FileContentResponse(
            file_path=path,
            content=content,
            total_lines=len(lines),
            start_line=start_line,
            end_line=end_line
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
