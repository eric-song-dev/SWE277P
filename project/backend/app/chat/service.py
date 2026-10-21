"""Conversations, the streamed chat turn, rerun and export (spec 7.6, 9).

``run_turn`` streams after the request's session has closed, so it opens its own short sessions
(one per DB step, run via ``asyncio.to_thread``) and never holds one across an LLM call.
"""

import asyncio
import contextlib
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import Response
from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.auth.schemas import CurrentUser
from app.chat.context import TurnContext, load_history
from app.chat.error_sanitizer import sanitize_db_error
from app.chat.executor import QueryResult, run_readonly
from app.chat.graph.build import build_chat_graph
from app.chat.graph.prompts import PROMPT_VERSION
from app.chat.graph.state import ChatDeps, ChatState
from app.chat.guard import GuardError, guard_sql
from app.chat.models import ChatTurn, Conversation
from app.chat.schemas import ConversationDetail, ConversationOut, MessageIn, QueryResultOut, TurnOut
from app.chat.sse import format_sse
from app.config import get_settings
from app.db import SessionLocal, get_app_engine, get_chatbot_engine
from app.errors import HubError
from app.llm.factory import build_chat_model
from app.llm.models import LlmProfile
from app.llm.service import get_profile_with_key

logger = logging.getLogger(__name__)

TITLE_MAX = 80
INTERNAL_ERROR = {
    "code": "internal_error",
    "message": "Something went wrong while answering. Please try again.",
}
TIMEOUT_ERROR = {
    "code": "turn_timeout",
    "message": "The question took too long to answer. Try a simpler question.",
}
DISCONNECT_ERROR = {  # logged only, never sent: nobody is listening
    "code": "client_disconnected",
    "message": "The client disconnected before the answer finished.",
}


def create_conversation(session: Session, user: CurrentUser) -> Conversation:
    conversation = Conversation(title=None, created_by=user.id)
    session.add(conversation)
    session.flush()
    session.refresh(conversation)
    return conversation


