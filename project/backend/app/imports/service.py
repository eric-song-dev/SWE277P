import hashlib
from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from app.auth.models import AppUser
from app.auth.schemas import CurrentUser
from app.config import get_settings
from app.dataset.models import Attendance
from app.errors import HubError
from app.events.models import Event
from app.imports.adapters import ADAPTERS, detect_adapter
from app.imports.adapters.base import Adapter, ParseResult, RowFlag
from app.imports.identity import IdentityLinker, count_in_file_duplicates
from app.imports.models import ImportFile
from app.imports.normalize import academic_year
from app.imports.reader import Grid, content_fingerprint, read_sheet
from app.imports.schemas import (
    CommitSummary,
    ErrorOut,
    EventDetailsIn,
    EventDraftOut,
    ImportEventRef,
    ImportFileOut,
    ImportPreview,
    ImportUserRef,
    SkippedRowOut,
)
from app.quality.models import DataQualityFlag
from app.quality.service import record_flags

# Serializes the duplicate check and insert of uploads (see _preview). Arbitrary constant.
UPLOAD_LOCK_KEY = 7_702_277_001

REJECTABLE = {"unreadable_file", "unknown_format", "file_too_large", "empty_file", "no_data_rows"}


def _read(file_name: str, content: bytes) -> tuple[Grid, list[int]]:
    grid, row_numbers = read_sheet(file_name, content)
    if not grid:
        raise HubError("unreadable_file", "The file contains no rows.", 422)
    return grid, row_numbers


def _parse_grid(grid: Grid, row_numbers: list[int]) -> tuple[Adapter, ParseResult]:
    adapter = detect_adapter(grid[0])
    return adapter, adapter.parse(grid, row_numbers)


def _parse(file_name: str, content: bytes) -> tuple[Adapter, ParseResult]:
    return _parse_grid(*_read(file_name, content))


def _adapter_for(source: str) -> Adapter:
    return next(a for a in ADAPTERS if a.source == source)


def _preview_from(
    import_id: int, file_name: str, adapter: Adapter, result: ParseResult, user: CurrentUser
) -> ImportPreview:
    counts: Counter[str] = Counter(f.code for row in result.rows for f in row.flags)
    if n := count_in_file_duplicates((r.netid, r.email) for r in result.rows):
        counts["duplicate_in_event"] = n
    if result.skipped:
        counts["not_attended_skipped"] = len(result.skipped)
    draft = adapter.prefill(file_name, result)
    return ImportPreview(
        id=import_id,
        file_name=file_name,
        status="pending",
        source=adapter.source,
        source_display=adapter.display_name,
        row_count=len(result.rows),
        skipped=[SkippedRowOut(source_row=s.source_row, reason=s.reason) for s in result.skipped],
        flag_counts=dict(counts),
        event_draft=EventDraftOut(**vars(draft), student_worker=user.display_name),
    )


def preview_upload(
    session: Session, file_name: str, content: bytes, user: CurrentUser
) -> ImportPreview:
    try:
        return _preview(session, file_name, content, user)
    except HubError as exc:
        if exc.code not in REJECTABLE:
            raise
        return ImportPreview(
            id=None,
            file_name=file_name,
            status="rejected",
            error=ErrorOut(code=exc.code, message=exc.message, details=exc.details),
        )


def format_size_limit(limit: int) -> str:
    """A byte limit in KB (nearest whole) below 1 MiB, else MB with up to one decimal."""
    if limit < 1_048_576:
        return f"{round(limit / 1024)} KB"
    return f"{round(limit / 1_048_576, 1):g} MB"


