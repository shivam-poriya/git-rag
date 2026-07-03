from langchain_core.documents import Document

from services.repo.chunking.constants import (
    CODE_SPLIT_THRESHOLD,
    MARKDOWN_SPLIT_THRESHOLD,
    CONFIG_SPLIT_THRESHOLD,
    CONFIG_EXTENSIONS,
    MARKDOWN_EXTENSIONS,
    LANGUAGE_REGISTRY,
    SPLITTER_REGISTRY,
)

from services.repo.chunking.splitters.recursive_splitter import (
    split_recursive_document,
)


def should_skip_splitting(
    document: Document,
) -> bool:

    extension = (
        document.metadata
        .get("extension", "")
        .lower()
    )

    content_length = len(
        document.page_content
    )

    if extension in MARKDOWN_EXTENSIONS:
        return (
            content_length
            <= MARKDOWN_SPLIT_THRESHOLD
        )

    if extension in CONFIG_EXTENSIONS:
        return (
            content_length
            <= CONFIG_SPLIT_THRESHOLD
        )

    return (
        content_length
        <= CODE_SPLIT_THRESHOLD
    )


def chunk_documents(
    documents: list[Document],
) -> list[Document]:

    all_chunks = []

    for document in documents:

        extension = (
            document.metadata
            .get("extension", "")
            .lower()
        )

        language = LANGUAGE_REGISTRY.get(
            extension,
            "text"
        )

        document.metadata = {
            **document.metadata,
            "language": language,
        }

        #
        # Small file optimization
        #
        if should_skip_splitting(document):

            document.metadata = {
                **document.metadata,
                "chunk_index": 1,
                "chunk_count": 1,
            }

            all_chunks.append(document)
            continue

        #
        # Select splitter
        #
        splitter = SPLITTER_REGISTRY.get(
            extension,
            split_recursive_document
        )

        chunks = splitter(document)

        all_chunks.extend(chunks)

    return all_chunks