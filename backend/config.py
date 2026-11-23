import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(dotenv_path=BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Directory paths
DATA_DIR = BASE_DIR / "data"
REPOSITORIES_DIR = DATA_DIR / "repositories"
QDRANT_STORAGE_DIR = DATA_DIR / "qdrant_storage"
METADATA_DB_PATH = DATA_DIR / "reposage.db"
CONVERSATION_DB_PATH = DATA_DIR / "conversations.db"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
QDRANT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Model & Indexing Settings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
QDRANT_COLLECTION_NAME = "repository_chunks"

CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# Chunking defaults
DEFAULT_CHUNK_SIZE = 80
DEFAULT_CHUNK_OVERLAP = 10

# Retrieval defaults
SEMANTIC_TOP_K = 10
KEYWORD_TOP_K = 10
FUSION_TOP_K = 10
RRF_K = 60
RERANK_TOP_K = 6