def _preview(session: Session, file_name: str, content: bytes, user: CurrentUser) -> ImportPreview:
    limit = get_settings().max_upload_bytes
    if len(content) > limit:
        raise HubError("file_too_large", f"File exceeds the {format_size_limit(limit)} limit.", 413)
    if not content:
        raise HubError("empty_file", "The file is empty.", 422)

    # Two simultaneous uploads of the same new file would both pass the checks below and the
    # second insert would hit a unique index. A transaction-level advisory lock makes the second
    # upload wait until the first commits, then find its row. Uploads are rare, so one global key.
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": UPLOAD_LOCK_KEY})

    # Same bytes first (cheap), then same parsed content: a copy re-saved by Excel has new bytes.
    digest = hashlib.sha256(content).hexdigest()
    existing = session.scalar(select(ImportFile).where(ImportFile.file_sha256 == digest))
    if existing is not None:
        return _existing_preview(existing, file_name, user)

    grid, row_numbers = _read(file_name, content)
    if len(grid) == 1:
        # Checked before the fingerprint: header-only exports of different events parse to the
        # same grid and would otherwise be reported as duplicates of each other.
        raise HubError("no_data_rows", "This file has a header row but no attendee rows.", 422)
    fingerprint = content_fingerprint(grid)
    existing = session.scalar(select(ImportFile).where(ImportFile.content_sha256 == fingerprint))
    if existing is not None:
        return _existing_preview(existing, file_name, user)

    adapter, result = _parse_grid(grid, row_numbers)
    record = ImportFile(
        file_name=file_name,
        file_sha256=digest,
        content_sha256=fingerprint,
        source=adapter.source,
        status="pending",
        content=content,
        row_count=len(result.rows),
        skipped_count=len(result.skipped),
        uploaded_by=user.id,
    )
    session.add(record)
    session.flush()
    return _preview_from(record.id, file_name, adapter, result, user)


def _existing_preview(existing: ImportFile, file_name: str, user: CurrentUser) -> ImportPreview:
    """A committed match is a duplicate; a pending match returns that same pending preview."""
    if existing.status == "committed":
        return ImportPreview(
            id=None,
            file_name=file_name,
            status="duplicate",
            source=existing.source,
            source_display=_adapter_for(existing.source).display_name,
            row_count=existing.row_count or 0,
            duplicate_of=existing.id,
        )
    adapter, result = _parse(existing.file_name, existing.content)
    return _preview_from(existing.id, existing.file_name, adapter, result, user)


def pending_preview(session: Session, import_id: int, user: CurrentUser) -> ImportPreview:
    """The preview of a pending import, rebuilt from its stored bytes (a card after a reload)."""
    record = session.get(ImportFile, import_id)
    if record is None:
        raise HubError("import_not_found", "Import not found.", 404)
    if record.status != "pending":
        raise HubError("import_not_pending", "This import has already been committed.", 409)
    return _existing_preview(record, record.file_name, user)


def _get_pending(session: Session, import_id: int) -> ImportFile:
    # Row lock: a concurrent commit or discard of the same import waits here until this
    # transaction ends, then re-reads the row and sees it is no longer pending.
    # populate_existing refreshes a copy already in the identity map.
    record = session.get(ImportFile, import_id, with_for_update=True, populate_existing=True)
    if record is None:
        raise HubError("import_not_found", "Import not found.", 404)
    if record.status != "pending":
        raise HubError("import_not_pending", "This import has already been committed.", 409)
    return record


