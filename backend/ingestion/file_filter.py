import os
from pathlib import Path

# Supported source file extensions
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".html", ".css", ".json",
    ".md", ".yaml", ".yml", ".sql"
}

# Directories to ignore
IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    "coverage",
    ".next",
    ".pytest_cache",
    ".mypy_cache",
    "target",
    "vendor"
}

# Files to ignore
IGNORED_FILES = {
    ".env",
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml"
}

# Maximum allowed file size (1 MB)
MAX_FILE_SIZE = 1 * 1024 * 1024

# Secret-related patterns
SECRET_PATTERNS = [
    ".env",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".crt",
    ".cer",
    ".secret",
    ".secrets",
    "id_rsa",
    "id_ed25519",
    "credentials",
    "secrets",
]


def is_binary_file(file_path: Path) -> bool:
    """Check whether a file contains binary data."""

    try:
        with open(file_path, "rb") as file:
            chunk = file.read(8192)

            if b"\0" in chunk:
                return True

            try:
                chunk.decode("utf-8")
                return False
            except UnicodeDecodeError:
                return True

    except OSError:
        return True


def is_secret_file(file_path: Path) -> bool:
    """Check whether a file is likely to contain secrets."""

    name = file_path.name.lower()

    if name == ".env" or name.startswith(".env."):
        return True

    if name in IGNORED_FILES:
        return True

    if any(pattern in name for pattern in SECRET_PATTERNS):
        return True

    return False


def is_valid_file(file_path: Path) -> bool:
    """Check whether a file is eligible for indexing."""

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False

    if is_secret_file(file_path):
        return False

    try:
        if file_path.is_symlink() or not file_path.is_file():
            return False

        if file_path.stat().st_size > MAX_FILE_SIZE:
            return False

        if is_binary_file(file_path):
            return False

        return True

    except OSError:
        return False


def filter_repository_files(repository_path: str) -> list:
    """
    Traverse repository and return eligible source files.

    Args:
        repository_path: Local path of cloned repository.

    Returns:
        List of eligible file paths.
    """

    repository_path = Path(repository_path).resolve()

    if not repository_path.exists() or not repository_path.is_dir():
        raise ValueError("Invalid repository directory.")

    eligible_files = []

    for root, dirs, files in os.walk(repository_path, followlinks=False):

        # Ignore unwanted directories
        dirs[:] = [
            directory for directory in dirs
            if directory not in IGNORED_DIRECTORIES
            and not directory.startswith(".")
            and not (Path(root) / directory).is_symlink()
        ]

        for filename in files:

            file_path = Path(root) / filename

            if is_valid_file(file_path):
                eligible_files.append(str(file_path))

    return eligible_files


if __name__ == "__main__":

    repository_path = "data/repositories/express"

    try:
        files = filter_repository_files(repository_path)

        print(f"Total eligible files: {len(files)}")

        for file in files:
            print(file)

    except ValueError as error:
        print(f"Error: {error}")