import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.auth.models import AppUser
from app.llm.models import LlmProfile

INSUFFICIENT_PRIVILEGE = "42501"
READ_ONLY_TRANSACTION = "25006"  # default_transaction_read_only is checked before privileges

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
    "sql,sqlstate",
    [
        ("SELECT * FROM hub.attendance", INSUFFICIENT_PRIVILEGE),
        ("SELECT * FROM hub.app_user", INSUFFICIENT_PRIVILEGE),
        ("SELECT * FROM hub.import_file", INSUFFICIENT_PRIVILEGE),
        ("INSERT INTO hub.event(name, term) VALUES ('x','Fall 2026')", READ_ONLY_TRANSACTION),
    ],
)
def test_chatbot_ro_cannot_touch_tables(chatbot_engine, sql, sqlstate):
    with chatbot_engine.connect() as c, pytest.raises(DBAPIError) as e:
        c.execute(text(sql))
    assert e.value.orig.sqlstate == sqlstate


CHATBOT_GRANTS = text(
    """
    SELECT c.relname, p.priv
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    CROSS JOIN unnest(ARRAY['SELECT', 'INSERT', 'UPDATE', 'DELETE']) AS p(priv)
    WHERE n.nspname = 'hub' AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
      AND has_table_privilege('chatbot_ro', c.oid, p.priv)
    ORDER BY c.relname, p.priv
    """
)


def test_chatbot_ro_can_only_select_the_view(db_session):
    """Covers every relation in schema hub, including tables added by later migrations."""
    assert db_session.execute(CHATBOT_GRANTS).all() == [("attendance_view", "SELECT")]


def test_chatbot_ro_session_settings(chatbot_engine):
    with chatbot_engine.connect() as c:
        assert c.execute(text("SHOW default_transaction_read_only")).scalar() == "on"
        assert c.execute(text("SHOW statement_timeout")).scalar() == "5s"


def test_chatbot_ro_has_no_sequence_privileges(db_session):
    rows = db_session.execute(
        text(
            """
            SELECT c.relname, p.priv
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            CROSS JOIN unnest(ARRAY['USAGE', 'SELECT', 'UPDATE']) AS p(priv)
            WHERE n.nspname = 'hub' AND c.relkind = 'S'
              AND has_sequence_privilege('chatbot_ro', c.oid, p.priv)
            ORDER BY c.relname, p.priv
            """
        )
    ).all()
    assert rows == []


@pytest.mark.parametrize("table", ["hub.llm_profile", "hub.conversation", "hub.chat_turn"])
def test_chatbot_ro_cannot_read_new_tables(chatbot_engine, table):
    with chatbot_engine.connect() as c, pytest.raises(DBAPIError) as e:
        c.execute(text(f"SELECT * FROM {table}"))
    assert e.value.orig.sqlstate == INSUFFICIENT_PRIVILEGE


def test_only_one_default_profile(db_session):
    def profile(name: str) -> LlmProfile:
        return LlmProfile(
            name=name,
            preset="custom",
            base_url="http://localhost",
            model="m",
            share_results_with_llm=False,
            is_default=True,
        )

    db_session.add(profile("a"))
    db_session.flush()
    db_session.add(profile("b"))
    with pytest.raises(IntegrityError):
        db_session.flush()
