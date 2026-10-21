from sqlalchemy.orm import Session

from app.imports.adapters.base import RowFlag
from app.quality.models import DataQualityFlag


def record_flags(
    session: Session,
    import_file_id: int,
    attendance_id: int | None,
    source_row: int,
    flags: list[RowFlag],
) -> None:
    """Add one data_quality_flag per flag. Flushes, never commits."""
    for flag in flags:
        session.add(
            DataQualityFlag(
                import_file_id=import_file_id,
                attendance_id=attendance_id,
                source_row=source_row,
                code=flag.code,
                detail=flag.detail or None,
            )
        )
    session.flush()
