from langchain_core.documents import Document
# pyrefly: ignore [missing-import]
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def split_markdown_document(
    document: Document,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> list[Document]:

    if not document.page_content.strip():
        return []

    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
        ("#####", "h5"),
        ("######", "h6"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    header_docs = markdown_splitter.split_text(
        document.page_content
    )

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []

    for header_doc in header_docs:

        merged_metadata = {
            **document.metadata,
            **header_doc.metadata,
        }

        section_parts = []

        for level in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if level in merged_metadata:
                section_parts.append(
                    merged_metadata[level]
                )

        if section_parts:
            merged_metadata["section_path"] = (
                " > ".join(section_parts)
            )

        header_doc.metadata = merged_metadata

        chunks.extend(
            recursive_splitter.split_documents(
                [header_doc]
            )
        )

    total_chunks = len(chunks)

    for idx, chunk in enumerate(chunks):
        chunk.metadata = {
            **chunk.metadata,
            "chunk_index": idx + 1,
            "chunk_count": total_chunks,
        }

    return chunks