from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Identity, LargeBinary, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ImportFile(Base):
    __tablename__ = "import_file"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    file_name: Mapped[str] = mapped_column(Text)
    file_sha256: Mapped[str] = mapped_column(Text, unique=True)
    source: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    row_count: Mapped[int | None]
    skipped_count: Mapped[int | None]
    event_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("hub.event.id"))
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("hub.app_user.id"))
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())
    committed_at: Mapped[datetime | None]
