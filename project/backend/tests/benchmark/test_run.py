"""The benchmark CLI end to end on hub_test, with the offline scripted model (no network)."""

import asyncio
import json
import logging
import re

import pytest
from sqlalchemy import select, text

from app.chat.graph.prompts import ANALYZE_SYSTEM
from app.config import get_settings
from app.dataset.models import Attendance
from app.llm.crypto import api_key_hint, encrypt_api_key
from app.llm.fake import ScriptedChatModel, ScriptEntry
from app.llm.models import LlmProfile
from benchmark import load_questions, run

KEY = "sk-bench-0123456789-SECRET-tail"
REPORT_NAME = re.compile(r"\d{8}-\d{4}-(?P<slug>[a-z0-9-]+?)(-\d+)?\.md")


def sql_reply(sql: str) -> str:
    return json.dumps({"kind": "sql", "sql": sql, "interpretation": "x", "assumptions": []})


def reference(qid: str) -> str:
    return next(q["reference_sql"] for q in load_questions() if q["id"] == qid)


def question(qid: str) -> str:
    return next(q["question"] for q in load_questions() if q["id"] == qid)


@pytest.fixture
def reports(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "REPORTS_DIR", tmp_path / "reports")
    return tmp_path / "reports"


@pytest.fixture
def add_profile(db_session, user):
    def _add(name: str = "Demo Fake", preset: str = "fake", key: str | None = None) -> None:
        db_session.add(
            LlmProfile(
                name=name,
                preset=preset,
                base_url="" if preset == "fake" else "https://api.openai.com/v1",
                model="scripted" if preset == "fake" else "gpt-test",
                api_key_ciphertext=encrypt_api_key(key) if key else None,
                api_key_hint=api_key_hint(key) if key else None,
                share_results_with_llm=True,  # the runner must not share even when allowed
                json_mode=True,
                created_by=user.id,
            )
        )
        db_session.commit()

    return _add


@pytest.fixture
def use_model(monkeypatch):
    """Replace the factory with one returning ``model``; records the key it was given."""
    seen: dict[str, str] = {}

    def _use(model: ScriptedChatModel) -> dict[str, str]:
        def build(profile, api_key, *, settings, http_async_client=None):
            seen["api_key"] = api_key
            return model

        monkeypatch.setattr(run, "build_chat_model", build)
        return seen

    return _use


def only_report(reports) -> str:
    (path,) = reports.iterdir()
    return path.read_text(encoding="utf-8")


def section(report: str, qid: str) -> str:
    return report.split(f"## {qid} ")[1].split("\n## ")[0]


def attendee_values(db_session) -> set[str]:
    values: set[str] = set()
    for email, first, last in db_session.execute(
        select(Attendance.email, Attendance.first_name, Attendance.last_name)
    ):
        if email:
            values.add(email)
        if first and last:
            values.add(f"{first} {last}")
    return values


def test_refuses_without_the_sample_rows(db_session, add_profile, reports, capsys):
    add_profile()
    assert run.main(["--profile", "Demo Fake"]) == 2
    err = capsys.readouterr().err
    assert "has 0 rows" in err and 'run "uv run python -m app.samples" first' in err
    assert not reports.exists()


def test_unknown_profile_is_refused(loaded_samples, reports, capsys):
    assert run.main(["--profile", "No Such Profile"]) == 2
    assert 'No LLM profile named "No Such Profile"' in capsys.readouterr().err
    assert not reports.exists()


def test_unknown_question_id_is_refused(loaded_samples, add_profile, reports, capsys):
    add_profile()
    assert run.main(["--profile", "Demo Fake", "--only", "q01,q99"]) == 2
    assert "q99" in capsys.readouterr().err
    assert not reports.exists()


def test_fake_profile_end_to_end(loaded_samples, db_session, add_profile, reports, capsys):
    add_profile()
    # the scripted demo model knows q04 and answers anything else with a clarification
    assert run.main(["--profile", "Demo Fake", "--only", "q04,q01"]) == 0
    out = capsys.readouterr().out
    assert "q04 PASS" in out and "q01 FAIL" in out and "Score: 1/2" in out

    (path,) = reports.iterdir()
    match = REPORT_NAME.fullmatch(path.name)
    assert match and match["slug"] == "demo-fake"
    assert str(path) in out
    report = path.read_text(encoding="utf-8")
    assert "Score: 1/2" in report
    assert report.index("## q01 ") < report.index("## q04 ")  # questions in benchmark order
    q04 = section(report, "q04")
    assert "PASS" in q04 and "SELECT DISTINCT email FROM attendance_view" in q04
    assert re.search(r"Attempts: 1\b", q04) and re.search(r"Latency: \d+ ms", q04)
    q01 = section(report, "q01")
    assert "FAIL" in q01 and "clarification" in q01 and "Generated SQL: none" in q01
    # SQL and scores only: no attendee values in the report
    for value in attendee_values(db_session):
        assert value not in report
    # the benchmark does not write chat_turn rows
    assert db_session.scalar(text("SELECT count(*) FROM hub.chat_turn")) == 0


