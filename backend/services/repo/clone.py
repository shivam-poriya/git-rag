import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MEDIA_REPOS_DIR = BASE_DIR / "media" / "repos"
MEDIA_REPOS_DIR.mkdir(parents=True, exist_ok=True)


def repo_exists(repo_url: str) -> bool:
    try:
        subprocess.run(
            ["git", "ls-remote", repo_url],
            capture_output=True,
            text=True,
            check=True
        )
        return True

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_repo_name(repo_url: str) -> str:
    return repo_url.split("/")[-1].replace(".git", "")


def clone_public(repo_url: str) -> Path:

    if not repo_exists(repo_url):
        raise ValueError("Repository does not exist or is inaccessible")

    repo_name = get_repo_name(repo_url)
    repo_path = MEDIA_REPOS_DIR / repo_name

    if repo_path.exists():
        return repo_path

    subprocess.run(
        ["git", "clone", repo_url, str(repo_path)],
        check=True
    )

    return repo_path

def clone_private(repo_url: str, token: str) -> Path:

    if not repo_exists(repo_url):
        raise ValueError("Repository does not exist or is inaccessible")

    repo_name = get_repo_name(repo_url)
    repo_path = MEDIA_REPOS_DIR / repo_name

    if repo_path.exists():
        return repo_path

    
    authenticated_url = repo_url.replace(
        "https://",
        f"https://{token}@"
    )

    subprocess.run(
        ["git", "clone", authenticated_url, str(repo_path)],
        check=True
    )

    return repo_path
