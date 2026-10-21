"""Read-only SQL executor (safety layer 2, spec 13).

Runs guarded SQL as the ``chatbot_ro`` role inside a read-only transaction with a
statement timeout. Database errors propagate unchanged; ``sanitize_db_error`` turns
them into value-free feedback.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from pydantic import JsonValue
from sqlalchemy import Engine, text
from sqlalchemy.exc import DBAPIError

from app.config import get_settings
from app.db import get_chatbot_engine


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[JsonValue]]
    row_count: int
    truncated: bool


def to_json_value(v: object) -> JsonValue:
    if isinstance(v, float) and not math.isfinite(v):
        # JSON has no NaN or Infinity numbers
        return "NaN" if math.isnan(v) else ("Infinity" if v > 0 else "-Infinity")
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (date, datetime)):  # datetime is a date subclass
        return v.isoformat()
    if isinstance(v, Decimal):
        if not v.is_finite():
            return str(v)  # "NaN", "Infinity", "-Infinity"
        return int(v) if v == v.to_integral_value() else float(v)
    return str(v)


def run_readonly(sql: str, *, max_rows: int, engine: Engine | None = None) -> QueryResult:
    engine = engine or get_chatbot_engine()
    timeout_ms = int(get_settings().statement_timeout_ms)  # an int from settings, never user input
    # Never committed: the transaction is read-only, and closing the connection rolls it back,
    # which also reverts any SET / set_config done by the query.
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        # Straight to the psycopg cursor: params=None means psycopg does no placeholder
        # processing (no :name, no %), and prepare=True forces the extended protocol, where
        # PostgreSQL refuses a string holding more than one statement.
        cursor = conn.connection.cursor()
        try:
            try:
                cursor.execute(sql, prepare=True)
            except conn.dialect.dbapi.Error as exc:
                # same exception type the rest of the app sees (DBAPIError with .orig)
                raise DBAPIError.instance(
                    sql, None, exc, conn.dialect.dbapi.Error, dialect=conn.dialect
                ) from exc
            columns = [c.name for c in cursor.description or []]
            fetched = cursor.fetchmany(max_rows + 1) if cursor.description else []
        finally:
            cursor.close()
    truncated = len(fetched) > max_rows
    rows = [[to_json_value(v) for v in row] for row in fetched[:max_rows]]
    return QueryResult(columns=columns, rows=rows, row_count=len(rows), truncated=truncated)
