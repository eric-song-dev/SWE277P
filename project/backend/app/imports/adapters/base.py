from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class RowFlag:
    code: str
    detail: str = ""


@dataclass
class NormalizedRow:
    source_row: int  # 1-based file row; header row is 1
    first_name: str | None
    last_name: str | None
    email: str | None
    netid: str | None
    student_id: str | None
    affiliation: str | None
    domestic_international: str | None
    school: str | None
    department: str | None
    raw: dict[str, str | None]  # header -> value; a repeated header gets " (2)" appended
    flags: list[RowFlag]


@dataclass
class SkippedRow:
    source_row: int
    reason: str


@dataclass
class ParseResult:
    rows: list[NormalizedRow]
    skipped: list[SkippedRow]


@dataclass
class EventDraft:
    name: str
    event_date: date | None
    term: str | None
    modality: str | None
    sponsors_hosts: str | None
    event_type: str | None
    on_campus_groups: bool
    attendance_source_note: str | None = None


class Adapter(Protocol):
    source: str
    display_name: str
    required_headers: tuple[str, ...]

    def parse(
        self, grid: list[list[str | None]], row_numbers: list[int] | None = None
    ) -> ParseResult:
        """`row_numbers[i]` is grid row i's 1-based file row; default: the grid's own order."""
        ...

    def prefill(self, file_name: str, result: ParseResult) -> EventDraft: ...


def file_rows(grid: list[list[str | None]], row_numbers: list[int] | None) -> list[int]:
    return row_numbers if row_numbers is not None else list(range(1, len(grid) + 1))


class HeaderIndex:
    """Position lookup by stripped header text, with occurrence-aware repeats."""

    def __init__(self, header: list[str | None]):
        self.keys: list[str] = []  # raw-dict key per column
        self._positions: dict[str, list[int]] = {}
        seen: Counter[str] = Counter()
        for i, cell in enumerate(header):
            name = (cell or "").strip()
            seen[name] += 1
            self.keys.append(name if seen[name] == 1 else f"{name} ({seen[name]})")
            self._positions.setdefault(name, []).append(i)

    def find(self, name: str, occurrence: int = 1) -> int | None:
        positions = self._positions.get(name, [])
        return positions[occurrence - 1] if len(positions) >= occurrence else None

    def find_prefix(self, prefix: str) -> int | None:
        for name, positions in self._positions.items():
            if name.startswith(prefix):
                return positions[0]
        return None

    def find_containing(self, text: str) -> int | None:
        """First column whose header contains `text`, ignoring case."""
        needle = text.casefold()
        for name, positions in self._positions.items():
            if needle in name.casefold():
                return positions[0]
        return None

    def raw(self, row: list[str | None]) -> dict[str, str | None]:
        return dict(zip(self.keys, row, strict=False))
