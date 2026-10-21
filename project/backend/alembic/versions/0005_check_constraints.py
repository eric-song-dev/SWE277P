"""CHECK constraints on the enumerated text columns

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

# (table, column, allowed values). Nullable columns pass the check on NULL.
CHECKS = [
    ("import_file", "source", ("campusgroups", "twelvetwenty")),
    ("import_file", "status", ("pending", "committed")),
    ("event", "modality", ("In Person", "Virtual", "Hybrid")),
    ("person_identifier", "kind", ("netid", "email")),
    ("attendance", "match_method", ("netid", "email", "none")),
    ("llm_profile", "preset", ("zotgpt", "openai", "deepseek", "custom", "fake")),
    ("chat_turn", "kind", ("answer", "clarification", "error")),
    ("chat_turn", "analysis_source", ("llm", "local")),
]


def _name(table: str, column: str) -> str:
    return f"ck_{table}_{column}"


def upgrade() -> None:
    for table, column, values in CHECKS:
        allowed = ", ".join(f"'{v}'" for v in values)
        op.create_check_constraint(
            _name(table, column), table, f"{column} IN ({allowed})", schema="hub"
        )


def downgrade() -> None:
    for table, column, _values in reversed(CHECKS):
        op.drop_constraint(_name(table, column), table, schema="hub", type_="check")
