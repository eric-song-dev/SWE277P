from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.chat import service
from app.chat.schemas import (
    ConversationDetail,
    ConversationOut,
    MessageIn,
    QueryResultOut,
)
from app.db import SessionDep

router = APIRouter(prefix="/api")

UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(session: SessionDep, user: UserDep) -> ConversationOut:
    return ConversationOut.model_validate(service.create_conversation(session, user))


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(session: SessionDep, user: UserDep) -> list[ConversationOut]:
    return service.list_conversations(session, user)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int, session: SessionDep, _user: UserDep
) -> ConversationDetail:
    return service.get_conversation(session, conversation_id)


@router.post("/conversations/{conversation_id}/messages")
def post_message(
    conversation_id: int, body: MessageIn, session: SessionDep, user: UserDep
) -> StreamingResponse:
    service.ensure_conversation(session, conversation_id)  # 404 before the stream starts
    return StreamingResponse(
        service.run_turn(conversation_id, body, user),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/turns/{turn_id}/rerun", response_model=QueryResultOut)
def rerun_turn(turn_id: int, session: SessionDep, _user: UserDep) -> QueryResultOut:
    return service.rerun_turn(session, turn_id)


@router.get("/chat/turns/{turn_id}/export")
def export_turn(
    turn_id: int,
    session: SessionDep,
    _user: UserDep,
    fmt: Annotated[Literal["xlsx", "csv"], Query(alias="format")] = "xlsx",
) -> Response:
    return service.export_turn(session, turn_id, fmt)
