"""Run the benchmark against a stored LLM profile (spec 8.2, 14 A3/A4).

    uv run python -m benchmark.run --profile "<name>" [--today 2026-11-02] [--only q01,q05]
                                   [--min-score 18]

Each question runs through the chat graph with an empty history and ``share_results=False``:
the benchmark scores the generated SQL's result, so no rows are ever sent to the model. The
reference SQL runs through the same guard and read-only role. The report (SQL and scores only,
never result rows) goes to ``benchmark/reports/<YYYYMMDD-HHMM>-<profile>.md``.

Exit codes: 0 done, 1 below ``--min-score``, 2 the benchmark could not run (no sample data,
unknown profile or question id, or any unexpected error; for an unexpected error only its
type is printed, never its message, which could carry a URL or a key).
"""

import argparse
import asyncio
import logging
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.chat.executor import QueryResult, run_readonly
from app.chat.graph.build import build_chat_graph
from app.chat.graph.prompts import PROMPT_VERSION
from app.chat.graph.state import ChatDeps, ChatState
from app.chat.guard import GuardError, guard_sql
from app.config import Settings, get_settings
from app.db import SessionLocal, get_app_engine, get_chatbot_engine
from app.errors import HubError
from app.llm.factory import build_chat_model
from app.llm.models import LlmProfile
from app.llm.service import get_profile_with_key
from benchmark import load_questions
from benchmark.score import results_match

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
SAMPLE_ROWS = 293
DEFAULT_TODAY = date(2026, 11, 2)  # Fall 2026, the term of the sample events
REFERENCE_CAP = 100_000


class BenchmarkError(Exception):
    """The benchmark cannot run; the message is safe to print."""


@dataclass
class Profile:
    name: str
    preset: str
    model: str
    json_mode: bool | None


@dataclass
class Outcome:
    id: str
    question: str
    ordered: bool
    reference_sql: str
    passed: bool
    reason: str
    kind: str  # answer | clarification | error
    sql: str | None
    interpretation: str | None
    assumptions: list[str]
    attempts: int
    latency_ms: int
    row_count: int | None


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m benchmark.run",
        description="Run the 20-question chatbot benchmark against a stored LLM profile.",
    )
    parser.add_argument("--profile", required=True, help="the LLM profile's name")
    parser.add_argument(
        "--today",
        type=date.fromisoformat,
        default=DEFAULT_TODAY,
        help=f"the date the chatbot is told it is (default {DEFAULT_TODAY.isoformat()})",
    )
    parser.add_argument("--only", help="comma-separated question ids, e.g. q01,q05")
    parser.add_argument(
        "--min-score", type=int, help="exit with status 1 when fewer questions pass"
    )
    return parser.parse_args(argv)


def _select(questions: list[dict], only: str | None) -> list[dict]:
    if not only:
        return questions
    wanted = [part.strip() for part in only.split(",") if part.strip()]
    known = {q["id"] for q in questions}
    unknown = [qid for qid in wanted if qid not in known]
    if unknown:
        raise BenchmarkError(f"Unknown question id(s): {', '.join(unknown)}.")
    return [q for q in questions if q["id"] in wanted]


def _load_profile(name: str, settings: Settings) -> tuple[BaseChatModel, Profile]:
    """Check the sample data, then build the profile's chat model. The key stays in here."""
    with SessionLocal(bind=get_app_engine()) as session:
        rows = session.scalar(text("SELECT count(*) FROM hub.attendance"))
        if rows != SAMPLE_ROWS:
            raise BenchmarkError(
                f"hub.attendance has {rows} rows; the benchmark needs exactly the "
                f"{SAMPLE_ROWS} sample rows. Start from an empty database and "
                f'run "uv run python -m app.samples" first.'
            )
        profile_id = session.scalar(select(LlmProfile.id).where(LlmProfile.name == name))
        if profile_id is None:
            raise BenchmarkError(f'No LLM profile named "{name}". Add it in Settings.')
        try:
            profile, api_key = get_profile_with_key(session, profile_id)
        except HubError as exc:
            raise BenchmarkError(exc.message) from None
        model = build_chat_model(profile, api_key, settings=settings)
        return model, Profile(profile.name, profile.preset, profile.model, profile.json_mode)


