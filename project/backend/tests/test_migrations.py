import os

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

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
