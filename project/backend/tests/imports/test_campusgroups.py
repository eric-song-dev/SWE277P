from datetime import date
from pathlib import Path

from app.imports.adapters.campusgroups import CampusGroupsAdapter
from app.imports.reader import read_grid
from tests.imports.helpers import drop_columns, rename_column

SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"


def cg(name):
    return read_grid(name, (SAMPLES / name).read_bytes())


def test_campusgroups_october_rows():
    res = CampusGroupsAdapter().parse(cg("Bagel Breakfast - October.csv"))
    assert len(res.rows) == 38 and res.skipped == []
    r = res.rows[0]
    assert (
        r.first_name,
        r.email,
        r.netid,
        r.student_id,
        r.school,
        r.affiliation,
        r.domestic_international,
    ) == (
        "Aaliyah",
        "aahmed@uci.edu",
        "aahmed",
        "87000000",
        "School of Biological Sciences",
        "Doctoral Student",
        "International",
    )
    assert r.source_row == 2 and r.raw["Email (2)"] == "aahmed@uci.edu"
    assert r.raw["Email"] == "aahmed@uci.edu"


def test_campusgroups_xlsx_december():
    assert len(CampusGroupsAdapter().parse(cg("Bagel Breakfast - December.xlsx")).rows) == 24


def test_campusgroups_row_counts():
    a = CampusGroupsAdapter()
    for name, n in [
        ("Bagel Breakfast - November.csv", 31),
        ("Cover Letters for Academic Jobs.csv", 29),
        ("Teaching Statements for Academic Jobs.csv", 26),
        ("Postdoc Wellness Lunch.csv", 18),
    ]:
        assert len(a.parse(cg(name)).rows) == n


def test_campusgroups_prefill():
    a = CampusGroupsAdapter()
    res = a.parse(cg("Bagel Breakfast - October.csv"))
    d = a.prefill("Bagel Breakfast - October.csv", res)
    assert (d.name, d.event_date, d.term, d.on_campus_groups) == (
        "Bagel Breakfast, October",
        date(2026, 10, 7),
        "Fall 2026",
        True,
    )
    assert d.modality is None and d.sponsors_hosts is None and d.event_type is None


def test_campusgroups_missing_netid_flagged():
    res = CampusGroupsAdapter().parse(cg("Bagel Breakfast - November.csv"))
    assert any(f.code == "missing_netid" for r in res.rows for f in r.flags)


def test_profile_falls_back_to_form_copy_and_flags_blanks():
    grid = cg("Bagel Breakfast - October.csv")
    header = [h for h in grid[0]]
    row = list(grid[1])
    row[0] = row[1] = row[2] = None
    row[21] = None  # Net ID
    row[10] = None  # Department
    res = CampusGroupsAdapter().parse([header, row])
    r = res.rows[0]
    assert (r.first_name, r.last_name, r.email) == ("Aaliyah", "Ahmed", "aahmed@uci.edu")
    assert r.netid is None
    assert {f.code for f in r.flags} == {"missing_netid", "missing_department"}


def test_header_whitespace_tolerated_in_parse():
    grid = cg("Bagel Breakfast - October.csv")
    grid = [[f" {h} " for h in grid[0]], *grid[1:]]
    assert CampusGroupsAdapter().parse(grid).rows[0].netid == "aahmed"


def test_parses_without_affiliation_and_student_id_columns():
    grid = drop_columns(
        cg("Bagel Breakfast - October.csv"), "Student ID #", "Please select what you identify as*"
    )
    rows = CampusGroupsAdapter().parse(grid).rows
    assert len(rows) == 38
    assert all(r.affiliation is None and r.student_id is None for r in rows)
    assert all("missing_affiliation" in {f.code for f in r.flags} for r in rows)
    assert rows[0].netid == "aahmed" and rows[0].school == "School of Biological Sciences"


def test_parses_without_any_optional_column():
    grid = cg("Bagel Breakfast - October.csv")
    required = {"First Name", "Last Name", "Email", "Net ID", "Event Registration UID"}
    keep = [i for i, h in enumerate(grid[0]) if h in required and not (h == "Email" and i == 7)]
    grid = [[row[i] for i in keep] for row in grid]
    r = CampusGroupsAdapter().parse(grid).rows[0]
    assert (r.first_name, r.email, r.netid) == ("Aaliyah", "aahmed@uci.edu", "aahmed")
    assert {f.code for f in r.flags} == {
        "missing_school",
        "missing_department",
        "missing_affiliation",
        "missing_domestic_international",
    }


def test_reworded_affiliation_and_domestic_questions_still_found():
    grid = cg("Bagel Breakfast - October.csv")
    grid = rename_column(
        grid,
        "Please select what you identify as: Doctoral Student, Staff, Faculty, Master's Student, "
        "Postdoc",
        "Please select what you identify as (choose one)",
    )
    grid = rename_column(
        grid,
        "Are you an international or domestic student/postdoc?",
        "Are you an International or Domestic scholar?",
    )
    r = CampusGroupsAdapter().parse(grid).rows[0]
    assert (r.affiliation, r.domestic_international) == ("Doctoral Student", "International")


def test_campusgroups_prefill_has_no_attendance_source_note():
    a = CampusGroupsAdapter()
    d = a.prefill("Bagel Breakfast - October.csv", a.parse(cg("Bagel Breakfast - October.csv")))
    assert d.attendance_source_note is None
