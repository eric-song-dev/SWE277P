import json
import re
from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx
import pytest
from langchain_core.messages import BaseMessage
from openai import AuthenticationError, BadRequestError
from pydantic import Field
from sqlalchemy import select

from app.chat.executor import QueryResult
from app.chat.graph.build import build_chat_graph
from app.chat.graph.prompts import ANALYZE_SYSTEM, REPAIR_PREFIX
from app.chat.graph.state import ChatDeps, LlmDraft, parse_draft
from app.chat.guard import GuardError, guard_sql
from app.chat.summary import local_summary
from app.config import Settings, get_settings
from app.dataset.models import Attendance
from app.llm.fake import ScriptedChatModel, ScriptEntry

QUESTION = "How many unique Biological Sciences students came to a Bagel Breakfast?"
SQL6_TEXT = (
    "SELECT COUNT(DISTINCT person_key) AS n FROM attendance_view WHERE school = "
    "'School of Biological Sciences' AND event_name ILIKE 'Bagel Breakfast%'"
)
SQL6 = '{"kind":"sql","sql":"SELECT COUNT(DISTINCT person_key) AS n FROM attendance_view WHERE school = \'School of Biological Sciences\' AND event_name ILIKE \'Bagel Breakfast%\'","interpretation":"Unique BioSci people at Bagel Breakfasts","assumptions":[]}'
BAD_TABLE = '{"kind":"sql","sql":"SELECT * FROM hub.app_user","interpretation":"x"}'
BAD_CAST = json.dumps(
    {
        "kind": "sql",
        "sql": "SELECT CAST(first_name AS integer) AS x FROM attendance_view",
        "interpretation": "x",
    }
)
JSON_FORMAT = {"type": "json_object"}
REQ = httpx.Request("POST", "https://x.test/v1/chat/completions")


def entry(match: str, *generate: str, analyze: str = "") -> ScriptEntry:
    return ScriptEntry(match=match, generate=list(generate), analyze=analyze)


def sql_reply(sql: str) -> str:
    return json.dumps({"kind": "sql", "sql": sql, "interpretation": "x", "assumptions": []})


def names(events: list[dict]) -> list[str]:
    return [e["event"] for e in events]


def steps(events: list[dict]) -> list[tuple[str, int]]:
    return [(e["data"]["name"], e["data"]["attempt"]) for e in events if e["event"] == "step"]


def data(events: list[dict], name: str) -> dict:
    (only,) = [e["data"] for e in events if e["event"] == name]
    return only


def repair_messages(call: list[BaseMessage]) -> list[str]:
    return [str(m.content) for m in call if str(m.content).startswith(REPAIR_PREFIX)]


def is_analyze(call: list[BaseMessage]) -> bool:
    return call[0].content == ANALYZE_SYSTEM


def guard_reason(sql: str) -> str:
    with pytest.raises(GuardError) as exc:
        guard_sql(sql, limit=10)
    return exc.value.reason


class FormatRecordingModel(ScriptedChatModel):
    """Records the response_format of each call; optionally rejects it like some providers."""

    reject_format: bool = False
    formats: list[Any] = Field(default_factory=list)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self.formats.append(kwargs.get("response_format"))
        if self.reject_format and "response_format" in kwargs:
            raise BadRequestError(
                "response_format is not supported",
                response=httpx.Response(400, request=REQ),
                body=None,
            )
        return await super()._agenerate(messages, stop, run_manager, **kwargs)


class AuthFailingModel(ScriptedChatModel):
    def _reply(self, messages):
        self.calls.append(list(messages))
        raise AuthenticationError(
            "invalid key sk-x-secret", response=httpx.Response(401, request=REQ), body=None
        )


class AnalyzeFailingModel(ScriptedChatModel):
    def _reply(self, messages):
        if is_analyze(messages):
            self.calls.append(list(messages))
            raise RuntimeError("provider exploded")
        return super()._reply(messages)


@dataclass
class Run:
    model: ScriptedChatModel
    events: list[dict]
    state: dict  # what record_turn received


@pytest.fixture
def run(loaded_samples, chatbot_engine):
    async def _run(
        script: list[ScriptEntry] | ScriptedChatModel,
        question: str,
        *,
        share: bool = False,
        history=(),
        json_mode: bool | None = True,
        settings: Settings | None = None,
    ) -> Run:
        model = (
            script if isinstance(script, ScriptedChatModel) else ScriptedChatModel(script=script)
        )
        recorded: list[dict] = []

        async def record_turn(state) -> int:
            recorded.append(dict(state))
            return 42

        deps = ChatDeps(
            model, json_mode, share, settings or get_settings(), chatbot_engine, record_turn
        )
        graph = build_chat_graph(deps)
        inputs = {"question": question, "history": list(history), "today": date(2026, 11, 2)}
        events = [chunk async for chunk in graph.astream(inputs, stream_mode="custom")]
        assert len(recorded) == 1
        return Run(model, events, recorded[0])

    return _run


