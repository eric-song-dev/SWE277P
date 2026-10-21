"""Nodes and routing of the chat graph (spec 7.1).

Each node writes UI events with ``get_stream_writer()`` as ``{"event": <name>, "data": {...}}``
(spec 7.6). Rows reach the model only in ``analyze``, and only when results are shared; repair
feedback is our own text, the guard's reason or the sanitizer's feedback, never row values.
"""

import asyncio
import logging
from datetime import date
from typing import Literal

from langchain_core.messages import BaseMessage
from langgraph.config import get_stream_writer
from sqlalchemy.exc import DBAPIError

from app.chat.context import load_controlled_values
from app.chat.error_sanitizer import sanitize_db_error
from app.chat.executor import run_readonly
from app.chat.graph import prompts
from app.chat.graph.state import ChatDeps, ChatState, parse_draft
from app.chat.guard import GuardError, guard_sql
from app.chat.summary import local_summary
from app.llm.errors import is_response_format_unsupported, map_llm_error
from app.llm.factory import json_mode_kwargs

logger = logging.getLogger(__name__)


def _emit(event: str, **data: object) -> None:
    get_stream_writer()({"event": event, "data": data})


def _step(name: str, attempt: int) -> None:
    _emit("step", name=name, attempt=attempt)


def _on_failure(state: ChatState) -> Literal["repair", "finalize"] | None:
    if state.get("outcome") == "error":
        return "finalize"
    if state.get("failure"):
        return "repair"
    return None


def route(state: ChatState) -> Literal["clarify", "guard", "repair", "finalize"]:
    """After generate: clarify drafts to clarify, SQL drafts to guard."""
    return _on_failure(state) or ("clarify" if state["draft"].kind == "clarify" else "guard")


def after_guard(state: ChatState) -> Literal["execute", "repair", "finalize"]:
    return _on_failure(state) or "execute"


def after_execute(state: ChatState) -> Literal["analyze", "repair", "finalize"]:
    return _on_failure(state) or "analyze"


