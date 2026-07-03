# services/repo/db/update_repository_metadata.py

from main import settings
from apps.db_models import Repository


def update_repository_metadata(
    repo_id: str,
    repo_name: str,
    total_files: int,
    total_chunks: int,
):
    session = settings.db.SessionLocal()

    try:

        repository = (
            session.query(Repository)
            .filter(
                Repository.id == repo_id
            )
            .first()
        )

        if repository is None:
            raise ValueError(
                f"Repository {repo_id} not found."
            )

        repository.repo_name = repo_name
        repository.total_files = total_files
        repository.total_chunks = total_chunks

        session.commit()

        session.refresh(
            repository
        )

        return repository

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()