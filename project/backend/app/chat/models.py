from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Identity, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str | None] = mapped_column(Text)  # NULL until the first question
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ChatTurn(Base):
    __tablename__ = "chat_turn"
    __table_args__ = (
        UniqueConstraint("conversation_id", "seq", name="chat_turn_conversation_seq_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hub.conversation.id", ondelete="CASCADE")
    )
    seq: Mapped[int]
    question: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)  # answer | clarification | error
    sql: Mapped[str | None] = mapped_column(Text)
    interpretation: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[Any | None] = mapped_column(JSONB)
    clarification_question: Mapped[str | None] = mapped_column(Text)
    row_count: Mapped[int | None]
    truncated: Mapped[bool] = mapped_column(server_default=text("false"))
    analysis_text: Mapped[str | None] = mapped_column(Text)
    analysis_source: Mapped[str | None] = mapped_column(Text)  # llm | local
    results_shared: Mapped[bool] = mapped_column(server_default=text("false"))
    llm_profile_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("hub.llm_profile.id", ondelete="SET NULL")
    )
    provider: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(server_default=text("0"))
    error_code: Mapped[str | None] = mapped_column(Text)
    latency_ms: Mapped[int | None]
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
