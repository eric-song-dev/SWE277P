from datetime import date

import pytest

from app.imports.normalize import (
    academic_year,
    clean,
    date_from_cg_uid,
    derive_netid,
    event_name_from_file_name,
    normalize_email,
    normalize_netid,
    term_for_date,
    validate_term,
)


@pytest.mark.parametrize(
    "email,netid",
    [
        ("aahmed@uci.edu", "aahmed"),
        (" AAhmed@UCI.EDU ", "aahmed"),
        ("jane.doe@uci.edu", None),
        ("x@hs.uci.edu", None),
        (None, None),
    ],
)
def test_derive_netid(email, netid):
    assert derive_netid(email) == netid


@pytest.mark.parametrize(
    "term,year",
    [
        ("Fall 2026", "2026-27"),
        ("Winter 2027", "2026-27"),
        ("Spring 2027", "2026-27"),
        ("Summer 2027", "2026-27"),
    ],
)
def test_academic_year(term, year):
    assert academic_year(term) == year


def test_validate_term_rejects_bad():
    pytest.raises(ValueError, validate_term, "fall 26")


def test_validate_term_returns_valid():
    assert validate_term("Fall 2026") == "Fall 2026"


@pytest.mark.parametrize(
    "d,term",
    [
        (date(2026, 10, 7), "Fall 2026"),
        (date(2027, 2, 1), "Winter 2027"),
        (date(2027, 5, 1), "Spring 2027"),
        (date(2027, 8, 1), "Summer 2027"),
    ],
)
def test_term_for_date(d, term):
    assert term_for_date(d) == term


def test_event_name_from_file_name():
    assert event_name_from_file_name("Bagel Breakfast - October.csv") == "Bagel Breakfast, October"
    assert event_name_from_file_name("Health Careers Mixer.xlsx") == "Health Careers Mixer"


def test_date_from_cg_uid():
    assert date_from_cg_uid("CG-20261007-001") == date(2026, 10, 7)


@pytest.mark.parametrize("uid", [None, "", "  ", "XX-1", "CG-20261340-001", "CG-2026-1"])
def test_date_from_cg_uid_bad(uid):
    assert date_from_cg_uid(uid) is None


def test_clean_and_normalizers():
    assert clean("  a ") == "a"
    assert clean("   ") is None
    assert clean(None) is None
    assert normalize_email(" A@B.com ") == "a@b.com"
    assert normalize_netid(" AAhmed ") == "aahmed"
    assert normalize_netid("") is None
