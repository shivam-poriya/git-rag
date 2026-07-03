from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)


def split_java_document(
    document: Document,
    chunk_size: int = 1500,
    chunk_overlap: int = 200,
) -> list[Document]:

    if not document.page_content.strip():
        return []

    splitter = RecursiveCharacterTextSplitter.from_language(
        language=Language.JAVA,
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