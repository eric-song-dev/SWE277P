import csv
import hashlib
import io
import json
from datetime import date, datetime
from pathlib import PurePath

from openpyxl import load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

from app.errors import HubError

Grid = list[list[str | None]]


def _unreadable(message: str) -> HubError:
    return HubError("unreadable_file", message, 422)


def _cell(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else str(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, datetime | date):
        return v.isoformat()
    # Control characters such as \x0b cannot be written to XLSX; drop them on the way in.
    return ILLEGAL_CHARACTERS_RE.sub("", str(v)).strip() or None


def _shape(rows: list[list]) -> tuple[Grid, list[int]]:
    """Drop blank rows; also return each kept row's 1-based number in the file."""
    cleaned = [(n, [_cell(c) for c in row]) for n, row in enumerate(rows, start=1)]
    kept = [(n, row) for n, row in cleaned if any(c is not None for c in row)]
    if not kept:
        return [], []
    width = max(i for i, c in enumerate(kept[0][1]) if c is not None) + 1
    return [(row + [None] * width)[:width] for _, row in kept], [n for n, _ in kept]


def _read_csv(content: bytes) -> list[list]:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("cp1252", errors="replace")
    try:
        return list(csv.reader(io.StringIO(text, newline="")))
    except csv.Error as exc:
        raise _unreadable("The file could not be parsed as CSV.") from exc


def _read_xlsx(content: bytes) -> list[list]:
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        try:
            ws = wb.worksheets[0]
            # Read-only mode trusts the file's <dimension> tag, which some exporters understate;
            # without this, rows and columns past it are silently dropped.
            ws.reset_dimensions()
            return [list(row) for row in ws.iter_rows(values_only=True)]
        finally:
            wb.close()
    except Exception as exc:
        raise _unreadable("The file could not be read as a spreadsheet.") from exc


def read_sheet(file_name: str, content: bytes) -> tuple[Grid, list[int]]:
    """The grid without blank rows, and the file row number (header included) of each grid row.

    Staff see these numbers in Excel or a CSV editor, so skipped-row reasons and flags use them.
    """
    ext = PurePath(file_name).suffix.lower()
    if ext == ".csv":
        rows = _read_csv(content)
    elif ext in (".xlsx", ".xlsm"):
        rows = _read_xlsx(content)
    else:
        raise _unreadable("Unsupported file type; upload a .csv, .xlsx, or .xlsm file.")
    return _shape(rows)


def read_grid(file_name: str, content: bytes) -> Grid:
    return read_sheet(file_name, content)[0]


def content_fingerprint(grid: Grid) -> str:
    """SHA-256 of the parsed grid as canonical JSON.

    Identifies a file by its content, so a copy re-saved by Excel (new bytes, same cells) or a
    CSV with another BOM or line ending is still recognised as the same upload.
    """
    canonical = json.dumps(grid, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
