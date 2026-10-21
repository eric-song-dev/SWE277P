import asyncio
import json
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.chat.graph.prompts import ANALYZE_SYSTEM
from app.llm.fake import ScriptedChatModel, ScriptEntry


async def test_scripted_model_uses_replies_in_order():
    m = ScriptedChatModel(script=[ScriptEntry(match="bagel", generate=["A", "B"], analyze="X")])
    outs = [
        (await m.ainvoke([SystemMessage("gen"), HumanMessage("Bagel?")])).content for _ in range(3)
    ]
    assert outs == ["A", "B", "B"] and len(m.calls) == 3


async def test_analyze_is_told_apart_by_system_message():
    m = ScriptedChatModel(script=[ScriptEntry(match="bagel", generate=["A"], analyze="X")])
    out = await m.ainvoke([SystemMessage(ANALYZE_SYSTEM), HumanMessage("question: BAGEL")])
    assert out.content == "X"


async def test_unmatched_question_clarifies():
    m = ScriptedChatModel.default()
    out = json.loads((await m.ainvoke([HumanMessage("weather?")])).content)
    assert out["kind"] == "clarify"


async def test_default_script_entries():
    m = ScriptedChatModel.default()
    asks = {
        "How many unique people attended Bagel Breakfast, October?": "unique_people",
        "Of those, how many are international?": "international_people",
        "Emails of everyone who attended any bagel breakfast": "SELECT DISTINCT email",
    }
    for q, needle in asks.items():
        out = json.loads((await m.ainvoke([SystemMessage("gen"), HumanMessage(q)])).content)
        assert out["kind"] == "sql" and needle in out["sql"] and out["interpretation"]
    out = json.loads((await m.ainvoke([HumanMessage("How many students this year?")])).content)
    assert out["clarification_question"].startswith("Do you mean the 2026-27 academic year")
    analysis = await m.ainvoke(
        [
            SystemMessage(ANALYZE_SYSTEM),
            HumanMessage("unique people attended Bagel Breakfast, October"),
        ]
    )
    assert analysis.content == "38 unique people attended the October Bagel Breakfast."


async def test_bind_extra_kwargs_and_streaming():
    m = ScriptedChatModel(script=[ScriptEntry(match="bagel", generate=["A"], analyze="X")])
    bound = m.bind(response_format={"type": "json_object"})
    assert (await bound.ainvoke([HumanMessage("bagel")])).content == "A"
    chunks = [c.content async for c in m.astream([HumanMessage("bagel")])]
    assert "".join(chunks) == "A"


async def test_delay_applies_to_generate_only(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    m = ScriptedChatModel(
        script=[ScriptEntry(match="bagel", generate=["A"], analyze="X", delay_seconds=2)]
    )
    await m.ainvoke([SystemMessage("gen"), HumanMessage("bagel")])
    assert slept == [2]
    await m.ainvoke([SystemMessage(ANALYZE_SYSTEM), HumanMessage("bagel")])
    assert slept == [2]


async def test_no_delay_by_default(monkeypatch):
    async def boom(seconds):
        raise AssertionError("slept")

    monkeypatch.setattr(asyncio, "sleep", boom)
    m = ScriptedChatModel(script=[ScriptEntry(match="bagel", generate=["A"], analyze="X")])
    await m.ainvoke([HumanMessage("bagel")])


def test_sync_generate_sleeps_with_time_sleep(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", slept.append)
    m = ScriptedChatModel(
        script=[ScriptEntry(match="bagel", generate=["A"], analyze="X", delay_seconds=3)]
    )
    m.invoke([HumanMessage("bagel")])
    assert slept == [3]


def test_default_script_has_the_walkthrough_entries():
    by_match = {e.match: e for e in ScriptedChatModel.default().script}
    assert by_match["Demo slow question"].delay_seconds == 10
    assert len(by_match["Demo repaired query"].generate) == 2