# --- the graph -------------------------------------------------------------------------------


async def test_happy_path_local_summary(run):
    r = await run([entry("biological", SQL6)], QUESTION)
    assert names(r.events) == ["step", "sql", "step", "step", "result", "analysis", "done"]
    assert steps(r.events) == [("generating", 1), ("checking", 1), ("running", 1)]
    # R8: the model's SQL, without the LIMIT the guard adds
    assert r.events[1]["data"] == {
        "sql": SQL6_TEXT,
        "interpretation": "Unique BioSci people at Bagel Breakfasts",
        "assumptions": [],
    }
    assert r.events[4]["data"] == {
        "columns": ["n"],
        "rows": [[6]],
        "row_count": 1,
        "truncated": False,
    }
    assert r.events[5]["data"] == {"text": "n: 6", "source": "local", "results_shared": False}
    assert r.events[6]["data"] == {"turn_id": 42}
    # without sharing, the model is only asked for SQL
    assert len(r.model.calls) == 1 and not is_analyze(r.model.calls[0])
    s = r.state
    assert (s["outcome"], s["attempts"], s["analysis"], s["analysis_source"]) == (
        "answer",
        1,
        "n: 6",
        "local",
    )
    assert s["results_shared"] is False and "error" not in s
    assert s["draft"].sql == SQL6_TEXT and s["guarded_sql"].endswith("LIMIT 1001")
    assert s["result"].rows == [[6]]


async def test_shared_analysis_streams_and_sends_capped_rows(run):
    r = await run([entry("biological", SQL6, analyze="Six students.")], QUESTION, share=True)
    assert names(r.events)[:5] == ["step", "sql", "step", "step", "result"]
    assert names(r.events)[-2:] == ["analysis", "done"]
    assert steps(r.events)[-1] == ("analyzing", 1)
    deltas = [e["data"]["text"] for e in r.events if e["event"] == "analysis_delta"]
    assert deltas and "".join(deltas) == "Six students."
    assert r.events[-2]["data"] == {
        "text": "Six students.",
        "source": "llm",
        "results_shared": True,
    }
    call = r.model.calls[-1]
    assert is_analyze(call) and call[-1].content == QUESTION
    context = str(call[-2].content)  # the analyze prompt carries the result
    assert "<result>\nn\n6\n</result>" in context
    assert SQL6_TEXT in context and "Rows returned: 1." in context
    s = r.state
    assert (s["outcome"], s["analysis_source"], s["results_shared"]) == ("answer", "llm", True)


@pytest.mark.parametrize(
    ("caps", "rows_sent"), [({"llm_result_max_rows": 2}, 2), ({"llm_result_max_chars": 1}, 0)]
)
async def test_analysis_gets_capped_rows_and_is_told_so(run, caps, rows_sent):
    sql = (
        "SELECT school, COUNT(*) AS n FROM attendance_view WHERE school IS NOT NULL "
        "GROUP BY school ORDER BY school"
    )
    settings = get_settings().model_copy(update=caps)
    r = await run(
        [entry("school", sql_reply(sql), analyze="ok")], "By school?", share=True, settings=settings
    )
    assert data(r.events, "result")["row_count"] > 2
    context = str(r.model.calls[-1][-2].content)
    block = context.split("<result>\n", 1)[1].split("\n</result>", 1)[0]
    assert block.splitlines() == ["school | n", *block.splitlines()[1:]]
    assert len(block.splitlines()) == 1 + rows_sent
    assert "Truncated" in context  # rows left out by the LLM caps count as truncation


async def test_display_cap_truncates_and_sql_event_keeps_model_sql(run):
    sql = "SELECT email FROM attendance_view WHERE email IS NOT NULL ORDER BY email"
    settings = get_settings().model_copy(update={"display_row_cap": 5})
    r = await run([entry("emails", sql_reply(sql))], "All emails?", settings=settings)
    assert data(r.events, "sql")["sql"] == sql
    result = data(r.events, "result")
    assert (result["row_count"], result["truncated"], len(result["rows"])) == (5, True, 5)
    assert data(r.events, "analysis")["text"] == "5 rows (showing the first 5)"
    assert r.state["guarded_sql"].endswith("LIMIT 6") and r.state["draft"].sql == sql


async def test_clarification_ends_turn(run):
    reply = '{"kind":"clarify","clarification_question":"Academic or calendar year?"}'
    r = await run([entry("this year", reply)], "How many came this year?")
    assert names(r.events) == ["step", "clarification", "done"]
    assert data(r.events, "clarification") == {"question": "Academic or calendar year?"}
    s = r.state
    assert (s["outcome"], s["attempts"], s["results_shared"]) == ("clarification", 1, False)
    assert s["draft"].clarification_question == "Academic or calendar year?"
    assert len(r.model.calls) == 1


