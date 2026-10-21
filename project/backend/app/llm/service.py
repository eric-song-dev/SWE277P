import logging
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.auth.models import AppUser
from app.auth.schemas import CurrentUser
from app.config import Settings, get_settings
from app.errors import HubError
from app.llm.crypto import api_key_hint, decrypt_api_key, encrypt_api_key
from app.llm.models import LlmProfile
from app.llm.presets import NO_URL_REQUIRED, PRESETS, available_presets
from app.llm.schemas import LlmProfileIn, LlmProfilePatch

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _invalid(message: str) -> HubError:
    return HubError("validation_error", message, status_code=422)


def _check_preset(preset: str, base_url: str, settings: Settings) -> None:
    if preset not in {p.key for p in available_presets(settings)}:
        raise _invalid("Unknown or unavailable preset.")
    if not base_url and PRESETS[preset].base_url is None and preset not in NO_URL_REQUIRED:
        raise _invalid("A base URL is required for this preset.")


def _clean_url(url: object | None) -> str | None:
    return str(url).rstrip("/") if url else None


def _name_free(session: Session, name: str, exclude_id: int | None = None) -> None:
    stmt = select(LlmProfile.id).where(LlmProfile.name == name)
    found = session.scalar(stmt)
    if found is not None and found != exclude_id:
        raise HubError(
            "profile_name_taken", "A profile with that name already exists.", status_code=409
        )


def list_profiles(session: Session) -> list[LlmProfile]:
    return list(session.scalars(select(LlmProfile).order_by(LlmProfile.created_at, LlmProfile.id)))


def get_profile(session: Session, profile_id: int) -> LlmProfile:
    profile = session.get(LlmProfile, profile_id)
    if profile is None:
        raise HubError("profile_not_found", "That AI profile no longer exists.", status_code=404)
    return profile


def create_profile(
    session: Session,
    data: LlmProfileIn,
    user: CurrentUser | None,
    settings: Settings | None = None,
) -> LlmProfile:
    settings = settings or get_settings()
    preset = PRESETS[data.preset]
    base_url = _clean_url(data.base_url) or preset.base_url or ""
    _check_preset(data.preset, base_url, settings)
    _name_free(session, data.name)
    key = data.api_key.get_secret_value() if data.api_key else ""
    share = (
        preset.share_results_default
        if data.share_results_with_llm is None
        else data.share_results_with_llm
    )
    has_any = session.scalar(select(func.count()).select_from(LlmProfile)) > 0
    profile = LlmProfile(
        name=data.name,
        preset=data.preset,
        base_url=base_url,
        model=data.model,
        api_key_ciphertext=encrypt_api_key(key) if key else None,
        api_key_hint=api_key_hint(key) if key else None,
        share_results_with_llm=share,
        is_default=not has_any,
        created_by=user.id if user else None,
    )
    session.add(profile)
    session.flush()
    session.refresh(profile)
    return profile


def update_profile(
    session: Session, profile_id: int, data: LlmProfilePatch, settings: Settings | None = None
) -> LlmProfile:
    settings = settings or get_settings()
    profile = get_profile(session, profile_id)
    fields = data.model_fields_set
    preset_key = data.preset or profile.preset
    if preset_key != profile.preset:
        _check_preset(
            preset_key, "x", settings
        )  # unknown or unavailable preset: 422 before indexing
    if "base_url" in fields:
        base_url = _clean_url(data.base_url) or PRESETS[preset_key].base_url or ""
    elif preset_key != profile.preset:
        base_url = PRESETS[preset_key].base_url or ""  # a new preset drops the old URL
    else:
        base_url = profile.base_url
    if preset_key != profile.preset or base_url != profile.base_url:
        _check_preset(preset_key, base_url, settings)
    if data.name is not None and data.name != profile.name:
        _name_free(session, data.name, profile.id)
        profile.name = data.name
    provider_changed = (
        preset_key != profile.preset
        or base_url != profile.base_url
        or (data.model is not None and data.model != profile.model)
        or (data.api_key is not None and bool(data.api_key.get_secret_value()))
    )
    profile.preset = preset_key
    profile.base_url = base_url
    if data.model is not None:
        profile.model = data.model
    if data.share_results_with_llm is not None:
        profile.share_results_with_llm = data.share_results_with_llm
    if data.api_key is not None and data.api_key.get_secret_value():
        key = data.api_key.get_secret_value()
        profile.api_key_ciphertext = encrypt_api_key(key)
        profile.api_key_hint = api_key_hint(key)
    if provider_changed:
        # Probe results describe the old endpoint/model/key; a stale json_mode=True would make
        # every question fail on a model that rejects response_format.
        profile.json_mode = None
        profile.last_test_ok = None
        profile.last_tested_at = None
    profile.updated_at = _now()
    session.flush()
    return profile


def _promote(session: Session, profile: LlmProfile) -> None:
    session.execute(
        update(LlmProfile)
        .where(LlmProfile.is_default, LlmProfile.id != profile.id)
        .values(is_default=False, updated_at=_now())
    )
    session.flush()  # the partial unique index must never see two defaults
    profile.is_default = True
    profile.updated_at = _now()
    session.flush()


def set_default(session: Session, profile_id: int) -> LlmProfile:
    profile = get_profile(session, profile_id)
    _promote(session, profile)
    return profile


def delete_profile(session: Session, profile_id: int) -> None:
    profile = get_profile(session, profile_id)
    was_default = profile.is_default
    session.delete(profile)
    session.flush()
    if was_default:
        oldest = session.scalar(
            select(LlmProfile).order_by(LlmProfile.created_at, LlmProfile.id).limit(1)
        )
        if oldest is not None:
            _promote(session, oldest)


def get_profile_with_key(session: Session, profile_id: int | None) -> tuple[LlmProfile, str]:
    """Return the profile (None: the default) and its decrypted key; the key stays in llm/."""
    if profile_id is None:
        profile = session.scalar(select(LlmProfile).where(LlmProfile.is_default))
        if profile is None:
            raise HubError("profile_not_found", "No AI profile is set up.", status_code=404)
    else:
        profile = get_profile(session, profile_id)
    if profile.preset == "fake":
        return profile, ""
    if profile.api_key_ciphertext is None:
        raise HubError(
            "profile_missing_key",
            "This AI profile has no API key. Add one in Settings.",
            status_code=409,
        )
    return profile, decrypt_api_key(profile.api_key_ciphertext)


def seed_profile_from_env(session: Session, settings: Settings) -> None:
    name = (settings.llm_seed_name or "").strip()
    if not name:
        return
    preset = (settings.llm_seed_preset or "").strip() or "custom"
    key = settings.llm_seed_api_key.get_secret_value() if settings.llm_seed_api_key else ""
    if not key and preset != "fake":
        return
    if session.scalar(select(LlmProfile.id).where(LlmProfile.name == name)) is not None:
        return
    share = (settings.llm_seed_share_results or "").strip().lower()
    data = LlmProfileIn(
        name=name,
        preset=preset,
        base_url=(settings.llm_seed_base_url or None),
        model=settings.llm_seed_model or "",
        api_key=key or None,
        share_results_with_llm=(share in {"1", "true", "yes", "on"}) if share else None,
    )
    local = session.scalar(select(AppUser).where(AppUser.username == "local"))
    user = (
        CurrentUser(id=local.id, username=local.username, display_name=local.display_name)
        if local
        else None
    )
    create_profile(session, data, user, settings)
