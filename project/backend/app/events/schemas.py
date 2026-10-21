from datetime import date

from pydantic import BaseModel


class EventOut(BaseModel):
    id: int
    name: str
    event_date: date | None
    term: str
    academic_year: str | None
    modality: str | None
    event_type: str | None
    attendee_count: int
