import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.auth.models import AppUser

VIEW_COLUMNS = [
    "person_key", "event_name", "event_date", "term", "academic_year", "modality",
    "sponsors_hosts", "event_type", "platform", "first_name", "last_name", "email", "netid",
    "affiliation", "domestic_international", "school", "department",
]  # fmt: skip


def test_view_has_exact_columns(db_session):
    cols = (
        db_session.execute(
            text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='hub' "
                "AND table_name='attendance_view' ORDER BY ordinal_position"
            )
        )
        .scalars()
        .all()
    )
    assert cols == VIEW_COLUMNS


def test_local_user_is_seeded(db_session):
    assert db_session.scalar(select(AppUser.username)) == "local"


def test_chatbot_ro_can_select_view(chatbot_engine):
    with chatbot_engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM attendance_view")).scalar() == 0


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM hub.attendance",
        "SELECT * FROM hub.app_user",
        "SELECT * FROM hub.import_file",
        "INSERT INTO hub.event(name, term) VALUES ('x','Fall 2026')",
    ],
)
def test_chatbot_ro_cannot_touch_tables(chatbot_engine, sql):
    with chatbot_engine.connect() as c, pytest.raises(DBAPIError):
        c.execute(text(sql))
