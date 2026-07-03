from pathlib import Path

IGNORED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".cache",
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".class",
    ".jar",
    ".pyc",
}


def collect_files(repo_path: Path) -> list[Path]:

    repo_path = Path(repo_path)

    files_to_process = []

    for file_path in repo_path.rglob("*"):

        # Skip directories
        if not file_path.is_file():
            continue

        # Skip ignored folders
        if any(part in IGNORED_DIRS for part in file_path.parts):
            continue

        # Skip binary files
        if file_path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        # Skip huge files (> 2 MB)
        try:
            if file_path.stat().st_size > 2 * 1024 * 1024:
                continue
        except OSError:
            continue

        files_to_process.append(file_path)

    return files_to_process

# files_c = collect_files("C:\\projects\\git-repo\\backend\\media\\repos\\Spoon-Knife")
# print(files_c)