class ChatNodes:
    def __init__(self, deps: ChatDeps):
        self.deps = deps

    def _failed(self, attempt: int, feedback: str, code: str, message: str) -> ChatState:
        """A failed attempt: repair while generations remain, else end the turn with ``code``."""
        if attempt >= self.deps.settings.max_generations:
            return {"outcome": "error", "error": {"code": code, "message": message}}
        return {"failure": feedback}

    async def load_context(self, state: ChatState) -> ChatState:
        controlled = await asyncio.to_thread(load_controlled_values, self.deps.chatbot_engine)
        return {
            "controlled": controlled,
            "history": state.get("history", []),
            "today": state.get("today") or date.today(),
            "attempts": 0,
            "feedback": [],
            "results_shared": False,
            "json_mode_detected": None,
        }

    async def _ask(self, messages: list[BaseMessage], state: ChatState, update: ChatState) -> str:
        """One generate call. Uses JSON mode unless the profile says it is unsupported; for an
        untested profile a rejected ``response_format`` is retried once without it (spec 7.3),
        and what was detected goes into ``update``."""
        model = self.deps.model
        mode = self.deps.json_mode
        if mode is None:
            mode = state.get("json_mode_detected")
        if mode is False:
            return str((await model.ainvoke(messages)).text)
        try:
            reply = await model.bind(**json_mode_kwargs()).ainvoke(messages)
        except Exception as exc:
            if mode is not None or not is_response_format_unsupported(exc):
                raise
            update["json_mode_detected"] = False
            return str((await model.ainvoke(messages)).text)
        if mode is None:
            update["json_mode_detected"] = True
        return str(reply.text)

    async def generate(self, state: ChatState) -> ChatState:
        attempt = state["attempts"] + 1
        _step("generating", attempt)
        messages = prompts.build_generate_messages(
            state["question"],
            state["controlled"],
            state["history"],
            state["today"],
            state["feedback"],
        )
        update: ChatState = {"attempts": attempt}
        try:
            raw = await self._ask(messages, state, update)
        except Exception as exc:  # noqa: BLE001 - every provider failure ends the turn, no repair
            err = map_llm_error(exc)
            return update | {
                "outcome": "error",
                "error": {"code": err.code, "message": err.message},
            }
        try:
            draft = parse_draft(raw)
        except ValueError as exc:
            message = (
                "The AI model did not reply in the expected format, even after retrying. "
                "Try again, or rephrase the question."
            )
            return update | self._failed(attempt, str(exc), "invalid_llm_reply", message)
        if draft.kind == "sql":
            _emit(
                "sql",
                sql=draft.sql,
                interpretation=draft.interpretation,
                assumptions=draft.assumptions,
            )
        return update | {"draft": draft}

    async def clarify(self, state: ChatState) -> ChatState:
        _emit("clarification", question=state["draft"].clarification_question)
        return {"outcome": "clarification"}

    async def guard(self, state: ChatState) -> ChatState:
        attempt = state["attempts"]
        _step("checking", attempt)
        try:
            # one row over the display cap, so the executor can tell the result was truncated
            guarded = guard_sql(state["draft"].sql, limit=self.deps.settings.display_row_cap + 1)
        except GuardError as exc:
            message = (
                f"The AI model's SQL was not allowed, even after retrying ({exc.reason}). "
                "Try rephrasing the question."
            )
            return self._failed(attempt, exc.reason, "sql_rejected", message)
        return {"guarded_sql": guarded.sql}

    async def execute(self, state: ChatState) -> ChatState:
        attempt = state["attempts"]
        _step("running", attempt)
        try:
            result = await asyncio.to_thread(
                run_readonly,
                state["guarded_sql"],
                max_rows=self.deps.settings.display_row_cap,
                engine=self.deps.chatbot_engine,
            )
        except DBAPIError as exc:
            sanitized = sanitize_db_error(exc)
            message = (
                f"{sanitized.user_message} The AI model could not fix the query, even after "
                "retrying. Try rephrasing the question."
            )
            return self._failed(attempt, sanitized.feedback, "query_failed", message)
        _emit(
            "result",
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            truncated=result.truncated,
        )
        return {"result": result}

    async def repair(self, state: ChatState) -> ChatState:
        _step("repairing", state["attempts"])
        return {"feedback": [*state["feedback"], state["failure"]], "failure": None}

    async def _llm_analysis(self, state: ChatState) -> str:
        settings = self.deps.settings
        result, draft = state["result"], state["draft"]
        result_text, _, cut = prompts.render_result_for_llm(
            result, max_rows=settings.llm_result_max_rows, max_chars=settings.llm_result_max_chars
        )
        messages = prompts.build_analyze_messages(
            state["question"],
            draft.sql,
            draft.interpretation or "(not stated)",
            result_text,
            result.row_count,
            result.truncated or cut,
        )
        parts: list[str] = []
        async for chunk in self.deps.model.astream(messages):
            if text := str(chunk.text):
                parts.append(text)
                _emit("analysis_delta", text=text)
        return "".join(parts).strip()

    async def analyze(self, state: ChatState) -> ChatState:
        shared = self.deps.share_results
        text = ""
        if shared:
            _step("analyzing", state["attempts"])
            try:
                text = await self._llm_analysis(state)
            except Exception as exc:  # noqa: BLE001 - the answer stands without the LLM analysis
                logger.warning(
                    "LLM analysis failed (%s); using the local summary", type(exc).__name__
                )
        source = "llm" if text else "local"
        if not text:
            text = local_summary(state["result"])
        _emit("analysis", text=text, source=source, results_shared=shared)
        return {
            "outcome": "answer",
            "analysis": text,
            "analysis_source": source,
            "results_shared": shared,
        }

    async def finalize(self, state: ChatState) -> ChatState:
        if state.get("outcome") == "error":
            error = state["error"]
            _emit("error", code=error["code"], message=error["message"])
        turn_id = await self.deps.record_turn(state)
        _emit("done", turn_id=turn_id)
        return {"turn_id": turn_id}
