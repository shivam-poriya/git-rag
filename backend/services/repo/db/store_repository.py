# services/repo/database/store_repository.py

# pyrefly: ignore [missing-import]
from apps.db_models import Repository
from main import settings
from services.repo.chunking.constants import STATUS_PROCESSING


def store_repository(
    repo_id,
    user_id,
    repo_name,
    repo_url,
    embedding_model,
    total_files,
    total_chunks,
    branch_name=None,
):

    session = settings.db.SessionLocal()

    try:

        repository = Repository(
            id=repo_id,
            user_id=user_id,
            repo_name=repo_name,
            repo_url=repo_url,
            branch_name=branch_name,
            embedding_model=embedding_model,
            total_files=total_files,
            total_chunks=total_chunks,
            status=STATUS_PROCESSING,
        )

        session.add(repository)

        session.commit()

        session.refresh(repository)

        return repository

    finally:
        session.close()