def list_conversations(session: Session, user: CurrentUser) -> list[ConversationOut]:
    rows = session.scalars(
        select(Conversation)
        .where(Conversation.created_by == user.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    )
    return [ConversationOut.model_validate(c) for c in rows]


def _conversation(session: Session, conversation_id: int) -> Conversation:
    conversation = session.get(Conversation, conversation_id)
    if conversation is None:
        raise HubError(
            "conversation_not_found", "That conversation no longer exists.", status_code=404
        )
    return conversation


def get_conversation(session: Session, conversation_id: int) -> ConversationDetail:
    conversation = _conversation(session, conversation_id)
    turns = session.scalars(
        select(ChatTurn).where(ChatTurn.conversation_id == conversation_id).order_by(ChatTurn.seq)
    )
    return ConversationDetail(
        **ConversationOut.model_validate(conversation).model_dump(),
        turns=[TurnOut.model_validate(t) for t in turns],
    )


def ensure_conversation(session: Session, conversation_id: int) -> None:
    _conversation(session, conversation_id)


@dataclass
class _Prepared:
    profile_id: int
    preset: str
    model_name: str
    share: bool  # the profile's switch; the request's is ANDed in by run_turn
    json_mode: bool | None
    api_key: str = field(repr=False)  # never in a repr or log
    base_url: str
    history: list[TurnContext]


def _prepare(conversation_id: int, profile_id: int | None) -> _Prepared:
    with SessionLocal(bind=get_app_engine()) as session:
        _conversation(session, conversation_id)
        profile, key = get_profile_with_key(session, profile_id)
        history = load_history(session, conversation_id)
        return _Prepared(
            profile_id=profile.id,
            preset=profile.preset,
            model_name=profile.model,
            share=profile.share_results_with_llm,
            json_mode=profile.json_mode,
            api_key=key,
            base_url=profile.base_url,
            history=history,
        )


def _write_turn(
    conversation_id: int,
    user_id: int,
    question: str,
    state: ChatState,
    *,
    profile_id: int | None,
    preset: str | None,
    model: str | None,
    latency_ms: int,
) -> int:
    draft = state.get("draft")
    result = state.get("result")
    error = state.get("error") or {}
    outcome = state.get("outcome", "error")
    now = datetime.now(UTC)
    with SessionLocal(bind=get_app_engine()) as session:
        # Serialize concurrent turns of one conversation so seq stays gap-free and unique.
        conversation = session.scalar(
            select(Conversation).where(Conversation.id == conversation_id).with_for_update()
        )
        if conversation is None:
            raise HubError("conversation_not_found", "That conversation no longer exists.", 404)
        seq = (
            session.scalar(
                select(func.max(ChatTurn.seq)).where(ChatTurn.conversation_id == conversation_id)
            )
            or 0
        ) + 1
        turn = ChatTurn(
            conversation_id=conversation_id,
            seq=seq,
            question=question,
            kind=outcome,
            sql=draft.sql if draft else None,
            interpretation=draft.interpretation if draft else None,
            assumptions=list(draft.assumptions) if draft else None,
            clarification_question=draft.clarification_question if draft else None,
            row_count=result.row_count if result else None,
            truncated=result.truncated if result else False,
            analysis_text=state.get("analysis"),
            analysis_source=state.get("analysis_source"),
            results_shared=bool(state.get("results_shared", False)),
            llm_profile_id=profile_id,
            provider=preset,
            model=model,
            prompt_version=PROMPT_VERSION,
            attempts=state.get("attempts", 0),
            error_code=error.get("code") if outcome == "error" else None,
            latency_ms=latency_ms,
            created_by=user_id,
        )
        session.add(turn)
        if conversation.title is None:
            conversation.title = question.strip()[:TITLE_MAX]
        conversation.updated_at = now
        detected = state.get("json_mode_detected")
        if detected is not None and profile_id is not None:
            profile = session.get(LlmProfile, profile_id)
            if profile is not None:
                profile.json_mode = detected
                profile.updated_at = now
        session.flush()
        turn_id = turn.id
        session.commit()
        return turn_id


def _log_write_failure(task: asyncio.Future) -> None:
    """Always retrieve the write's exception (a cancelled shield wrapper would otherwise leave it
    to asyncio's default handler) and log only its type: the message can carry bound values."""
    if not task.cancelled() and (exc := task.exception()) is not None:
        logger.error("Recording the turn failed (%s)", type(exc).__name__)


async def run_turn(conversation_id: int, body: MessageIn, user: CurrentUser) -> AsyncIterator[str]:
    settings = get_settings()
    loop = asyncio.get_running_loop()
    started = time.monotonic()
    deadline = loop.time() + settings.turn_timeout_s
    profile_id: int | None = None
    preset: str | None = None
    model_name: str | None = None
    record_task: asyncio.Future[int] | None = None  # the one write of this turn
    error_sent = False
    done_sent = False
    last_state: ChatState = {}  # latest "values" snapshot: what the graph did so far
    attempts = 0
    analyzing = False  # rows went (or were about to go) to the provider
    shared = False

    async def record(state: ChatState) -> int:
        nonlocal record_task
        # Shielded: a timeout that cancels this await must not start a second write.
        record_task = asyncio.ensure_future(
            asyncio.to_thread(
                _write_turn,
                conversation_id,
                user.id,
                body.question,
                state,
                profile_id=profile_id,
                preset=preset,
                model=model_name,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
        )
        record_task.add_done_callback(_log_write_failure)
        return await asyncio.shield(record_task)

    async def final_turn_id(failure: dict | None) -> int | None:
        """The id of this question's turn: the graph's write if there was one, else a write of
        what the graph did so far plus the failure."""
        if record_task is not None:
            try:
                return await asyncio.shield(record_task)
            except Exception as exc:  # noqa: BLE001 - CancelledError propagates
                logger.error("Recording the turn failed (%s)", type(exc).__name__)
        state: ChatState = dict(last_state)  # type: ignore[assignment]
        state["attempts"] = max(attempts, state.get("attempts", 0))
        # An audit flag errs toward true: rows may have been sent once a result exists.
        state["results_shared"] = shared and ("result" in last_state or analyzing)
        state["outcome"] = "error"
        state["error"] = failure or INTERNAL_ERROR
        try:
            return await record(state)
        except Exception as exc:  # noqa: BLE001
            logger.error("Recording the failed turn failed (%s)", type(exc).__name__)
            return None

    failure: dict | None = None
    try:
        stream = None
        try:
            try:
                prepared = await asyncio.to_thread(_prepare, conversation_id, body.llm_profile_id)
            except HubError as exc:
                if body.llm_profile_id is not None and exc.code == "profile_missing_key":
                    profile_id = body.llm_profile_id
                failure = {"code": exc.code, "message": exc.message}
            else:
                profile_id = prepared.profile_id
                preset = prepared.preset
                model_name = prepared.model_name
                transient = (
                    LlmProfile(  # not attached to a session; only the fields the factory reads
                        preset=prepared.preset,
                        base_url=prepared.base_url,
                        model=prepared.model_name,
                    )
                )
                model = build_chat_model(transient, prepared.api_key, settings=settings)
                shared = prepared.share and body.share_results
                deps = ChatDeps(
                    model=model,
                    json_mode=prepared.json_mode,
                    share_results=shared,
                    settings=settings,
                    chatbot_engine=get_chatbot_engine(),
                    record_turn=record,
                )
                stream = build_chat_graph(deps).astream(
                    {"question": body.question, "history": prepared.history},
                    stream_mode=["custom", "values"],
                )
                while True:
                    # The deadline covers only the wait for the next chunk, never a yield, so it
                    # cannot cancel Starlette's send.
                    try:
                        async with asyncio.timeout_at(deadline) as scope:
                            mode, payload = await anext(stream)
                    except StopAsyncIteration:
                        break
                    except TimeoutError:
                        if not scope.expired():  # some other timeout raised inside the graph
                            raise
                        failure = TIMEOUT_ERROR
                        break
                    if mode == "values":
                        last_state = payload
                        continue
                    name = payload["event"]
                    if name == "step":
                        attempts = max(attempts, payload["data"]["attempt"])
                        analyzing = analyzing or payload["data"]["name"] == "analyzing"
                    error_sent = error_sent or name == "error"
                    done_sent = done_sent or name == "done"
                    yield format_sse(name, payload["data"])
        except Exception as exc:  # noqa: BLE001 - CancelledError is a BaseException and propagates
            # Type only: the message could carry row values or a key.
            logger.error("Chat turn failed (%s)", type(exc).__name__, exc_info=False)
            failure = INTERNAL_ERROR
        finally:
            if stream is not None:
                with contextlib.suppress(Exception):
                    await stream.aclose()

        if done_sent:
            return
        if failure is not None and not error_sent:
            yield format_sse("error", failure)
        turn_id = await final_turn_id(failure)
        yield format_sse("done", {"turn_id": turn_id})
    except (asyncio.CancelledError, GeneratorExit):
        # The client is gone (Starlette cancelled the stream, or closed it at a yield). Record
        # what happened, shielded so this very cancellation cannot abort the write, then let it
        # propagate. Nothing is yielded: there is no one to send to.
        if not done_sent:
            await final_turn_id(failure or DISCONNECT_ERROR)
        raise


def _get_turn(session: Session, turn_id: int) -> ChatTurn:
    turn = session.get(ChatTurn, turn_id)
    if turn is None:
        raise HubError("turn_not_found", "That question no longer exists.", status_code=404)
    return turn


def _run_logged_sql(turn: ChatTurn, cap: int) -> QueryResult:
    if turn.kind != "answer" or not turn.sql:
        raise HubError(
            "turn_has_no_result", "This question did not produce a result.", status_code=409
        )
    try:
        guarded = guard_sql(turn.sql, limit=cap + 1)
    except GuardError as exc:
        raise HubError(
            "sql_rejected", f"The saved SQL is no longer allowed ({exc.reason}).", 422
        ) from exc
    try:
        return run_readonly(guarded.sql, max_rows=cap, engine=get_chatbot_engine())
    except DBAPIError as exc:
        raise HubError("query_failed", sanitize_db_error(exc).user_message, 422) from exc


def rerun_turn(session: Session, turn_id: int) -> QueryResultOut:
    turn = _get_turn(session, turn_id)
    result = _run_logged_sql(turn, get_settings().display_row_cap)
    return QueryResultOut(
        columns=result.columns,
        rows=result.rows,
        row_count=result.row_count,
        truncated=result.truncated,
    )


def export_turn(session: Session, turn_id: int, fmt: str) -> Response:
    from app.export.writers import export_response

    turn = _get_turn(session, turn_id)
    cap = get_settings().export_row_cap
    result = _run_logged_sql(turn, cap)
    # The file holds at most `cap` rows; the headers tell the UI whether rows were left out.
    return export_response(
        result.columns,
        result.rows,
        fmt,
        f"turn-{turn.id}",
        extra_headers={
            "X-Hub-Truncated": "true" if result.truncated else "false",
            "X-Hub-Row-Cap": str(cap),
        },
    )