def _reference(q: dict) -> QueryResult:
    try:
        guarded = guard_sql(q["reference_sql"], limit=REFERENCE_CAP)
        result = run_readonly(guarded.sql, max_rows=REFERENCE_CAP, engine=get_chatbot_engine())
    except (GuardError, DBAPIError) as exc:
        raise BenchmarkError(
            f"The reference SQL of {q['id']} failed ({type(exc).__name__})."
        ) from None
    if result.truncated:
        raise BenchmarkError(f"The reference result of {q['id']} is over {REFERENCE_CAP} rows.")
    return result


async def _no_record(state: ChatState) -> int:
    return 0  # the benchmark does not write chat_turn rows


async def _ask(
    q: dict, model: BaseChatModel, json_mode: bool | None, settings: Settings, today: date
) -> tuple[ChatState, int, dict | None]:
    """One graph run: its final state, latency, and an error the graph could not report."""
    deps = ChatDeps(
        model=model,
        json_mode=json_mode,
        share_results=False,  # no rows reach the model
        settings=settings,
        chatbot_engine=get_chatbot_engine(),
        record_turn=_no_record,
    )
    graph = build_chat_graph(deps)
    state: ChatState = {}
    failure: dict | None = None
    started = time.monotonic()
    try:
        async with asyncio.timeout(settings.turn_timeout_s) as scope:
            async for snapshot in graph.astream(
                {"question": q["question"], "history": [], "today": today},
                stream_mode="values",
            ):
                state = snapshot
    except TimeoutError:
        failure = (
            {"code": "turn_timeout", "message": "the question took too long"}
            if scope.expired()  # else a timeout raised inside the graph
            else {"code": "internal_error", "message": "TimeoutError"}
        )
    except Exception as exc:  # noqa: BLE001 - type only: a message could carry a value
        logger.error("Benchmark question %s failed (%s)", q["id"], type(exc).__name__)
        failure = {"code": "internal_error", "message": type(exc).__name__}
    return state, int((time.monotonic() - started) * 1000), failure


def _score(
    q: dict, expected: QueryResult, state: ChatState, failure: dict | None, ms: int
) -> Outcome:
    draft = state.get("draft")
    result = state.get("result")
    kind = "error" if failure else state.get("outcome", "error")
    passed = False
    if failure:
        reason = f"error: {failure['code']} ({failure['message']})"
    elif kind == "answer" and result is not None:
        passed = results_match(expected, result, ordered=q["ordered"])
        reason = (
            "matches the reference"
            if passed
            else f"result differs from the reference ({result.row_count} rows; "
            f"{expected.row_count} expected)"
        )
    elif kind == "clarification":
        asked = draft.clarification_question if draft else None
        reason = f"asked a clarification instead of answering: {asked}"
    else:
        error = state.get("error") or {}  # the graph's sanitized, user-facing error
        reason = f"error: {error.get('code', 'unknown')} ({error.get('message', '')})"
    return Outcome(
        id=q["id"],
        question=q["question"],
        ordered=q["ordered"],
        reference_sql=q["reference_sql"].strip(),
        passed=passed,
        reason=reason,
        kind=kind,
        sql=draft.sql if draft and draft.kind == "sql" else None,
        interpretation=draft.interpretation if draft else None,
        assumptions=list(draft.assumptions) if draft else [],
        attempts=state.get("attempts", 0),
        latency_ms=ms,
        row_count=result.row_count if result is not None else None,
    )


