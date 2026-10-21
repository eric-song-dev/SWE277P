from app.imports.adapters.base import (
    EventDraft,
    HeaderIndex,
    NormalizedRow,
    ParseResult,
    RowFlag,
    SkippedRow,
    file_rows,
)
from app.imports.normalize import (
    clean,
    derive_netid,
    event_name_from_file_name,
    normalize_email,
)

# Only the columns that identify a 12twenty attendee export; Degree, Degree Level,
# College/School, Major/Academic Program and the rest are optional (absent reads as None).
REQUIRED_HEADERS = ("First Name", "Last Name", "Email", "Registration Date", "Attended?")

_DOCTORAL = "Doctoral Student"
_MASTERS = "Master’s Student"
_POSTDOC = "Postdoc"

# Keys are lowercase; values are the canonical affiliation labels.
_DEGREE = {"doctoral": _DOCTORAL, "masters": _MASTERS, "postdoctoral": _POSTDOC}
_DEGREE_LEVEL = {
    "doctorate": _DOCTORAL,
    "masters": _MASTERS,
    "postdoctoral scholar": _POSTDOC,
}


def _map(value: str | None, table: dict[str, str]) -> str | None:
    v = clean(value)
    return table.get(v.lower(), v) if v else None


class TwelveTwentyAdapter:
    source = "twelvetwenty"
    display_name = "12twenty"
    required_headers = REQUIRED_HEADERS

    def parse(
        self, grid: list[list[str | None]], row_numbers: list[int] | None = None
    ) -> ParseResult:
        idx = HeaderIndex(grid[0])
        n = len(grid[0])

        def col(row: list[str | None], name: str) -> str | None:
            pos = idx.find(name)
            return row[pos] if pos is not None and pos < len(row) else None

        rows: list[NormalizedRow] = []
        skipped: list[SkippedRow] = []
        for i, row in zip(file_rows(grid, row_numbers)[1:], grid[1:], strict=True):
            row = [*row, *([None] * (n - len(row)))]
            if (clean(col(row, "Attended?")) or "").upper() != "YES":
                skipped.append(SkippedRow(i, "not_attended"))
                continue
            email = normalize_email(col(row, "Email"))
            netid = derive_netid(email)
            affiliation = _map(col(row, "Degree"), _DEGREE)
            missing_degree = affiliation is None
            if missing_degree:
                affiliation = _map(col(row, "Degree Level"), _DEGREE_LEVEL)
            fields = {
                "first_name": clean(col(row, "First Name")),
                "last_name": clean(col(row, "Last Name")),
                "email": email,
                "netid": netid,
                "student_id": None,
                "affiliation": affiliation,
                "domestic_international": None,
                "school": clean(col(row, "College/School")),
                "department": clean(col(row, "Major/Academic Program")),
            }
            flags = [
                RowFlag(f"missing_{key}")
                for key in ("netid", "email", "school", "department", "affiliation")
                if fields[key] is None
            ]
            if email is not None and netid is None:
                flags.append(RowFlag("non_standard_email"))
            if missing_degree:
                flags.append(RowFlag("missing_degree"))
            rows.append(NormalizedRow(source_row=i, raw=idx.raw(row), flags=flags, **fields))
        return ParseResult(rows=rows, skipped=skipped)

    def prefill(self, file_name: str, result: ParseResult) -> EventDraft:
        return EventDraft(
            name=event_name_from_file_name(file_name),
            event_date=None,
            term=None,
            modality=None,
            sponsors_hosts=None,
            event_type=None,
            on_campus_groups=False,
            attendance_source_note="12twenty attendance export",
        )
