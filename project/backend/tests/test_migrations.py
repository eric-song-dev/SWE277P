import os

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.imports.reader import content_fingerprint, read_grid
from tests.db_fixtures import BACKEND_DIR
from tests.imports.helpers import sample_bytes

SCRATCH_DB = "hub_test_migration"
OCT = "Bagel Breakfast - October.csv"


@pytest.fixture
def scratch_db():
    """An empty database, separate from hub_test, for stepping through migrations."""
    admin = create_engine(os.environ["TEST_ADMIN_DATABASE_URL"], isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {SCRATCH_DB} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {SCRATCH_DB} OWNER hub_app"))
    url = make_url(os.environ["DATABASE_URL"]).set(database=SCRATCH_DB)
    url = url.render_as_string(hide_password=False)
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    engine = create_engine(url)
    try:
        yield cfg, engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {SCRATCH_DB} WITH (FORCE)"))
        admin.dispose()


def test_0002_backfills_content_fingerprint(scratch_db):
    cfg, engine = scratch_db
    command.upgrade(cfg, "0001")
    content = sample_bytes(OCT)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO hub.import_file "
                "(file_name, file_sha256, source, status, content, uploaded_by) "
                "SELECT :name, 'abc', 'campusgroups', 'committed', :content, id "
                "FROM hub.app_user WHERE username = 'local'"
            ),
            {"name": OCT, "content": content},
        )

    command.upgrade(cfg, "head")
    with engine.connect() as conn:
        stored = conn.scalar(text("SELECT content_sha256 FROM hub.import_file"))
        nullable = conn.scalar(
            text(
                "SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'hub' "
                "AND table_name = 'import_file' AND column_name = 'content_sha256'"
            )
        )
    assert stored == content_fingerprint(read_grid(OCT, content))
    assert nullable == "NO"

    command.downgrade(cfg, "0001")
    with engine.connect() as conn:
        cols = conn.scalars(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'hub' AND table_name = 'import_file'"
            )
        ).all()
    assert "content_sha256" not in cols


# (table, column, a value outside the allowed set, extra columns the insert needs)
CHECKED = [
    ("import_file", "source", "excel", {}),
    ("import_file", "status", "stale", {}),
    ("event", "modality", "Online", {}),
    ("person_identifier", "kind", "phone", {}),
    ("attendance", "match_method", "guess", {}),
    ("llm_profile", "preset", "azure", {}),
    ("chat_turn", "kind", "refusal", {}),
    ("chat_turn", "analysis_source", "human", {}),
]


def _insert_row(conn, table, overrides):
    """Insert one valid row of `table` (and its parents), with `overrides` applied last."""
    uid = conn.scalar(text("SELECT id FROM hub.app_user WHERE username = 'local'"))
    ev = conn.scalar(
        text("INSERT INTO hub.event (name, term) VALUES ('E', 'Fall 2026') RETURNING id")
    )
    imp = conn.scalar(
        text(
            "INSERT INTO hub.import_file (file_name, file_sha256, content_sha256, source, status, "
            "content, uploaded_by) VALUES ('f', md5(random()::text), md5(random()::text), "
            "'campusgroups', 'pending', '\\x00', :u) RETURNING id"
        ),
        {"u": uid},
    )
    person = conn.scalar(text("INSERT INTO hub.person DEFAULT VALUES RETURNING id"))
    conv = conn.scalar(
        text("INSERT INTO hub.conversation (created_by) VALUES (:u) RETURNING id"), {"u": uid}
    )
    rows = {
        "import_file": (
            "file_name, file_sha256, content_sha256, source, status, content, uploaded_by",
            "'f2', md5(random()::text), md5(random()::text), 'campusgroups', 'pending', '\\x00', :u",
        ),
        "event": ("name, term, modality", "'E2', 'Fall 2026', 'In Person'"),
        "person_identifier": ("person_id, kind, value", ":p, 'netid', md5(random()::text)"),
        "attendance": ("event_id, import_file_id, match_method", ":e, :i, 'none'"),
        "llm_profile": ("name, preset, base_url, model", "md5(random()::text), 'custom', 'u', 'm'"),
        "chat_turn": (
            "conversation_id, seq, question, kind, created_by",
            ":c, 1, 'q', 'answer', :u",
        ),
    }
    cols, vals = rows[table]
    for column, value in overrides.items():
        cols = ", ".join(c for c in cols.split(", ") if c != column) + f", {column}"
        parts = [
            v
            for c, v in zip(rows[table][0].split(", "), _split(rows[table][1]), strict=True)
            if c != column
        ]
        vals = ", ".join([*parts, f"'{value}'"])
    conn.execute(
        text(f"INSERT INTO hub.{table} ({cols}) VALUES ({vals})"),
        {"u": uid, "p": person, "e": ev, "i": imp, "c": conv},
    )


def _split(values: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in values:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return [*out, cur.strip()]


@pytest.mark.parametrize(("table", "column", "bad", "_extra"), CHECKED)
def test_0005_check_constraints_reject_unknown_values(scratch_db, table, column, bad, _extra):
    cfg, engine = scratch_db
    command.upgrade(cfg, "head")
    with engine.begin() as conn:
        _insert_row(conn, table, {})  # the helper's defaults are valid
    with pytest.raises(IntegrityError, match="check constraint"), engine.begin() as conn:
        _insert_row(conn, table, {column: bad})


def test_0005_upgrades_existing_rows_and_downgrades(scratch_db):
    cfg, engine = scratch_db
    command.upgrade(cfg, "0004")
    with engine.begin() as conn:
        _insert_row(conn, "event", {})
        _insert_row(conn, "llm_profile", {})
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "0004")
    with engine.begin() as conn:
        _insert_row(conn, "event", {"modality": "Online"})  # constraint is gone again
