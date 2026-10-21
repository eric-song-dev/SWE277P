from datetime import datetime

import pytest

from app.errors import HubError
from app.imports.reader import read_grid


def test_csv_utf8_bom():
    assert read_grid("a.csv", "﻿Name\nJosé\n".encode())[1] == ["José"]


def test_csv_cp1252_fallback():
    assert read_grid("a.csv", "Name\nJosé\n".encode("cp1252"))[1] == ["José"]


def test_xlsx_integral_float_becomes_int_string(tmp_xlsx):
    assert read_grid("a.xlsx", tmp_xlsx([["Student ID #"], [87000000.0]]))[1] == ["87000000"]


def test_blank_rows_and_trailing_columns_dropped(tmp_xlsx):
    grid = read_grid(
        "a.xlsx",
        tmp_xlsx([["A", "B", None, None], ["1", None, None, None], [None] * 4]),
    )
    assert grid == [["A", "B"], ["1", None]]


def test_unknown_extension_rejected():
    with pytest.raises(HubError) as e:
        read_grid("a.pdf", b"%PDF")
    assert e.value.code == "unreadable_file"
    assert e.value.status_code == 422


def test_corrupt_xlsx_rejected():
    with pytest.raises(HubError) as e:
        read_grid("a.xlsx", b"not a zip")
    assert e.value.code == "unreadable_file"


def test_extension_case_insensitive(tmp_xlsx):
    assert read_grid("A.XLSX", tmp_xlsx([["A"], ["x"]])) == [["A"], ["x"]]


def test_xlsx_ints_datetimes_and_strings(tmp_xlsx):
    grid = read_grid(
        "a.xlsx",
        tmp_xlsx([["#", "When", "F", "S"], [3, datetime(2026, 10, 7, 9, 30), 1.5, "  x "]]),
    )
    assert grid[1] == ["3", "2026-10-07T09:30:00", "1.5", "x"]


def test_rows_padded_and_truncated_to_header_width():
    grid = read_grid("a.csv", b"A,B\n1\n1,2,3\n")
    assert grid == [["A", "B"], ["1", None], ["1", "2"]]


def test_empty_input_returns_empty_grid():
    assert read_grid("a.csv", b"") == []
    assert read_grid("a.csv", b",,\n\n") == []
