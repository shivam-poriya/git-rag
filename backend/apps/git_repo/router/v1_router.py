from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
import uuid
import os
import shutil

from apps.custom_auth.oauth2 import get_current_user
from apps.git_repo.router.models.v1_model import (
    RepoCloneRequest,
    RepoPrivateCloneRequest,
)

from services.repo.process import process_repo
from services.repo.db.store_repository import (
    store_repository,
)
from main import settings
from apps.db_models import Repository

router = APIRouter()


@router.post("/repo/clone/")
def clone_repo(
    request: RepoCloneRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):

    repo_id = str(uuid.uuid4())

    store_repository(
        repo_id=repo_id,
        user_id=current_user.id,
        repo_name="pending",
        repo_url=request.repo_url,
        embedding_model="models/gemini-embedding-001",
        total_files=0,
        total_chunks=0,
    )

    background_tasks.add_task(
        process_repo,
        repo_id=repo_id,
        repo_url=request.repo_url,
    )

    return {
        "status": "accepted",
        "repo_id": repo_id,
        "message": "Repository processing started.",
    }


@router.post("/repo/clone-private/")
def clone_private_repo(
    request: RepoPrivateCloneRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
):

    repo_id = str(uuid.uuid4())

    store_repository(
        repo_id=repo_id,
        user_id=current_user.id,
        repo_name="pending",
        repo_url=request.repo_url,
        embedding_model="models/gemini-embedding-001",
        total_files=0,
        total_chunks=0,
    )

    background_tasks.add_task(
        process_repo,
        repo_id=repo_id,
        repo_url=request.repo_url,
        token=request.token,
    )

    return {
        "status": "accepted",
        "repo_id": repo_id,
        "message": "Repository processing started.",
    }


@router.get("/repos/repositories")
def get_repos(
    current_user=Depends(get_current_user),
):

    session = settings.db.SessionLocal()
    try:
        repositories = (
            session.query(Repository)
            .filter(Repository.user_id == current_user.id)
            .all()
        )
        return [
            {
                "id": str(repo.id),
                "repo_name": repo.repo_name,
                "repo_url": repo.repo_url,
                "branch_name": repo.branch_name,
                "embedding_model": repo.embedding_model,
                "total_files": repo.total_files,
                "total_chunks": repo.total_chunks,
                "status": repo.status,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
            }
            for repo in repositories
        ]
    finally:
        session.close()


@router.delete(
    "/repos/repository/{repo_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_repo(
    repo_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete a repository, its vector chunks from the database, and its files on disk.
    """
    session = settings.db.SessionLocal()
    try:
        repo = (
            session.query(Repository)
            .filter(
                Repository.id == repo_id,
                Repository.user_id == current_user.id,
            )
            .first()
        )

        if repo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{repo_id}' not found.",
            )

        # Remove cloned folder on disk if it exists
        if repo.repo_name and repo.repo_name != "pending":
            repo_path = os.path.join("media", "repos", repo.repo_name)
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)

        session.delete(repo)
        session.commit()

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete repository: {str(e)}",
        )
    finally:
        session.close()
