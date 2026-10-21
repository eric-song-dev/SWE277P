import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.chat.error_sanitizer import sanitize_db_error
from app.chat.executor import run_readonly
from app.chat.guard import GuardError, guard_sql

pytestmark = pytest.mark.acceptance

HARMFUL = [
    "DROP TABLE hub.attendance",
    "DELETE FROM hub.attendance",
    "SELECT 1; DELETE FROM hub.attendance",
    "SELECT * FROM hub.app_user",
    "SELECT set_config('transaction_read_only', 'off', true); UPDATE hub.event SET name = 'x'",
]

GUARD_ONLY = [
    "SELECT pg_sleep(10)",
    "WITH pg_locKs AS (SELECT 1 AS x) SELECT locktype, pid, mode FROM pg_locks",
    "SELECT user FROM attendance_view",
    "SELECT current_user FROM attendance_view",
]


@pytest.mark.parametrize("sql", HARMFUL)
def test_a8_db_role_refuses_with_guard_bypassed(loaded_samples, chatbot_engine, db_session, sql):
    with pytest.raises(DBAPIError):
        run_readonly(sql, max_rows=10, engine=chatbot_engine)
    assert db_session.scalar(text("SELECT count(*) FROM hub.attendance")) == 293


def test_a8_pg_sleep_is_cancelled(chatbot_engine):
    start = time.monotonic()
    with pytest.raises(DBAPIError):
        run_readonly("SELECT pg_sleep(10)", max_rows=10, engine=chatbot_engine)
    assert time.monotonic() - start < 6


@pytest.mark.parametrize("sql", [*HARMFUL, *GUARD_ONLY])
def test_a8_guard_refuses(sql):
    with pytest.raises(GuardError):
        guard_sql(sql, limit=1001)


def _setting(engine, name):
    with engine.connect() as conn:
        return conn.execute(text(f"SHOW {name}")).scalar()


def test_a8_multiple_statements_refused_by_the_driver(chatbot_engine):
    with pytest.raises(DBAPIError) as e:
        run_readonly("SELECT 1; SELECT 2", max_rows=10, engine=chatbot_engine)
    assert sanitize_db_error(e.value).code != "unknown"


def test_a8_commit_then_disable_timeout_refused(chatbot_engine):
    start = time.monotonic()
    with pytest.raises(DBAPIError):
        run_readonly(
            "COMMIT; SET statement_timeout = 0; SELECT pg_sleep(7)",
            max_rows=10,
            engine=chatbot_engine,
        )
    assert time.monotonic() - start < 2


def test_a8_commit_then_disable_read_only_refused(chatbot_engine):
    with pytest.raises(DBAPIError):
        run_readonly(
            "COMMIT; SET default_transaction_read_only = off; COMMIT; "
            "CREATE TEMP TABLE zz2(a int); SELECT 1",
            max_rows=10,
            engine=chatbot_engine,
        )


@pytest.mark.parametrize(
    ("sql", "name", "expected"),
    [
        ("SELECT set_config('statement_timeout', '0', false)", "statement_timeout", "5s"),
        (
            "SELECT set_config('default_transaction_read_only', 'off', false)",
            "default_transaction_read_only",
            "on",
        ),
        ("SET statement_timeout = 0", "statement_timeout", "5s"),
        ("SET default_transaction_read_only = off", "default_transaction_read_only", "on"),
    ],
)
def test_a8_session_changes_do_not_persist_on_pooled_connection(
    chatbot_engine, sql, name, expected
):
    try:
        run_readonly(sql, max_rows=10, engine=chatbot_engine)
    except DBAPIError:
        pass  # refusing is fine too; the connection must still be clean
    assert _setting(chatbot_engine, name) == expected