def test_min_score(loaded_samples, add_profile, reports, capsys):
    add_profile()
    assert run.main(["--profile", "Demo Fake", "--only", "q04,q01", "--min-score", "2"]) == 1
    assert run.main(["--profile", "Demo Fake", "--only", "q04,q01", "--min-score", "1"]) == 0
    assert len(list(reports.iterdir())) == 2  # a second run never overwrites the first report
    assert "below the minimum of 2" in capsys.readouterr().err


def test_pass_wrong_answer_and_error(loaded_samples, add_profile, reports, use_model):
    add_profile()
    model = ScriptedChatModel(
        script=[
            ScriptEntry(
                match="emails of everyone", generate=[sql_reply(reference("q04"))], analyze=""
            ),
            # counts records, not unique people: a wrong answer
            ScriptEntry(
                match="unique biological sciences",
                generate=[
                    sql_reply("SELECT count(*) FROM attendance_view WHERE event_name LIKE 'Bagel%'")
                ],
                analyze="",
            ),
            # rejected by the guard on every attempt
            ScriptEntry(
                match="health careers",
                generate=[sql_reply("SELECT * FROM hub.app_user")],
                analyze="",
            ),
        ]
    )
    use_model(model)
    assert run.main(["--profile", "Demo Fake", "--only", "q01,q04,q07", "--min-score", "1"]) == 0
    report = only_report(reports)
    assert "Score: 1/3" in report
    assert "PASS" in section(report, "q04")
    q01 = section(report, "q01")
    assert "FAIL" in q01 and "differs from the reference" in q01 and "count(*)" in q01
    q07 = section(report, "q07")
    assert "FAIL" in q07 and "sql_rejected" in q07 and re.search(r"Attempts: 3\b", q07)


def test_today_is_passed_and_no_rows_reach_the_model(
    loaded_samples, db_session, add_profile, reports, use_model
):
    add_profile()
    model = ScriptedChatModel.default()
    use_model(model)
    assert run.main(["--profile", "Demo Fake", "--only", "q04", "--today", "2027-02-15"]) == 0
    assert model.calls  # the SQL was generated by this model
    # share_results is off: the analyze step never calls the model, so no rows are sent
    assert all(call[0].content != ANALYZE_SYSTEM for call in model.calls)
    sent = "\n".join(str(m.content) for call in model.calls for m in call)
    assert "2027-02-15" in sent
    assert question("q04") in sent
    for value in attendee_values(db_session):
        assert value not in sent


def test_default_today_is_fall_2026(loaded_samples, add_profile, reports, use_model):
    add_profile()
    model = ScriptedChatModel.default()
    use_model(model)
    run.main(["--profile", "Demo Fake", "--only", "q06"])
    assert "2026-11-02" in "\n".join(str(m.content) for m in model.calls[0])


def test_key_is_used_but_never_printed(
    loaded_samples, add_profile, reports, use_model, capsys, caplog
):
    caplog.set_level(logging.DEBUG)
    add_profile(name="OpenAI Test", preset="openai", key=KEY)
    seen = use_model(ScriptedChatModel.default())
    assert run.main(["--profile", "OpenAI Test", "--only", "q04"]) == 0
    assert seen["api_key"] == KEY  # decrypted for the factory only
    out = capsys.readouterr()
    for text_ in (out.out, out.err, caplog.text, only_report(reports)):
        assert KEY not in text_ and "SECRET" not in text_


class SlowModel(ScriptedChatModel):
    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        await asyncio.sleep(5)
        return await super()._agenerate(messages, stop, run_manager, **kwargs)


def test_question_timeout_is_a_failure(
    loaded_samples, add_profile, reports, use_model, monkeypatch
):
    add_profile()
    use_model(SlowModel.default())
    settings = get_settings().model_copy(update={"turn_timeout_s": 0.5})
    monkeypatch.setattr(run, "get_settings", lambda: settings)
    assert run.main(["--profile", "Demo Fake", "--only", "q04"]) == 0
    q04 = section(only_report(reports), "q04")
    assert "FAIL" in q04 and "turn_timeout" in q04
