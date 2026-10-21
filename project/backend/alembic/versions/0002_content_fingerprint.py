"""content fingerprint on import_file

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa

from alembic import op

# The app's own reader, so backfilled fingerprints are exactly what preview computes for the same
# file. If read_grid or content_fingerprint ever change their output, add a migration that
# recomputes content_sha256 for every row.
from app.errors import HubError
from app.imports.reader import content_fingerprint, read_grid

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

S = "hub"


def _backfill() -> None:
    conn = op.get_bind()
    ids = conn.execute(sa.text("SELECT id FROM hub.import_file ORDER BY id")).scalars().all()
    for import_id in ids:  # one row at a time: content is up to 10 MB per file
        row = conn.execute(
            sa.text("SELECT file_name, content, file_sha256 FROM hub.import_file WHERE id = :id"),
            {"id": import_id},
        ).one()
        try:
            fingerprint = content_fingerprint(read_grid(row.file_name, bytes(row.content)))
        except HubError:
            # Cannot happen for rows that passed preview; fall back to byte identity.
            fingerprint = row.file_sha256
        conn.execute(
            sa.text("UPDATE hub.import_file SET content_sha256 = :fp WHERE id = :id"),
            {"fp": fingerprint, "id": import_id},
        )


def upgrade() -> None:
    op.add_column("import_file", sa.Column("content_sha256", sa.Text), schema=S)
    _backfill()
    op.alter_column("import_file", "content_sha256", nullable=False, schema=S)
    op.create_unique_constraint(
        "import_file_content_sha256_key", "import_file", ["content_sha256"], schema=S
    )


def downgrade() -> None:
    op.drop_constraint("import_file_content_sha256_key", "import_file", schema=S)
    op.drop_column("import_file", "content_sha256", schema=S)
