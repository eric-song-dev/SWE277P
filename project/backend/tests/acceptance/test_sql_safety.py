import time

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

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
