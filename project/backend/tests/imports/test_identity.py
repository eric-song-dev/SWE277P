from sqlalchemy import select

from app.dataset.models import Person, PersonIdentifier
from app.imports.adapters.base import RowFlag
from app.imports.identity import IdentityLinker


def _idents(session, person_id):
    rows = session.scalars(
        select(PersonIdentifier).where(PersonIdentifier.person_id == person_id)
    ).all()
    return sorted((r.kind, r.value) for r in rows)


def test_new_person_by_netid(db_session):
    r = IdentityLinker(db_session).link("aahmed", "aahmed@uci.edu")
    assert r.method == "netid" and r.person_id and r.flags == []
    assert r.created is True


def test_same_netid_links_same_person(db_session):
    l = IdentityLinker(db_session)
    a = l.link("aahmed", "aahmed@uci.edu")
    b = l.link("aahmed", None)
    assert a.person_id == b.person_id and b.method == "netid"
    assert b.created is False


def test_email_only_links_to_existing(db_session):
    l = IdentityLinker(db_session)
    a = l.link("cdiaz", "cdiaz@uci.edu")
    b = l.link(None, "cdiaz@uci.edu")
    assert (b.person_id, b.method) == (a.person_id, "email")
    assert b.created is False


def test_email_only_creates_person(db_session):
    r = IdentityLinker(db_session).link(None, "new@uci.edu")
    assert r.method == "email" and r.created is True and r.flags == []
    assert _idents(db_session, r.person_id) == [("email", "new@uci.edu")]


def test_netid_attaches_to_email_only_person(db_session):
    l = IdentityLinker(db_session)
    a = l.link(None, "jane.doe@uci.edu")
    b = l.link("jdoe", "jane.doe@uci.edu")
    assert b.person_id == a.person_id and l.link("jdoe", None).person_id == a.person_id
    assert (b.method, b.created, b.flags) == ("email", False, [])


def test_conflicting_netid_wins_and_flags(db_session):
    l = IdentityLinker(db_session)
    a = l.link("aaa", "x@uci.edu")
    b = l.link("bbb", "x@uci.edu")
    assert b.person_id != a.person_id
    assert [f.code for f in b.flags] == ["netid_email_conflict"]
    assert (b.method, b.created) == ("netid", True)
    assert _idents(db_session, a.person_id) == [("email", "x@uci.edu"), ("netid", "aaa")]
    assert _idents(db_session, b.person_id) == [("netid", "bbb")]
    assert RowFlag("netid_email_conflict") in [RowFlag(f.code) for f in b.flags]


def test_conflict_uses_existing_netid_owner(db_session):
    l = IdentityLinker(db_session)
    a = l.link("aaa", "x@uci.edu")
    b = l.link("bbb", None)
    c = l.link("bbb", "x@uci.edu")
    assert c.person_id == b.person_id != a.person_id
    assert c.created is False
    assert [f.code for f in c.flags] == ["email_owned_by_other"]


def test_no_identity(db_session):
    r = IdentityLinker(db_session).link(None, None)
    assert (r.person_id, r.method, [f.code for f in r.flags]) == (
        None,
        "none",
        ["missing_identity"],
    )
    assert r.created is False
    assert db_session.scalars(select(Person)).all() == []


def test_netid_match_adds_new_email(db_session):
    l = IdentityLinker(db_session)
    a = l.link("aahmed", "aahmed@uci.edu")
    b = l.link("aahmed", "alt@uci.edu")
    assert b.person_id == a.person_id and b.flags == []
    assert _idents(db_session, a.person_id) == [
        ("email", "aahmed@uci.edu"),
        ("email", "alt@uci.edu"),
        ("netid", "aahmed"),
    ]
    assert l.link(None, "alt@uci.edu").person_id == a.person_id


def test_netid_match_with_email_owned_by_other_flags(db_session):
    l = IdentityLinker(db_session)
    a = l.link("aaa", "x@uci.edu")
    b = l.link("bbb", "b@uci.edu")
    c = l.link("bbb", "x@uci.edu")
    assert c.person_id == b.person_id and c.created is False
    assert [f.code for f in c.flags] == ["email_owned_by_other"]
    assert _idents(db_session, b.person_id) == [("email", "b@uci.edu"), ("netid", "bbb")]
    assert l.link(None, "x@uci.edu").person_id == a.person_id


def test_created_only_when_person_created(db_session):
    l = IdentityLinker(db_session)
    results = [
        l.link("a1", "a1@uci.edu"),
        l.link("a1", "a1@uci.edu"),
        l.link(None, "a1@uci.edu"),
        l.link(None, None),
        l.link(None, "b1@uci.edu"),
        l.link("b2", "b1@uci.edu"),
    ]
    assert [r.created for r in results] == [True, False, False, False, True, False]
