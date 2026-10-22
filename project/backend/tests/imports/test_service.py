import hashlib
import threading
import time
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from openpyxl import load_workbook
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.dataset.models import Attendance, Person
from app.errors import HubError
from app.events.models import Event
from app.imports.models import ImportFile
from app.imports.reader import content_fingerprint, read_grid
from app.imports.schemas import EventDetailsIn
from app.imports.service import commit_import, discard_import, list_imports, preview_upload
from app.quality.models import DataQualityFlag
from tests.imports.helpers import (
    CG_HEADER,
    ROW_AAHMED,
    commit_after_preview,
    csv_with_rows,
    details,
    sample_bytes,
)

OCT = "Bagel Breakfast - October.csv"
NOV = "Bagel Breakfast - November.csv"
XLSX = "Health Careers Mixer.xlsx"


def count(session, model):
    return session.scalar(select(func.count()).select_from(model))


def test_preview_then_commit(db_session, user):
    p = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    assert (p.status, p.source, p.row_count, p.event_draft.name) == (
        "pending",
        "campusgroups",
        38,
        "Bagel Breakfast, October",
    )
    assert p.event_draft.student_worker == user.display_name
    s = commit_import(
        db_session,
        p.id,
        EventDetailsIn(
            name="Bagel Breakfast, October",
            term="Fall 2026",
            modality="In Person",
            event_type="Wellness/Mental Health",
            sponsors_hosts="GPSRC",
        ),
        user,
    )
    assert s.inserted == 38
    assert s.linked_by_netid + s.linked_by_email + s.new_people + s.unlinked == 38
    event = db_session.get(Event, s.event_id)
    assert event.academic_year == "2026-27" and event.on_campus_groups is True
    assert event.created_by == user.id and event.student_worker == user.display_name
    record = db_session.get(ImportFile, p.id)
    assert (record.status, record.event_id, record.uploaded_by) == ("committed", event.id, user.id)
    assert record.committed_at is not None


def test_reupload_committed_is_duplicate(db_session, user):
    first = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    again = preview_upload(db_session, "renamed.csv", sample_bytes(OCT), user)
    assert (again.status, again.duplicate_of, again.id) == ("duplicate", first.import_id, None)
    assert count(db_session, ImportFile) == 1


def test_reupload_pending_returns_same_pending(db_session, user):
    first = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    again = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    assert again.status == "pending" and again.id == first.id
    assert again.row_count == first.row_count == 38
    assert count(db_session, ImportFile) == 1


def test_duplicate_person_in_file_is_skipped(db_session, user):
    content = csv_with_rows(header=CG_HEADER, rows=[ROW_AAHMED, ROW_AAHMED])
    s = commit_after_preview(db_session, "dup.csv", content, user)
    assert (s.inserted, s.duplicates_in_event) == (1, 1)
    assert count(db_session, Attendance) == 1
    flag = db_session.scalar(
        select(DataQualityFlag).where(DataQualityFlag.code == "duplicate_in_event")
    )
    assert flag.attendance_id is None and flag.source_row == 3


def test_commit_twice_is_conflict(db_session, user):
    s = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    with pytest.raises(HubError) as exc:
        commit_import(db_session, s.import_id, details(), user)
    assert (exc.value.code, exc.value.status_code) == ("import_not_pending", 409)


def test_commit_unknown_import_is_not_found(db_session, user):
    with pytest.raises(HubError) as exc:
        commit_import(db_session, 999999, details(), user)
    assert (exc.value.code, exc.value.status_code) == ("import_not_found", 404)


def test_second_file_links_to_people_from_first(db_session, user):
    first = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    people = count(db_session, Person)
    second = commit_after_preview(db_session, NOV, sample_bytes(NOV), user, name="Nov")
    assert first.new_people == people
    assert second.new_people < second.inserted
    assert count(db_session, Person) == people + second.new_people
    assert second.linked_by_netid > 0


def test_empty_hub_links_nobody(db_session, user):
    s = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    assert (s.linked_by_netid, s.linked_by_email, s.new_people) == (0, 0, 38)


def test_linked_counts_cover_only_people_who_already_existed(db_session, user):
    commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    before = set(db_session.scalars(select(Person.id)))
    second = commit_after_preview(db_session, NOV, sample_bytes(NOV), user, name="Nov")
    person_ids = db_session.scalars(
        select(Attendance.person_id).where(Attendance.import_file_id == second.import_id)
    ).all()
    existing_rows = sum(1 for pid in person_ids if pid in before)
    assert existing_rows > 0
    assert second.linked_by_netid + second.linked_by_email == existing_rows
    assert second.linked_by_netid + second.linked_by_email + second.new_people == second.inserted


