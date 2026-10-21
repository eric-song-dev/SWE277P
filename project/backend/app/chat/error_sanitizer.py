"""Turn database errors into feedback for the LLM that never carries row values (spec 7.5).

PostgreSQL messages can quote data (``invalid input syntax for type integer: "abc"``),
so only SQLSTATEs whose messages name identifiers from the SQL keep their message.
"""

from dataclasses import dataclass

# The messages of these states only name identifiers that appear in the SQL itself.
_PASS_THROUGH = frozenset({"42601", "42703", "42883", "42P01", "42803", "42P10"})
_TIMEOUT = "57014"

_CLASS_DESCRIPTIONS = {
    "22": "data exception",
    "23": "integrity constraint violation",
    "25": "invalid transaction state",
    "28": "invalid authorization",
    "42": "syntax error or access rule violation",
    "53": "insufficient resources",
    "54": "program limit exceeded",
    "55": "object not in prerequisite state",
    "57": "operator intervention",
    "XX": "internal error",
}


@dataclass
class SanitizedError:
    code: str  # SQLSTATE, or "unknown"
    feedback: str  # for the LLM
    user_message: str  # for the staff member


def sanitize_db_error(exc: BaseException) -> SanitizedError:
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None)
    if not isinstance(sqlstate, str) or len(sqlstate) != 5:
        return SanitizedError(
            "unknown",
            "the database rejected the query; rewrite it without relying on specific data values",
            "The query could not be run.",
        )
    if sqlstate == _TIMEOUT:
        return SanitizedError(
            sqlstate, "the query was too slow; simplify it", "The query took too long."
        )
    if sqlstate in _PASS_THROUGH:
        primary = getattr(exc.orig, "diag", None)
        message = getattr(primary, "message_primary", None) or str(exc.orig).splitlines()[0]
        return SanitizedError(sqlstate, message, "The query could not be run.")
    description = _CLASS_DESCRIPTIONS.get(sqlstate[:2], "database error")
    return SanitizedError(
        sqlstate,
        f"{description} ({sqlstate}); rewrite the query without relying on specific data values",
        "The query could not be run.",
    )
