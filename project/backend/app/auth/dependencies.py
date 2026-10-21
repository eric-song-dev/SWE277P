from sqlalchemy import select

from app.auth.models import AppUser
from app.auth.schemas import CurrentUser
from app.config import get_settings
from app.db import SessionDep
from app.errors import HubError

LOCAL_USERNAME = "local"


def get_current_user(session: SessionDep) -> CurrentUser:
    """Single seam for identifying the caller; every route except /api/health depends on it."""
    # AUTH_MODE=password plugs in here: resolve the user from the session cookie instead.
    if get_settings().auth_mode == "none":
        user = session.scalar(select(AppUser).where(AppUser.username == LOCAL_USERNAME))
        if user is None:
            raise HubError(
                "auth_user_missing",
                "The built-in 'local' user is missing; run the database migrations.",
                status_code=500,
            )
        return CurrentUser(id=user.id, username=user.username, display_name=user.display_name)
    raise HubError("auth_mode_unsupported", "Unsupported AUTH_MODE", status_code=500)
