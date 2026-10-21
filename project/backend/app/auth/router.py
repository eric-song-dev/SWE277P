from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser, MeResponse
from app.config import get_settings

router = APIRouter(prefix="/api")


@router.get("/me", response_model=MeResponse)
def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(**user.model_dump(), auth_mode=get_settings().auth_mode)
