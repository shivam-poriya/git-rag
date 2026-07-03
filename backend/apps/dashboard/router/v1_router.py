from fastapi import APIRouter, Depends, HTTPException
from main import settings
from apps.custom_auth.oauth2 import get_current_user
from apps.db_models import Repository, RepositoryChunk

router = APIRouter()

@router.get("/stats")
def get_dashboard_stats(current_user=Depends(get_current_user)):
    """
    Fetch dashboard metrics for the logged-in user:
    1. Total repositories owned by the user.
    2. Total chunks stored in the vector store across all the user's repositories.
    3. Count of repositories currently in 'processing' status.
    """
    session = settings.db.SessionLocal()
    
    try:
        total_repositories = (
            session.query(Repository)
            .filter(Repository.user_id == current_user.id)
            .count()
        )
        
        repo_ids = [
            r[0] for r in session.query(Repository.id)
            .filter(Repository.user_id == current_user.id)
            .all()
        ]
        
        total_chunks = 0
        if repo_ids:
            total_chunks = (
                session.query(RepositoryChunk)
                .filter(RepositoryChunk.repo_id.in_(repo_ids))
                .count()
            )
            
        processing_repositories = (
            session.query(Repository)
            .filter(
                Repository.user_id == current_user.id,
                Repository.status == "processing"
            )
            .count()
        )
        
        return {
            "total_repositories": total_repositories,
            "total_chunks": total_chunks,
            "processing_repositories": processing_repositories
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching dashboard statistics: {str(e)}"
        )
        
    finally:
        session.close()