def commit_import(
    session: Session, import_id: int, details: EventDetailsIn, user: CurrentUser
) -> CommitSummary:
    record = _get_pending(session, import_id)
    _adapter, result = _parse(record.file_name, record.content)

    event = Event(
        name=details.name,
        event_date=details.event_date,
        term=details.term,
        academic_year=academic_year(details.term),
        modality=details.modality,
        sponsors_hosts=details.sponsors_hosts,
        event_type=details.event_type,
        on_campus_groups=record.source == "campusgroups",
        attendance_source_note=details.attendance_source_note,
        student_worker=details.student_worker or user.display_name,
        created_by=user.id,
    )
    session.add(event)
    session.flush()

    linker = IdentityLinker(session)
    seen_people: set[int] = set()
    methods: Counter[str] = Counter()
    inserted = new_people = flagged_rows = duplicates = 0

    for row in result.rows:
        link = linker.link(row.netid, row.email)
        new_people += link.created
        if link.person_id is not None and link.person_id in seen_people:
            record_flags(
                session,
                record.id,
                None,
                row.source_row,
                [RowFlag("duplicate_in_event", "person already attended this event in the file")],
            )
            duplicates += 1
            continue
        if link.person_id is not None:
            seen_people.add(link.person_id)
        attendance = Attendance(
            event_id=event.id,
            person_id=link.person_id,
            import_file_id=record.id,
            source_row=row.source_row,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            netid=row.netid,
            student_id=row.student_id,
            affiliation=row.affiliation,
            domestic_international=row.domestic_international,
            school=row.school,
            department=row.department,
            match_method=link.method,
            raw_row=row.raw,
        )
        session.add(attendance)
        session.flush()
        flags = [*row.flags, *link.flags]
        record_flags(session, record.id, attendance.id, row.source_row, flags)
        inserted += 1
        if not link.created:  # a person this commit created is counted in new_people only
            methods[link.method] += 1
        flagged_rows += bool(flags)

    for skipped in result.skipped:
        record_flags(
            session,
            record.id,
            None,
            skipped.source_row,
            [RowFlag("not_attended_skipped", skipped.reason)],
        )

    record.status = "committed"
    record.event_id = event.id
    record.committed_at = datetime.now(UTC)
    session.flush()
    return CommitSummary(
        import_id=record.id,
        event_id=event.id,
        inserted=inserted,
        linked_by_netid=methods["netid"],
        linked_by_email=methods["email"],
        new_people=new_people,
        unlinked=methods["none"],
        flagged_rows=flagged_rows,
        skipped=len(result.skipped),
        duplicates_in_event=duplicates,
    )


def discard_import(session: Session, import_id: int, user: CurrentUser) -> None:
    record = _get_pending(session, import_id)
    session.delete(record)
    session.flush()


def _import_out_query():
    flag_counts = (
        select(DataQualityFlag.import_file_id, func.count().label("n"))
        .group_by(DataQualityFlag.import_file_id)
        .subquery()
    )
    imported_rows = (
        select(Attendance.import_file_id, func.count().label("n"))
        .group_by(Attendance.import_file_id)
        .subquery()
    )
    return (
        select(
            ImportFile.id,
            ImportFile.file_name,
            ImportFile.source,
            ImportFile.status,
            ImportFile.row_count,
            ImportFile.skipped_count,
            ImportFile.uploaded_at,
            ImportFile.committed_at,
            Event.id.label("event_id"),
            Event.name.label("event_name"),
            Event.term.label("event_term"),
            AppUser.id.label("user_id"),
            AppUser.display_name.label("user_name"),
            func.coalesce(flag_counts.c.n, 0).label("flag_count"),
            case(
                (ImportFile.status == "committed", func.coalesce(imported_rows.c.n, 0)),
                else_=None,
            ).label("imported_rows"),
        )
        .join(AppUser, AppUser.id == ImportFile.uploaded_by)
        .outerjoin(Event, Event.id == ImportFile.event_id)
        .outerjoin(flag_counts, flag_counts.c.import_file_id == ImportFile.id)
        .outerjoin(imported_rows, imported_rows.c.import_file_id == ImportFile.id)
    )


def _to_out(r) -> ImportFileOut:
    return ImportFileOut(
        id=r.id,
        file_name=r.file_name,
        source=r.source,
        status=r.status,
        row_count=r.row_count,
        skipped_count=r.skipped_count,
        imported_rows=r.imported_rows,
        event=(
            ImportEventRef(id=r.event_id, name=r.event_name, term=r.event_term)
            if r.event_id is not None
            else None
        ),
        flag_count=r.flag_count,
        uploaded_by=ImportUserRef(id=r.user_id, display_name=r.user_name),
        uploaded_at=r.uploaded_at,
        committed_at=r.committed_at,
    )


def list_imports(session: Session) -> list[ImportFileOut]:
    rows = session.execute(
        _import_out_query().order_by(ImportFile.uploaded_at.desc(), ImportFile.id.desc())
    ).all()
    return [_to_out(r) for r in rows]


def get_import(session: Session, import_id: int) -> ImportFileOut:
    row = session.execute(_import_out_query().where(ImportFile.id == import_id)).first()
    if row is None:
        raise HubError("import_not_found", "Import not found.", 404)
    return _to_out(row)
