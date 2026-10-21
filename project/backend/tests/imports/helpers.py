import csv
import io
from pathlib import Path

from app.auth.schemas import CurrentUser
from app.imports.schemas import EventDetailsIn
from app.imports.service import commit_import, preview_upload

SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"
_OCTOBER = "Bagel Breakfast - October.csv"


def sample_bytes(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()


def _october_rows() -> list[list[str]]:
    return list(csv.reader(io.StringIO(sample_bytes(_OCTOBER).decode("utf-8-sig"), newline="")))


CG_HEADER = _october_rows()[0]
ROW_AAHMED = _october_rows()[1]


def csv_with_rows(header: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO(newline="")
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue().encode()


def details(**overrides) -> EventDetailsIn:
    data = {
        "name": "Test Event",
        "term": "Fall 2026",
        "modality": "In Person",
        "event_type": "Wellness/Mental Health",
    }
    return EventDetailsIn(**{**data, **overrides})


def commit_after_preview(session, file_name: str, content: bytes, user: CurrentUser, **overrides):
    preview = preview_upload(session, file_name, content, user)
    assert preview.status == "pending", preview
    return commit_import(session, preview.id, details(**overrides), user)


def drop_columns(grid: list[list], *names: str) -> list[list]:
    """Remove every column whose header equals one of `names` or starts with one ending in '*'."""

    def dropped(header: str | None) -> bool:
        h = header or ""
        return any(h.startswith(n[:-1]) if n.endswith("*") else h == n for n in names)

    keep = [i for i, h in enumerate(grid[0]) if not dropped(h)]
    return [[row[i] for i in keep] for row in grid]


def rename_column(grid: list[list], old: str, new: str) -> list[list]:
    return [[new if h == old else h for h in grid[0]], *grid[1:]]
