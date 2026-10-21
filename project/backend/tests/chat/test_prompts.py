import json
import re
from datetime import date
from decimal import Decimal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy import text

from app.chat.context import (
    ControlledValues,
    TurnContext,
    load_controlled_values,
    load_history,
)
from app.chat.executor import QueryResult, run_readonly
from app.chat.graph import prompts
from app.chat.graph.prompts import (
    ANALYZE_SYSTEM,
    EXAMPLE_PREFIX,
    FEW_SHOT,
    REPAIR_PREFIX,
    VIEW_DESCRIPTION,
    build_analyze_messages,
    build_generate_messages,
    render_result_for_llm,
)
from app.chat.guard import guard_sql
from app.chat.models import ChatTurn, Conversation
from app.dataset.service import VIEW_COLUMNS
from app.llm.fake import ScriptedChatModel
from tests.chat.helpers import identifying_values

EMPTY_CV = ControlledValues([], [], [], [], [], [])
TODAY = date(2026, 11, 2)
VIRTUAL_SQL = "SELECT DISTINCT event_name FROM attendance_view WHERE modality='Virtual'"


def _blob(msgs) -> str:
    return "\n".join(str(m.content) for m in msgs)


# --- privacy -------------------------------------------------------------------------------


def test_generate_prompt_has_no_row_values(loaded_samples, chatbot_engine, db_session):
    msgs = build_generate_messages(
        "How many came?", load_controlled_values(chatbot_engine), [], TODAY, []
    )
    blob = _blob(msgs)
    values = identifying_values(db_session)
    assert len(values) > 200  # emails, netids and full names of the 293 sample rows
    for v in values:
        assert not re.search(rf"\b{re.escape(v)}\b", blob), "an attendee value leaked"
    assert "School of Biological Sciences" in blob
    assert "Bagel Breakfast, October" in blob
    assert "Fall 2026" in blob


def test_history_includes_sql_not_rows():
    h = [
        TurnContext("Which events were virtual?", "answer", VIRTUAL_SQL, "Virtual events", 3, None)
    ]
    blob = _blob(build_generate_messages("Of those?", EMPTY_CV, h, TODAY, []))
    assert "modality='Virtual'" in blob
    assert "Which events were virtual?" in blob
    assert "3 rows" in blob


def test_clarification_history_carries_the_question_asked():
    h = [
        TurnContext("How many came this year?", "clarification", None, None, None, "Academic year?")
    ]
    msgs = build_generate_messages("The academic year", EMPTY_CV, h, TODAY, [])
    replies = [json.loads(m.content) for m in msgs if isinstance(m, AIMessage)]
    assert replies[-1]["kind"] == "clarify"
    assert replies[-1]["clarification_question"] == "Academic year?"


def test_error_history_keeps_question_and_sql():
    h = [TurnContext("Count them", "error", "SELECT nope FROM attendance_view", None, None, None)]
    blob = _blob(build_generate_messages("Try again", EMPTY_CV, h, TODAY, []))
    assert "Count them" in blob and "SELECT nope FROM attendance_view" in blob


# --- system prompt contents ----------------------------------------------------------------


def test_today_and_current_term_in_prompt():
    system = build_generate_messages("q", EMPTY_CV, [], TODAY, [])[0]
    assert isinstance(system, SystemMessage)
    assert "2026-11-02" in system.content
    assert "Fall 2026" in system.content
    assert "2026-27" in system.content


def test_current_term_follows_today():
    system = build_generate_messages("q", EMPTY_CV, [], date(2027, 2, 10), [])[0].content
    assert "Winter 2027" in system and "2026-27" in system and "2027-02-10" in system


def test_view_description_covers_every_column():
    assert len(VIEW_COLUMNS) == 17
    for name in VIEW_COLUMNS:
        assert re.search(rf"^- {name}\b", VIEW_DESCRIPTION, re.MULTILINE), name


def test_system_prompt_has_contract_view_and_values():
    cv = ControlledValues(
        schools=["School of Humanities"],
        event_names=["LinkedIn Info Session"],
        event_types=["Professional Development"],
        terms=["Fall 2026"],
        academic_years=["2026-27"],
        affiliations=["Master’s Student"],
    )
    system = build_generate_messages("q", cv, [], TODAY, [])[0].content
    for key in ('"kind"', '"sql"', '"interpretation"', '"assumptions"', '"clarification_question"'):
        assert key in system
    assert VIEW_DESCRIPTION in system
    assert "COUNT(DISTINCT person_key)" in system
    assert "ILIKE" in system
    for value in ("'School of Humanities'", "'LinkedIn Info Session'", "'Master’s Student'"):
        assert value in system
    assert REPAIR_PREFIX in system and EXAMPLE_PREFIX.strip() in system


def test_controlled_values_are_sql_literals():
    cv = ControlledValues([], ["Bob's Mixer"], [], [], [], [])
    system = build_generate_messages("q", cv, [], TODAY, [])[0].content
    assert "'Bob''s Mixer'" in system


