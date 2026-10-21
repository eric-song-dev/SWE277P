from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dataset.models import Attendance


def identifying_values(db_session: Session) -> set[str]:
    """Every attendee identifier in hub.attendance: emails, NetIDs, Student IDs, "first last" names."""
    values: set[str] = set()
    rows = db_session.execute(
        select(
            Attendance.email,
            Attendance.netid,
            Attendance.student_id,
            Attendance.first_name,
            Attendance.last_name,
        )
    )
    for email, netid, student_id, first_name, last_name in rows:
        values.update(v for v in (email, netid, student_id) if v)
        if first_name and last_name:
            values.add(f"{first_name} {last_name}")
    return values
