from app.imports.adapters.base import (
    EventDraft,
    HeaderIndex,
    NormalizedRow,
    ParseResult,
    RowFlag,
)
from app.imports.normalize import (
    clean,
    date_from_cg_uid,
    event_name_from_file_name,
    normalize_email,
    normalize_netid,
    term_for_date,
)

REQUIRED_HEADERS = (
    "First Name",
    "Last Name",
    "Email",
    "Member Tags",
    "User Tags",
    "First name",
    "Last name",
    "Email",
    "Student ID #",
    "School (drop down menu)",
    "Department",
    "Please select what you identify as: Doctoral Student, Staff, Faculty, Master's Student, Postdoc",
    "Are you an international or domestic student/postdoc?",
    "Attendee's Comment",
    "Officer's Notes",
    "Member's Notes",
    "Payment Date",
    "On the Wait List",
    "Promoted to Main List",
    "Attendee's Rating",
    "Attendee's Feedback",
    "Net ID",
    "Event Registration UID",
    "CG Payment UID",
    "CG Payment ID",
    "Alumni ID",
)

_AFFILIATION_PREFIX = "Please select what you identify as"
_DOMESTIC = "Are you an international or domestic student/postdoc?"


class CampusGroupsAdapter:
    source = "campusgroups"
    display_name = "CampusGroups"
    required_headers = REQUIRED_HEADERS

    def parse(self, grid: list[list[str | None]]) -> ParseResult:
        idx = HeaderIndex(grid[0])
        n = len(grid[0])

        def cell(row: list[str | None], pos: int | None) -> str | None:
            return row[pos] if pos is not None and pos < len(row) else None

        def col(row: list[str | None], name: str, occurrence: int = 1) -> str | None:
            return cell(row, idx.find(name, occurrence))

        affiliation_pos = idx.find_prefix(_AFFILIATION_PREFIX)
        rows: list[NormalizedRow] = []
        for i, row in enumerate(grid[1:], start=2):
            row = [*row, *([None] * (n - len(row)))]
            fields = {
                "first_name": clean(col(row, "First Name")) or clean(col(row, "First name")),
                "last_name": clean(col(row, "Last Name")) or clean(col(row, "Last name")),
                "email": normalize_email(col(row, "Email", 1))
                or normalize_email(col(row, "Email", 2)),
                "netid": normalize_netid(col(row, "Net ID")),
                "student_id": clean(col(row, "Student ID #")),
                "affiliation": clean(cell(row, affiliation_pos)),
                "domestic_international": clean(col(row, _DOMESTIC)),
                "school": clean(col(row, "School (drop down menu)")),
                "department": clean(col(row, "Department")),
            }
            flags = [
                RowFlag(f"missing_{key}")
                for key in (
                    "netid",
                    "email",
                    "school",
                    "department",
                    "affiliation",
                    "domestic_international",
                )
                if fields[key] is None
            ]
            rows.append(NormalizedRow(source_row=i, raw=idx.raw(row), flags=flags, **fields))
        return ParseResult(rows=rows, skipped=[])

    def prefill(self, file_name: str, result: ParseResult) -> EventDraft:
        uid = next(
            (
                r.raw.get("Event Registration UID")
                for r in result.rows
                if r.raw.get("Event Registration UID")
            ),
            None,
        )
        event_date = date_from_cg_uid(uid)
        return EventDraft(
            name=event_name_from_file_name(file_name),
            event_date=event_date,
            term=term_for_date(event_date) if event_date else None,
            modality=None,
            sponsors_hosts=None,
            event_type=None,
            on_campus_groups=True,
        )
