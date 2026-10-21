import pytest
from sqlalchemy.exc import DBAPIError

from app.chat.error_sanitizer import sanitize_db_error
from app.chat.executor import run_readonly


class FakeOrig(Exception):
    def __init__(self, sqlstate, message):
        super().__init__(message)
        self.sqlstate = sqlstate


def db_error(sqlstate, message="boom"):
    return DBAPIError("SELECT 1", None, FakeOrig(sqlstate, message))


def test_passthrough_states_keep_message():
    for state in ("42601", "42703", "42883", "42P01", "42803", "42P10"):
        s = sanitize_db_error(db_error(state, 'column "abc" does not exist'))
        assert s.code == state and 'column "abc" does not exist' in s.feedback


def test_other_states_use_template_without_message():
    s = sanitize_db_error(db_error("22P02", 'invalid input syntax for type integer: "secret"'))
    assert s.code == "22P02"
    assert "secret" not in s.feedback and "secret" not in s.user_message
    assert s.feedback == (
        "data exception (22P02); rewrite the query without relying on specific data values"
    )


def test_class_descriptions():
    for state, text in [
        ("23505", "integrity constraint violation"),
        ("25006", "invalid transaction state"),
        ("28000", "invalid authorization"),
        ("53200", "insufficient resources"),
        ("54001", "program limit exceeded"),
        ("55000", "object not in prerequisite state"),
        ("XX000", "internal error"),
        ("99999", "database error"),
    ]:
        assert text in sanitize_db_error(db_error(state, "leak")).feedback


def test_insufficient_privilege_hides_message():
    s = sanitize_db_error(db_error("42501", "permission denied for table app_user"))
    assert s.code == "42501" and "app_user" not in s.feedback
    assert "syntax error or access rule violation" in s.feedback


def test_timeout():
    s = sanitize_db_error(db_error("57014", "canceling statement"))
    assert s.code == "57014"
    assert s.feedback == "the query was too slow; simplify it"
    assert "too long" in s.user_message


def test_non_db_exception():
    s = sanitize_db_error(ValueError("row value Aaliyah"))
    assert s.code == "unknown" and "Aaliyah" not in s.feedback + s.user_message


def test_dbapi_error_without_sqlstate():
    s = sanitize_db_error(DBAPIError("SELECT 1", None, Exception("Aaliyah")))
    assert s.code == "unknown" and "Aaliyah" not in s.feedback + s.user_message


def test_distinct_order_by_error_keeps_its_message(chatbot_engine):
    # 42P10 names only the rule broken by the SQL, never a data value
    with pytest.raises(DBAPIError) as info:
        run_readonly(
            "SELECT DISTINCT email FROM attendance_view ORDER BY last_name",
            max_rows=10,
            engine=chatbot_engine,
        )
    s = sanitize_db_error(info.value)
    assert s.code == "42P10"
    assert s.feedback == "for SELECT DISTINCT, ORDER BY expressions must appear in select list"
