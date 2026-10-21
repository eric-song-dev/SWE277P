"""Independent expected answers: pandas over the sponsor's compiled sheet (spec 14, A3).

Nothing here reads the database or uses the import code; the only thing shared with the app is
the QueryResult container the scorer compares. The person key is the NetID, falling back to the
NetID of whoever used the same email on another row (the November Bagel Breakfast row
``cdiaz@uci.edu`` joins ``cdiaz``), then to the email itself; a row with neither has no person.
Each function follows the reading recorded in that question's ``notes`` in questions.yaml.
"""

from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from functools import cache
from pathlib import Path

import pandas as pd

from app.chat.executor import QueryResult

COMPILED = Path(__file__).resolve().parents[2] / "sample_data" / "GSPRC Compiled Dataset.xlsm"

# The sheet's exact headers (trailing spaces included) -> short names.
COLUMNS = {
    "Event Term": "term",
    "On Campus Groups?": "on_campus_groups",
    "Event Name ": "event",
    "Virtual/ In-Person/ Hybrid ": "modality",
    "Event type (Professional Development, Wellness/Mental Health, Fellowships)": "event_type",
    "First Name of Attendee": "first_name",
    "Last Name of Attendee": "last_name",
    "Email": "email",
    "NetID": "netid",
    "Affiliation": "affiliation",
    "Domestic or International": "domestic_international",
    "School": "school",
    "Department ": "department",
}

BAGEL = "Bagel Breakfast"
FALL_2026 = "Fall 2026"


def _clean(value: object) -> object:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, str):
        return value.strip() or None
    return value


@cache
def _sheet() -> pd.DataFrame:
    raw = pd.read_excel(COMPILED, sheet_name="Master Attendance", dtype=object)
    df = raw[list(COLUMNS)].rename(columns=COLUMNS).map(_clean)
    df = df[df.notna().any(axis=1)].reset_index(drop=True)
    for col in ("email", "netid"):
        df[col] = df[col].map(lambda v: v.lower() if isinstance(v, str) else None)
    pairs = list(zip(df["netid"], df["email"], strict=True))
    # pandas stores a missing value as NaN (which is truthy), so test for strings explicitly
    owner = {e: n for n, e in pairs if isinstance(n, str) and isinstance(e, str)}
    df["person"] = [
        n if isinstance(n, str) else owner.get(e, e) if isinstance(e, str) else None
        for n, e in pairs
    ]
    # the platform is CampusGroups for events on CampusGroups, else the 12twenty export
    df["platform"] = df["on_campus_groups"].map(
        lambda v: "CampusGroups" if v == "Yes" else "12twenty"
    )
    assert len(df) == 293, len(df)
    return df


def sheet() -> pd.DataFrame:
    return _sheet().copy()


def _linked() -> pd.DataFrame:
    df = sheet()
    return df[df["person"].notna()]


def _is(df: pd.DataFrame, col: str, value: str) -> pd.Series:
    return df[col].map(lambda v: v == value)


def _starts(df: pd.DataFrame, col: str, prefix: str) -> pd.Series:
    return df[col].map(lambda v: isinstance(v, str) and v.startswith(prefix))


def _native(value: object) -> object:
    return value.item() if hasattr(value, "item") else value


def _result(columns: list[str], rows: list[list[object]]) -> QueryResult:
    rows = [[_native(v) for v in row] for row in rows]
    return QueryResult(columns=columns, rows=rows, row_count=len(rows), truncated=False)


def _scalar(column: str, value: object) -> QueryResult:
    return _result([column], [[value]])


def _list(column: str, values) -> QueryResult:
    return _result([column], [[v] for v in sorted(values)])


def q01() -> QueryResult:
    df = sheet()
    m = (
        _is(df, "school", "School of Biological Sciences")
        & _starts(df, "event", BAGEL)
        & _is(df, "term", FALL_2026)
    )
    return _scalar("unique_people", df[m]["person"].nunique())


def q02() -> QueryResult:
    df = sheet()
    people = set(df[_is(df, "netid", "aahmed")]["person"])
    rows = df[df["person"].isin(people) & _is(df, "term", FALL_2026)]
    return _scalar("events", rows["event"].nunique())


def q03() -> QueryResult:
    df = sheet()
    df = df[_is(df, "term", FALL_2026) & df["school"].notna()]
    per_school = df.groupby("school")["person"].nunique()
    return _list("school", per_school[per_school == per_school.min()].index)


def q04() -> QueryResult:
    df = sheet()
    return _list("email", set(df[_starts(df, "event", BAGEL)]["email"].dropna()))


def q05() -> QueryResult:
    per_type = sheet().groupby("event_type")["person"].nunique()
    return _result(["event_type", "unique_people"], [[t, n] for t, n in per_type.items()])


def q06() -> QueryResult:
    df = sheet()
    return _scalar("unique_people", df[_is(df, "term", FALL_2026)]["person"].nunique())


def q07() -> QueryResult:
    df = sheet()
    return _scalar("attendees", int(_is(df, "event", "Health Careers Mixer").sum()))


def q08() -> QueryResult:
    df = sheet()
    counts = df[df["school"].notna()].groupby("school").size()
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return _result(["school", "records"], [[s, n] for s, n in ranked])


def q09() -> QueryResult:
    df = sheet()
    intl = df[_is(df, "domestic_international", "International")]
    return _scalar("unique_people", intl["person"].nunique())


def q10() -> QueryResult:
    df = sheet()
    m = _is(df, "school", "School of Medicine") & _is(df, "event", "Bagel Breakfast, October")
    people = df[m][["first_name", "last_name", "email"]].drop_duplicates()
    return _result(["first_name", "last_name", "email"], people.values.tolist())


