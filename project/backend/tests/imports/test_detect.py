from collections import Counter
from pathlib import Path

import pytest

from app.errors import HubError
from app.imports.adapters import _missing, detect_adapter
from app.imports.reader import read_grid
from tests.imports.helpers import drop_columns, rename_column

SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"
TT = "Health Careers Mixer.xlsx"


def cg(name):
    return read_grid(name, (SAMPLES / name).read_bytes())


def test_detects_campusgroups():
    assert detect_adapter(cg("Bagel Breakfast - October.csv")[0]).source == "campusgroups"


def test_unknown_format_lists_missing():
    header = list(cg("Bagel Breakfast - October.csv")[0])
    header.remove("Net ID")
    with pytest.raises(HubError) as e:
        detect_adapter(header)
    assert e.value.code == "unknown_format"
    assert e.value.details["closest"] == "CampusGroups"
    assert e.value.details["missing"] == ["Net ID"]


def test_repeated_required_header_needs_each_occurrence():
    class TwoEmails:
        required_headers = ("Email", "Email", "Net ID")

    assert _missing(TwoEmails(), Counter(["Email", "Net ID"])) == ["Email"]
    assert _missing(TwoEmails(), Counter(["Email", "Email", "Net ID"])) == []


def test_form_copy_columns_are_optional_for_detection():
    header = list(cg("Bagel Breakfast - October.csv")[0])
    del header[5:8]  # "First name", "Last name", second "Email"
    assert detect_adapter(header).source == "campusgroups"


def test_campusgroups_detected_without_unused_or_reworded_columns():
    grid = drop_columns(
        cg("Bagel Breakfast - October.csv"),
        "Student ID #",
        "Please select what you identify as*",
        "Attendee's Feedback",
        "CG Payment UID",
        "Alumni ID",
    )
    grid = rename_column(
        grid, "Are you an international or domestic student/postdoc?", "Intl or domestic?"
    )
    assert detect_adapter(grid[0]).source == "campusgroups"


def test_twelvetwenty_detected_without_optional_columns():
    grid = drop_columns(
        read_grid(TT, (SAMPLES / TT).read_bytes()), "Assigned Adviser", "Student Group"
    )
    assert detect_adapter(grid[0]).source == "twelvetwenty"


def test_twelvetwenty_missing_identifying_column_is_unknown():
    grid = drop_columns(read_grid(TT, (SAMPLES / TT).read_bytes()), "Attended?")
    with pytest.raises(HubError) as e:
        detect_adapter(grid[0])
    assert e.value.details == {"closest": "12twenty", "missing": ["Attended?"]}


def test_header_whitespace_tolerated():
    header = [f" {h} " for h in cg("Bagel Breakfast - October.csv")[0]]
    assert detect_adapter(header).source == "campusgroups"
