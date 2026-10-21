"""core schema

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0001"
down_revision = None
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
        "app_user",
        _id(),
        sa.Column("username", sa.Text, nullable=False, unique=True),
        sa.Column("display_name", sa.Text, nullable=False),
        _now("created_at"),
        schema=S,
    )
    op.create_table(
        "event",
        _id(),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("event_date", sa.Date),
        sa.Column("term", sa.Text, nullable=False),
        sa.Column("academic_year", sa.Text),
        sa.Column("modality", sa.Text),
        sa.Column("sponsors_hosts", sa.Text),
        sa.Column("event_type", sa.Text),
        sa.Column("on_campus_groups", sa.Boolean),
        sa.Column("attendance_source_note", sa.Text),
        sa.Column("student_worker", sa.Text),
        sa.Column("created_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id")),
        schema=S,
    )
    op.create_table(
        "import_file",
        _id(),
        sa.Column("file_name", sa.Text, nullable=False),
        sa.Column("file_sha256", sa.Text, nullable=False, unique=True),
        sa.Column("source", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("content", sa.LargeBinary, nullable=False),
        sa.Column("row_count", sa.Integer),
        sa.Column("skipped_count", sa.Integer),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey(f"{S}.event.id")),
        sa.Column("uploaded_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id"), nullable=False),
        _now("uploaded_at"),
        sa.Column("committed_at", sa.DateTime(timezone=True)),
        schema=S,
    )
    op.create_table("person", _id(), _now("created_at"), schema=S)
    op.create_table(
        "person_identifier",
        _id(),
        sa.Column("person_id", sa.BigInteger, sa.ForeignKey(f"{S}.person.id"), nullable=False),
        sa.Column("kind", sa.Text, nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.UniqueConstraint("kind", "value"),
        schema=S,
    )
    op.create_table(
        "attendance",
        _id(),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey(f"{S}.event.id"), nullable=False),
        sa.Column("person_id", sa.BigInteger, sa.ForeignKey(f"{S}.person.id")),
        sa.Column(
            "import_file_id", sa.BigInteger, sa.ForeignKey(f"{S}.import_file.id"), nullable=False
        ),
        sa.Column("source_row", sa.Integer),
        sa.Column("first_name", sa.Text),
        sa.Column("last_name", sa.Text),
        sa.Column("email", sa.Text),
        sa.Column("netid", sa.Text),
        sa.Column("student_id", sa.Text),
        sa.Column("affiliation", sa.Text),
        sa.Column("domestic_international", sa.Text),
        sa.Column("school", sa.Text),
        sa.Column("department", sa.Text),
        sa.Column("match_method", sa.Text, nullable=False),
        sa.Column("raw_row", JSONB),
        sa.UniqueConstraint("event_id", "person_id"),
        schema=S,
    )
    op.create_table(
        "data_quality_flag",
        _id(),
        sa.Column(
            "import_file_id", sa.BigInteger, sa.ForeignKey(f"{S}.import_file.id"), nullable=False
        ),
        sa.Column("attendance_id", sa.BigInteger, sa.ForeignKey(f"{S}.attendance.id")),
        sa.Column("source_row", sa.Integer),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("detail", sa.Text),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", sa.BigInteger, sa.ForeignKey(f"{S}.app_user.id")),
        schema=S,
    )

    op.execute("INSERT INTO hub.app_user (username, display_name) VALUES ('local', 'GPSRC Staff')")
    op.execute(
        """
        CREATE VIEW hub.attendance_view AS
        SELECT a.person_id AS person_key, e.name AS event_name, e.event_date, e.term,
               e.academic_year, e.modality, e.sponsors_hosts, e.event_type,
               CASE f.source WHEN 'campusgroups' THEN 'CampusGroups' ELSE '12twenty' END
                   AS platform,
               a.first_name, a.last_name, a.email, a.netid, a.affiliation,
               a.domestic_international, a.school, a.department
        FROM hub.attendance a
        JOIN hub.event e ON e.id = a.event_id
        JOIN hub.import_file f ON f.id = a.import_file_id
        """
    )
    op.execute("GRANT USAGE ON SCHEMA hub TO chatbot_ro")
    op.execute("GRANT SELECT ON hub.attendance_view TO chatbot_ro")


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS hub.attendance_view")
    for table in (
        "data_quality_flag",
        "attendance",
        "person_identifier",
        "person",
        "import_file",
        "event",
        "app_user",
    ):
        op.drop_table(table, schema=S)