def q11() -> QueryResult:
    df = sheet()
    m = _is(df, "event", "Postdoc Wellness Lunch") & _is(df, "affiliation", "Postdoc")
    return _scalar("postdocs", int(m.sum()))


def q12() -> QueryResult:
    per_event = sheet().groupby(["event", "term"]).size()
    top = per_event[per_event == per_event.max()]
    return _list("event_name", {event for event, _term in top.index})


def _events_per_person() -> pd.DataFrame:
    linked = _linked().assign(event_key=lambda d: d["event"] + " | " + d["term"])
    return linked.groupby("person").agg(
        first_name=("first_name", "first"),
        last_name=("last_name", "first"),
        events=("event_key", "nunique"),
    )


def q13() -> QueryResult:
    df = sheet()
    m = _is(df, "affiliation", "Master’s Student") & _is(
        df, "event_type", "Professional Development"
    )
    return _scalar("unique_people", df[m]["person"].nunique())


def q14() -> QueryResult:
    per = _events_per_person()
    regulars = per[per["events"] >= 5]
    return _result(
        ["first_name", "last_name", "events"],
        regulars[["first_name", "last_name", "events"]].values.tolist(),
    )


def q15() -> QueryResult:
    df = sheet()
    virtual = df[_is(df, "modality", "Virtual")]
    doctoral = int(_is(virtual, "affiliation", "Doctoral Student").sum())
    pct = (Decimal(100 * doctoral) / Decimal(len(virtual))).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )
    return _scalar("doctoral_pct", float(pct))


def q16() -> QueryResult:
    df = sheet()
    return _scalar("attendees", int(_is(df, "modality", "Hybrid").sum()))


def q17() -> QueryResult:
    df = sheet()
    eng = df[_is(df, "school", "School of Engineering") & df["department"].notna()]
    per_dept = eng.groupby("department")["person"].nunique()
    return _result(["department", "unique_people"], [[d, n] for d, n in per_dept.items()])


def q18() -> QueryResult:
    linked = _linked()
    cover = set(linked[_is(linked, "event", "Cover Letters for Academic Jobs")]["person"])
    teaching = set(linked[_is(linked, "event", "Teaching Statements for Academic Jobs")]["person"])
    both = _events_per_person().loc[sorted(cover & teaching)]
    return _result(["first_name", "last_name"], both[["first_name", "last_name"]].values.tolist())


def q19() -> QueryResult:
    per = _events_per_person()
    return _scalar("people", int((per["events"] == 1).sum()))


def q20() -> QueryResult:
    df = sheet()
    m = _is(df, "school", "School of Social Sciences") & _is(
        df, "event_type", "Wellness/Mental Health"
    )
    return _list("email", set(df[m]["email"].dropna()))


# The holdout (benchmark/holdout.yaml): same readings, written before any prompt tuning.


def h01() -> QueryResult:
    df = sheet()
    return _scalar("turnout", int(_starts(df, "event", BAGEL).sum()))


def h02() -> QueryResult:
    df = sheet()
    missing = df[df["email"].isna()].groupby("event").size()
    return _result(["event_name", "missing_email"], [[e, n] for e, n in missing.items()])


def h03() -> QueryResult:
    df = sheet()
    m = _is(df, "event", "Building your Brand Workshop") & df["school"].notna()
    per_school = df[m].groupby("school")["person"].nunique()
    return _result(["school", "people"], [[s, n] for s, n in per_school.items()])


def h04() -> QueryResult:
    linked = _linked()
    pd_people = set(linked[_is(linked, "event_type", "Professional Development")]["person"])
    wellness = set(linked[_is(linked, "event_type", "Wellness/Mental Health")]["person"])
    return _scalar("people", len(wellness - pd_people))


def h05() -> QueryResult:
    df = sheet()  # every sample event is in Fall 2026, the first term of academic year 2026-27
    return _scalar("unique_people", df[_is(df, "modality", "In Person")]["person"].nunique())


def h06() -> QueryResult:
    df = sheet()
    m = df["event"].map(lambda v: "academic jobs" in v.lower())
    return _scalar("unique_people", df[m]["person"].nunique())


def h07() -> QueryResult:
    df = sheet()
    per_event = (
        df[_is(df, "domestic_international", "International")].groupby(["event", "term"]).size()
    )
    top = per_event[per_event == per_event.max()]
    return _list("event_name", {event for event, _term in top.index})


def h08() -> QueryResult:
    per_platform = sheet().groupby("platform")["person"].nunique()
    return _result(["platform", "unique_people"], [[p, n] for p, n in per_platform.items()])


def h09() -> QueryResult:
    df = sheet()
    m = (
        _is(df, "domestic_international", "Domestic")
        & _is(df, "affiliation", "Doctoral Student")
        & _is(df, "modality", "In Person")
    )
    return _scalar("unique_people", df[m]["person"].nunique())


def h10() -> QueryResult:
    linked = _linked()
    lunch = set(linked[_is(linked, "event", "Postdoc Wellness Lunch")]["person"])
    bagel = set(linked[_starts(linked, "event", BAGEL)]["person"])
    both = _events_per_person().loc[sorted(lunch & bagel)]
    return _result(["first_name", "last_name"], both[["first_name", "last_name"]].values.tolist())


PANDAS: dict[str, Callable[[], QueryResult]] = {
    **{f"q{i:02d}": globals()[f"q{i:02d}"] for i in range(1, 21)},
    **{f"h{i:02d}": globals()[f"h{i:02d}"] for i in range(1, 11)},
}
