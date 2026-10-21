from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import DBAPIError

from app.chat.error_sanitizer import sanitize_db_error
from app.chat.executor import run_readonly, to_json_value


def test_json_values():
    values = (date(2026, 10, 7), Decimal(6), Decimal("1.5"), None)
    assert [to_json_value(v) for v in values] == ["2026-10-07", 6, 1.5, None]


def test_json_value_other_types():
    assert to_json_value(datetime(2026, 10, 7, 9, 30)) == "2026-10-07T09:30:00"
    assert to_json_value(5) == 5  # JSON-native values pass through
    assert to_json_value(True) is True
    assert to_json_value("x") == "x"
    assert to_json_value(b"ab") == "b'ab'"  # anything else goes through str


def test_truncation(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email FROM attendance_view LIMIT 11", max_rows=10, engine=chatbot_engine
    )
    assert (r.row_count, r.truncated, len(r.rows)) == (10, True, 10)
    assert r.columns == ["email"]


def test_not_truncated_at_exact_cap(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email FROM attendance_view LIMIT 10", max_rows=10, engine=chatbot_engine
    )
    assert (r.row_count, r.truncated) == (10, False)


def test_empty_result(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email FROM attendance_view WHERE false", max_rows=10, engine=chatbot_engine
    )
    assert (r.rows, r.row_count, r.truncated) == ([], 0, False)
    assert r.columns == ["email"]


def test_rows_are_json_values(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT current_date AS d, count(*) AS n FROM attendance_view",
        max_rows=10,
        engine=chatbot_engine,
    )
    assert date.fromisoformat(r.rows[0][0]) and r.rows[0][1] == 293


def test_connection_usable_after_error(loaded_samples, chatbot_engine):
    with pytest.raises(DBAPIError):
        run_readonly("SELECT nope FROM attendance_view", max_rows=10, engine=chatbot_engine)
    r = run_readonly("SELECT 1 AS one", max_rows=10, engine=chatbot_engine)
    assert r.rows == [[1]]
    assert chatbot_engine.pool.checkedout() == 0


def test_data_error_does_not_leak_value(loaded_samples, chatbot_engine):
    with pytest.raises(DBAPIError) as e:
        run_readonly(
            "SELECT CAST(first_name AS integer) FROM attendance_view",
            max_rows=10,
            engine=chatbot_engine,
        )
    s = sanitize_db_error(e.value)
    assert s.code == "22P02" and "Aaliyah" not in s.feedback and "Aaliyah" not in s.user_message


def test_undefined_column_passes_message(loaded_samples, chatbot_engine):
    with pytest.raises(DBAPIError) as e:
        run_readonly("SELECT no_such_col FROM attendance_view", max_rows=10, engine=chatbot_engine)
    s = sanitize_db_error(e.value)
    assert s.code == "42703" and "no_such_col" in s.feedback


def test_timeout_message(chatbot_engine):
    with pytest.raises(DBAPIError) as e:
        run_readonly("SELECT pg_sleep(10)", max_rows=10, engine=chatbot_engine)
    s = sanitize_db_error(e.value)
    assert s.code == "57014" and "too slow" in s.feedback


def test_bagel_ilike_pattern_returns_rows(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email FROM attendance_view WHERE event_name ILIKE 'Bagel Breakfast%'",
        max_rows=500,
        engine=chatbot_engine,
    )
    assert r.row_count > 0


@pytest.mark.parametrize("literal", ["a :x", "100%s", "50%% off", "x:y:z", "%"])
def test_literals_are_sent_verbatim(chatbot_engine, literal):
    r = run_readonly(f"SELECT '{literal}' AS v", max_rows=10, engine=chatbot_engine)
    assert r.rows == [[literal]]


def test_colon_literal_in_where_clause(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email FROM attendance_view WHERE email = 'a :x' LIMIT 5",
        max_rows=10,
        engine=chatbot_engine,
    )
    assert r.rows == []


def test_double_colon_cast(loaded_samples, chatbot_engine):
    r = run_readonly(
        "SELECT email::text AS e, 1::text AS one FROM attendance_view LIMIT 2",
        max_rows=10,
        engine=chatbot_engine,
    )
    assert r.row_count == 2 and r.rows[0][1] == "1"
