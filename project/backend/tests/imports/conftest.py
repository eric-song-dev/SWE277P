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
