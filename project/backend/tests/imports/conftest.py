from io import BytesIO

import pytest
from openpyxl import Workbook


@pytest.fixture
def tmp_xlsx():
    def build(rows: list[list]) -> bytes:
        wb = Workbook()
        ws = wb.active
        for row in rows:
            ws.append(row)
        buf = BytesIO()
        wb.save(buf)
        return buf.getvalue()

    return build


@pytest.fixture
def user(db_session):
    from sqlalchemy import select

    from app.auth.models import AppUser
    from app.auth.schemas import CurrentUser

    row = db_session.scalar(select(AppUser).where(AppUser.username == "local"))
    return CurrentUser(id=row.id, username=row.username, display_name=row.display_name)
