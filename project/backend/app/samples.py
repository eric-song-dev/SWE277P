"""Load the bundled synthetic sample exports (used by tests, demos and other sessions)."""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import CurrentUser
from app.db import SessionLocal, get_app_engine
from app.imports.schemas import CommitSummary, EventDetailsIn
from app.imports.service import commit_import, preview_upload

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "sample_data" / "exports"
EVENTS_FILE = SAMPLE_DIR.parent / "events.json"


def load_sample_exports(session: Session, user: CurrentUser) -> list[CommitSummary]:
    """Preview and commit every sample file; files already imported are skipped.

    Does not commit the session; callers outside an HTTP request must do so.
    """
    return [s for _name, s in _load(session, user)]


def _load(session: Session, user: CurrentUser) -> list[tuple[str, CommitSummary]]:
    events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    committed: list[tuple[str, CommitSummary]] = []
    for file_name, details in events.items():
        preview = preview_upload(session, file_name, (SAMPLE_DIR / file_name).read_bytes(), user)
        if preview.status == "duplicate":
            continue
        if preview.status == "rejected":
            raise RuntimeError(f"Sample file {file_name!r} was rejected: {preview.error}")
        summary = commit_import(session, preview.id, EventDetailsIn(**details), user)
        committed.append((file_name, summary))
    return committed


def main() -> None:
    total = len(json.loads(EVENTS_FILE.read_text(encoding="utf-8")))
    with SessionLocal(bind=get_app_engine()) as session:
        user = get_current_user(session)
        committed = _load(session, user)
        session.commit()
    for name, s in committed:
        print(
            f"{name}: inserted={s.inserted} linked_by_netid={s.linked_by_netid} "
            f"linked_by_email={s.linked_by_email} new_people={s.new_people} "
            f"flagged={s.flagged_rows}"
        )
    print(f"Skipped {total - len(committed)} file(s) already imported.")


if __name__ == "__main__":
    main()
