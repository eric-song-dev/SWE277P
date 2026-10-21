"""llm_profile, conversation, and chat_turn

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

S = "hub"


def _id() -> sa.Column:
    return sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True)


def _now(name: str) -> sa.Column:
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "llm_profile",
        _id(),
        sa.Column("name", sa.Text, nullable=False, unique=True),
        sa.Column("preset", sa.Text, nullable=False),
        sa.Column("base_url", sa.Text, nullable=False),
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("api_key_ciphertext", sa.LargeBinary),
        sa.Column("api_key_hint", sa.Text),
        sa.Column("share_results_with_llm", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("json_mode", sa.Boolean),
        sa.Column("is_default", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id")),
        _now("created_at"),
        _now("updated_at"),
        sa.Column("last_tested_at", sa.DateTime(timezone=True)),
        sa.Column("last_test_ok", sa.Boolean),
        schema=S,
    )
    op.create_index(
        "llm_profile_one_default",
        "llm_profile",
        ["is_default"],
        unique=True,
        schema=S,
        postgresql_where=sa.text("is_default"),
    )
    op.create_table(
        "conversation",
        _id(),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id"), nullable=False),
        _now("created_at"),
        _now("updated_at"),
        schema=S,
    )
    op.create_table(
        "chat_turn",
        _id(),
        sa.Column(
            "conversation_id",
            sa.BigInteger,
            sa.ForeignKey(f"{S}.conversation.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seq", sa.Integer, nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("sql", sa.Text),
        sa.Column("interpretation", sa.Text),
        sa.Column("assumptions", JSONB),
        sa.Column("clarification_question", sa.Text),
        sa.Column("row_count", sa.Integer),
        sa.Column("truncated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("analysis_text", sa.Text),
        sa.Column("analysis_source", sa.Text),
        sa.Column("results_shared", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "llm_profile_id",
            sa.BigInteger,
            sa.ForeignKey(f"{S}.llm_profile.id", ondelete="SET NULL"),
        ),
        sa.Column("provider", sa.Text),
        sa.Column("model", sa.Text),
        sa.Column("prompt_version", sa.Text),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_code", sa.Text),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id"), nullable=False),
        _now("created_at"),
        sa.UniqueConstraint("conversation_id", "seq", name="chat_turn_conversation_seq_key"),
        schema=S,
    )


def downgrade() -> None:
    op.drop_table("chat_turn", schema=S)
    op.drop_table("conversation", schema=S)
    op.drop_index("llm_profile_one_default", table_name="llm_profile", schema=S)
    op.drop_table("llm_profile", schema=S)
