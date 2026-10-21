from datetime import date

from sqlalchemy import BigInteger, Boolean, ForeignKey, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Event(Base):
    __tablename__ = "event"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    event_date: Mapped[date | None]
    term: Mapped[str] = mapped_column(Text)
    academic_year: Mapped[str | None] = mapped_column(Text)
    modality: Mapped[str | None] = mapped_column(Text)
    sponsors_hosts: Mapped[str | None] = mapped_column(Text)
    event_type: Mapped[str | None] = mapped_column(Text)
    on_campus_groups: Mapped[bool | None] = mapped_column(Boolean)
    attendance_source_note: Mapped[str | None] = mapped_column(Text)
    student_worker: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
