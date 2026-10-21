import re
from datetime import date
from pathlib import PurePath

_NETID_EMAIL_RE = re.compile(r"^[a-z0-9]+@uci\.edu$")
_TERM_RE = re.compile(r"^(Fall|Winter|Spring|Summer) (\d{4})$")
_CG_UID_RE = re.compile(r"^CG-(\d{4})(\d{2})(\d{2})-")


def clean(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def normalize_email(v) -> str | None:
    s = clean(v)
    return s.lower() if s else None


def normalize_netid(v) -> str | None:
    return normalize_email(v)


def derive_netid(email: str | None) -> str | None:
    normalized = normalize_email(email)
    if normalized and _NETID_EMAIL_RE.match(normalized):
        return normalized.split("@", 1)[0]
    return None


def validate_term(term: str) -> str:
    if not isinstance(term, str) or not _TERM_RE.match(term):
        raise ValueError(f"Invalid term {term!r}; expected e.g. 'Fall 2026'")
    return term


def academic_year(term: str) -> str:
    season, year_text = validate_term(term).split()
    year = int(year_text)
    start = year if season == "Fall" else year - 1
    return f"{start}-{(start + 1) % 100:02d}"


def term_for_date(d: date) -> str:
    if d.month >= 9:
        season = "Fall"
    elif d.month <= 3:
        season = "Winter"
    elif d.month <= 6:
        season = "Spring"
    else:
        season = "Summer"
    return f"{season} {d.year}"


def event_name_from_file_name(name: str) -> str:
    return PurePath(name).stem.replace(" - ", ", ")


def date_from_cg_uid(uid: str | None) -> date | None:
    s = clean(uid)
    m = _CG_UID_RE.match(s) if s else None
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None
