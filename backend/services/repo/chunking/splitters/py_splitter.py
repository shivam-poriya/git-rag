from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)

from pathlib import Path


def split_python_document(
    document: Document,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> list[Document]:

    if not document.page_content.strip():
        return []

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.PYTHON,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_documents([document])

    total_chunks = len(chunks)

    for idx, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,
            "chunk_index": idx + 1,
            "chunk_count": total_chunks,
        }

    return chunks





################################

# file_path = Path(__file__).parent / "temp.py"

# document = Document(
#     page_content=file_path.read_text(
#         encoding="utf-8",
#         errors="ignore"
#     ),
#     metadata={
#         "repo_id": "test_repo",
#         "path": str(file_path),
#         "filename": file_path.name,
#         "extension": file_path.suffix,
#         "size": file_path.stat().st_size,
#     }
# )


# chunks = split_python_document(document)

# for chunk in chunks:
#     print("\n" + "=" * 80)
#     print(chunk.metadata)
#     print("=" * 80)
#     print(chunk.page_content)

# print(f"Total chunks: {len(chunks)}")

# for chunk in chunks:
#     print(
#         f"Chunk {chunk.metadata['chunk_index']}/"
#         f"{chunk.metadata['chunk_count']} "
#         f"Length: {len(chunk.page_content)}"
#     )