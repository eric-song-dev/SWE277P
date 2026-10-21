"""Context for SQL generation (spec 7.1 ``load_context``).

Only controlled values (event attributes and drop-down answers) and prior questions with their
SQL reach the generate prompt; attendee row values never do (spec 13 item 4).
"""

from dataclasses import dataclass

from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session

from app.chat.models import ChatTurn

MAX_EVENT_NAMES = 300


@dataclass
class ControlledValues:
    schools: list[str]
    event_names: list[str]
    event_types: list[str]
    terms: list[str]
    academic_years: list[str]
    # A CampusGroups self-selection drop-down, so safe to send; the exact spelling matters
    # (Master’s Student uses U+2019).
    affiliations: list[str]


@dataclass
class TurnContext:
    question: str
    kind: str  # answer | clarification | error
    sql: str | None
    interpretation: str | None
    row_count: int | None
    clarification_question: str | None


# Column names are constants, never user input.
_DISTINCT = "SELECT DISTINCT {col} FROM attendance_view WHERE {col} IS NOT NULL"
# Most recent first: by term (year, then Winter < Spring < Summer < Fall), then by date.
_RECENT_EVENT_NAMES = text(
    """
    SELECT event_name FROM attendance_view
    WHERE event_name IS NOT NULL
    GROUP BY event_name
    ORDER BY max(split_part(term, ' ', 2)::int * 10
                 + CASE split_part(term, ' ', 1)
                     WHEN 'Winter' THEN 1 WHEN 'Spring' THEN 2 WHEN 'Summer' THEN 3 ELSE 4
                   END) DESC,
             max(event_date) DESC NULLS LAST,
             event_name
    LIMIT :n
    """
)


def load_controlled_values(engine: Engine) -> ControlledValues:
    """Distinct non-null values, sorted, read through the read-only chatbot engine."""
    with engine.connect() as conn:

        def distinct(col: str) -> list[str]:
            return sorted(conn.execute(text(_DISTINCT.format(col=col))).scalars())

        return ControlledValues(
            schools=distinct("school"),
            event_names=sorted(conn.execute(_RECENT_EVENT_NAMES, {"n": MAX_EVENT_NAMES}).scalars()),
            event_types=distinct("event_type"),
            terms=distinct("term"),
            academic_years=distinct("academic_year"),
            affiliations=distinct("affiliation"),
        )


def load_history(session: Session, conversation_id: int, limit: int = 10) -> list[TurnContext]:
    """The conversation's last ``limit`` turns, oldest first (no result rows or analysis)."""
    turns = session.scalars(
        select(ChatTurn)
        .where(ChatTurn.conversation_id == conversation_id)
        .order_by(ChatTurn.seq.desc())
        .limit(limit)
    ).all()
    return [
        TurnContext(
            question=t.question,
            kind=t.kind,
            sql=t.sql,
            interpretation=t.interpretation,
            row_count=t.row_count,
            clarification_question=t.clarification_question,
        )
        for t in reversed(turns)
    ]
