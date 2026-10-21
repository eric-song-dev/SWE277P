from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, JsonValue, StringConstraints


class MessageIn(BaseModel):
    question: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)
    ]
    llm_profile_id: int | None = None
    share_results: bool = False  # the per-question switch (spec D2)


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class TurnOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    seq: int
    question: str
    kind: str
    sql: str | None
    interpretation: str | None
    assumptions: list[str] | None
    clarification_question: str | None
    row_count: int | None
    truncated: bool
    analysis_text: str | None
    analysis_source: str | None
    results_shared: bool
    llm_profile_id: int | None
    model: str | None
    error_code: str | None
    created_at: datetime


class ConversationDetail(ConversationOut):
    turns: list[TurnOut]


class QueryResultOut(BaseModel):
    columns: list[str]
    rows: list[list[JsonValue]]
    row_count: int
    truncated: bool
