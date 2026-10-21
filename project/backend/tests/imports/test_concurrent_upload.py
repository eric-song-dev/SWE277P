import threading
import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.imports.models import ImportFile
from app.imports.service import preview_upload
from tests.imports.helpers import sample_bytes

OCT = "Bagel Breakfast - October.csv"


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
        time.sleep(0.5)  # let the second request reach the same new file
        first.commit()
    thread.join(timeout=10)

    a, b = results["a"], results["b"]
    assert not isinstance(b, Exception), repr(b)
    assert a.status == b.status == "pending"
    assert a.id == b.id
    assert db_session.scalar(select(func.count()).select_from(ImportFile)) == 1