async def _run_all(
    questions: list[dict],
    references: dict[str, QueryResult],
    model: BaseChatModel,
    profile: Profile,
    settings: Settings,
    today: date,
) -> list[Outcome]:
    outcomes: list[Outcome] = []
    json_mode = profile.json_mode
    for q in questions:
        state, ms, failure = await _ask(q, model, json_mode, settings, today)
        if json_mode is None and state.get("json_mode_detected") is not None:
            json_mode = state["json_mode_detected"]  # an untested profile: detect it once
        outcome = _score(q, references[q["id"]], state, failure, ms)
        outcomes.append(outcome)
        attempts = f"{outcome.attempts} attempt{'' if outcome.attempts == 1 else 's'}"
        status = "PASS" if outcome.passed else "FAIL"
        print(f"{q['id']} {status}  {attempts}, {ms / 1000:.1f} s  {outcome.reason}", flush=True)
    return outcomes


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "profile"


def _report_path(started: datetime, profile_name: str) -> Path:
    stem = f"{started:%Y%m%d-%H%M}-{_slug(profile_name)}"
    path = REPORTS_DIR / f"{stem}.md"
    n = 2
    while path.exists():  # never overwrite an earlier run's report
        path = REPORTS_DIR / f"{stem}-{n}.md"
        n += 1
    return path


def _fence(sql: str) -> str:
    return f"```sql\n{sql.strip()}\n```"


def _render(outcomes: list[Outcome], profile: Profile, started: datetime, today: date) -> str:
    score = sum(o.passed for o in outcomes)
    lines = [
        f"# Benchmark: {profile.name}",
        "",
        f"Score: {score}/{len(outcomes)}",
        "",
        f"- Run: {started:%Y-%m-%d %H:%M}",
        f"- Profile: {profile.name} (preset {profile.preset}, model {profile.model})",
        f"- Prompt version: {PROMPT_VERSION}",
        f"- Today: {today.isoformat()}",
        "- Results shared with the model: no (the benchmark scores the SQL's result only)",
        "",
        "| Question | Result | Attempts | Latency (ms) | Outcome |",
        "|---|---|---|---|---|",
    ]
    for o in outcomes:
        status = "PASS" if o.passed else "FAIL"
        lines.append(f"| {o.id} | {status} | {o.attempts} | {o.latency_ms} | {o.kind} |")
    for o in outcomes:
        status = "PASS" if o.passed else "FAIL"
        lines += [
            "",
            f"## {o.id} {status}",
            "",
            f"Question: {o.question}",
            "",
            f"- Result: {status}, {o.reason}",
            f"- Attempts: {o.attempts}",
            f"- Latency: {o.latency_ms} ms",
            f"- Rows returned: {o.row_count if o.row_count is not None else 'none'}",
            f"- Ordered: {'yes' if o.ordered else 'no'}",
        ]
        if o.interpretation:
            lines.append(f"- Interpretation: {o.interpretation}")
        for assumption in o.assumptions:
            lines.append(f"- Assumption: {assumption}")
        lines.append("")
        if o.sql:
            lines += ["Generated SQL:", "", _fence(o.sql)]
        else:
            lines.append("Generated SQL: none")
        if not o.passed:
            lines += ["", "Reference SQL:", "", _fence(o.reference_sql)]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        return _main(args)
    except BenchmarkError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - type only: a message could carry a URL or a key
        print(f"The benchmark could not run ({type(exc).__name__}).", file=sys.stderr)
        return 2


def _main(args: argparse.Namespace) -> int:
    settings = get_settings()
    started = datetime.now()
    questions = _select(load_questions(), args.only)
    model, profile = _load_profile(args.profile, settings)
    references = {q["id"]: _reference(q) for q in questions}

    print(f"Running {len(questions)} question(s) with profile {profile.name!r}", flush=True)
    outcomes = asyncio.run(_run_all(questions, references, model, profile, settings, args.today))
    score = sum(o.passed for o in outcomes)
    path = _report_path(started, profile.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_render(outcomes, profile, started, args.today), encoding="utf-8")
    print(f"Score: {score}/{len(outcomes)}")
    print(f"Report: {path}")
    if args.min_score is not None and score < args.min_score:
        print(f"The score {score} is below the minimum of {args.min_score}.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
