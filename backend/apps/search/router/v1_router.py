# apps/search/router/v1_router.py

from fastapi import APIRouter, Depends, HTTPException, status

from apps.custom_auth.oauth2 import get_current_user
from apps.db_models import Repository
from apps.search.router.models.v1_model import (
    SemanticSearchRequest,
    SearchResultItem,
)
from main import settings
from services.search.semantic_search import semantic_search

router = APIRouter()


@router.post(
    "/semantic/",
    response_model=list[SearchResultItem],
)
def semantic_search_endpoint(
    request: SemanticSearchRequest,
    current_user=Depends(get_current_user),
):
    """
    Perform semantic (vector) search over the user's repository chunks.

    - Embeds the query with the same model used at indexing time.
    - Queries the pgvector store using cosine similarity.
    - Optionally scoped to a single repository via `repo_id`.
    - Returns the top-k most relevant code chunks with similarity scores.
    """

    # If a repo_id is provided, verify the user owns that repository.
    if request.repo_id:

        session = settings.db.SessionLocal()

        try:
            repo = (
                session.query(Repository)
                .filter(
                    Repository.id == request.repo_id,
                    Repository.user_id == current_user.id,
                )
                .first()
            )

            if repo is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=(
                        f"Repository '{request.repo_id}' not found "
                        f"or does not belong to the current user."
                    ),
                )

            if repo.status != "completed":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Repository '{repo.repo_name}' is not ready yet "
                        f"(current status: {repo.status}). "
                        f"Please wait until processing is complete."
                    ),
                )

        finally:
            session.close()

    results = semantic_search(
        query=request.query,
        user_id=current_user.id,
        repo_id=request.repo_id,
        top_k=request.top_k,
    )

    return results
