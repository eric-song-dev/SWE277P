"""Context for SQL generation (spec 7.1 ``load_context``).

Only controlled values (event attributes and drop-down answers) and prior questions with their
SQL reach the generate prompt; attendee row values never do (spec 13 item 4).
"""

from dataclasses import dataclass, field

from sqlalchemy import Engine, select, text
from sqlalchemy.orm import Session

from app.chat.models import ChatTurn

MAX_EVENTS = 300


@dataclass
class ControlledValues:
    schools: list[str]
    event_names: list[str]  # names of the MAX_EVENTS most recent events (event_name + term)
    event_types: list[str]
    terms: list[str]  # oldest first, so "the latest term" is the last one
    academic_years: list[str]
    # A CampusGroups self-selection drop-down, so safe to send; the exact spelling matters
    # (Master’s Student uses U+2019).
    affiliations: list[str]
    # event name -> the terms it was held in, oldest first; a recurring event keeps its name
    event_terms: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class TurnContext:
    question: str
    kind: str  # answer | clarification | error
    sql: str | None
    interpretation: str | None
    row_count: int | None
    clarification_question: str | None


_SEASONS = {"Winter": 1, "Spring": 2, "Summer": 3, "Fall": 4}


def _term_key(term: str) -> tuple[int, int]:
    """Chronological order of 'Fall 2026'-style terms: by year, then Winter < ... < Fall."""
    season, _, year = term.partition(" ")
    return (int(year) if year.isascii() and year.isdigit() else 0), _SEASONS.get(season, 0)


# Column names are constants, never user input.
_DISTINCT = "SELECT DISTINCT {col} FROM attendance_view WHERE {col} IS NOT NULL"
# One row per event (event_name + term), most recent first: by term (year, then
# Winter < Spring < Summer < Fall), then by date.
_RECENT_EVENTS = text(
    """
    SELECT event_name, term,
           split_part(term, ' ', 2)::int * 10
           + CASE split_part(term, ' ', 1)
               WHEN 'Winter' THEN 1 WHEN 'Spring' THEN 2 WHEN 'Summer' THEN 3 ELSE 4
             END AS term_key
    FROM attendance_view
    WHERE event_name IS NOT NULL
    GROUP BY event_name, term
    ORDER BY term_key DESC, max(event_date) DESC NULLS LAST, event_name
    LIMIT :n
    """
)


def load_controlled_values(engine: Engine) -> ControlledValues:
    """Distinct non-null values, sorted (terms chronologically), read through chatbot_ro."""
    with engine.connect() as conn:

        def distinct(col: str) -> list[str]:
            return sorted(conn.execute(text(_DISTINCT.format(col=col))).scalars())

        events = conn.execute(_RECENT_EVENTS, {"n": MAX_EVENTS}).all()
        keyed: dict[str, list[tuple[int, str]]] = {}
        for name, term, term_key in events:
            keyed.setdefault(name, []).append((term_key, term))
        event_names = sorted(keyed)
        return ControlledValues(
            schools=distinct("school"),
            event_names=event_names,
            event_types=distinct("event_type"),
            terms=sorted(distinct("term"), key=_term_key),
            academic_years=distinct("academic_year"),
            affiliations=distinct("affiliation"),
            event_terms={name: [t for _, t in sorted(keyed[name])] for name in event_names},
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
