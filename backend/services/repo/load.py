from pathlib import Path
from services.repo.collect import collect_files
from langchain_core.documents import Document


def load_files(
    files: list[Path],
    repo_id: str) -> list[Document]:

    documents = []

    for file_path in files:
        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if not content.strip():
                continue

            stat = file_path.stat()

            suffix = file_path.suffix.lower()
            if not suffix and file_path.name.startswith("."):
                suffix = file_path.name.lower()

            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "repo_id": repo_id,

                        # file information
                        "path": str(file_path),
                        "filename": file_path.name,
                        "extension": suffix,

                        # useful later
                        "size": stat.st_size,
                    }
                )
            )

        except Exception as e:
            print(f"Failed to read {file_path}: {e}")

    return documents

# files_c = collect_files("C:\\projects\\git-repo\\backend\\media\\repos\\langchain")
# loaded_file = load_files(files_c,"Demo-repo-id")
# print((loaded_file))