from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Identity, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class DataQualityFlag(Base):
    __tablename__ = "data_quality_flag"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    import_file_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.import_file.id"))
    attendance_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.attendance.id"))
    source_row: Mapped[int | None]
    code: Mapped[str] = mapped_column(Text)
    detail: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None]
    resolved_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
