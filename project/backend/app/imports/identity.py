from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dataset.models import Person, PersonIdentifier
from app.imports.adapters.base import RowFlag


@dataclass
class LinkResult:
    person_id: int | None
    method: Literal["netid", "email", "none"]
    flags: list[RowFlag]
    created: bool  # True when this call created the person


class IdentityLinker:
    """Links one imported row to a person. Flushes, never commits."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def link(self, netid: str | None, email: str | None) -> LinkResult:
        if not netid and not email:
            return LinkResult(None, "none", [RowFlag("missing_identity")], False)

        flags: list[RowFlag] = []
        created = False

        if netid:
            owner = self._owner("netid", netid)
            method: Literal["netid", "email"] = "netid"
            if owner is not None:
                person_id = owner
            else:
                email_owner = self._owner("email", email) if email else None
                if email_owner is None:
                    person_id = self._create_person()
                    created = True
                    self._add("netid", netid, person_id)
                elif self._has_netid(email_owner):
                    person_id = self._create_person()
                    created = True
                    self._add("netid", netid, person_id)
                    flags.append(
                        RowFlag(
                            "netid_email_conflict",
                            f"email {email} belongs to a person with a different NetID "
                            f"than {netid}",
                        )
                    )
                    return LinkResult(person_id, "netid", flags, created)
                else:
                    person_id = email_owner
                    self._add("netid", netid, person_id)
                    method = "email"
        else:
            assert email
            owner = self._owner("email", email)
            method = "email"
            if owner is not None:
                person_id = owner
            else:
                person_id = self._create_person()
                created = True

        if email:
            email_owner = self._owner("email", email)
            if email_owner is None:
                self._add("email", email, person_id)
            elif email_owner != person_id:
                flags.append(
                    RowFlag("email_owned_by_other", f"email {email} belongs to another person")
                )
        return LinkResult(person_id, method, flags, created)

    def _owner(self, kind: str, value: str) -> int | None:
        return self._session.scalar(
            select(PersonIdentifier.person_id).where(
                PersonIdentifier.kind == kind, PersonIdentifier.value == value
            )
        )

    def _has_netid(self, person_id: int) -> bool:
        return (
            self._session.scalar(
                select(PersonIdentifier.id)
                .where(PersonIdentifier.person_id == person_id, PersonIdentifier.kind == "netid")
                .limit(1)
            )
            is not None
        )

    def _create_person(self) -> int:
        person = Person()
        self._session.add(person)
        self._session.flush()
        return person.id

    def _add(self, kind: str, value: str, person_id: int) -> None:
        self._session.add(PersonIdentifier(person_id=person_id, kind=kind, value=value))
        self._session.flush()


def count_in_file_duplicates(keys: Iterable[tuple[str | None, str | None]]) -> int:
    """Rows that repeat a person already seen earlier in the file.

    Applies IdentityLinker's rules 1-4 to the file alone (no database): a row repeats a person
    when its NetID was seen, when it has a new NetID and its email belongs to an in-file person
    with no NetID (the attach case), or when it has no NetID and its email was seen. Two NetIDs
    sharing one email are two people. A row with neither NetID nor email is never a duplicate.
    """
    netids: set[str] = set()
    email_netid: dict[str, str | None] = {}  # email -> its in-file owner's NetID, if any
    duplicates = 0
    for netid, email in keys:
        if not netid and not email:
            continue
        if netid:
            if netid in netids:
                duplicates += 1
                continue
            netids.add(netid)
            if email and email in email_netid and email_netid[email] is None:
                email_netid[email] = netid
                duplicates += 1
            elif email and email not in email_netid:
                email_netid[email] = netid
        elif email in email_netid:
            duplicates += 1
        else:
            assert email
            email_netid[email] = None
    return duplicates
