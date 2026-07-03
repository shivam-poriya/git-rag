from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime,BigInteger
from sqlalchemy.sql import func

from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(70), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    address = Column(String(255), default="")
    first_name = Column(String(70), default="")
    last_name = Column(String(70), default="")
    organization_name = Column(String(70), default="")
    location = Column(String(70), default="")
    phone = Column(String(70), nullable=True)
    birthday = Column(String(70), default="")
    profile_photo = Column(String(255), nullable=True)


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    repo_name = Column(
        String(255),
        nullable=False,
    )

    repo_url = Column(
        Text,
        nullable=False,
    )

    branch_name = Column(
        String(255),
        nullable=True,
    )

    embedding_model = Column(
        String(100),
        nullable=False,
    )

    total_files = Column(
        Integer,
        default=0,
    )

    total_chunks = Column(
        Integer,
        default=0,
    )

    status = Column(
        String(30),
        default="processing",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class RepositoryChunk(Base):
    __tablename__ = "repository_chunks"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    repo_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "repositories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    path = Column(
        Text,
        nullable=False,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    extension = Column(
        String(50),
    )

    language = Column(
        String(50),
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    chunk_count = Column(
        Integer,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    embedding = Column(
        Vector(3072),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    repo_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "repositories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    # JSON-serialised list of source file paths, e.g. '["src/main.py"]'
    sources = Column(
        Text,
        nullable=True,
        default="[]",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )

