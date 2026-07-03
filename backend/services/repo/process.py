from pathlib import Path

from services.repo.clone import (
    clone_public,
    clone_private,
)

from services.repo.collect import collect_files
from services.repo.load import load_files

from services.repo.chunking.splitter_router import (
    chunk_documents,
)

from services.repo.embeddings.embed_chunks import (
    generate_embeddings,
)

from services.repo.db.store_repository import (
    store_repository,
)

from services.repo.db.store_chunks import (
    store_chunks,
)

from services.repo.db.update_repository_status import (
    update_repository_status,
)

from services.repo.chunking.constants import (
    STATUS_COMPLETED,
    STATUS_FAILED,
)

from services.repo.db.update_repository_metadata import (
    update_repository_metadata,
)

def process_repo(
    repo_id: str,
    repo_url: str,
    token: str = None,
):

    try:


        if token is None:
            path = clone_public(repo_url)
        else:
            path = clone_private(
                repo_url,
                token,
            )

        files = collect_files(path)

        docs = load_files(
            files,
            repo_id,
        )

        chunks = chunk_documents(
            docs,
        )

        repo_name = Path(path).name

        update_repository_metadata(
            repo_id=repo_id,
            repo_name=repo_name,
            total_files=len(files),
            total_chunks=len(chunks),
        )

        embeddings = generate_embeddings(
            chunks,
        )


        store_chunks(
            repo_id=repo_id,
            chunks=chunks,
            embeddings=embeddings,
        )

        update_repository_status(
            repo_id,
            STATUS_COMPLETED,
        )

    except Exception as e:

        print(
            f"Repository processing failed: {e}"
        )

        try:

            update_repository_status(
                repo_id,
                STATUS_FAILED,
            )

        except Exception:
            pass

        raise