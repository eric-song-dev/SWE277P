from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.imports.normalize import validate_term


class SkippedRowOut(BaseModel):
    source_row: int
    reason: str


class ErrorOut(BaseModel):
    code: str
    message: str
    details: dict | None = None


class EventDraftOut(BaseModel):
    name: str
    event_date: date | None
    term: str | None
    modality: str | None
    sponsors_hosts: str | None
    event_type: str | None
    on_campus_groups: bool
    student_worker: str | None


class ImportPreview(BaseModel):
    id: int | None
    file_name: str
    status: Literal["pending", "duplicate", "rejected"]
    source: str | None = None
    source_display: str | None = None
    row_count: int = 0
    skipped: list[SkippedRowOut] = Field(default_factory=list)
    flag_counts: dict[str, int] = Field(default_factory=dict)
    event_draft: EventDraftOut | None = None
    duplicate_of: int | None = None
    error: ErrorOut | None = None


class ImportPreviewBatch(BaseModel):
    files: list[ImportPreview]


class EventDetailsIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    event_date: date | None = None
    term: Annotated[str, StringConstraints(strip_whitespace=True)]
    modality: Literal["In Person", "Virtual", "Hybrid"]
    sponsors_hosts: str | None = None
    event_type: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    attendance_source_note: str | None = None
    student_worker: str | None = None

    @field_validator("sponsors_hosts", "attendance_source_note", "student_worker")
    @classmethod
    def _blank_to_none(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @field_validator("term")
    @classmethod
    def _term(cls, v: str) -> str:
        return validate_term(v)


class CommitSummary(BaseModel):
    import_id: int
    event_id: int
    inserted: int
    linked_by_netid: int
    linked_by_email: int
    new_people: int
    unlinked: int
    flagged_rows: int
    skipped: int
    duplicates_in_event: int


class ImportEventRef(BaseModel):
    id: int
    name: str
    term: str


class ImportUserRef(BaseModel):
    id: int
    display_name: str


class ImportFileOut(BaseModel):
    id: int
    file_name: str
    source: str
    status: str
    row_count: int | None
    skipped_count: int | None
    event: ImportEventRef | None
    flag_count: int
    uploaded_by: ImportUserRef
    uploaded_at: datetime
    committed_at: datetime | None
