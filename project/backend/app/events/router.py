from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.db import SessionDep
from app.events import service
from app.events.schemas import EventOut

router = APIRouter(prefix="/api")


@router.get("/events", response_model=list[EventOut])
def list_events(
    session: SessionDep,
    _user: Annotated[CurrentUser, Depends(get_current_user)],
) -> list[EventOut]:
    return service.list_events(session)
