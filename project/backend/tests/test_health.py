def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_unknown_route_uses_error_shape(client):
    body = client.get("/api/nope").json()
    assert set(body["error"]) == {"code", "message", "details"}