def test_summary_counts_and_flags(db_session, user):
    s = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    flagged = db_session.scalar(
        select(func.count(func.distinct(DataQualityFlag.attendance_id))).where(
            DataQualityFlag.attendance_id.is_not(None)
        )
    )
    assert s.flagged_rows == flagged
    assert s.new_people == count(db_session, Person) <= s.inserted


def test_discard_pending_import(db_session, user):
    p = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    discard_import(db_session, p.id, user)
    assert count(db_session, ImportFile) == 0
    with pytest.raises(HubError) as exc:
        discard_import(db_session, p.id, user)
    assert exc.value.code == "import_not_found"


def test_discard_committed_import_is_conflict(db_session, user):
    s = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    with pytest.raises(HubError) as exc:
        discard_import(db_session, s.import_id, user)
    assert (exc.value.code, exc.value.status_code) == ("import_not_pending", 409)


def test_list_imports_newest_first_with_flag_count(db_session, user):
    a = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    b = preview_upload(db_session, NOV, sample_bytes(NOV), user)
    items = list_imports(db_session)
    assert [i.id for i in items] == [b.id, a.import_id]
    assert items[1].event.name == "Test Event" and items[1].uploaded_by.id == user.id
    assert items[0].event is None


def test_committed_at_is_timezone_aware_and_current(db_session, user):
    s = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    db_session.expire_all()
    committed_at = db_session.get(ImportFile, s.import_id).committed_at
    assert committed_at.tzinfo is not None
    assert abs(datetime.now(UTC) - committed_at) < timedelta(minutes=1)


def _wait_until_lock_wait(observer: Session, pid: int, timeout_s: float = 10.0) -> None:
    """Block until backend `pid` is waiting on a lock (no fixed sleeps: poll the server state)."""
    deadline = time.monotonic() + timeout_s
    query = text("SELECT wait_event_type FROM pg_stat_activity WHERE pid = :pid")
    while observer.scalar(query, {"pid": pid}) != "Lock":
        assert time.monotonic() < deadline, "second commit never waited for the first"
        time.sleep(0.01)


def test_concurrent_second_commit_waits_then_conflicts(db_session, user):
    pending = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    db_session.commit()
    engine = db_session.get_bind()
    outcome: dict[str, object] = {}

    with Session(engine, expire_on_commit=False) as a, Session(engine) as b:
        b_pid = b.scalar(text("SELECT pg_backend_pid()"))

        def second_commit() -> None:
            try:
                outcome["summary"] = commit_import(b, pending.id, details(), user)
                b.commit()
            except Exception as exc:  # noqa: BLE001 -- thread errors are asserted below
                b.rollback()
                outcome["error"] = exc

        thread = threading.Thread(target=second_commit)
        try:
            commit_import(a, pending.id, details(), user)  # A holds the import row, uncommitted
            thread.start()
            _wait_until_lock_wait(db_session, b_pid)
            a.commit()
        finally:
            a.rollback()
            if thread.ident is not None:  # started; joining an unstarted thread raises
                thread.join(timeout=10)
        assert not thread.is_alive()

    error = outcome.get("error")
    assert isinstance(error, HubError), outcome
    assert (error.code, error.status_code) == ("import_not_pending", 409)
    assert count(db_session, Event) == 1
    assert count(db_session, Attendance) == 38


def _resaved(name: str) -> bytes:
    """The sample opened and saved again (as Excel would on "Save"), with no content change."""
    original = sample_bytes(name)
    buf = BytesIO()
    load_workbook(BytesIO(original)).save(buf)
    assert buf.getvalue() != original
    return buf.getvalue()


def test_preview_stores_file_and_content_hashes(db_session, user):
    p = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    record = db_session.get(ImportFile, p.id)
    assert record.file_sha256 == hashlib.sha256(sample_bytes(OCT)).hexdigest()
    assert record.content_sha256 == content_fingerprint(read_grid(OCT, sample_bytes(OCT)))


def test_resaved_copy_of_committed_file_is_duplicate(db_session, user):
    first = commit_after_preview(db_session, XLSX, sample_bytes(XLSX), user)
    again = preview_upload(db_session, "Health Careers Mixer (1).xlsx", _resaved(XLSX), user)
    assert (again.status, again.duplicate_of, again.id) == ("duplicate", first.import_id, None)
    assert (again.source, again.row_count) == ("twelvetwenty", first.inserted)
    assert count(db_session, ImportFile) == 1


def test_resaved_copy_of_pending_file_returns_same_pending(db_session, user):
    first = preview_upload(db_session, XLSX, sample_bytes(XLSX), user)
    again = preview_upload(db_session, XLSX, _resaved(XLSX), user)
    assert (again.status, again.id, again.row_count) == ("pending", first.id, first.row_count)
    assert count(db_session, ImportFile) == 1


