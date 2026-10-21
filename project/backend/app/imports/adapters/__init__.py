from collections import Counter

from app.errors import HubError
from app.imports.adapters.base import Adapter
from app.imports.adapters.campusgroups import CampusGroupsAdapter

ADAPTERS: tuple[Adapter, ...] = (CampusGroupsAdapter(),)


def _missing(adapter: Adapter, have: Counter[str]) -> list[str]:
    need: Counter[str] = Counter()
    missing: list[str] = []
    for h in adapter.required_headers:
        need[h] += 1
        if need[h] > have[h]:
            missing.append(h)
    return missing


def detect_adapter(header: list[str | None]) -> Adapter:
    have = Counter(c.strip() for c in header if c is not None)
    best: tuple[Adapter, list[str]] | None = None
    for adapter in ADAPTERS:
        missing = _missing(adapter, have)
        if not missing:
            return adapter
        if best is None or len(missing) < len(best[1]):
            best = (adapter, missing)
    assert best is not None
    raise HubError(
        "unknown_format",
        f"File does not match a known export format; closest is {best[0].display_name}.",
        422,
        {"closest": best[0].display_name, "missing": best[1]},
    )
