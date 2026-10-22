import csv
import io

import pytest

from app.imports.identity import count_in_file_duplicates
from app.imports.service import commit_import, preview_upload
from tests.imports.helpers import (
    CG_HEADER,
    csv_with_rows,
    details,
    sample_bytes,
)

OCT = "Bagel Breakfast - October.csv"


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        ([("ab1", "a@uci.edu"), ("ab1", "x@gmail.com")], 1),
        ([("ab1", "a@uci.edu"), ("ab1", "x@gmail.com"), (None, "x@gmail.com")], 2),
        ([("ab1", "a@uci.edu"), (None, "a@uci.edu")], 1),
        ([(None, "a@uci.edu"), ("ab1", "a@uci.edu")], 1),
        ([("ab1", "a@uci.edu"), ("cd2", "a@uci.edu")], 0),
        ([(None, None), (None, None)], 0),
        ([("ab1", None), ("ab1", None), ("ab1", None)], 2),
        ([(None, "a@uci.edu"), ("ab1", "a@uci.edu"), ("ab1", None)], 2),
        ([("ab1", "a@uci.edu"), ("cd2", "a@uci.edu"), (None, "a@uci.edu")], 1),
    ],
)
def test_count_in_file_duplicates(keys, expected):
    assert count_in_file_duplicates(keys) == expected


def _october_with_first_row_again() -> tuple[bytes, int]:
    rows = list(csv.reader(io.StringIO(sample_bytes(OCT).decode("utf-8-sig"), newline="")))
    body = rows[1:]
    return csv_with_rows(CG_HEADER, [*body, body[0]]), len(body)


def test_preview_counts_a_person_listed_twice(db_session, user):
    original = preview_upload(db_session, OCT, sample_bytes(OCT), user)
    assert "duplicate_in_event" not in original.flag_counts

    content, n = _october_with_first_row_again()
    preview = preview_upload(db_session, "Bagel Breakfast - October (again).csv", content, user)
    assert preview.status == "pending"
    assert preview.row_count == original.row_count + 1 == n + 1
    assert preview.flag_counts["duplicate_in_event"] == 1

    summary = commit_import(db_session, preview.id, details(), user)
    assert summary.duplicates_in_event == 1
    assert summary.inserted == original.row_count
