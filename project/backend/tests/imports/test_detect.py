from pathlib import Path

import pytest

from app.errors import HubError
from app.imports.adapters import detect_adapter
from app.imports.reader import read_grid

SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"


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


def test_repeated_header_counts_as_missing():
    header = list(cg("Bagel Breakfast - October.csv")[0])
    header.pop(7)  # second Email
    with pytest.raises(HubError) as e:
        detect_adapter(header)
    assert e.value.details["missing"] == ["Email"]


def test_header_whitespace_tolerated():
    header = [f" {h} " for h in cg("Bagel Breakfast - October.csv")[0]]
    assert detect_adapter(header).source == "campusgroups"
