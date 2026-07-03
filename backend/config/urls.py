from fastapi import APIRouter
from apps.custom_auth.router.v1_router import router as custom_auth_v1_router
from apps.git_repo.router.v1_router import router as git_repo_v1_router
from apps.dashboard.router.v1_router import router as dashboard_v1_router
from apps.search.router.v1_router import router as search_v1_router
from apps.chat.router.v1_router import router as chat_v1_router

urls_router = APIRouter()

# Include version 1 routers
urls_router.include_router(custom_auth_v1_router, prefix="/v1/custom-auth")
urls_router.include_router(git_repo_v1_router, prefix="/v1/git-repo")
urls_router.include_router(dashboard_v1_router, prefix="/v1/dashboard")
urls_router.include_router(search_v1_router, prefix="/v1/search")
urls_router.include_router(chat_v1_router, prefix="/v1/chat")