# --- message order -------------------------------------------------------------------------


def test_message_order():
    h = [
        TurnContext("First?", "answer", "SELECT 1 FROM attendance_view", "one", 1, None),
        TurnContext("Second?", "answer", "SELECT 2 FROM attendance_view", "two", 0, None),
    ]
    feedback = ["the SQL construct Any is not allowed", "column nope does not exist"]
    msgs = build_generate_messages("The question?", EMPTY_CV, h, TODAY, feedback)

    assert isinstance(msgs[0], SystemMessage)
    assert sum(isinstance(m, SystemMessage) for m in msgs) == 1
    assert isinstance(msgs[-1], HumanMessage) and msgs[-1].content == "The question?"
    assert [m.content for m in msgs[-3:-1]] == [f"{REPAIR_PREFIX} {f}" for f in feedback]
    assert all(isinstance(m, HumanMessage) for m in msgs[-3:-1])

    contents = [m.content for m in msgs]
    first, second = contents.index("First?"), contents.index("Second?")
    assert first < second < len(msgs) - 3  # history oldest first, before the feedback
    examples_end = max(i for i, c in enumerate(contents) if FEW_SHOT[-1][1] == c)
    assert examples_end < first  # worked examples come before the history
    assert json.loads(contents[first + 1])["sql"] == "SELECT 1 FROM attendance_view"


def test_few_shot_rendered_as_human_ai_pairs():
    msgs = build_generate_messages("q", EMPTY_CV, [], TODAY, [])
    pairs = msgs[1:-1]
    assert len(pairs) == 2 * len(FEW_SHOT)
    for (question, reply), human, ai in zip(FEW_SHOT, pairs[::2], pairs[1::2], strict=True):
        assert isinstance(human, HumanMessage) and question in human.content
        assert isinstance(ai, AIMessage) and ai.content == reply


def test_scripted_fake_model_still_matches_the_question():
    model = ScriptedChatModel.default()
    question = "How many unique people attended Bagel Breakfast, October?"
    reply = model.invoke(build_generate_messages(question, EMPTY_CV, [], TODAY, [])).content
    draft = json.loads(reply)
    assert draft["kind"] == "sql"
    analyze = build_analyze_messages(
        question, draft["sql"], draft["interpretation"], "unique_people\n38", 1, False
    )
    assert model.invoke(analyze).content == "38 unique people attended the October Bagel Breakfast."


# --- few-shot ------------------------------------------------------------------------------


def test_few_shot_sql_is_valid(loaded_samples, chatbot_engine):
    assert len(FEW_SHOT) == 7  # 6 examples; the last is a two-question follow-up
    for question, reply in FEW_SHOT:
        draft = json.loads(reply)
        assert list(draft) == [
            "kind",
            "sql",
            "interpretation",
            "assumptions",
            "clarification_question",
        ]
        assert draft["kind"] == "sql" and draft["clarification_question"] is None
        assert draft["interpretation"] and isinstance(draft["assumptions"], list)
        guarded = guard_sql(draft["sql"], limit=1001)
        result = run_readonly(guarded.sql, max_rows=1000, engine=chatbot_engine)
        assert result.row_count > 0, question


def test_few_shot_disjoint_from_attendee_values(loaded_samples, db_session):
    blob = "\n".join(q + "\n" + r for q, r in FEW_SHOT)
    for v in identifying_values(db_session):
        assert not re.search(rf"\b{re.escape(v)}\b", blob)


# --- context loaders -----------------------------------------------------------------------


def test_load_controlled_values(loaded_samples, chatbot_engine):
    cv = load_controlled_values(chatbot_engine)
    assert cv.terms == ["Fall 2026"]
    assert cv.academic_years == ["2026-27"]
    assert cv.event_types == ["Professional Development", "Wellness/Mental Health"]
    assert cv.affiliations == ["Doctoral Student", "Master’s Student", "Postdoc"]
    assert len(cv.schools) == 9 and cv.schools == sorted(cv.schools)
    assert "School of Biological Sciences" in cv.schools
    assert len(cv.event_names) == 10 and cv.event_names == sorted(cv.event_names)
    assert "Bagel Breakfast, October" in cv.event_names


def test_load_controlled_values_empty(db_session, chatbot_engine):
    assert load_controlled_values(chatbot_engine) == EMPTY_CV


