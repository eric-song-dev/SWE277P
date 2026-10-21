"""conversation.title is NULL until the first question

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation", "title", existing_type=sa.Text, nullable=True, schema="hub")


def downgrade() -> None:
    op.execute("UPDATE hub.conversation SET title = '' WHERE title IS NULL")
    op.alter_column("conversation", "title", existing_type=sa.Text, nullable=False, schema="hub")
