"""Result-set comparison for the benchmark (spec 14, "Benchmark format").

Execution accuracy: an answer is correct when its result holds the expected result. Column names
and extra columns are ignored; values, row counts and (when the question asks for it) row order
are not.
"""

import math
import re
from collections import Counter
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from app.chat.executor import QueryResult

REL_TOL = 1e-6

_NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")

# A normalized cell: a finite number as a Decimal, anything else as a string ("" for NULL).
Cell = Decimal | str
Row = tuple[Cell, ...]


def _cell(value: object) -> Cell:
    if value is None:
        return ""
    if isinstance(value, bool):  # before int: bool is an int subclass
        return "true" if value else "false"
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        value = Decimal(repr(value))  # the shortest repr: 58.4, not its binary expansion
    if isinstance(value, Decimal):
        if value.is_nan():
            return ""
        return value if value.is_finite() else str(value)
    text = str(value)
    if _NUMBER.fullmatch(text):
        try:
            return Decimal(text)
        except InvalidOperation:
            return text
    return text


def _is_whole(d: Decimal) -> bool:
    return d == d.to_integral_value()


def _cells_equal(a: Cell, b: Cell) -> bool:
    if isinstance(a, Decimal) and isinstance(b, Decimal):
        if a == b:
            return True
        # Counts and identifiers must be equal; the tolerance is for fractions.
        if _is_whole(a) and _is_whole(b):
            return False
        return math.isclose(float(a), float(b), rel_tol=REL_TOL)
    if isinstance(a, Decimal) or isinstance(b, Decimal):
        return False
    return a == b


def _rows_equal(a: Row, b: Row) -> bool:
    return all(_cells_equal(x, y) for x, y in zip(a, b, strict=True))


def _shape(row: Row) -> tuple[str | None, ...]:
    """The row's strings; numbers become None. Rows can only be equal if their shapes are."""
    return tuple(None if isinstance(c, Decimal) else c for c in row)


def _perfect_matching(xs: list[Row], ys: list[Row]) -> bool:
    """Whether every x pairs with a distinct equal y (Kuhn's augmenting paths)."""
    candidates = [[j for j, y in enumerate(ys) if _rows_equal(x, y)] for x in xs]
    owner = [-1] * len(ys)

    def assign(i: int, seen: set[int]) -> bool:
        for j in candidates[i]:
            if j in seen:
                continue
            seen.add(j)
            if owner[j] == -1 or assign(owner[j], seen):
                owner[j] = i
                return True
        return False

    return all(assign(i, set()) for i in range(len(xs)))


def _multisets_equal(a: list[Row], b: list[Row]) -> bool:
    if len(a) != len(b):
        return False
    if Counter(a) == Counter(b):  # exact (Decimal hashes by value: 6 == 6.0)
        return True
    # Numbers within the tolerance: match rows of the same shape against each other.
    groups: dict[tuple[str | None, ...], tuple[list[Row], list[Row]]] = {}
    for row in a:
        groups.setdefault(_shape(row), ([], []))[0].append(row)
    for row in b:
        groups.setdefault(_shape(row), ([], []))[1].append(row)
    return all(len(xs) == len(ys) and _perfect_matching(xs, ys) for xs, ys in groups.values())


def _rows_match(expected: list[Row], actual: list[Row], *, ordered: bool) -> bool:
    if ordered:
        return len(expected) == len(actual) and all(
            _rows_equal(e, a) for e, a in zip(expected, actual, strict=True)
        )
    return _multisets_equal(expected, actual)


def _normalize(rows: Sequence[Sequence[object]]) -> list[Row]:
    return [tuple(_cell(v) for v in row) for row in rows]


def results_match(expected: QueryResult, actual: QueryResult, *, ordered: bool) -> bool:
    """Whether ``actual`` answers with ``expected``.

    Each expected column is mapped to a different actual column holding the same multiset of
    values; every such injective mapping is tried. The projected rows must then be equal as a
    multiset, or as a sequence when ``ordered``. Numbers compare with a relative tolerance of
    1e-6 (whole numbers exactly), NULL equals "", and a truncated result never matches.
    """
    if expected.truncated or actual.truncated:
        return False
    exp_rows, act_rows = _normalize(expected.rows), _normalize(actual.rows)
    if len(exp_rows) != len(act_rows):
        return False
    n_exp = len(expected.columns)
    n_act = len(actual.columns)
    if n_exp > n_act:
        return False

    def column(rows: list[Row], i: int) -> list[Row]:
        return [(row[i],) for row in rows]

    candidates = [
        [j for j in range(n_act) if _multisets_equal(column(exp_rows, i), column(act_rows, j))]
        for i in range(n_exp)
    ]

    def search(i: int, mapping: list[int]) -> bool:
        if i == n_exp:
            projected = [tuple(row[j] for j in mapping) for row in act_rows]
            return _rows_match(exp_rows, projected, ordered=ordered)
        return any(search(i + 1, [*mapping, j]) for j in candidates[i] if j not in mapping)

    return search(0, [])