async def test_repair_after_guard_failure(run):
    r = await run([entry("bio", BAD_TABLE, SQL6)], "bio?")
    assert names(r.events) == [
        *("step", "sql", "step", "step"),
        *("step", "sql", "step", "step", "result", "analysis", "done"),
    ]
    assert steps(r.events) == [
        ("generating", 1),
        ("checking", 1),
        ("repairing", 1),
        ("generating", 2),
        ("checking", 2),
        ("running", 2),
    ]
    reason = guard_reason("SELECT * FROM hub.app_user")
    assert repair_messages(r.model.calls[1]) == [
        f"{REPAIR_PREFIX} {reason}"
    ]  # guard reason fed back
    assert repair_messages(r.model.calls[0]) == []
    assert data(r.events, "result")["rows"] == [[6]]
    s = r.state
    assert (s["outcome"], s["attempts"], s["feedback"]) == ("answer", 2, [reason])


async def test_repair_after_db_error_has_no_values(run, db_session):
    r = await run([entry("bio", BAD_CAST, SQL6)], "bio?")
    assert ("repairing", 1) in steps(r.events) and "error" not in names(r.events)
    assert data(r.events, "result")["rows"] == [[6]]
    (feedback,) = repair_messages(r.model.calls[1])
    assert "22P02" in feedback
    first_names = {n for n in db_session.scalars(select(Attendance.first_name)) if n}
    assert len(first_names) > 50
    for name in first_names:
        assert not re.search(rf"\b{re.escape(name)}\b", feedback), "a row value reached the LLM"


@pytest.mark.parametrize(
    ("reply", "code", "sql_events"),
    [
        (BAD_TABLE, "sql_rejected", 3),
        (BAD_CAST, "query_failed", 3),
        ("I would rather not answer in JSON.", "invalid_llm_reply", 0),
    ],
)
async def test_gives_up_after_three(run, reply, code, sql_events):
    r = await run([entry("bio", reply)], "bio?")
    assert len(r.model.calls) == 3  # exactly max_generations generate calls
    assert [n for n, _ in steps(r.events)].count("generating") == 3
    assert [a for n, a in steps(r.events) if n == "repairing"] == [1, 2]
    assert names(r.events)[-2:] == ["error", "done"]
    assert names(r.events).count("sql") == sql_events
    err = data(r.events, "error")
    assert err["code"] == code and set(err) == {"code", "message"} and err["message"]
    s = r.state
    assert (s["outcome"], s["attempts"], s["error"]) == ("error", 3, err)
    assert len(s["feedback"]) == 2 and "result" not in s
    if sql_events:  # the last draft's SQL stays in the state for the turn log
        assert s["draft"].sql == json.loads(reply)["sql"]


async def test_parse_failure_feedback_is_short_and_does_not_echo_reply(run):
    long_reply = "Here is my thinking about the data. " * 200
    r = await run([entry("bio", long_reply, SQL6)], "bio?")
    (feedback,) = repair_messages(r.model.calls[1])
    assert len(feedback) < 300 and "my thinking" not in feedback
    assert data(r.events, "result")["rows"] == [[6]]


@pytest.mark.parametrize(
    "reply",
    [
        "Sure! ```json\n" + SQL6 + "\n``` hope this helps",
        "```json\n" + SQL6 + "\n```",
        json.dumps(
            {
                "kind": "sql",
                "sql": "```sql\n" + SQL6_TEXT + ";\n```",
                "interpretation": "Unique BioSci people at Bagel Breakfasts",
                "assumptions": [],
            }
        ),
    ],
)
async def test_prose_fences_and_semicolon_need_no_repair(run, reply):
    r = await run([entry("bio", reply)], "bio?")
    assert "repairing" not in [n for n, _ in steps(r.events)]
    assert data(r.events, "sql")["sql"] == SQL6_TEXT
    assert data(r.events, "result")["rows"] == [[6]]
    assert r.state["attempts"] == 1 and r.state["draft"].sql == SQL6_TEXT


async def test_empty_result_summary(run):
    r = await run(
        [entry("nobody", sql_reply("SELECT email FROM attendance_view WHERE false"))], "nobody?"
    )
    assert data(r.events, "result") == {
        "columns": ["email"],
        "rows": [],
        "row_count": 0,
        "truncated": False,
    }
    assert data(r.events, "analysis")["text"] == "No matching records."


async def test_empty_result_analyze_prompt_says_empty(run):
    script = [
        entry("nobody", sql_reply("SELECT email FROM attendance_view WHERE false"), analyze="None.")
    ]
    r = await run(script, "nobody?", share=True)
    context = str(r.model.calls[-1][-2].content)
    assert "the result is empty" in context and "(no rows)" in context
    assert data(r.events, "analysis") == {"text": "None.", "source": "llm", "results_shared": True}


