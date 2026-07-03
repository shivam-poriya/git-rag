# services/repo/db/store_chunks.py

from langchain_core.documents import Document

from main import settings
from apps.db_models import RepositoryChunk


def store_chunks(
    repo_id: str,
    chunks: list[Document],
    embeddings: list[list[float]],
):
    session = settings.db.SessionLocal()

    try:

        chunk_objects = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):

            chunk_objects.append(
                RepositoryChunk(
                    repo_id=repo_id,

                    path=chunk.metadata.get(
                        "path"
                    ),

                    filename=chunk.metadata.get(
                        "filename"
                    ),

                    extension=chunk.metadata.get(
                        "extension"
                    ),

                    language=chunk.metadata.get(
                        "language"
                    ),

                    chunk_index=chunk.metadata.get(
                        "chunk_index"
                    ),

                    chunk_count=chunk.metadata.get(
                        "chunk_count"
                    ),

                    content=chunk.page_content,

                    embedding=embedding,
                )
            )

        session.bulk_save_objects(
            chunk_objects
        )

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()