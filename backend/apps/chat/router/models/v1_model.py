# apps/chat/router/models/v1_model.py

from typing import Optional
from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):

    name: str = Field(
        ...,
        description="Display name for this chat session.",
        min_length=1,
        max_length=255,
    )

    repo_id: str = Field(
        ...,
        description="UUID of the repository this chat is scoped to.",
    )


class SendMessageRequest(BaseModel):

    session_id: str = Field(
        ...,
        description="UUID of the active chat session.",
    )

    message: str = Field(
        ...,
        description="The user's question or message.",
        min_length=1,
    )


class ChatSessionResponse(BaseModel):

    id: str
    name: str
    repo_id: str
    repo_name: Optional[str] = None
    message_count: int
    created_at: str


class ChatMessageResponse(BaseModel):

    id: int
    role: str
    content: str
    sources: list[str]
    created_at: str


class SendMessageResponse(BaseModel):

    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
