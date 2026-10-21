from datetime import UTC, datetime
from functools import partial
from typing import Annotated

import anyio.from_thread
from fastapi import APIRouter, Depends, Response

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.config import get_settings
from app.db import SessionDep
from app.llm import service
from app.llm.presets import available_presets
from app.llm.probe import probe_profile
from app.llm.schemas import LlmProfileIn, LlmProfileOut, LlmProfilePatch, PresetOut, ProbeResultOut

router = APIRouter(prefix="/api/llm-profiles")

UserDep = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("", response_model=list[LlmProfileOut])
def list_profiles(session: SessionDep, _user: UserDep) -> list[LlmProfileOut]:
    return [LlmProfileOut.from_profile(p) for p in service.list_profiles(session)]


@router.get("/presets", response_model=list[PresetOut])
def list_presets(session: SessionDep, _user: UserDep) -> list[PresetOut]:
    return [PresetOut.model_validate(p) for p in available_presets(get_settings())]


@router.post("", response_model=LlmProfileOut, status_code=201)
def create_profile(data: LlmProfileIn, session: SessionDep, user: UserDep) -> LlmProfileOut:
    return LlmProfileOut.from_profile(service.create_profile(session, data, user))


@router.patch("/{profile_id}", response_model=LlmProfileOut)
def update_profile(
    profile_id: int, data: LlmProfilePatch, session: SessionDep, _user: UserDep
) -> LlmProfileOut:
    return LlmProfileOut.from_profile(service.update_profile(session, profile_id, data))


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: int, session: SessionDep, _user: UserDep) -> Response:
    service.delete_profile(session, profile_id)
    return Response(status_code=204)


@router.post("/{profile_id}/default", response_model=LlmProfileOut)
def set_default(profile_id: int, session: SessionDep, _user: UserDep) -> LlmProfileOut:
    return LlmProfileOut.from_profile(service.set_default(session, profile_id))


@router.post("/{profile_id}/test", response_model=ProbeResultOut)
def test_connection(profile_id: int, session: SessionDep, _user: UserDep) -> ProbeResultOut:
    # A plain def runs in the threadpool, so DB and decrypt work stays off the event loop.
    profile, api_key = service.get_profile_with_key(session, profile_id)
    session.expunge(profile)  # keep the loaded values; the commit below must not expire them
    session.commit()  # end the transaction so no connection is held during the network probe
    result = anyio.from_thread.run(
        partial(probe_profile, profile, api_key, settings=get_settings())
    )
    stored = service.get_profile(session, profile_id)
    now = datetime.now(UTC)
    stored.last_tested_at = now
    stored.last_test_ok = result.ok
    if result.json_mode is not None:
        stored.json_mode = result.json_mode
    stored.updated_at = now
    return result
