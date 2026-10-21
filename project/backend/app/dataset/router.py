from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.dataset import service
from app.db import get_session
from app.export.writers import export_response

router = APIRouter(prefix="/api/dataset")


@router.get("/export")
def export_dataset(
    session: Annotated[Session, Depends(get_session)],
    _user: Annotated[CurrentUser, Depends(get_current_user)],
    fmt: Annotated[Literal["xlsx", "csv"], Query(alias="format")] = "xlsx",
) -> Response:
    columns, rows = service.gpsrc_layout_rows(session)
    return export_response(columns, rows, fmt, "dataset")
