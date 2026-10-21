from sqlalchemy import text

from app.auth.dependencies import get_current_user
from tests.route_utils import routes_missing_dependency


def test_me_returns_local_user(client):
    body = client.get("/api/me").json()
    assert body["username"] == "local" and body["auth_mode"] == "none"
    assert body["display_name"] == "GPSRC Staff"


def test_me_errors_clearly_when_local_user_missing(client, db_session):
    with db_session.get_bind().begin() as conn:
        conn.execute(text("DELETE FROM hub.app_user WHERE username = 'local'"))
    response = client.get("/api/me")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "auth_user_missing"


def test_every_api_route_depends_on_current_user(app):
    assert routes_missing_dependency(app, get_current_user) == ["GET /api/health"]
