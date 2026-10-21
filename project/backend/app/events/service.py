from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dataset.models import Attendance
from app.events.models import Event
from app.events.schemas import EventOut


def list_events(session: Session) -> list[EventOut]:
    counts = (
        select(Attendance.event_id, func.count().label("n"))
        .group_by(Attendance.event_id)
        .subquery()
    )
    rows = session.execute(
        select(Event, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.event_id == Event.id)
        .order_by(Event.event_date.desc().nulls_last(), Event.id.desc())
    ).all()
    return [
        EventOut(
            id=e.id,
            name=e.name,
            event_date=e.event_date,
            term=e.term,
            academic_year=e.academic_year,
            modality=e.modality,
            event_type=e.event_type,
            attendee_count=n,
        )
        for e, n in rows
    ]