def test_csv_with_bom_and_lf_endings_is_duplicate_of_original(db_session, user):
    first = commit_after_preview(db_session, OCT, sample_bytes(OCT), user)
    variant = b"\xef\xbb\xbf" + sample_bytes(OCT).replace(b"\r\n", b"\n")
    again = preview_upload(db_session, OCT, variant, user)
    assert (again.status, again.duplicate_of) == ("duplicate", first.import_id)


TT_HEADER = read_grid(XLSX, sample_bytes(XLSX))[0]


def tt_row(first: str, attended: str | None, email: str) -> list[str | None]:
    row: list[str | None] = [None] * len(TT_HEADER)
    for name, value in (
        ("First Name", first),
        ("Last Name", "Tester"),
        ("Email", email),
        ("Attended?", attended),
    ):
        row[TT_HEADER.index(name)] = value
    return row


def test_twelvetwenty_keeps_only_attended_yes_rows(db_session, user):
    rows = [
        tt_row("Ann", "YES", "ann@uci.edu"),
        tt_row("Bob", "NO", "bob@uci.edu"),
        tt_row("Cy", None, "cy@uci.edu"),
        tt_row("Di", "yes", "di@uci.edu"),
        tt_row("Ed", "", "ed@uci.edu"),
    ]
    p = preview_upload(db_session, "tt.csv", csv_with_rows(TT_HEADER, rows), user)
    assert (p.status, p.source, p.row_count) == ("pending", "twelvetwenty", 2)
    assert [(s.source_row, s.reason) for s in p.skipped] == [
        (3, "not_attended"),
        (4, "not_attended"),
        (6, "not_attended"),
    ]
    assert p.flag_counts["not_attended_skipped"] == 3
    summary = commit_import(db_session, p.id, details(), user)
    assert (summary.inserted, summary.skipped) == (2, 3)
    assert count(db_session, Attendance) == 2


def test_source_row_matches_the_file_row_after_blank_rows(db_session, user):
    # file rows: 1 header, 2 Ann (YES), 3 blank, 4 Bob (NO), 5 blank, 6 blank, 7 Cy (YES, no email)
    text = csv_with_rows(
        TT_HEADER,
        [
            tt_row("Ann", "YES", "ann@uci.edu"),
            [],
            tt_row("Bob", "NO", "bob@uci.edu"),
            [],
            [],
            tt_row("Cy", "YES", ""),
        ],
    )
    p = preview_upload(db_session, "tt.csv", text, user)
    assert [s.source_row for s in p.skipped] == [4]
    commit_import(db_session, p.id, details(), user)
    flags = db_session.scalars(select(DataQualityFlag)).all()
    assert {f.source_row for f in flags if f.code == "missing_email"} == {7}
    skipped = {f.source_row for f in flags if f.code == "not_attended_skipped"}
    assert skipped == {4}
    assert {f.source_row for f in flags} == {2, 4, 7}  # never the blank rows' numbers


def test_source_row_counts_leading_blank_rows_and_xlsx(db_session, user, tmp_xlsx):
    content = tmp_xlsx(
        [
            [],
            TT_HEADER,
            tt_row("Ann", "YES", "ann@uci.edu"),
            [],
            tt_row("Bob", "NO", "bob@uci.edu"),
        ]
    )
    p = preview_upload(db_session, "tt.xlsx", content, user)
    assert [s.source_row for s in p.skipped] == [5]
    cg_rows = csv_with_rows(
        CG_HEADER, [ROW_AAHMED, [], ROW_AAHMED[:4] + [""] * (len(CG_HEADER) - 4)]
    )
    p = preview_upload(db_session, "cg.csv", cg_rows, user)
    assert p.status == "pending" and p.row_count == 2
    commit_import(db_session, p.id, details(), user)
    rows = db_session.scalars(select(DataQualityFlag.source_row)).all()
    assert rows and set(rows) <= {4}


@pytest.mark.parametrize("name", ["empty.csv", "empty.xlsx"])
def test_header_only_file_is_rejected_and_not_stored(db_session, user, tmp_xlsx, name):
    for header in (TT_HEADER, CG_HEADER):  # two different events, identical grids
        content = (
            tmp_xlsx([header, [], []]) if name.endswith("xlsx") else csv_with_rows(header, [[]])
        )
        p = preview_upload(db_session, name, content, user)
        assert p.status == "rejected" and p.id is None
        assert p.error.code == "no_data_rows"
        assert p.error.message == "This file has a header row but no attendee rows."
    assert count(db_session, ImportFile) == 0
