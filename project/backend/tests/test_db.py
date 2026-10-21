from sqlalchemy import DateTime, select

import app.auth.models
import app.dataset.models
import app.events.models
import app.imports.models
import app.quality.models  # noqa: F401 -- import so every table is registered on Base.metadata
from app.db import Base
from app.imports.models import ImportFile


def test_every_datetime_column_is_timezone_aware():
    columns = [
        f"{table.name}.{col.name}"
        for table in Base.metadata.tables.values()
        for col in table.columns
        if isinstance(col.type, DateTime) and not col.type.timezone
    ]
    assert columns == []


def test_import_file_timestamps_read_back_timezone_aware(db_session, committed_october):
    db_session.expire_all()
    imp = db_session.scalars(select(ImportFile)).one()
    assert imp.uploaded_at.tzinfo is not None
    assert imp.committed_at is not None and imp.committed_at.tzinfo is not None
