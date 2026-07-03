# apps/chat/router/v1_router.py

import json
import uuid
import traceback

from fastapi import APIRouter, Depends, HTTPException, status

from apps.custom_auth.oauth2 import get_current_user
from apps.db_models import ChatSession, ChatMessage, Repository
from apps.chat.router.models.v1_model import (
    CreateSessionRequest,
    SendMessageRequest,
    ChatSessionResponse,
    ChatMessageResponse,
    SendMessageResponse,
)
from main import settings
from services.chat.rag_chat import rag_chat

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _session_to_response(session: ChatSession, repo_name: str) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=str(session.id),
        name=session.name,
        repo_id=str(session.repo_id),
        repo_name=repo_name,
        message_count=len(session.messages) if session.messages else 0,
        created_at=session.created_at.isoformat() if session.created_at else "",
    )


def _message_to_response(msg: ChatMessage) -> ChatMessageResponse:
    try:
        sources = json.loads(msg.sources or "[]")
    except (json.JSONDecodeError, TypeError):
        sources = []

    return ChatMessageResponse(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        sources=sources,
        created_at=msg.created_at.isoformat() if msg.created_at else "",
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/session/",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    request: CreateSessionRequest,
    current_user=Depends(get_current_user),
):
    """
    Create a new chat session tied to a specific repository.
    The repository must be 'completed' and owned by the current user.
    """
    session_db = settings.db.SessionLocal()

    try:
        # Validate the repo exists, is owned by the user, and is ready
        repo = (
            session_db.query(Repository)
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
                    f"(status: {repo.status}). "
                    f"Please wait until indexing is complete."
                ),
            )

        chat_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            repo_id=request.repo_id,
            name=request.name,
        )

        session_db.add(chat_session)
        session_db.commit()
        session_db.refresh(chat_session)

        return ChatSessionResponse(
            id=str(chat_session.id),
            name=chat_session.name,
            repo_id=str(chat_session.repo_id),
            repo_name=repo.repo_name,
            message_count=0,
            created_at=chat_session.created_at.isoformat() if chat_session.created_at else "",
        )

    except HTTPException:
        raise

    except Exception as e:
        session_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat session: {str(e)}",
        )

    finally:
        session_db.close()


@router.get(
    "/sessions/",
    response_model=list[ChatSessionResponse],
)
def get_sessions(
    current_user=Depends(get_current_user),
):
    """
    List all chat sessions for the current user, newest first.
    """
    session_db = settings.db.SessionLocal()

    try:
        sessions = (
            session_db.query(ChatSession)
            .filter(ChatSession.user_id == current_user.id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

        result = []
        for s in sessions:
            repo = (
                session_db.query(Repository)
                .filter(Repository.id == s.repo_id)
                .first()
            )
            repo_name = repo.repo_name if repo else "Unknown Repository"

            message_count = (
                session_db.query(ChatMessage)
                .filter(ChatMessage.session_id == s.id)
                .count()
            )

            result.append(
                ChatSessionResponse(
                    id=str(s.id),
                    name=s.name,
                    repo_id=str(s.repo_id),
                    repo_name=repo_name,
                    message_count=message_count,
                    created_at=s.created_at.isoformat() if s.created_at else "",
                )
            )

        return result

    finally:
        session_db.close()


@router.get(
    "/session/{session_id}/messages/",
    response_model=list[ChatMessageResponse],
)
def get_messages(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """
    Load full message history for a chat session.
    Verifies the session belongs to the current user.
    """
    session_db = settings.db.SessionLocal()

    try:
        chat_session = (
            session_db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )

        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{session_id}' not found.",
            )

        messages = (
            session_db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        return [_message_to_response(m) for m in messages]

    finally:
        session_db.close()


@router.post(
    "/chat/",
    response_model=SendMessageResponse,
)
def send_message(
    request: SendMessageRequest,
    current_user=Depends(get_current_user),
):
    """
    Send a user message to the RAG chat pipeline.

    Steps:
    1. Validate session ownership.
    2. Persist the user message.
    3. Run rag_chat() — retrieves context from pgvector, calls Gemini.
    4. Persist the assistant message.
    5. Return both messages in the response.
    """
    session_db = settings.db.SessionLocal()

    try:
        # Validate session ownership
        chat_session = (
            session_db.query(ChatSession)
            .filter(
                ChatSession.id == request.session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )

        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{request.session_id}' not found.",
            )

        # Extract repo_id immediately before session commit expires the instance
        repo_id = str(chat_session.repo_id)

        # Persist user message
        user_msg = ChatMessage(
            session_id=request.session_id,
            role="user",
            content=request.message,
            sources="[]",
        )
        session_db.add(user_msg)
        session_db.commit()
        session_db.refresh(user_msg)

    except HTTPException:
        raise

    except Exception as e:
        session_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store user message: {str(e)}",
        )

    finally:
        session_db.close()

    # Run RAG pipeline (outside the DB session to avoid long-held connections)
    try:
        rag_result = rag_chat(
            query=request.message,
            repo_id=repo_id,
            session_id=request.session_id,
            user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM pipeline failed: {str(e)}",
        )

    # Persist assistant message
    session_db2 = settings.db.SessionLocal()

    try:
        assistant_msg = ChatMessage(
            session_id=request.session_id,
            role="assistant",
            content=rag_result["answer"],
            sources=json.dumps(rag_result["sources"]),
        )
        session_db2.add(assistant_msg)
        session_db2.commit()
        session_db2.refresh(assistant_msg)

        # Reload user_msg with created_at populated
        user_msg_fresh = (
            session_db2.query(ChatMessage)
            .filter(ChatMessage.id == user_msg.id)
            .first()
        )

        return SendMessageResponse(
            user_message=_message_to_response(user_msg_fresh),
            assistant_message=_message_to_response(assistant_msg),
        )

    except Exception as e:
        session_db2.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist assistant message: {str(e)}",
        )

    finally:
        session_db2.close()


@router.delete(
    "/session/{session_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """
    Delete a chat session and all its messages (cascade).
    """
    session_db = settings.db.SessionLocal()

    try:
        chat_session = (
            session_db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )

        if chat_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session '{session_id}' not found.",
            )

        session_db.delete(chat_session)
        session_db.commit()

    except HTTPException:
        raise

    except Exception as e:
        session_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}",
        )

    finally:
        session_db.close()
