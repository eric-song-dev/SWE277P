"""The chatbot benchmark: 20 sponsor-style questions with reference SQL (spec 8.2, 14 A3/A4),
plus a 10-question holdout set that is never used to tune the prompts.

Run it with ``uv run python -m benchmark.run --profile "<name>" [--set main|holdout]``.
"""

from pathlib import Path

import yaml

QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.yaml"
HOLDOUT_FILE = Path(__file__).resolve().parent / "holdout.yaml"


def _load(path: Path) -> list[dict]:
    entries = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [{**entry, "ordered": bool(entry.get("ordered", False))} for entry in entries]


def load_questions() -> list[dict]:
    """The benchmark entries in file order, with ``ordered`` defaulting to False."""
    return _load(QUESTIONS_FILE)


def load_holdout() -> list[dict]:
    """The holdout entries (h01 to h10), in the same shape as :func:`load_questions`."""
    return _load(HOLDOUT_FILE)
