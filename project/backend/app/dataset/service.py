from dataclasses import dataclass
from typing import Literal

from sqlalchemy import column, func, select, table
from sqlalchemy.orm import Session

from app.dataset.models import Attendance
from app.errors import HubError
from app.events.models import Event
from app.imports.models import ImportFile
from app.quality.models import DataQualityFlag

GPSRC_HEADERS: tuple[str, ...] = (
    "Student Worker",
    "Event Date",
    "Event Term",
    "Event Name ",
    "Virtual/ In-Person/ Hybrid ",
    "Sponsor/Host/Parnters",
    "Event type (Professional Development, Wellness/Mental Health, Fellowships)",
    "On Campus Groups?",
    "If not on Campus Groups, where was attendance found? State where + Link it",
    "First Name of Attendee",
    "Last Name of Attendee",
    "Email",
    "Affiliation",
    "Student ID or Employee ID",
    "NetID",
    "Domestic or International",
    "School",
    "Department ",
    "Notes",
)

VIEW_COLUMNS: tuple[str, ...] = (
    "person_key", "event_name", "event_date", "term", "academic_year", "modality",
    "sponsors_hosts", "event_type", "platform", "first_name", "last_name", "email",
    "netid", "affiliation", "domestic_international", "school", "department",
)  # fmt: skip
ALLOWED_COLUMNS: frozenset[str] = frozenset(VIEW_COLUMNS)

_VIEW = table("attendance_view", *[column(c) for c in VIEW_COLUMNS], schema="hub")


_DEFAULT_ORDER = ("event_date", "event_name", "last_name", "first_name", "person_key")


@dataclass(frozen=True)
class DatasetFilter:
    column: str
    op: Literal["eq", "ilike", "is_null"]
    value: str | None = None


def _check_column(name: str) -> None:
    if name not in ALLOWED_COLUMNS:
        raise HubError("invalid_column", f"Unknown dataset column: {name}", 422)


def query_dataset(
    session: Session,
    filters: tuple[DatasetFilter, ...] | list[DatasetFilter] = (),
    sort: tuple[tuple[str, str], ...] | list[tuple[str, str]] = (),
    limit: int | None = None,
    offset: int = 0,
) -> tuple[list[str], list[tuple]]:
    """Read the attendance view with validated identifiers and bound values (F11 seam)."""
    stmt = select(*[_VIEW.c[c] for c in VIEW_COLUMNS])
    for f in filters:
        _check_column(f.column)
        col = _VIEW.c[f.column]
        if f.op in ("eq", "ilike") and f.value is None:
            # `col == None` would silently become IS NULL; callers must say so with is_null.
            raise HubError("invalid_filter", f"Filter {f.op} needs a value; use is_null", 422)
        if f.op == "eq":
            stmt = stmt.where(col == f.value)
        elif f.op == "ilike":
            stmt = stmt.where(col.ilike(f.value))
        elif f.op == "is_null":
            stmt = stmt.where(col.is_(None))
        else:
            raise HubError("invalid_filter", f"Unknown filter operator: {f.op}", 422)
    for name, direction in sort:
        _check_column(name)
        if direction not in ("asc", "desc"):
            raise HubError("invalid_sort", f"Unknown sort direction: {direction}", 422)
    # Pages must not repeat or skip rows, so the order has to be total up to identical rows:
    # the caller's sort (or the default one), then every default column, then every other view
    # column. person_key alone is not unique (a person has one row per event, and unlinked rows
    # are NULL), so leftover ties are only between rows with identical values.
    order = list(sort) or [(c, "asc") for c in _DEFAULT_ORDER]
    used = {name for name, _ in order}
    order += [
        (c, "asc") for c in (*_DEFAULT_ORDER, *VIEW_COLUMNS) if c not in used and not used.add(c)
    ]
    for name, direction in order:
        col = _VIEW.c[name]
        stmt = stmt.order_by(col.asc().nulls_last() if direction == "asc" else col.desc())
    if limit is not None:
        stmt = stmt.limit(limit)
    if offset:
        stmt = stmt.offset(offset)
    return list(VIEW_COLUMNS), [tuple(r) for r in session.execute(stmt).all()]


_PREFIX = {
    "campusgroups": "Source: CampusGroups export",
    "twelvetwenty": (
        "Source: 12twenty export; 12twenty does not supply Student/Employee ID "
        "or domestic/international status"
    ),
}
_INCOMPLETE = (
    ("missing_identity", "email/NetID unavailable"),
    ("missing_netid", "NetID missing"),
    ("missing_email", "email missing"),
    ("missing_affiliation", "affiliation missing"),
    ("missing_degree", "degree missing"),
    ("missing_school", "school missing"),
    ("missing_department", "department missing"),
    ("missing_domestic_international", "domestic/international missing"),
)
_CHECK = (
    ("non_standard_email", "non-standard email, NetID not derived"),
    ("netid_email_conflict", "NetID/email conflict"),
    ("email_owned_by_other", "email belongs to another person"),
)


def build_note(source: str, flag_codes: list[str]) -> str:
    codes = set(flag_codes)
    incomplete = [text for code, text in _INCOMPLETE if code in codes]
    if "missing_identity" in codes:
        incomplete = [t for t in incomplete if t not in ("NetID missing", "email missing")]
    known = {c for c, _ in _INCOMPLETE} | {c for c, _ in _CHECK}
    check = [text for code, text in _CHECK if code in codes]
    check += sorted(codes - known)
    note = _PREFIX.get(source, f"Source: {source}")
    if incomplete:
        note += "; INCOMPLETE: " + ", ".join(incomplete)
    if check:
        note += "; CHECK: " + ", ".join(check)
    return note


def gpsrc_layout_rows(session: Session) -> tuple[list[str], list[list[object]]]:
    """Rows in the sponsor's 19-column GPSRC layout (two queries, no per-row lookups)."""
    stmt = (
        select(Attendance, Event, ImportFile.source)
        .join(Event, Event.id == Attendance.event_id)
        .join(ImportFile, ImportFile.id == Attendance.import_file_id)
        .order_by(Event.id, Attendance.source_row, Attendance.id)
    )
    flags: dict[int, list[str]] = {}
    flag_stmt = (
        select(DataQualityFlag.attendance_id, func.array_agg(DataQualityFlag.code))
        .where(DataQualityFlag.attendance_id.is_not(None))
        .group_by(DataQualityFlag.attendance_id)
    )
    for attendance_id, codes in session.execute(flag_stmt):
        flags[attendance_id] = list(codes)

    rows: list[list[object]] = []
    for a, e, source in session.execute(stmt):
        rows.append(
            [
                e.student_worker,
                e.event_date,
                e.term,
                e.name,
                e.modality,
                e.sponsors_hosts,
                e.event_type,
                "Yes" if e.on_campus_groups else "No",
                e.attendance_source_note,
                a.first_name,
                a.last_name,
                a.email,
                a.affiliation,
                a.student_id,
                a.netid,
                a.domestic_international,
                a.school,
                a.department,
                build_note(source, flags.get(a.id, [])),
            ]
        )
    return list(GPSRC_HEADERS), rows
