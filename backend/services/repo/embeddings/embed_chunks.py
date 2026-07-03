from langchain_core.documents import Document

from services.repo.embeddings.embedding_model import embedding_model

def generate_embeddings(
    chunks: list[Document],
    batch_size: int = 100,
):
    all_embeddings = []

    total_batches = (
        len(chunks) + batch_size - 1
    ) // batch_size

    for i in range(
        0,
        len(chunks),
        batch_size,
    ):

        batch = chunks[i:i + batch_size]

        print(
            f"Batch "
            f"{i // batch_size + 1}"
            f"/{total_batches}"
        )

        texts = [
            chunk.page_content
            for chunk in batch
        ]

        embeddings = (
            embedding_model
            .embed_documents(texts)
        )

        all_embeddings.extend(
            embeddings
        )

    return all_embeddings