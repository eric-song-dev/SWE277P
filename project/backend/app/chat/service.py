"""Conversations, the streamed chat turn, rerun and export (spec 7.6, 9).

``run_turn`` streams after the request's session has closed, so it opens its own short sessions
(one per DB step, run via ``asyncio.to_thread``) and never holds one across an LLM call.
"""

import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
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
    api_key: str
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


async def run_turn(conversation_id: int, body: MessageIn, user: CurrentUser) -> AsyncIterator[str]:
    settings = get_settings()
    started = time.monotonic()
    profile_id: int | None = None
    preset: str | None = None
    model_name: str | None = None
    recorded = False
    error_sent = False
    done_sent = False

    def elapsed_ms() -> int:
        return int((time.monotonic() - started) * 1000)

    async def record(state: ChatState) -> int:
        nonlocal recorded
        turn_id = await asyncio.to_thread(
            _write_turn,
            conversation_id,
            user.id,
            body.question,
            state,
            profile_id=profile_id,
            preset=preset,
            model=model_name,
            latency_ms=elapsed_ms(),
        )
        recorded = True
        return turn_id

    failure: dict | None = None
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
            transient = LlmProfile(  # not attached to a session; only the fields the factory reads
                preset=prepared.preset, base_url=prepared.base_url, model=prepared.model_name
            )
            model = build_chat_model(transient, prepared.api_key, settings=settings)
            deps = ChatDeps(
                model=model,
                json_mode=prepared.json_mode,
                share_results=prepared.share and body.share_results,
                settings=settings,
                chatbot_engine=get_chatbot_engine(),
                record_turn=record,
            )
            graph = build_chat_graph(deps)
            try:
                async with asyncio.timeout(settings.turn_timeout_s):
                    async for chunk in graph.astream(
                        {"question": body.question, "history": prepared.history},
                        stream_mode="custom",
                    ):
                        name = chunk["event"]
                        error_sent = error_sent or name == "error"
                        done_sent = done_sent or name == "done"
                        yield format_sse(name, chunk["data"])
            except TimeoutError:
                failure = TIMEOUT_ERROR
    except Exception as exc:  # noqa: BLE001 - CancelledError is a BaseException and propagates
        # Type only: the message could carry row values or a key.
        logger.error("Chat turn failed (%s)", type(exc).__name__, exc_info=False)
        failure = INTERNAL_ERROR

    if done_sent:
        return
    if failure is not None:
        if not error_sent:
            yield format_sse("error", failure)
        if not recorded:
            state: ChatState = {"outcome": "error", "error": failure}
            try:
                turn_id = await record(state)
            except Exception as exc:  # noqa: BLE001
                logger.error("Recording the failed turn failed (%s)", type(exc).__name__)
                turn_id = None
            if turn_id is not None:
                yield format_sse("done", {"turn_id": turn_id})
                return
        yield format_sse("done", {"turn_id": None})
    elif not recorded:  # the graph ended without finalizing; should not happen
        yield format_sse("done", {"turn_id": None})


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
    result = _run_logged_sql(turn, get_settings().export_row_cap)
    return export_response(result.columns, result.rows, fmt, f"turn-{turn.id}")
