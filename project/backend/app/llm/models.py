from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Identity, Index, LargeBinary, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LlmProfile(Base):
    __tablename__ = "llm_profile"
    __table_args__ = (
        Index(
            "llm_profile_one_default",
            "is_default",
            unique=True,
            postgresql_where=text("is_default"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)
    preset: Mapped[str] = mapped_column(Text)  # zotgpt | openai | deepseek | custom
    base_url: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    api_key_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary)  # Fernet token
    api_key_hint: Mapped[str | None] = mapped_column(Text)  # last 4 characters
    share_results_with_llm: Mapped[bool] = mapped_column(server_default=text("false"))
    json_mode: Mapped[bool | None]  # NULL until tested
    is_default: Mapped[bool] = mapped_column(server_default=text("false"))
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    last_tested_at: Mapped[datetime | None]
    last_test_ok: Mapped[bool | None]
