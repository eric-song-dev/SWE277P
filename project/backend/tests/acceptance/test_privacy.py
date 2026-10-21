import json
import re

import pytest
from sqlalchemy import select

from app.chat import service
from app.config import get_settings
from app.dataset.models import Attendance
from app.llm.fake import ScriptedChatModel, ScriptEntry
from tests.chat.helpers import identifying_values

pytestmark = pytest.mark.acceptance

# Benchmark-style questions that name no attendee (controller ruling R13).
QUESTIONS = [
    "How many unique people attended Bagel Breakfast, October?",
    "Of those, how many are international?",
    "List emails of everyone who attended any Bagel Breakfast",
    "How many people came this year?",
]
ALL_EMAILS_Q = "Show every attendee email address in the dataset"
ALL_EMAILS_SQL = json.dumps(
    {
        "kind": "sql",
        "sql": "SELECT email FROM attendance_view WHERE email IS NOT NULL ORDER BY email",
        "interpretation": "Every attendee email address.",
        "assumptions": [],
    }
)


@pytest.fixture
def fake_llm(monkeypatch):
    monkeypatch.setenv("HUB_ENABLE_FAKE_LLM", "true")
    get_settings.cache_clear()
    yield monkeypatch
    monkeypatch.undo()
    get_settings.cache_clear()


def make_profile(client, share: bool) -> int:
    res = client.post(
        "/api/llm-profiles",
        json={
            "name": "Demo",
            "preset": "fake",
            "model": "scripted",
            "share_results_with_llm": share,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def run_questions(client, profile_id, questions, share_results) -> None:
    cid = client.post("/api/conversations").json()["id"]
    for question in questions:
        with client.stream(
            "POST",
            f"/api/conversations/{cid}/messages",
            json={
                "question": question,
                "llm_profile_id": profile_id,
                "share_results": share_results,
            },
        ) as r:
            assert r.status_code == 200
            body = r.read().decode()
        assert "event: error" not in body, body
        assert body.rstrip().endswith("}") and "event: done" in body


def all_prompt_text(calls) -> str:
    return "\n".join(str(m.content) for call in calls for m in call)


def leaked(db_session, blob: str) -> list[str]:
    return [v for v in identifying_values(db_session) if re.search(rf"\b{re.escape(v)}\b", blob)]


def inject(fake_llm, model) -> None:
    fake_llm.setattr(service, "build_chat_model", lambda *a, **k: model)


@pytest.mark.parametrize(
    "profile_share,request_share",
    [(False, False), (False, True), (True, False)],
    ids=["profile-off", "profile-off-request-on", "request-off-profile-on"],
)
def test_a6_sharing_off_sends_no_attendee_values(
    client, db_session, loaded_samples, fake_llm, profile_share, request_share
):
    model = ScriptedChatModel.default()
    inject(fake_llm, model)
    profile_id = make_profile(client, profile_share)
    run_questions(client, profile_id, QUESTIONS, request_share)
    assert len(model.calls) >= len(QUESTIONS)
    assert identifying_values(db_session)  # the check below is meaningful
    assert leaked(db_session, all_prompt_text(model.calls)) == []


def test_a6_sharing_on_sends_only_capped_result_rows(client, db_session, loaded_samples, fake_llm):
    fake_llm.setenv("LLM_RESULT_MAX_ROWS", "50")
    get_settings.cache_clear()
    model = ScriptedChatModel(
        script=[ScriptEntry(match="every attendee email", generate=[ALL_EMAILS_SQL], analyze="ok")]
    )
    inject(fake_llm, model)
    profile_id = make_profile(client, True)
    run_questions(client, profile_id, [ALL_EMAILS_Q], True)

    assert len(model.calls) == 2  # one generate call, one analyze call
    analyze_prompt = str(model.calls[-1][-2].content)
    shared = sum(1 for line in analyze_prompt.splitlines() if "@uci.edu" in line)
    assert 0 < shared <= 50
    student_ids = {s for s in db_session.scalars(select(Attendance.student_id)) if s}
    assert student_ids
    assert not any(sid in all_prompt_text(model.calls) for sid in student_ids)
    emails = {e for e in db_session.scalars(select(Attendance.email)) if e}
    assert len(emails) > 50
    generate_blob = all_prompt_text(model.calls[:-1])
    assert not any(e in generate_blob for e in emails)
