from tests.imports.helpers import sample_bytes

OCT = "Bagel Breakfast - October.csv"
DETAILS = {
    "name": "Bagel Breakfast, October",
    "term": "Fall 2026",
    "modality": "In Person",
    "event_type": "Wellness/Mental Health",
    "sponsors_hosts": "  ",
}


def upload(client, name=OCT, content=None, ctype="text/csv"):
    content = sample_bytes(name) if content is None else content
    return client.post("/api/imports", files=[("files", (name, content, ctype))])


def test_batch_with_bad_files_still_previews_good(client):
    files = [
        ("files", (OCT, sample_bytes(OCT), "text/csv")),
        ("files", ("empty.csv", b"", "text/csv")),
        ("files", ("notes.pdf", b"%PDF-1.4", "application/pdf")),
        ("files", ("big.csv", b"a" * (10_485_760 + 1), "text/csv")),
    ]
    res = client.post("/api/imports", files=files)
    assert res.status_code == 200
    body = res.json()["files"]
    assert [f["status"] for f in body] == ["pending", "rejected", "rejected", "rejected"]
    assert [f["error"]["code"] for f in body[1:]] == [
        "empty_file",
        "unreadable_file",
        "file_too_large",
    ]


def test_unknown_format_rejected_with_missing_columns(client):
    body = upload(client, "other.csv", b"a,b,c\n1,2,3\n").json()["files"][0]
    assert body["status"] == "rejected" and body["error"]["code"] == "unknown_format"
    assert body["error"]["details"]["missing"]


def test_commit_validation_error_shape(client):
    import_id = upload(client).json()["files"][0]["id"]
    res = client.post(f"/api/imports/{import_id}/commit", json={**DETAILS, "term": "Autumn 26"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "validation_error"


def test_full_flow_over_http(client):
    preview = upload(client).json()["files"][0]
    assert preview["status"] == "pending" and preview["row_count"] == 38
    import_id = preview["id"]

    res = client.post(f"/api/imports/{import_id}/commit", json=DETAILS)
    assert res.status_code == 200 and res.json()["inserted"] == 38
    event_id = res.json()["event_id"]

    again = client.post(f"/api/imports/{import_id}/commit", json=DETAILS)
    assert (again.status_code, again.json()["error"]["code"]) == (409, "import_not_pending")

    dup = upload(client).json()["files"][0]
    assert (dup["status"], dup["duplicate_of"]) == ("duplicate", import_id)

    one = client.get(f"/api/imports/{import_id}").json()
    assert one["status"] == "committed" and one["event"]["id"] == event_id
    assert one["uploaded_by"]["display_name"]
    assert [i["id"] for i in client.get("/api/imports").json()] == [import_id]

    events = client.get("/api/events").json()
    assert events[0]["id"] == event_id and events[0]["attendee_count"] == 38
    assert events[0]["academic_year"] == "2026-27"


def test_get_missing_import_is_404(client):
    res = client.get("/api/imports/999999")
    assert (res.status_code, res.json()["error"]["code"]) == (404, "import_not_found")


def test_discard_returns_204_then_404(client):
    import_id = upload(client).json()["files"][0]["id"]
    assert client.delete(f"/api/imports/{import_id}").status_code == 204
    res = client.delete(f"/api/imports/{import_id}")
    assert (res.status_code, res.json()["error"]["code"]) == (404, "import_not_found")


def test_discard_committed_is_409(client):
    import_id = upload(client).json()["files"][0]["id"]
    client.post(f"/api/imports/{import_id}/commit", json=DETAILS)
    res = client.delete(f"/api/imports/{import_id}")
    assert (res.status_code, res.json()["error"]["code"]) == (409, "import_not_pending")


def test_failed_commit_returns_error_and_persists_nothing(app, db_session, monkeypatch):
    from fastapi.testclient import TestClient
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from app.dataset.models import Attendance
    from app.events.models import Event
    from app.imports.models import ImportFile

    client = TestClient(app, raise_server_exceptions=False)
    import_id = upload(client).json()["files"][0]["id"]

    def failing_commit(self):
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(Session, "commit", failing_commit)
    res = client.post(f"/api/imports/{import_id}/commit", json=DETAILS)

    assert res.status_code >= 500
    assert res.json() == {
        "error": {"code": "internal_error", "message": "Internal server error", "details": None}
    }
    statuses = db_session.scalars(select(ImportFile.status)).all()
    assert statuses == ["pending"]
    assert db_session.scalar(select(func.count()).select_from(Event)) == 0
    assert db_session.scalar(select(func.count()).select_from(Attendance)) == 0
