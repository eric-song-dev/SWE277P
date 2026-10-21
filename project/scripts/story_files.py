"""Write the synthetic edge-case upload files the user stories need (docs/user-stories/).

Usage, from project/:

    uv run --project backend python scripts/story_files.py <out_dir>

Every file is built from the synthetic sample exports in backend/sample_data/exports/ and written
into <out_dir>, which is created if missing. Nothing is written anywhere else. Put <out_dir>
outside the repo (a scratch or temp folder): these files are walkthrough inputs, never committed.
Standard library only.
"""

import csv
import io
import re
import sys
import zipfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
EXPORTS = PROJECT_DIR / "backend" / "sample_data" / "exports"

OCTOBER = "Bagel Breakfast - October.csv"
LUNCH = "Postdoc Wellness Lunch.csv"
COVER_LETTERS = "Cover Letters for Academic Jobs.csv"
EDWARDS = "Edwards Life Science Site Visit.xlsx"

# UP-10 restarts the api with MAX_UPLOAD_BYTES=20000; the largest sample is under 10 KB.
SIZE_LIMIT_BYTES = 20_000
# UP-02: the 12twenty rows (file row numbers, header = row 1) marked as not attended.
NO_SHOW_ROWS = (3, 5)


def grid(content: bytes) -> list[list[str]]:
    """The cell grid, read the way the Hub reads a CSV (UTF-8 with an optional BOM)."""
    return list(csv.reader(io.StringIO(content.decode("utf-8-sig"), newline="")))


def line_ending(content: bytes) -> bytes:
    """The file's line ending; the sample CSVs use one style throughout."""
    crlf = content.count(b"\r\n")
    lf = content.count(b"\n")
    if crlf == lf and crlf > 0:
        return b"\r\n"
    if crlf == 0 and lf > 0:
        return b"\n"
    raise SystemExit("mixed line endings in a sample CSV; cannot switch them safely")


def physical_lines(content: bytes) -> list[bytes]:
    """The file's lines without their endings. Each must be one CSV record (no quoted newlines)."""
    eol = line_ending(content)
    lines = content.split(eol)
    if lines and lines[-1] == b"":
        lines.pop()
    if len(lines) != len(grid(content)):
        raise SystemExit("a sample CSV has quoted newlines; rows cannot be copied line by line")
    return lines


def header_only(october: bytes) -> bytes:
    """The October export's header row alone, as CampusGroups writes it."""
    eol = line_ending(october)
    return physical_lines(october)[0] + eol


def unknown_format() -> bytes:
    """A CSV that is neither export. It has attendee rows, so it is not rejected as header-only."""
    rows = [
        ["Name", "Mail", "Event"],
        ["Pat Example", "pexample@example.com", "Bagel Breakfast"],
        ["Sam Sample", "ssample@example.com", "Bagel Breakfast"],
    ]
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\r\n").writerows(rows)
    return out.getvalue().encode("utf-8")


def notes_txt() -> bytes:
    return b"Notes from the October Bagel Breakfast: bring more coffee next time.\n"


def switched_line_endings(october: bytes) -> bytes:
    """New bytes, same grid: CRLF becomes LF (or LF becomes CRLF)."""
    if line_ending(october) == b"\r\n":
        return october.replace(b"\r\n", b"\n")
    return october.replace(b"\n", b"\r\n")


def duplicate_person(lunch: bytes) -> bytes:
    """The lunch export with its first attendee row (the first row after the header) appended again."""
    eol = line_ending(lunch)
    lines = physical_lines(lunch)
    first_attendee = next(line for line in lines[1:] if line.strip(b", \t"))
    body = lunch if lunch.endswith(eol) else lunch + eol
    return body + first_attendee + eol


def over_size_limit(october: bytes) -> bytes:
    """The October export with its attendee rows repeated until the file passes SIZE_LIMIT_BYTES."""
    eol = line_ending(october)
    lines = physical_lines(october)
    header, rows = lines[0], lines[1:]
    out = header + eol
    while len(out) <= SIZE_LIMIT_BYTES:
        out += b"".join(row + eol for row in rows)
    return out


def no_shows(edwards: bytes) -> bytes:
    """The 12twenty export with "Attended?" set to NO in NO_SHOW_ROWS (so those rows are skipped)."""
    sheet_name = "xl/worksheets/sheet1.xml"
    src = zipfile.ZipFile(io.BytesIO(edwards))
    sheet = src.read(sheet_name).decode("utf-8")
    header_row = re.search(r'<x:row r="1"[ >].*?</x:row>', sheet)
    if header_row is None:
        raise SystemExit(f"{EDWARDS}: no header row in {sheet_name}")
    column = re.search(r'<x:c r="([A-Z]+)1"[^>]*><x:v>Attended\?</x:v>', header_row.group(0))
    if column is None:
        raise SystemExit(f'{EDWARDS}: no "Attended?" header')
    for row in NO_SHOW_ROWS:
        cell = re.compile(rf'(<x:c r="{column.group(1)}{row}"[^>]*><x:v>)YES(</x:v>)')
        sheet, n = cell.subn(r"\g<1>NO\g<2>", sheet)
        if n != 1:
            raise SystemExit(f"{EDWARDS}: row {row} is not marked YES under Attended?")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as dst:
        for info in src.infolist():
            data = sheet.encode("utf-8") if info.filename == sheet_name else src.read(info)
            dst.writestr(info, data)
    return out.getvalue()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: story_files.py <out_dir>")
    out_dir = Path(sys.argv[1]).expanduser().resolve()
    if out_dir == PROJECT_DIR or PROJECT_DIR in out_dir.parents:
        print(f"note: {out_dir} is inside the repo; do not commit these files", file=sys.stderr)
    out_dir.mkdir(parents=True, exist_ok=True)

    october = (EXPORTS / OCTOBER).read_bytes()
    lunch = (EXPORTS / LUNCH).read_bytes()

    copy = switched_line_endings(october)
    if copy == october or grid(copy) != grid(october):
        raise SystemExit("the line-ending copy must have new bytes and the same grid")

    files = {
        "Header Only.csv": header_only(october),
        "Unknown Format.csv": unknown_format(),
        "Notes.txt": notes_txt(),
        "Bagel Breakfast - October (copy).csv": copy,
        "Duplicate Person.csv": duplicate_person(lunch),
        "Pending Then Broken.csv": (EXPORTS / COVER_LETTERS).read_bytes(),
        "Over Size Limit.csv": over_size_limit(october),
        "Edwards Site Visit - No Shows.xlsx": no_shows((EXPORTS / EDWARDS).read_bytes()),
    }
    for name, content in files.items():
        (out_dir / name).write_bytes(content)
        print(f"{name}: {len(content):,} bytes")
    print(f"Wrote {len(files)} files to {out_dir}")


if __name__ == "__main__":
    main()
