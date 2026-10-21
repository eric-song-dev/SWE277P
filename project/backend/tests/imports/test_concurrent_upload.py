import threading
import time

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.imports.models import ImportFile
from app.imports.service import preview_upload
from tests.imports.helpers import sample_bytes

OCT = "Bagel Breakfast - October.csv"


def _wait_for_ungranted_advisory_lock(observer, timeout_s: float = 5.0) -> None:
    """Block until some backend waits for an advisory lock (the second upload is queued)."""
    deadline = time.monotonic() + timeout_s
    query = text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted")
    while observer.scalar(query) == 0:
        assert time.monotonic() < deadline, "the second upload never waited for the advisory lock"
        time.sleep(0.01)


def test_simultaneous_uploads_of_a_new_file_share_one_pending_import(db_session, user):
    engine = db_session.get_bind()
    content = sample_bytes(OCT)
    results: dict[str, object] = {}

    def second_request():
        try:
            with Session(engine, expire_on_commit=False) as s:
                results["b"] = preview_upload(s, OCT, content, user)
                s.commit()
        except Exception as exc:  # noqa: BLE001
            results["b"] = exc

    with Session(engine, expire_on_commit=False) as first:
        results["a"] = preview_upload(first, OCT, content, user)  # flushed, not yet committed
        thread = threading.Thread(target=second_request)
        thread.start()
        with Session(engine) as observer:  # a third connection: the first one holds its lock
            _wait_for_ungranted_advisory_lock(observer)
        first.commit()
    thread.join(timeout=10)
    assert not thread.is_alive(), "the second upload is still blocked 10 s after the first commit"

    a, b = results["a"], results["b"]
    assert not isinstance(b, Exception), repr(b)
    assert a.status == b.status == "pending"
    assert a.id == b.id
    assert db_session.scalar(select(func.count()).select_from(ImportFile)) == 1
