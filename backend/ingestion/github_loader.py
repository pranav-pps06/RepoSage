import os
import re
import uuid
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from git import Repo, GitCommandError, Git

BASE_DIR = Path(__file__).resolve().parent.parent
REPOSITORY_DIR = BASE_DIR / "data" / "repositories"

MAX_REPOSITORY_SIZE = 100 * 1024 * 1024  # 100 MB
CLONE_TIMEOUT = 120  # seconds


def validate_github_url(url: str) -> bool:
    """Validate public GitHub repository URL."""

    try:
        parsed_url = urlparse(url)

        if parsed_url.scheme != "https":
            return False

        if parsed_url.netloc.lower() != "github.com":
            return False

        path_parts = parsed_url.path.strip("/").split("/")

        if len(path_parts) != 2:
            return False

        username, repository = path_parts

        if not re.fullmatch(r"[A-Za-z0-9-]+", username):
            return False

        repository = repository.removesuffix(".git")

        if not re.fullmatch(r"[A-Za-z0-9._-]+", repository):
            return False

        return True

    except Exception:
        return False


def extract_repository_name(url: str) -> str:
    """Extract repository name from GitHub URL."""

    path = urlparse(url).path.strip("/")
    repository_name = path.split("/")[-1]

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    return repository_name


def calculate_directory_size(directory: Path) -> int:
    """Calculate total repository size in bytes."""

    total_size = 0

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file

            if file_path.is_symlink():
                continue

            total_size += file_path.stat().st_size

    return total_size

def clone_repository(github_url: str) -> dict:

    if not validate_github_url(github_url):
        raise ValueError("Invalid GitHub repository URL.")

    repository_name = extract_repository_name(github_url)
    repository_id = str(uuid.uuid4())

    REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)

    clone_path = REPOSITORY_DIR / f"{repository_name}_{repository_id}"

    temp_path = Path(
        tempfile.mkdtemp(
            prefix=f"{repository_id}_",
            dir=REPOSITORY_DIR
        )
    )

    try:
        import subprocess

        Repo.clone_from(
            github_url,
            str(temp_path),
            depth=1,
            single_branch=True,
            no_tags=True,
            multi_options=[]
        )

        repository_size = calculate_directory_size(temp_path)

        if repository_size > MAX_REPOSITORY_SIZE:
            raise ValueError("Repository exceeds the 100 MB size limit.")

        temp_path.rename(clone_path)

        return {
            "repository_id": repository_id,
            "repository_name": repository_name,
            "repository_path": str(clone_path.resolve()),
            "size_bytes": repository_size,
            "status": "success"
        }

    except GitCommandError as error:
        raise RuntimeError(
            f"Failed to clone repository: {error}"
        ) from error

    except Exception:
        raise

    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)
    """
    Clone a public GitHub repository into a unique local directory.

    Returns:
        Dictionary containing repository ID, name and local path.
    """

    if not validate_github_url(github_url):
        raise ValueError("Invalid GitHub repository URL.")

    repository_name = extract_repository_name(github_url)

    repository_id = str(uuid.uuid4())

    REPOSITORY_DIR.mkdir(parents=True, exist_ok=True)

    clone_path = REPOSITORY_DIR / f"{repository_name}_{repository_id}"

    temp_path = Path(
        tempfile.mkdtemp(
            prefix=f"{repository_id}_",
            dir=REPOSITORY_DIR
        )
    )

    try:
        Git().clone(
            github_url,
            str(temp_path),
            depth=1,
            timeout=CLONE_TIMEOUT,
            single_branch=True,
            no_tags=True
        )

        repository_size = calculate_directory_size(temp_path)

        if repository_size > MAX_REPOSITORY_SIZE:
            raise ValueError("Repository exceeds the 100 MB size limit.")

        temp_path.rename(clone_path)

        return {
            "repository_id": repository_id,
            "repository_name": repository_name,
            "repository_path": str(clone_path.resolve()),
            "size_bytes": repository_size,
            "status": "success"
        }

    except GitCommandError as error:
        raise RuntimeError(
            f"Failed to clone repository: {error}"
        ) from error

    except Exception:
        raise

    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path, ignore_errors=True)


if __name__ == "__main__":

    github_url = "https://github.com/expressjs/express"

    try:
        result = clone_repository(github_url)
        print(result)

    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}")