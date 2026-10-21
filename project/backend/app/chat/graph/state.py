"""State, dependencies and the LLM's draft for the chat graph (spec 7.1, 7.3)."""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Literal, Self, TypedDict

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from sqlalchemy import Engine

from app.chat.context import ControlledValues, TurnContext
from app.chat.executor import QueryResult
from app.chat.guard import strip_sql_wrapping
from app.config import Settings

_MAX_REASON = 200


class LlmDraft(BaseModel):
    """The JSON object the generate prompt asks for. ``sql`` is stored without fences or ``;``."""

    kind: Literal["sql", "clarify"]
    sql: str | None = None
    interpretation: str | None = None
    assumptions: list[str] = []
    clarification_question: str | None = None

    @field_validator("sql")
    @classmethod
    def _clean_sql(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return strip_sql_wrapping(value) or None  # fences only, or blank: no SQL

    @field_validator("assumptions", mode="before")
    @classmethod
    def _null_assumptions(cls, value: object) -> object:
        return [] if value is None else value

    @model_validator(mode="after")
    def _required_for_kind(self) -> Self:
        if self.kind == "sql" and not self.sql:
            raise ValueError('"sql" is required when "kind" is "sql"')
        if self.kind == "clarify" and not (self.clarification_question or "").strip():
            raise ValueError('"clarification_question" is required when "kind" is "clarify"')
        return self


def _first_json_object(raw: str) -> dict | None:
    """The first ``{...}`` in ``raw`` that decodes as a JSON object (prose and fences around it
    are ignored)."""
    decoder = json.JSONDecoder()
    start = raw.find("{")
    while start != -1:
        try:
            value, _ = decoder.raw_decode(raw, start)
        except json.JSONDecodeError:
            pass
        else:
            if isinstance(value, dict):
                return value
        start = raw.find("{", start + 1)
    return None


def _validation_reason(exc: ValidationError) -> str:
    # loc and msg only: pydantic's messages do not quote the input
    parts = []
    for err in exc.errors(include_input=False, include_url=False):
        loc = ".".join(str(p) for p in err["loc"])
        msg = err["msg"].removeprefix("Value error, ")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts)


def parse_draft(raw: str) -> LlmDraft:
    """Extract the first JSON object from ``raw`` and validate it.

    Raises ValueError with a short reason that is safe to send back to the LLM: it never quotes
    the reply.
    """
    obj = _first_json_object(raw)
    if obj is None:
        raise ValueError(
            "the reply did not contain a JSON object; reply with exactly one JSON object"
        )
    try:
        return LlmDraft.model_validate(obj)
    except ValidationError as exc:
        reason = _validation_reason(exc)
        if len(reason) > _MAX_REASON:
            reason = reason[: _MAX_REASON - 3] + "..."
        raise ValueError(f"the JSON object did not match the reply format ({reason})") from None


class ChatState(TypedDict, total=False):
    question: str
    history: list[TurnContext]
    controlled: ControlledValues
    today: date
    draft: LlmDraft  # the latest valid draft; kept after later failures for the turn log
    guarded_sql: str  # what actually runs: the draft's SQL with the guard's LIMIT
    result: QueryResult
    attempts: int  # generate calls so far (the JSON-mode fallback retry is not one)
    failure: str | None  # feedback for the failed attempt, until repair adds it to `feedback`
    feedback: list[str]  # sanitized repair feedback, never row values
    analysis: str
    analysis_source: Literal["llm", "local"]
    results_shared: bool
    outcome: Literal["answer", "clarification", "error"]
    error: dict  # {"code", "message"}
    json_mode_detected: bool | None
    turn_id: int


@dataclass
class ChatDeps:
    model: BaseChatModel
    json_mode: bool | None  # the profile's flag; None = not tested yet
    share_results: bool  # the effective value (spec D2), computed by the caller
    settings: Settings
    chatbot_engine: Engine
    record_turn: Callable[[ChatState], Awaitable[int]]  # writes chat_turn, returns its id