async def test_provider_error_no_repair(run):
    r = await run(AuthFailingModel(script=[]), "bio?")
    assert names(r.events) == ["step", "error", "done"]
    err = data(r.events, "error")
    assert err["code"] == "llm_auth_failed" and "sk-x-secret" not in err["message"]
    assert len(r.model.calls) == 1
    s = r.state
    assert (s["outcome"], s["attempts"], s["error"]) == ("error", 1, err)
    assert "draft" not in s


async def test_analysis_failure_falls_back_to_local_summary(run):
    model = AnalyzeFailingModel(script=[entry("biological", SQL6, analyze="unused")])
    r = await run(model, QUESTION, share=True)
    assert "error" not in names(r.events) and names(r.events)[-2:] == ["analysis", "done"]
    assert ("analyzing", 1) in steps(r.events)
    assert data(r.events, "analysis") == {"text": "n: 6", "source": "local", "results_shared": True}
    s = r.state
    assert (s["outcome"], s["analysis_source"], s["results_shared"]) == ("answer", "local", True)
    assert is_analyze(r.model.calls[-1])  # the rows were sent before the call failed


@pytest.mark.parametrize(
    ("json_mode", "formats", "detected"),
    [(True, [JSON_FORMAT], None), (False, [None], None), (None, [JSON_FORMAT], True)],
)
async def test_json_mode_binding(run, json_mode, formats, detected):
    model = FormatRecordingModel(script=[entry("biological", SQL6)])
    r = await run(model, QUESTION, json_mode=json_mode)
    assert model.formats == formats
    assert r.state["json_mode_detected"] is detected


async def test_json_mode_fallback_when_untested(run):
    model = FormatRecordingModel(script=[entry("bio", BAD_TABLE, SQL6)], reject_format=True)
    r = await run(model, "bio?", json_mode=None)
    # attempt 1: JSON mode rejected, then plain; attempt 2 (the repair) goes plain directly
    assert model.formats == [JSON_FORMAT, None, None]
    assert [a for n, a in steps(r.events) if n == "generating"] == [1, 2]
    assert data(r.events, "result")["rows"] == [[6]]
    s = r.state
    assert (s["attempts"], s["json_mode_detected"], s["outcome"]) == (2, False, "answer")


async def test_no_fallback_when_json_mode_is_known(run):
    model = FormatRecordingModel(script=[entry("bio", SQL6)], reject_format=True)
    r = await run(model, "bio?", json_mode=True)
    assert model.formats == [JSON_FORMAT]
    assert data(r.events, "error")["code"] == "llm_bad_request"
    assert r.state["attempts"] == 1


# --- parse_draft -----------------------------------------------------------------------------


def test_parse_draft_plain_and_wrapped():
    plain = parse_draft(SQL6)
    assert plain == LlmDraft(
        kind="sql", sql=SQL6_TEXT, interpretation="Unique BioSci people at Bagel Breakfasts"
    )
    assert parse_draft(f"Here {{is}} it:\n```json\n{SQL6}\n```\nDone.") == plain
    assert parse_draft('{"kind": "clarify", "clarification_question": "Which term?"}') == LlmDraft(
        kind="clarify", clarification_question="Which term?"
    )


def test_parse_draft_cleans_sql_and_tolerates_null_assumptions():
    raw = json.dumps({"kind": "sql", "sql": "```sql\nSELECT 1;\n```", "assumptions": None})
    draft = parse_draft(raw)
    assert (draft.sql, draft.assumptions) == ("SELECT 1", [])


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "SELECT 1",
        "[1, 2]",
        '{"kind": "sql"}',
        '{"kind": "sql", "sql": "```sql\\n```"}',
        '{"kind": "clarify"}',
        '{"kind": "answer", "sql": "SELECT 1"}',
        '{"kind": "sql", "sql": 5}',
        '{"kind": "sql", "sql": "SELECT 1"',
    ],
)
def test_parse_draft_rejects(raw):
    with pytest.raises(ValueError) as exc:
        parse_draft(raw)
    assert 0 < len(str(exc.value)) < 300


# --- local_summary ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("result", "text"),
    [
        (QueryResult(["email"], [], 0, False), "No matching records."),
        (QueryResult(["n"], [[6]], 1, False), "n: 6"),
        (QueryResult(["latest"], [[None]], 1, False), "latest: NULL"),
        (QueryResult(["a", "b"], [[1, 2]], 1, False), "1 row"),
        (QueryResult(["a"], [[1], [2], [3]], 3, False), "3 rows"),
        (QueryResult(["a"], [[1], [2]], 2, True), "2 rows (showing the first 2)"),
    ],
)
def test_local_summary(result, text):
    assert local_summary(result) == text
