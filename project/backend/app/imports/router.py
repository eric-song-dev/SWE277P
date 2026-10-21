from typing import Annotated

from fastapi import APIRouter, Depends, Response, UploadFile

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.config import get_settings
from app.db import SessionDep
from app.imports import service
from app.imports.schemas import (
    CommitSummary,
    EventDetailsIn,
    ImportFileOut,
    ImportPreviewBatch,
)

router = APIRouter(prefix="/api")

UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.post("/imports", response_model=ImportPreviewBatch)
async def upload_imports(
    files: list[UploadFile], session: SessionDep, user: UserDep
) -> ImportPreviewBatch:
    limit = get_settings().max_upload_bytes
    previews = []
    for f in files:
        content = await f.read(limit + 1)
        previews.append(service.preview_upload(session, f.filename or "upload", content, user))
    return ImportPreviewBatch(files=previews)


@router.get("/imports", response_model=list[ImportFileOut])
def list_imports(session: SessionDep, _user: UserDep) -> list[ImportFileOut]:
    return service.list_imports(session)


@router.get("/imports/{import_id}", response_model=ImportFileOut)
def get_import(import_id: int, session: SessionDep, _user: UserDep) -> ImportFileOut:
    return service.get_import(session, import_id)


@router.post("/imports/{import_id}/commit", response_model=CommitSummary)
def commit_import(
    import_id: int, details: EventDetailsIn, session: SessionDep, user: UserDep
) -> CommitSummary:
    return service.commit_import(session, import_id, details, user)


@router.delete("/imports/{import_id}", status_code=204)
def discard_import(import_id: int, session: SessionDep, user: UserDep) -> Response:
    service.discard_import(session, import_id, user)
    return Response(status_code=204)