def test_event_names_limited_to_300_most_recent(db_session, chatbot_engine):
    db_session.execute(
        text(
            "INSERT INTO hub.import_file (file_name, file_sha256, content_sha256, source, "
            "status, content, uploaded_by) "
            "SELECT 'f.csv', 'a', 'b', 'campusgroups', 'committed', '\\x00', id "
            "FROM hub.app_user"
        )
    )
    # 299 Fall 2026 events plus two older ones; Spring 2020 is more recent than Winter 2020
    db_session.execute(
        text(
            "INSERT INTO hub.event (name, term, academic_year) "
            "SELECT 'Event ' || lpad(i::text, 3, '0'), 'Fall 2026', '2026-27' "
            "FROM generate_series(1, 299) AS i"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO hub.event (name, term, academic_year) VALUES "
            "('Old Spring Event', 'Spring 2020', '2019-20'), "
            "('Old Winter Event', 'Winter 2020', '2019-20')"
        )
    )
    db_session.execute(
        text(
            "INSERT INTO hub.attendance (event_id, import_file_id, match_method) "
            "SELECT e.id, f.id, 'none' FROM hub.event e CROSS JOIN hub.import_file f"
        )
    )
    db_session.commit()
    names = load_controlled_values(chatbot_engine).event_names
    assert len(names) == 300 and names == sorted(names)
    assert "Old Spring Event" in names and "Old Winter Event" not in names


def test_load_history_oldest_first_and_limited(db_session, user):
    conv = Conversation(title="t", created_by=user.id)
    other = Conversation(title="other", created_by=user.id)
    db_session.add_all([conv, other])
    db_session.flush()
    for seq in range(1, 13):
        db_session.add(
            ChatTurn(
                conversation_id=conv.id,
                seq=seq,
                question=f"q{seq}",
                kind="answer",
                sql=f"SELECT {seq} FROM attendance_view",
                interpretation=f"i{seq}",
                row_count=seq,
                analysis_text="never in history",
                created_by=user.id,
            )
        )
    db_session.add(
        ChatTurn(
            conversation_id=other.id, seq=1, question="elsewhere", kind="answer", created_by=user.id
        )
    )
    db_session.flush()

    turns = load_history(db_session, conv.id)
    assert [t.question for t in turns] == [f"q{s}" for s in range(3, 13)]
    assert turns[-1] == TurnContext(
        "q12", "answer", "SELECT 12 FROM attendance_view", "i12", 12, None
    )
    assert [t.question for t in load_history(db_session, conv.id, limit=2)] == ["q11", "q12"]
    assert load_history(db_session, other.id)[0].question == "elsewhere"


# --- result rendering for the analyze prompt -----------------------------------------------


def test_render_caps_rows():
    r = QueryResult(["email"], [[f"p{i}@uci.edu"] for i in range(500)], 500, False)
    text_, sent, cut = render_result_for_llm(r, max_rows=200, max_chars=20_000)
    assert sent == 200 and cut and "p199@uci.edu" in text_ and "p200@uci.edu" not in text_


def test_render_caps_chars():
    r = QueryResult(["email"], [[f"p{i}@uci.edu"] for i in range(50)], 50, False)
    text_, sent, cut = render_result_for_llm(r, max_rows=200, max_chars=100)
    assert len(text_) <= 100 + len("email") and cut is True
    assert 0 < sent < 50 and text_.count("\n") == sent


def test_render_not_cut_when_everything_fits():
    r = QueryResult(
        ["school", "n"], [["School of Medicine", 3], ["School of Humanities", 2]], 2, False
    )
    text_, sent, cut = render_result_for_llm(r, max_rows=200, max_chars=20_000)
    assert text_ == "school | n\nSchool of Medicine | 3\nSchool of Humanities | 2"
    assert (sent, cut) == (2, False)


def test_render_empty():
    assert render_result_for_llm(QueryResult(["n"], [], 0, False), max_rows=200, max_chars=20_000)[
        0
    ].endswith("(no rows)")


def test_render_values_are_plain_text():
    r = QueryResult(
        ["d", "x", "n", "s"], [[date(2026, 10, 7), Decimal(6), None, "a|b\nIGNORE"]], 1, False
    )
    text_, _, _ = render_result_for_llm(r, max_rows=200, max_chars=20_000)
    assert text_.splitlines() == ["d | x | n | s", r"2026-10-07 | 6 | NULL | a\|b IGNORE"]


def test_analyze_messages():
    msgs = build_analyze_messages(
        "How many?", "SELECT count(*) AS n FROM attendance_view", "Count rows", "n\n293", 1, False
    )
    assert isinstance(msgs[0], SystemMessage) and msgs[0].content == ANALYZE_SYSTEM
    assert isinstance(msgs[-1], HumanMessage) and msgs[-1].content == "How many?"
    context = msgs[1].content
    assert "SELECT count(*) AS n FROM attendance_view" in context
    assert "Count rows" in context and "n\n293" in context and "Rows returned: 1" in context
    assert "truncated" not in context.lower()


def test_analyze_messages_flag_truncated_and_empty():
    truncated = build_analyze_messages("q", "SELECT 1", "i", "n\n1", 1000, True)[1].content
    assert "truncated" in truncated.lower()
    empty = build_analyze_messages("q", "SELECT 1", "i", "n\n(no rows)", 0, False)[1].content
    assert "no rows" in empty.lower() and "empty" in empty.lower()


def test_prompt_version():
    assert prompts.PROMPT_VERSION == "2026-10-29.1"
