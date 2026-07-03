# services/repo/db/update_repository_status.py

from main import settings
from apps.db_models import Repository



def update_repository_status(
    repo_id: str,
    status: str,
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

        repository.status = status

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()