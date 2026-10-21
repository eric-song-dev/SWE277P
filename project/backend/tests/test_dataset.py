import itertools

import pytest

from app.dataset.service import (
    ALLOWED_COLUMNS,
    GPSRC_HEADERS,
    DatasetFilter,
    build_note,
    gpsrc_layout_rows,
    query_dataset,
)
from app.errors import HubError
from tests.imports.helpers import commit_after_preview, sample_bytes

VIEW_COLUMNS = [
    "person_key", "event_name", "event_date", "term", "academic_year", "modality",
    "sponsors_hosts", "event_type", "platform", "first_name", "last_name", "email",
    "netid", "affiliation", "domestic_international", "school", "department",
]  # fmt: skip


def test_query_dataset_rejects_unknown_column(db_session):
    with pytest.raises(HubError) as exc:
        query_dataset(db_session, [DatasetFilter("student_id", "eq", "1")])
    assert exc.value.code == "invalid_column" and exc.value.status_code == 422


def test_query_dataset_rejects_unknown_sort_column_and_direction(db_session):
    with pytest.raises(HubError):
        query_dataset(db_session, sort=[("raw_row", "asc")])
    with pytest.raises(HubError):
        query_dataset(db_session, sort=[("email", "sideways")])


def test_allowed_columns():
    assert ALLOWED_COLUMNS == frozenset(VIEW_COLUMNS)


def test_query_dataset_filter_sort_limit(db_session, committed_october):
    cols, rows = query_dataset(db_session)
    assert cols == VIEW_COLUMNS and len(rows) == 38
    cols, rows = query_dataset(
        db_session,
        filters=[DatasetFilter("platform", "eq", "CampusGroups")],
        sort=[("last_name", "asc"), ("first_name", "desc")],
        limit=5,
        offset=1,
    )
    assert len(rows) == 5
    last = [r[cols.index("last_name")] for r in rows]
    assert last == sorted(last, key=lambda s: (s is None, s))
    _, none = query_dataset(db_session, filters=[DatasetFilter("platform", "eq", "12twenty")])
    assert none == []


def test_query_dataset_ilike_and_is_null_and_injection_safe(db_session, committed_october):
    _, rows = query_dataset(db_session, filters=[DatasetFilter("email", "ilike", "%@uci.edu")])
    assert rows
    _, rows = query_dataset(db_session, filters=[DatasetFilter("email", "is_null", None)])
    assert isinstance(rows, list)
    _, rows = query_dataset(db_session, filters=[DatasetFilter("email", "eq", "x' OR '1'='1")])
    assert rows == []


def test_gpsrc_layout_rows(db_session, committed_october):
    cols, rows = gpsrc_layout_rows(db_session)
    assert cols == list(GPSRC_HEADERS) and len(rows) == 38
    assert all(len(r) == 19 for r in rows)
    assert {r[7] for r in rows} == {"Yes"}
    assert rows[0][3] == "Test Event"
    assert all(r[18].startswith("Source: CampusGroups export") for r in rows)


def test_notes_for_flagged_row(db_session, user):
    name = "Bagel Breakfast - November.csv"
    commit_after_preview(db_session, name, sample_bytes(name), user)
    db_session.commit()
    _, rows = gpsrc_layout_rows(db_session)
    notes = [r[18] for r in rows]
    assert any("INCOMPLETE" in n and "NetID missing" in n for n in notes)


def test_build_note_combinations():
    cg = "Source: CampusGroups export"
    assert build_note("campusgroups", []) == cg
    assert build_note("campusgroups", ["missing_email"]) == f"{cg}; INCOMPLETE: email missing"
    assert build_note("campusgroups", ["missing_email", "missing_email"]) == (
        f"{cg}; INCOMPLETE: email missing"
    )
    assert (
        build_note("campusgroups", ["missing_department", "missing_netid", "missing_school"])
        == f"{cg}; INCOMPLETE: NetID missing, school missing, department missing"
    )
    assert (
        build_note("campusgroups", ["missing_identity", "missing_netid", "missing_email"])
        == f"{cg}; INCOMPLETE: email/NetID unavailable"
    )
    assert build_note("campusgroups", ["non_standard_email"]) == (
        f"{cg}; CHECK: non-standard email, NetID not derived"
    )
    assert build_note(
        "campusgroups",
        ["email_owned_by_other", "mystery", "netid_email_conflict", "missing_degree"],
    ) == (
        f"{cg}; INCOMPLETE: degree missing; CHECK: NetID/email conflict, "
        "email belongs to another person, mystery"
    )
    assert build_note(
        "twelvetwenty", ["missing_affiliation", "missing_domestic_international"]
    ) == (
        "Source: 12twenty export; 12twenty does not supply Student/Employee ID or "
        "domestic/international status; INCOMPLETE: affiliation missing, "
        "domestic/international missing"
    )


def _pages(session, page_size, **kw):
    out, offset = [], 0
    while chunk := query_dataset(session, limit=page_size, offset=offset, **kw)[1]:
        out += chunk
        offset += page_size
    return out


def test_query_dataset_default_order_is_stable_across_pages(db_session, loaded_samples):
    _, full = query_dataset(db_session)
    assert len(full) > 100
    assert _pages(db_session, 7) == full
    by_hand = [("event_date", "asc"), ("event_name", "asc"), ("last_name", "asc"),
               ("first_name", "asc")]  # fmt: skip
    assert query_dataset(db_session, sort=by_hand)[1] == full  # person_key breaks the last ties


def test_query_dataset_sort_gets_person_key_tie_breaker(db_session, loaded_samples):
    cols, full = query_dataset(db_session, sort=[("event_name", "asc")])
    assert _pages(db_session, 11, sort=[("event_name", "asc")]) == full
    name, key = cols.index("event_name"), cols.index("person_key")
    for a, b in itertools.pairwise(full):
        if a[name] == b[name] and a[key] is not None and b[key] is not None:
            assert a[key] <= b[key]


@pytest.mark.parametrize("op", ["eq", "ilike"])
def test_query_dataset_none_value_is_invalid_filter(db_session, op):
    with pytest.raises(HubError) as exc:
        query_dataset(db_session, [DatasetFilter("email", op, None)])
    assert exc.value.code == "invalid_filter" and exc.value.status_code == 422
