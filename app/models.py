
import enum

from pgvector.sqlalchemy import Vector
from app.core.config import EMBEDDING_DIMENSIONS
from sqlalchemy import (
    Boolean,
    Enum,
    Integer,
    JSON,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    faqs: Mapped[list["FAQ"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    memberships: Mapped[list["OrganizationMembership"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    chatbots: Mapped[list["Chatbot"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    knowledge_sources: Mapped[list["KnowledgeSource"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )


class MemberRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"
    MEMBER = "member"


# Higher index = more privilege. Used for role comparisons.
ROLE_ORDER = {
    MemberRole.OWNER: 3,
    MemberRole.ADMIN: 2,
    MemberRole.AGENT: 1,
    MemberRole.MEMBER: 0,
}


class OrganizationMembership(Base):
    __tablename__ = "organization_memberships"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole, native_enum=False, length=20),
        nullable=False,
        default=MemberRole.MEMBER
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "organization_id",
            name="uq_membership_user_org"
        ),
    )

    user: Mapped["User"] = relationship()
    organization: Mapped["Organization"] = relationship(
        back_populates="memberships"
    )

    @property
    def email(self) -> str | None:
        return self.user.email if self.user else None

    @property
    def full_name(self) -> str | None:
        return self.user.full_name if self.user else None


class Chatbot(Base):
    __tablename__ = "chatbots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    # Public identifier embedded in the widget script tag.
    # Random and unguessable — NOT an authentication secret.
    public_widget_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    welcome_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Widget appearance/behavior config, e.g.
    # {"primary_color": "#4f46e5", "position": "bottom-right"}
    branding: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    # Domains allowed to embed the widget, e.g. ["example.com"]
    allowed_domains: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="chatbots"
    )


class ProcessingStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    # Optional: scope the source to a single chatbot.
    # NULL means it is available to all chatbots in the org.
    chatbot_id: Mapped[int | None] = mapped_column(
        ForeignKey("chatbots.id"),
        nullable=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False, length=20),
        default=ProcessingStatus.PENDING,
        nullable=False
    )

    chunk_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="knowledge_sources"
    )
    chatbot: Mapped["Chatbot"] = relationship()
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    chatbot_id: Mapped[int | None] = mapped_column(
        ForeignKey("chatbots.id"),
        nullable=True,
        index=True
    )

    knowledge_source_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_sources.id"),
        nullable=False,
        index=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # Embedding vector for semantic search. Dimension must match
    # EMBEDDING_DIMENSIONS in config (1536 for text-embedding-3-small).
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    source: Mapped["KnowledgeSource"] = relationship(
        back_populates="chunks"
    )


class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    WAITING_HUMAN = "waiting_human"
    HUMAN = "human"
    CLOSED = "closed"


class SenderType(enum.Enum):
    CUSTOMER = "customer"
    AI = "ai"
    AGENT = "agent"
    SYSTEM = "system"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # Unguessable public identifier used in widget API URLs.
    public_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    chatbot_id: Mapped[int] = mapped_column(
        ForeignKey("chatbots.id"),
        nullable=False,
        index=True
    )

    # Identifier the widget generates for the visitor's browser.
    customer_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, native_enum=False, length=20),
        default=ConversationStatus.ACTIVE,
        nullable=False
    )

    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    organization: Mapped["Organization"] = relationship()
    chatbot: Mapped["Chatbot"] = relationship()
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.id",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )

    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType, native_enum=False, length=20),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Extra data: sources, handoff flags, etc.
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True
    )

    # Internal notes are visible to agents only, never to customers.
    is_internal: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )


class FAQ(Base):
    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"),
        nullable=False,
        index=True
    )

    question: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="faqs"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    full_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # SHA-256 hash of the token. The raw token is never stored.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    expires_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    revoked_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens"
    )
