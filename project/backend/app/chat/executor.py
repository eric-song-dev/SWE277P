"""Read-only SQL executor (safety layer 2, spec 13).

Runs guarded SQL as the ``chatbot_ro`` role inside a read-only transaction with a
statement timeout. Database errors propagate unchanged; ``sanitize_db_error`` turns
them into value-free feedback.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pydantic import JsonValue
from sqlalchemy import Engine, text

from app.config import get_settings
from app.db import get_chatbot_engine


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[JsonValue]]
    row_count: int
    truncated: bool


def to_json_value(v: object) -> JsonValue:
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (date, datetime)):  # datetime is a date subclass
        return v.isoformat()
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    return str(v)


def run_readonly(sql: str, *, max_rows: int, engine: Engine | None = None) -> QueryResult:
    engine = engine or get_chatbot_engine()
    timeout_ms = int(get_settings().statement_timeout_ms)  # an int from settings, never user input
    with engine.connect() as conn, conn.begin():
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        # Verbatim: no_parameters makes the driver call cursor.execute(sql) without a
        # parameter argument, so psycopg does no %-processing and SQLAlchemy no :name parsing.
        result = conn.execution_options(no_parameters=True).exec_driver_sql(sql)
        columns = list(result.keys())
        fetched = result.fetchmany(max_rows + 1)
    truncated = len(fetched) > max_rows
    rows = [[to_json_value(v) for v in row] for row in fetched[:max_rows]]
    return QueryResult(columns=columns, rows=rows, row_count=len(rows), truncated=truncated)
