from pathlib import Path

from app.imports.adapters import detect_adapter
from app.imports.adapters.base import RowFlag, SkippedRow
from app.imports.adapters.twelvetwenty import TwelveTwentyAdapter
from app.imports.reader import read_grid
from tests.imports.helpers import drop_columns

SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"


def tt(name):
    return read_grid(name, (SAMPLES / name).read_bytes())


def test_detects_twelvetwenty():
    assert detect_adapter(tt("Health Careers Mixer.xlsx")[0]).source == "twelvetwenty"


def test_twelvetwenty_rows_and_mapping():
    res = TwelveTwentyAdapter().parse(tt("Building your Brand Workshop.xlsx"))
    assert len(res.rows) == 27
    r = res.rows[0]
    assert (
        r.email,
        r.netid,
        r.school,
        r.department,
        r.affiliation,
        r.student_id,
        r.domestic_international,
    ) == (
        "aahmed@uci.edu",
        "aahmed",
        "School of Biological Sciences",
        "Molecular Biology and Biochemistry",
        "Doctoral Student",
        None,
        None,
    )


def test_masters_maps_to_curly_apostrophe():
    rows = TwelveTwentyAdapter().parse(tt("Building your Brand Workshop.xlsx")).rows
    assert "Master’s Student" in {r.affiliation for r in rows}


def test_blank_degree_falls_back_to_degree_level():
    rows = TwelveTwentyAdapter().parse(tt("Building your Brand Workshop.xlsx")).rows
    r = next(r for r in rows if r.email == "jpark@uci.edu")
    assert r.affiliation == "Doctoral Student"
    assert RowFlag("missing_degree") in r.flags
    assert RowFlag("missing_affiliation") not in r.flags
    assert all(RowFlag("missing_degree") not in x.flags for x in rows if x is not r)


def test_both_degree_columns_blank():
    grid = tt("Health Careers Mixer.xlsx")
    grid[1][11] = None
    grid[1][12] = None
    r = TwelveTwentyAdapter().parse(grid).rows[0]
    assert r.affiliation is None
    assert RowFlag("missing_affiliation") in r.flags and RowFlag("missing_degree") in r.flags


def test_degree_mapping_case_insensitive_and_unknown_kept():
    grid = tt("Health Careers Mixer.xlsx")
    grid[1][11] = " doctoral "
    grid[2][11] = "Postdoctoral"
    grid[3][11] = "Professional"
    rows = TwelveTwentyAdapter().parse(grid).rows
    assert [r.affiliation for r in rows[:3]] == ["Doctoral Student", "Postdoc", "Professional"]


def test_not_attended_rows_skipped():
    grid = tt("Health Careers Mixer.xlsx")
    grid[1][7] = "NO"
    res = TwelveTwentyAdapter().parse(grid)
    assert len(res.rows) == 44 and res.skipped == [SkippedRow(2, "not_attended")]


def test_blank_attended_skipped():
    grid = tt("Health Careers Mixer.xlsx")
    grid[1][7] = None
    assert TwelveTwentyAdapter().parse(grid).skipped == [SkippedRow(2, "not_attended")]


def test_non_standard_email_flagged():
    grid = tt("Health Careers Mixer.xlsx")
    grid[1][5] = "Jane.Doe@uci.edu"
    r = TwelveTwentyAdapter().parse(grid).rows[0]
    assert r.netid is None and RowFlag("non_standard_email") in r.flags


def test_linkedin_row_without_email_has_no_identity():
    rows = TwelveTwentyAdapter().parse(tt("LinkedIn Info Session.xlsx")).rows
    assert len(rows) == 34
    assert sum(1 for r in rows if r.email is None and r.netid is None) == 1
    bad = next(r for r in rows if r.email is None)
    codes = {f.code for f in bad.flags}
    assert {"missing_email", "missing_netid"} <= codes and "non_standard_email" not in codes
    assert "missing_domestic_international" not in codes


def test_prefill_has_no_date():
    a = TwelveTwentyAdapter()
    d = a.prefill("Health Careers Mixer.xlsx", a.parse(tt("Health Careers Mixer.xlsx")))
    assert (d.name, d.event_date, d.on_campus_groups) == ("Health Careers Mixer", None, False)


def test_parses_without_degree_school_and_major_columns():
    grid = drop_columns(
        tt("Health Careers Mixer.xlsx"),
        "Degree",
        "Degree Level",
        "College/School",
        "Major/Academic Program",
        "Student Group",
        "Assigned Adviser",
    )
    assert detect_adapter(grid[0]).source == "twelvetwenty"
    r = TwelveTwentyAdapter().parse(grid).rows[0]
    assert (r.affiliation, r.school, r.department) == (None, None, None)
    assert {"missing_affiliation", "missing_degree", "missing_school", "missing_department"} <= {
        f.code for f in r.flags
    }


def test_prefill_notes_the_attendance_source():
    a = TwelveTwentyAdapter()
    d = a.prefill("Health Careers Mixer.xlsx", a.parse(tt("Health Careers Mixer.xlsx")))
    assert d.attendance_source_note == "12twenty attendance export"
