from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, Identity, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Person(Base):
    __tablename__ = "person"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PersonIdentifier(Base):
    __tablename__ = "person_identifier"
    __table_args__ = (UniqueConstraint("kind", "value"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    person_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.person.id"))
    kind: Mapped[str] = mapped_column(Text)
    value: Mapped[str] = mapped_column(Text)


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("event_id", "person_id"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    event_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.event.id"))
    person_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.person.id"))
    import_file_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.import_file.id"))
    source_row: Mapped[int | None]
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    netid: Mapped[str | None] = mapped_column(Text)
    student_id: Mapped[str | None] = mapped_column(Text)
    affiliation: Mapped[str | None] = mapped_column(Text)
    domestic_international: Mapped[str | None] = mapped_column(Text)
    school: Mapped[str | None] = mapped_column(Text)
    department: Mapped[str | None] = mapped_column(Text)
    match_method: Mapped[str] = mapped_column(Text)
    raw_row: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
