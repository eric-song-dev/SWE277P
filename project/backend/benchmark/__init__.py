"""The chatbot benchmark: 20 sponsor-style questions with reference SQL (spec 8.2, 14 A3/A4).

Run it with ``uv run python -m benchmark.run --profile "<name>"``.
"""

from pathlib import Path

import yaml

QUESTIONS_FILE = Path(__file__).resolve().parent / "questions.yaml"


def load_questions() -> list[dict]:
    """The benchmark entries in file order, with ``ordered`` defaulting to False."""
    entries = yaml.safe_load(QUESTIONS_FILE.read_text(encoding="utf-8"))
    return [{**entry, "ordered": bool(entry.get("ordered", False))} for entry in entries]
