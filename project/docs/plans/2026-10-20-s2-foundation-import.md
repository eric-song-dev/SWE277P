# S2: Foundation and Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable skeleton (Compose, FastAPI, PostgreSQL with both roles, React placeholder) plus the complete import pipeline. The 10 sample exports reproduce the compiled sheet (A1), re-uploads add nothing (A2), and exports are formula-safe (A9).

**Architecture:** Modular-monolith FastAPI app under `project/backend/app/`. Sync SQLAlchemy 2 runs on psycopg 3. Alembic owns the `hub` schema. Imports go through pure adapter functions (grid in, normalized rows out), then a commit service that links identities inside one transaction.

**Tech Stack:** Python 3.12 (uv), FastAPI 0.156, SQLAlchemy 2.1, Alembic 1.20, psycopg 3.3, pydantic-settings 2.16, openpyxl 3.1, cryptography 50, pytest 9, httpx 0.28, ruff. Frontend skeleton: Vite + React 19 + TypeScript, MUI 9. PostgreSQL 16, nginx stable.

**Spec:** `project/docs/specs/2026-10-20-data-hub-design.md` (Sections 4, 5, 6, 9, 10, 11, 12, 14).

## Global Constraints

- All paths below are relative to `project/`. Run backend commands from `project/backend`.
- Python `>=3.12,<3.13` (`.python-version` = `3.12`). Code, comments, and commit messages in English.
- Commit after every task with Conventional Commits. Stage by path, never `git add -A` or `git add .`. Add the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Synthetic data only. The sample exports are synthetic and may be copied into `backend/sample_data/`.
- Every API route except `GET /api/health` depends on `get_current_user` (spec §11).
- Error responses always look like `{"error": {"code": str, "message": str, "details": object|null}}`.
- Only `chat/executor.py` and the chat export (S3) may use the `chatbot_ro` engine. S2 creates the engine but uses it only in tests.
- The view has exactly these 17 columns, in this order: `person_key, event_name, event_date, term, academic_year, modality, sponsors_hosts, event_type, platform, first_name, last_name, email, netid, affiliation, domestic_international, school, department`.
- Affiliation values: `Doctoral Student`, `Master’s Student` (**U+2019 right single quote**, as in the CampusGroups exports and the compiled sheet), `Postdoc`. 12twenty `Degree` maps Doctoral → `Doctoral Student`, Masters → `Master’s Student`, Postdoctoral → `Postdoc`. Any other value is kept as recorded.
- The full-dataset export uses the template's exact 19 headers, including the trailing spaces and the "Parnters" typo: `Student Worker`, `Event Date`, `Event Term`, `Event Name `, `Virtual/ In-Person/ Hybrid `, `Sponsor/Host/Parnters`, `Event type (Professional Development, Wellness/Mental Health, Fellowships)`, `On Campus Groups?`, `If not on Campus Groups, where was attendance found? State where + Link it`, `First Name of Attendee`, `Last Name of Attendee`, `Email`, `Affiliation`, `Student ID or Employee ID`, `NetID`, `Domestic or International`, `School`, `Department `, `Notes`.
- Max upload size: 10 MB per file.

## Review Focus

1. **A CSV saved by Excel on Windows** (cp1252, or UTF-8 with a BOM). Expected: imports with accents intact. The test is in Task 4.
2. **An XLSX with trailing blank rows or columns** (the CampusGroups template has 1,000 rows and 26 columns, mostly empty). Expected: blank rows are ignored and `row_count` counts real rows only. The test is in Task 4.
3. **An empty, non-spreadsheet, or oversized file.** Expected: that file is `rejected` with a clear code, the others in the batch still preview, and nothing returns a 500. The test is in Task 8.
4. **The same person twice in one file.** Expected: the second row is skipped and flagged `duplicate_in_event`, with no unique-constraint 500. The test is in Task 8.
5. **A numeric Student ID in an XLSX** (`87000000.0`). Expected: stored as `"87000000"`. The test is in Task 4.

---

### Task 1: Backend skeleton, settings, health, error shape

**Files:**
- Create: `backend/pyproject.toml`, `backend/.python-version`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/errors.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`, `backend/tests/test_health.py`, `backend/tests/test_config.py`, `.env.example`, `.gitignore`

**Interfaces:**
- Produces:
  - `app.config.Settings`
  - `app.config.get_settings() -> Settings` (lru_cache)
  - `app.errors.HubError(code: str, message: str, status_code: int = 400, details: dict | None = None)`
  - `app.errors.install_error_handlers(app: FastAPI) -> None`
  - `app.main.create_app() -> FastAPI`
  - `app.main.app`

Settings fields (env name = upper-case field name):

| Field | Type / default |
|---|---|
| `database_url` | `str` (required) |
| `chatbot_database_url` | `str` (required) |
| `hub_secret_key` | `SecretStr`, validated as a Fernet key |
| `auth_mode` | `Literal["none"] = "none"` |
| `display_row_cap` | `int = 1000` |
| `export_row_cap` | `int = 100_000` |
| `llm_result_max_rows` | `int = 200` |
| `llm_result_max_chars` | `int = 20_000` |
| `llm_timeout_s` | `float = 30` |
| `statement_timeout_ms` | `int = 5000` |
| `turn_timeout_s` | `float = 90` |
| `max_generations` | `int = 3` |
| `hub_enable_fake_llm` | `bool = False` |
| `max_upload_bytes` | `int = 10_485_760` |

`model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")`.

- [ ] **Step 1: Create `pyproject.toml` with uv.**
  - Runtime deps: fastapi, uvicorn[standard], sqlalchemy, alembic, psycopg[binary], pydantic-settings, openpyxl, cryptography, python-multipart.
  - Dev group: pytest, httpx, ruff.
  - `[tool.pytest.ini_options]`: `testpaths=["tests"]`, `markers=["acceptance: MVP acceptance tests"]`.
  - `[tool.ruff]`: `line-length=100`, `target-version="py312"`.
  - Run `uv sync`. Expected: `.venv` is created and uses Python 3.12.

- [ ] **Step 2: Write the failing tests.**

```python
# tests/test_health.py
def test_health_returns_ok(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}

def test_unknown_route_uses_error_shape(client):
    body = client.get("/api/nope").json()
    assert set(body["error"]) == {"code", "message", "details"}

# tests/test_config.py
def test_invalid_secret_key_is_rejected(monkeypatch):
    monkeypatch.setenv("HUB_SECRET_KEY", "not-a-fernet-key")
    with pytest.raises(ValidationError, match="Fernet"):
        Settings()
```

`tests/conftest.py`:
- before importing the app, sets `DATABASE_URL`, `CHATBOT_DATABASE_URL`, and a generated `HUB_SECRET_KEY`;
- calls `get_settings.cache_clear()`;
- provides a `client` fixture (`fastapi.testclient.TestClient(create_app())`).

- [ ] **Step 3: Run `uv run pytest tests/test_health.py tests/test_config.py -v`.** Expected: FAIL (`ModuleNotFoundError: app.main`).

- [ ] **Step 4: Implement `config.py`, `errors.py`, and `main.py`.**
  - The Fernet check calls `Fernet(value.get_secret_value())`. On failure it raises with the message: `HUB_SECRET_KEY must be a Fernet key; generate one with: uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.
  - Error handlers cover `HubError`, `StarletteHTTPException` (code `not_found` / `http_<status>`), `RequestValidationError` (code `validation_error`, details = errors), and a catch-all `Exception` (code `internal_error`, generic message, logged).

- [ ] **Step 5: Write `.env.example` and `.gitignore`.**
  - `.env.example` lists every Settings env var, plus `POSTGRES_PASSWORD`, `HUB_APP_PASSWORD`, `CHATBOT_RO_PASSWORD`, `TEST_ADMIN_DATABASE_URL`, with placeholder values and one comment line each.
  - `.gitignore` covers `.env`, `.venv/`, `__pycache__/`, `node_modules/`, `dist/`, `.pytest_cache/`, `.ruff_cache/`, `backend/benchmark/reports/`, `frontend/test-results/`, `frontend/playwright-report/`.

- [ ] **Step 6: Run tests and lint.** Run `uv run pytest -v && uv run ruff check . && uv run ruff format --check .`. Expected: 3 passed, no lint errors.

- [ ] **Step 7: Commit** `chore(backend): scaffold FastAPI app with settings and error shape`.

---

### Task 2: Database, roles, core migration, test database

**Files:**
- Create:
  - `docker-compose.yml` (only the `db` service in this task)
  - `docker-compose.dev.yml` (publishes `127.0.0.1:5432:5432` for db)
  - `db/init/01-roles.sh`
  - `backend/app/db.py`
  - `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_core_schema.py`
  - `backend/app/auth/models.py`, `backend/app/imports/models.py`, `backend/app/events/models.py`, `backend/app/dataset/models.py`, `backend/app/quality/models.py` (each package also gets an `__init__.py`)
  - `backend/tests/db_fixtures.py`, `backend/tests/test_schema.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Produces:
  - `app.db.Base` (DeclarativeBase)
  - `app.db.get_app_engine() -> Engine`
  - `app.db.get_chatbot_engine() -> Engine`
  - `app.db.SessionLocal`
  - `app.db.get_session() -> Iterator[Session]` (FastAPI dependency; commits on success, rolls back on error)
  - ORM classes: `AppUser`, `ImportFile`, `Event`, `Person`, `PersonIdentifier`, `Attendance`, `DataQualityFlag`, with columns per spec §5
  - Test fixtures: `db_session` (Session on hub_test, tables truncated before each test, `local` user re-seeded) and `chatbot_engine` (Engine as chatbot_ro on hub_test)

- [ ] **Step 1: Write the compose `db` service and `01-roles.sh`.** First run `cp .env.example .env`, then fill in the passwords and a generated `HUB_SECRET_KEY`. `TEST_ADMIN_DATABASE_URL` is `postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/postgres`.
  - `docker-compose.yml`: `postgres:16`, env from `.env`, named volume `hub-pgdata`, init dir mounted at `/docker-entrypoint-initdb.d`, healthcheck `pg_isready`.
  - `01-roles.sh` runs as the superuser:
    - creates `hub_app` (LOGIN, password `$HUB_APP_PASSWORD`) and `chatbot_ro` (LOGIN, password `$CHATBOT_RO_PASSWORD`);
    - creates database `hub` owned by `hub_app`;
    - `ALTER ROLE chatbot_ro SET default_transaction_read_only = on`, `SET statement_timeout = '5s'`, `SET search_path = hub`.

- [ ] **Step 2: Write the failing schema tests.**

```python
# tests/test_schema.py
VIEW_COLUMNS = ["person_key", "event_name", "event_date", "term", "academic_year", "modality",
    "sponsors_hosts", "event_type", "platform", "first_name", "last_name", "email", "netid",
    "affiliation", "domestic_international", "school", "department"]

def test_view_has_exact_columns(db_session):
    cols = db_session.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='hub' "
        "AND table_name='attendance_view' ORDER BY ordinal_position")).scalars().all()
    assert cols == VIEW_COLUMNS

def test_local_user_is_seeded(db_session):
    assert db_session.scalar(select(AppUser.username)) == "local"

def test_chatbot_ro_can_select_view(chatbot_engine):
    with chatbot_engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM attendance_view")).scalar() == 0

@pytest.mark.parametrize("sql", [
    "SELECT * FROM hub.attendance", "SELECT * FROM hub.app_user",
    "SELECT * FROM hub.import_file", "INSERT INTO hub.event(name, term) VALUES ('x','Fall 2026')"])
def test_chatbot_ro_cannot_touch_tables(chatbot_engine, sql):
    with chatbot_engine.connect() as c, pytest.raises(DBAPIError):
        c.execute(text(sql))
```

  The `db_fixtures.py` session fixture:
  - connects with `TEST_ADMIN_DATABASE_URL` (superuser) and drops and recreates `hub_test` owned by `hub_app`;
  - runs `alembic upgrade head` with `DATABASE_URL` pointed at hub_test;
  - builds the hub_app and chatbot_ro URLs for hub_test from the configured URLs by swapping the database name.

- [ ] **Step 3: Run the tests.** Run `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db && uv run pytest tests/test_schema.py -v`. Expected: FAIL (no migration).

- [ ] **Step 4: Implement `db.py`, the ORM models, and migration `0001`.**
  - Column types: ids are `BigInteger` identity, strings are `Text`, timestamps are `timestamptz` with server default `now()`. `import_file.content` is `LargeBinary`. `attendance.raw_row` is `JSONB`.
  - `event.academic_year` is a plain `Text` column. The service sets it with `academic_year(term)` from Task 4.
  - Unique constraints: `import_file.file_sha256`; `person_identifier(kind, value)`; `attendance(event_id, person_id)` (NULL `person_id` values do not collide).
  - The migration seeds `app_user('local', 'GPSRC Staff')`, creates the view below, and runs `GRANT USAGE ON SCHEMA hub TO chatbot_ro; GRANT SELECT ON hub.attendance_view TO chatbot_ro;`.

```sql
CREATE VIEW hub.attendance_view AS
SELECT a.person_id AS person_key, e.name AS event_name, e.event_date, e.term, e.academic_year,
       e.modality, e.sponsors_hosts, e.event_type,
       CASE f.source WHEN 'campusgroups' THEN 'CampusGroups' ELSE '12twenty' END AS platform,
       a.first_name, a.last_name, a.email, a.netid, a.affiliation, a.domestic_international,
       a.school, a.department
FROM hub.attendance a
JOIN hub.event e ON e.id = a.event_id
JOIN hub.import_file f ON f.id = a.import_file_id;
```

- [ ] **Step 5: Run `uv run pytest -v`.** Expected: all pass.

- [ ] **Step 6: Commit** `feat(db): add core schema, attendance view, and read-only chatbot role`.

---

### Task 3: Auth seam

**Files:**
- Create: `backend/app/auth/dependencies.py`, `backend/app/auth/router.py`, `backend/app/auth/schemas.py`, `backend/tests/test_auth_seam.py`, `backend/tests/route_utils.py`
- Modify: `backend/app/main.py` (include the router)

**Interfaces:**
- Produces:
  - `app.auth.schemas.CurrentUser(BaseModel)` with `id: int`, `username: str`, `display_name: str`
  - `app.auth.dependencies.get_current_user(session: Session = Depends(get_session)) -> CurrentUser`
  - `GET /api/me` returns `CurrentUser` plus `auth_mode`
  - `tests.route_utils.routes_missing_dependency(app, dep) -> list[str]`

- [ ] **Step 1: Write the failing tests.**

```python
def test_me_returns_local_user(client):
    body = client.get("/api/me").json()
    assert body["username"] == "local" and body["auth_mode"] == "none"

def test_every_api_route_depends_on_current_user(app):
    # walks app.routes (APIRoute), flattens route.dependant.dependencies recursively
    assert routes_missing_dependency(app, get_current_user) == ["GET /api/health"]
```

- [ ] **Step 2: Run them.** Expected: FAIL.

- [ ] **Step 3: Implement.** With `auth_mode == "none"`, `get_current_user` loads the `local` user. Leave one comment marking where `AUTH_MODE=password` plugs in.

- [ ] **Step 4: Run `uv run pytest -v`.** Expected: pass.

- [ ] **Step 5: Commit** `feat(auth): add get_current_user seam and /api/me`.

---

### Task 4: File reader and normalization helpers

**Files:**
- Create: `backend/app/imports/reader.py`, `backend/app/imports/normalize.py`, `backend/tests/imports/__init__.py`, `backend/tests/imports/test_reader.py`, `backend/tests/imports/test_normalize.py`

**Interfaces:**
- Produces:
  - `read_grid(file_name: str, content: bytes) -> list[list[str | None]]`. Raises `HubError("unreadable_file", ..., 422)`.
  - `normalize.clean(v: str | None) -> str | None`
  - `normalize_email(v) -> str | None`
  - `normalize_netid(v) -> str | None`
  - `derive_netid(email: str | None) -> str | None`
  - `validate_term(term: str) -> str`
  - `academic_year(term: str) -> str`
  - `term_for_date(d: date) -> str`
  - `event_name_from_file_name(name: str) -> str`
  - `date_from_cg_uid(uid: str | None) -> date | None`

- [ ] **Step 1: Write the failing tests.**

```python
def test_csv_utf8_bom(): assert read_grid("a.csv", "﻿Name\nJosé\n".encode())[1] == ["José"]
def test_csv_cp1252_fallback(): assert read_grid("a.csv", "Name\nJosé\n".encode("cp1252"))[1] == ["José"]
def test_xlsx_integral_float_becomes_int_string(tmp_xlsx):  # cell 87000000.0
    assert read_grid("a.xlsx", tmp_xlsx([["Student ID #"], [87000000.0]]))[1] == ["87000000"]
def test_blank_rows_and_trailing_columns_dropped(tmp_xlsx):
    grid = read_grid("a.xlsx", tmp_xlsx([["A", "B", None, None], ["1", None, None, None], [None] * 4]))
    assert grid == [["A", "B"], ["1", None]]
def test_unknown_extension_rejected():
    with pytest.raises(HubError) as e: read_grid("a.pdf", b"%PDF")
    assert e.value.code == "unreadable_file"

@pytest.mark.parametrize("email,netid", [("aahmed@uci.edu", "aahmed"), (" AAhmed@UCI.EDU ", "aahmed"),
    ("jane.doe@uci.edu", None), ("x@hs.uci.edu", None), (None, None)])
def test_derive_netid(email, netid): assert derive_netid(email) == netid
@pytest.mark.parametrize("term,year", [("Fall 2026", "2026-27"), ("Winter 2027", "2026-27"),
    ("Spring 2027", "2026-27"), ("Summer 2027", "2026-27")])
def test_academic_year(term, year): assert academic_year(term) == year
def test_validate_term_rejects_bad(): pytest.raises(ValueError, validate_term, "fall 26")
@pytest.mark.parametrize("d,term", [(date(2026, 10, 7), "Fall 2026"), (date(2027, 2, 1), "Winter 2027"),
    (date(2027, 5, 1), "Spring 2027"), (date(2027, 8, 1), "Summer 2027")])
def test_term_for_date(d, term): assert term_for_date(d) == term
def test_event_name_from_file_name():
    assert event_name_from_file_name("Bagel Breakfast - October.csv") == "Bagel Breakfast, October"
    assert event_name_from_file_name("Health Careers Mixer.xlsx") == "Health Careers Mixer"
def test_date_from_cg_uid(): assert date_from_cg_uid("CG-20261007-001") == date(2026, 10, 7)
```

- [ ] **Step 2: Run `uv run pytest tests/imports -v`.** Expected: FAIL.

- [ ] **Step 3: Implement.**
  - CSV: decode `utf-8-sig`, fall back to `cp1252`, parse with the `csv` module.
  - XLSX/XLSM: `openpyxl.load_workbook(BytesIO, read_only=True, data_only=True)`, first worksheet.
  - Cell conversion: integral float → `str(int(v))`; `datetime`/`date` → ISO string; strip strings and turn `""` into `None`.
  - Drop fully empty rows. Cut columns past the last non-empty header cell.
  - `term_for_date` month ranges: Sep–Dec → Fall Y; Jan–Mar → Winter Y; Apr–Jun → Spring Y; Jul–Aug → Summer Y.

- [ ] **Step 4: Run the tests.** Expected: PASS.

- [ ] **Step 5: Commit** `feat(import): add file reader and normalization helpers`.

---

### Task 5: Adapter contract, detection, CampusGroups adapter

**Files:**
- Create: `backend/app/imports/adapters/__init__.py`, `backend/app/imports/adapters/base.py`, `backend/app/imports/adapters/campusgroups.py`, `backend/tests/imports/test_campusgroups.py`, `backend/tests/imports/test_detect.py`
- Create: `backend/sample_data/exports/` holding the 10 files copied unchanged from `../data/Example Data/Campus Groups Files/` and `../data/Example Data/12twenty Data Files/`, plus `backend/sample_data/GSPRC Compiled Dataset.xlsm`

**Interfaces:**
- Produces (`base.py`):

```python
@dataclass(frozen=True)
class RowFlag: code: str; detail: str = ""
@dataclass
class NormalizedRow:
    source_row: int  # 1-based file row; header row is 1
    first_name: str | None; last_name: str | None; email: str | None; netid: str | None
    student_id: str | None; affiliation: str | None; domestic_international: str | None
    school: str | None; department: str | None
    raw: dict[str, str | None]  # header -> value; a repeated header gets " (2)" appended
    flags: list[RowFlag]
@dataclass
class SkippedRow: source_row: int; reason: str
@dataclass
class ParseResult: rows: list[NormalizedRow]; skipped: list[SkippedRow]
@dataclass
class EventDraft:
    name: str; event_date: date | None; term: str | None; modality: str | None
    sponsors_hosts: str | None; event_type: str | None; on_campus_groups: bool
class Adapter(Protocol):
    source: str; display_name: str; required_headers: tuple[str, ...]
    def parse(self, grid: list[list[str | None]]) -> ParseResult: ...
    def prefill(self, file_name: str, result: ParseResult) -> EventDraft: ...
```

- Produces (`__init__.py`):
  - `ADAPTERS: tuple[Adapter, ...]`
  - `detect_adapter(header: list[str | None]) -> Adapter`. Headers are compared after `strip()`, as multisets. On no match it raises `HubError("unknown_format", "...", 422, {"closest": <display_name>, "missing": [...]})`, where `closest` is the adapter with the fewest missing headers.
- Row flags emitted by adapters: `missing_netid`, `missing_email`, `missing_school`, `missing_department`, `missing_affiliation`, `missing_domestic_international` (CampusGroups only), `non_standard_email` (12twenty only). `student_worker` is not part of `EventDraft`; the service fills it (Task 8).

- [ ] **Step 1: Copy the sample files** (byte-identical; check with `shasum`).

- [ ] **Step 2: Write the failing tests.**

```python
SAMPLES = Path(__file__).parents[2] / "sample_data" / "exports"
def cg(name): return read_grid(name, (SAMPLES / name).read_bytes())

def test_detects_campusgroups(): assert detect_adapter(cg("Bagel Breakfast - October.csv")[0]).source == "campusgroups"
def test_unknown_format_lists_missing():
    with pytest.raises(HubError) as e: detect_adapter(["First Name", "Last Name", "Email"])
    assert e.value.code == "unknown_format" and "Net ID" in e.value.details["missing"]
def test_header_whitespace_tolerated():
    header = [f" {h} " for h in cg("Bagel Breakfast - October.csv")[0]]
    assert detect_adapter(header).source == "campusgroups"

def test_campusgroups_october_rows():
    res = CampusGroupsAdapter().parse(cg("Bagel Breakfast - October.csv"))
    assert len(res.rows) == 38 and res.skipped == []
    r = res.rows[0]
    assert (r.first_name, r.email, r.netid, r.student_id, r.school, r.affiliation, r.domestic_international) == (
        "Aaliyah", "aahmed@uci.edu", "aahmed", "87000000", "School of Biological Sciences",
        "Doctoral Student", "International")
    assert r.source_row == 2 and r.raw["Email (2)"] == "aahmed@uci.edu"
def test_campusgroups_xlsx_december(): assert len(CampusGroupsAdapter().parse(cg("Bagel Breakfast - December.xlsx")).rows) == 24
def test_campusgroups_prefill():
    a = CampusGroupsAdapter(); res = a.parse(cg("Bagel Breakfast - October.csv"))
    d = a.prefill("Bagel Breakfast - October.csv", res)
    assert (d.name, d.event_date, d.term, d.on_campus_groups) == (
        "Bagel Breakfast, October", date(2026, 10, 7), "Fall 2026", True)
def test_campusgroups_missing_netid_flagged():
    res = CampusGroupsAdapter().parse(cg("Bagel Breakfast - November.csv"))
    assert any(f.code == "missing_netid" for r in res.rows for f in r.flags)
```

- [ ] **Step 3: Run `uv run pytest tests/imports -v`.** Expected: FAIL.

- [ ] **Step 4: Implement the adapter contract, the registry, and `CampusGroupsAdapter`.**
  - `source="campusgroups"`, `display_name="CampusGroups"`, `required_headers` = the 26 headers from spec §6 and the template.
  - Name and email use the profile copy (occurrence 1 of `First Name`/`Last Name`/`Email`) and fall back to the form copy (`First name`, `Last name`, `Email` occurrence 2).
  - NetID comes from `Net ID`, Student ID from `Student ID #`, school from `School (drop down menu)`, and department from `Department`.
  - Affiliation comes from the header starting `Please select what you identify as`. Domestic/international comes from `Are you an international or domestic student/postdoc?`.
  - Prefill: the date comes from the first non-empty `Event Registration UID`. The term is `term_for_date(date)` when there is a date; otherwise `None`.

- [ ] **Step 5: Run the tests.** Expected: PASS.

- [ ] **Step 6: Commit** `feat(import): add adapter registry and CampusGroups adapter`.

---

### Task 6: 12twenty adapter

**Files:**
- Create: `backend/app/imports/adapters/twelvetwenty.py`, `backend/tests/imports/test_twelvetwenty.py`
- Modify: `backend/app/imports/adapters/__init__.py` (register the adapter)

**Interfaces:**
- Consumes: the Task 5 contract
- Produces: `TwelveTwentyAdapter` (`source="twelvetwenty"`, `display_name="12twenty"`, `required_headers` = the 16 headers)

- [ ] **Step 1: Write the failing tests.**

```python
def tt(name): return read_grid(name, (SAMPLES / name).read_bytes())
def test_detects_twelvetwenty(): assert detect_adapter(tt("Health Careers Mixer.xlsx")[0]).source == "twelvetwenty"
def test_twelvetwenty_rows_and_mapping():
    res = TwelveTwentyAdapter().parse(tt("Building your Brand Workshop.xlsx"))
    assert len(res.rows) == 27
    r = res.rows[0]
    assert (r.email, r.netid, r.school, r.department, r.affiliation, r.student_id, r.domestic_international) == (
        "aahmed@uci.edu", "aahmed", "School of Biological Sciences", "Molecular Biology and Biochemistry",
        "Doctoral Student", None, None)
def test_masters_maps_to_curly_apostrophe():
    rows = TwelveTwentyAdapter().parse(tt("Building your Brand Workshop.xlsx")).rows
    assert "Master’s Student" in {r.affiliation for r in rows}
def test_not_attended_rows_skipped():
    grid = tt("Health Careers Mixer.xlsx"); grid[1][7] = "NO"
    res = TwelveTwentyAdapter().parse(grid)
    assert len(res.rows) == 44 and res.skipped == [SkippedRow(2, "not_attended")]
def test_non_standard_email_flagged():
    grid = tt("Health Careers Mixer.xlsx"); grid[1][5] = "Jane.Doe@uci.edu"
    r = TwelveTwentyAdapter().parse(grid).rows[0]
    assert r.netid is None and RowFlag("non_standard_email") in r.flags
def test_linkedin_row_without_email_has_no_identity():
    rows = TwelveTwentyAdapter().parse(tt("LinkedIn Info Session.xlsx")).rows
    assert len(rows) == 34 and sum(1 for r in rows if r.email is None and r.netid is None) == 1
def test_prefill_has_no_date():
    a = TwelveTwentyAdapter(); d = a.prefill("Health Careers Mixer.xlsx", a.parse(tt("Health Careers Mixer.xlsx")))
    assert (d.name, d.event_date, d.on_campus_groups) == ("Health Careers Mixer", None, False)
```

- [ ] **Step 2: Run `uv run pytest tests/imports/test_twelvetwenty.py -v`.** Expected: FAIL.

- [ ] **Step 3: Implement.**
  - Keep only rows where `Attended?`, uppercased, equals `YES`.
  - The NetID comes only from `derive_netid(email)`. Emit `non_standard_email` when the email is present but no NetID can be derived.
  - `Registration Date` is ignored apart from `raw`.

- [ ] **Step 4: Run the tests.** Expected: PASS.

- [ ] **Step 5: Commit** `feat(import): add 12twenty adapter`.

---

### Task 7: Identity linker

**Files:**
- Create: `backend/app/imports/identity.py`, `backend/tests/imports/test_identity.py`

**Interfaces:**
- Produces:

```python
@dataclass
class LinkResult:
    person_id: int | None; method: Literal["netid", "email", "none"]; flags: list[RowFlag]
    created: bool  # True when this call created the person (feeds CommitSummary.new_people)
class IdentityLinker:
    def __init__(self, session: Session) -> None: ...
    def link(self, netid: str | None, email: str | None) -> LinkResult: ...  # flushes, never commits
```

Linker flags: `missing_identity`, `netid_email_conflict`, `email_owned_by_other`. Rules are in spec §6 ("Identity linking", 1–5, then the email-attach rule).

- [ ] **Step 1: Write the failing tests** (`db_session` fixture).

```python
def test_new_person_by_netid(db_session):
    r = IdentityLinker(db_session).link("aahmed", "aahmed@uci.edu")
    assert r.method == "netid" and r.person_id and r.flags == []
def test_same_netid_links_same_person(db_session):
    l = IdentityLinker(db_session); a = l.link("aahmed", "aahmed@uci.edu"); b = l.link("aahmed", None)
    assert a.person_id == b.person_id and b.method == "netid"
def test_email_only_links_to_existing(db_session):
    l = IdentityLinker(db_session); a = l.link("cdiaz", "cdiaz@uci.edu"); b = l.link(None, "cdiaz@uci.edu")
    assert (b.person_id, b.method) == (a.person_id, "email")
def test_netid_attaches_to_email_only_person(db_session):
    l = IdentityLinker(db_session); a = l.link(None, "jane.doe@uci.edu"); b = l.link("jdoe", "jane.doe@uci.edu")
    assert b.person_id == a.person_id and l.link("jdoe", None).person_id == a.person_id
def test_conflicting_netid_wins_and_flags(db_session):
    l = IdentityLinker(db_session); a = l.link("aaa", "x@uci.edu"); b = l.link("bbb", "x@uci.edu")
    assert b.person_id != a.person_id and RowFlag("netid_email_conflict") in [RowFlag(f.code) for f in b.flags]
def test_no_identity(db_session):
    r = IdentityLinker(db_session).link(None, None)
    assert (r.person_id, r.method, [f.code for f in r.flags]) == (None, "none", ["missing_identity"])
```

- [ ] **Step 2: Run `uv run pytest tests/imports/test_identity.py -v`.** Expected: FAIL.

- [ ] **Step 3: Implement.** Use one `SELECT` on `person_identifier` per lookup, `session.add` + `flush()` for new rows, and no caching.

- [ ] **Step 4: Run the tests.** Expected: PASS.

- [ ] **Step 5: Commit** `feat(import): link attendees to people by NetID then email`.

---

### Task 8: Import service and routers

**Files:**
- Create: `backend/app/imports/schemas.py`, `backend/app/imports/service.py`, `backend/app/imports/router.py`, `backend/app/events/schemas.py`, `backend/app/events/service.py`, `backend/app/events/router.py`, `backend/app/quality/service.py`, `backend/tests/imports/test_service.py`, `backend/tests/imports/test_router.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `read_grid`, `detect_adapter`, `IdentityLinker`, `CurrentUser`, `get_session`, `get_current_user`
- Produces (schemas, Pydantic):
  - `EventDraftOut`: the `EventDraft` fields plus `student_worker: str | None`
  - `ImportPreview`: `id: int | None`, `file_name`, `status: Literal["pending", "duplicate", "rejected"]`, `source: str | None`, `source_display: str | None`, `row_count: int`, `skipped: list[SkippedRowOut]`, `flag_counts: dict[str, int]`, `event_draft: EventDraftOut | None`, `duplicate_of: int | None`, `error: ErrorOut | None`
  - `EventDetailsIn`: `name` (1–200 chars), `event_date: date | None`, `term: str` (validated with `validate_term`), `modality: Literal["In Person", "Virtual", "Hybrid"]`, `sponsors_hosts: str | None`, `event_type: str` (1–100 chars), `attendance_source_note: str | None`, `student_worker: str | None`
  - `CommitSummary`: `import_id`, `event_id`, `inserted`, `linked_by_netid`, `linked_by_email`, `new_people`, `unlinked`, `flagged_rows`, `skipped`, `duplicates_in_event`
  - `ImportFileOut`: `id`, `file_name`, `source`, `status`, `row_count`, `skipped_count`, `event: {id, name, term} | None`, `flag_count`, `uploaded_by: {id, display_name}`, `uploaded_at`, `committed_at`
  - `EventOut`: `id`, `name`, `event_date`, `term`, `academic_year`, `modality`, `event_type`, `attendee_count`
- Produces (functions):
  - `preview_upload(session, file_name: str, content: bytes, user: CurrentUser) -> ImportPreview`
  - `commit_import(session, import_id: int, details: EventDetailsIn, user: CurrentUser) -> CommitSummary`
  - `discard_import(session, import_id: int, user: CurrentUser) -> None`
  - `list_imports(session) -> list[ImportFileOut]`
  - `quality.service.record_flags(session, import_file_id: int, attendance_id: int | None, source_row: int, flags: list[RowFlag]) -> None`
  - `events.service.list_events(session) -> list[EventOut]`
- Routes:
  - `POST /api/imports` (multipart `files`) → `{"files": list[ImportPreview]}`
  - `GET /api/imports`, `GET /api/imports/{id}`, `POST /api/imports/{id}/commit`, `DELETE /api/imports/{id}`, `GET /api/events`
- Error codes:
  - `unreadable_file`, `unknown_format`, `file_too_large`, `empty_file`: these become per-file `rejected`, never batch failures
  - `import_not_found` (404), `import_not_pending` (409), `validation_error` (422)

- [ ] **Step 1: Write the failing tests.**

```python
def test_preview_then_commit(db_session, user):
    p = preview_upload(db_session, "Bagel Breakfast - October.csv", sample_bytes("Bagel Breakfast - October.csv"), user)
    assert (p.status, p.source, p.row_count, p.event_draft.name) == ("pending", "campusgroups", 38, "Bagel Breakfast, October")
    s = commit_import(db_session, p.id, EventDetailsIn(name="Bagel Breakfast, October", term="Fall 2026",
        modality="In Person", event_type="Wellness/Mental Health", sponsors_hosts="GPSRC"), user)
    assert s.inserted == 38 and s.linked_by_netid + s.linked_by_email + s.unlinked == 38
def test_reupload_committed_is_duplicate(db_session, user): ...  # second preview: status "duplicate", duplicate_of == first id, no new pending row
def test_reupload_pending_returns_same_pending(db_session, user): ...  # same id, still one import_file row
def test_duplicate_person_in_file_is_skipped(db_session, user):
    content = csv_with_rows(header=CG_HEADER, rows=[ROW_AAHMED, ROW_AAHMED])
    s = commit_after_preview(db_session, "dup.csv", content, user)
    assert (s.inserted, s.duplicates_in_event) == (1, 1)
def test_commit_twice_is_conflict(db_session, user): ...  # HubError code "import_not_pending", status 409

# tests/imports/test_router.py
def test_batch_with_bad_files_still_previews_good(client):
    files = [("files", ("Bagel Breakfast - October.csv", sample_bytes("Bagel Breakfast - October.csv"), "text/csv")),
             ("files", ("empty.csv", b"", "text/csv")), ("files", ("notes.pdf", b"%PDF-1.4", "application/pdf")),
             ("files", ("big.csv", b"a" * (10_485_760 + 1), "text/csv"))]
    body = client.post("/api/imports", files=files).json()["files"]
    assert [f["status"] for f in body] == ["pending", "rejected", "rejected", "rejected"]
    assert [f["error"]["code"] for f in body[1:]] == ["empty_file", "unreadable_file", "file_too_large"]
def test_unknown_format_rejected_with_missing_columns(client): ...  # error.details.missing non-empty
def test_commit_validation_error_shape(client): ...  # bad term -> 422, error.code == "validation_error"
```

- [ ] **Step 2: Run `uv run pytest tests/imports -v`.** Expected: FAIL.

- [ ] **Step 3: Implement the service and routers.**
  - Preview: check size, then the empty case, then hash, then look for a duplicate or pending file, then `read_grid`, `detect_adapter`, and `parse`. Store `content`, then return the preview with `flag_counts` taken from the row flags.
  - Commit, in one transaction:
    - re-parse the stored bytes and create the `Event` (`academic_year(term)`, `on_campus_groups` from the source, `student_worker` = details or the user's display name, `created_by` = user);
    - for each row: `IdentityLinker.link` → skip it (flag `duplicate_in_event`) if `(event_id, person_id)` is already used in this commit → insert the `Attendance` with `raw_row=row.raw` → `record_flags`;
    - record skipped rows as `not_attended_skipped` flags with `attendance_id=None`.

- [ ] **Step 4: Run `uv run pytest -v`.** Expected: all pass, including the route-dependency test from Task 3.

- [ ] **Step 5: Commit** `feat(import): add preview/commit import service and API`.

---

### Task 9: Export writers, dataset service, full-dataset export

**Files:**
- Create: `backend/app/export/__init__.py`, `backend/app/export/writers.py`, `backend/app/dataset/service.py`, `backend/app/dataset/router.py`, `backend/tests/test_export.py`, `backend/tests/test_dataset.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces:
  - `guard_cell(value: object) -> object`. A string starting with `=`, `+`, `-`, `@`, `\t`, or `\r` is marked as text.
  - `to_xlsx(columns: list[str], rows: Iterable[Sequence[object]]) -> bytes`. Guarded strings are written with `cell.data_type = "s"`.
  - `to_csv(columns, rows) -> bytes`. Encoded `utf-8-sig`; guarded strings are prefixed with `'`.
  - `export_filename(stem: str, ext: str, now: datetime) -> str`, giving `hub-<stem>-YYYYMMDD-HHMM.<ext>`.
  - `export_response(columns, rows, fmt: Literal["xlsx", "csv"], stem: str) -> Response`, with Content-Disposition attachment.
  - `dataset.service.GPSRC_HEADERS: tuple[str, ...]` (the 19 headers from Global Constraints)
  - `ALLOWED_COLUMNS: frozenset[str]` (the 17 view columns)
  - `DatasetFilter(column: str, op: Literal["eq", "ilike", "is_null"], value: str | None)`
  - `query_dataset(session, filters: list[DatasetFilter] = [], sort: list[tuple[str, Literal["asc", "desc"]]] = [], limit: int | None = None, offset: int = 0) -> tuple[list[str], list[tuple]]`. Reads the view through the app engine with bound parameters. Unknown columns raise `HubError("invalid_column", 422)`. This is the F11 seam.
  - `gpsrc_layout_rows(session) -> tuple[list[str], list[list[object]]]`. The 19 columns include Student ID. `On Campus Groups?` is written as `"Yes"`/`"No"`. Notes = `build_note(source, flag_codes)`.
  - `build_note(source: str, flag_codes: list[str]) -> str`. Example: `"Source: CampusGroups export; INCOMPLETE: email missing"`.
  - Route `GET /api/dataset/export?format=xlsx|csv` (stem `dataset`).

- [ ] **Step 1: Write the failing tests.**

```python
def test_formula_value_is_text_in_xlsx():
    wb = openpyxl.load_workbook(BytesIO(to_xlsx(["Department"], [["=HYPERLINK(\"x\")"]])))
    c = wb.active["A2"]; assert c.data_type == "s" and c.value == '=HYPERLINK("x")'
def test_formula_value_prefixed_in_csv(): assert to_csv(["d"], [["+1"]]).decode("utf-8-sig").splitlines()[1] == "'+1"
def test_plain_values_untouched(): assert guard_cell("Biology") == "Biology" and guard_cell(5) == 5
def test_export_filename(): assert export_filename("dataset", "xlsx", datetime(2026, 10, 22, 9, 5)) == "hub-dataset-20261022-0905.xlsx"
def test_query_dataset_rejects_unknown_column(db_session):
    with pytest.raises(HubError): query_dataset(db_session, [DatasetFilter("student_id", "eq", "1")])
def test_full_export_headers(client, committed_october):
    r = client.get("/api/dataset/export?format=xlsx")
    ws = openpyxl.load_workbook(BytesIO(r.content)).active
    assert [c.value for c in ws[1]] == list(GPSRC_HEADERS) and ws.max_row == 39
```

- [ ] **Step 2: Run `uv run pytest tests/test_export.py tests/test_dataset.py -v`.** Expected: FAIL.

- [ ] **Step 3: Implement.** In `to_xlsx`, use openpyxl `Workbook(write_only=False)`. For guarded strings, assign the value and then set `cell.data_type = "s"`.

- [ ] **Step 4: Run `uv run pytest -v`.** Expected: all pass.

- [ ] **Step 5: Commit** `feat(export): add formula-safe XLSX/CSV writers and full-dataset export`.

---

### Task 10: Sample loader and acceptance tests A1, A2, A9

**Files:**
- Create: `backend/sample_data/events.json`, `backend/app/samples.py`, `backend/tests/acceptance/__init__.py`, `backend/tests/acceptance/test_import_acceptance.py`

**Interfaces:**
- Produces:
  - `app.samples.SAMPLE_DIR: Path`
  - `load_sample_exports(session, user: CurrentUser) -> list[CommitSummary]`. Previews and commits all 10 files with the details from `events.json`.
  - CLI `uv run python -m app.samples` loads the samples into the configured DB and prints the summaries. S3, S5, and demos use it.
- `events.json` maps each file name to `{name, term: "Fall 2026", modality, sponsors_hosts, event_type, student_worker: "Rosie Victor", event_date: null}`:

| File | name | modality | sponsors_hosts | event_type |
|---|---|---|---|---|
| Bagel Breakfast - October.csv | Bagel Breakfast, October | In Person | GPSRC | Wellness/Mental Health |
| Bagel Breakfast - November.csv | Bagel Breakfast, November | In Person | GPSRC | Wellness/Mental Health |
| Bagel Breakfast - December.xlsx | Bagel Breakfast, December | In Person | GPSRC | Wellness/Mental Health |
| Cover Letters for Academic Jobs.csv | Cover Letters for Academic Jobs | Virtual | GPSRC / Graduate Writing Hub | Professional Development |
| Teaching Statements for Academic Jobs.csv | Teaching Statements for Academic Jobs | Virtual | GPSRC / Graduate Writing Hub | Professional Development |
| Postdoc Wellness Lunch.csv | Postdoc Wellness Lunch | In Person | Postdoctoral Affairs | Wellness/Mental Health |
| Building your Brand Workshop.xlsx | Building your Brand Workshop | Hybrid | GPSRC / Activate to Captivate | Professional Development |
| Edwards Life Science Site Visit.xlsx | Edwards Life Science Site Visit | In Person | GPSRC / Edwards Lifesciences | Professional Development |
| Health Careers Mixer.xlsx | Health Careers Mixer | In Person | GPSRC / GPS-STEM | Professional Development |
| LinkedIn Info Session.xlsx | LinkedIn Info Session | Virtual | GPSRC / Division of Career Pathways | Professional Development |

- [ ] **Step 1: Write the failing acceptance tests** (`@pytest.mark.acceptance`).

```python
COMPARE = ["Student Worker", "Event Term", "Event Name ", "Virtual/ In-Person/ Hybrid ", "Sponsor/Host/Parnters",
    "Event type (Professional Development, Wellness/Mental Health, Fellowships)", "On Campus Groups?",
    "First Name of Attendee", "Last Name of Attendee", "Email", "Affiliation", "Student ID or Employee ID",
    "NetID", "Domestic or International", "School", "Department "]

def test_a1_import_reproduces_compiled_sheet(db_session, user):
    load_sample_exports(db_session, user)
    cols, rows = gpsrc_layout_rows(db_session)
    ours = Counter(tuple(norm(r[cols.index(c)]) for c in COMPARE) for r in rows)
    theirs = Counter(compiled_rows(SAMPLE_DIR.parent / "GSPRC Compiled Dataset.xlsm", COMPARE))  # sheet "Master Attendance"
    assert sum(ours.values()) == 293 and ours == theirs
    assert db_session.scalar(text("SELECT count(DISTINCT netid) FROM hub.attendance_view")) == 79
def test_a1_identity_edge_rows(db_session, user):
    load_sample_exports(db_session, user)
    # Bagel Breakfast, November row with email cdiaz@uci.edu and no NetID -> match_method "email", linked to the cdiaz person
    # LinkedIn Info Session row with neither -> person_id NULL and a "missing_identity" flag
def test_a2_reupload_adds_nothing(db_session, user):
    load_sample_exports(db_session, user)
    for f in sorted(SAMPLE_DIR.iterdir()):
        assert preview_upload(db_session, f.name, f.read_bytes(), user).status == "duplicate"
    assert db_session.scalar(text("SELECT count(*) FROM hub.attendance")) == 293
def test_a9_formula_cell_exported_as_text(): ...  # to_xlsx with "=1+1" -> data_type "s" after reload
```

  - `norm()` maps `None`, `""`, `"Yes"`, `"No"`, and numbers to comparable strings: `True` → `"Yes"`, `False` → `"No"`, `None` → `""`.
  - `compiled_rows` reads the 19-column sheet with openpyxl and skips empty rows.

- [ ] **Step 2: Run `uv run pytest -m acceptance -v`.** Expected: FAIL (no loader).

- [ ] **Step 3: Implement `events.json` and `app/samples.py`.**

- [ ] **Step 4: Run `uv run pytest -m acceptance -v`.** Expected: PASS. If A1 differs, print the multiset difference (both directions) and fix the adapter or normalization. Never edit the compiled sheet or the expected values.

- [ ] **Step 5: Commit** `test(acceptance): import samples reproduce compiled sheet (A1, A2, A9)`.

---

### Task 11: Frontend skeleton, Docker full stack, docs

**Files:**
- Create:
  - `frontend/` (from `npm create vite@latest frontend -- --template react-ts`)
  - `frontend/src/api/client.ts`, `frontend/src/app/App.tsx`, `frontend/src/app/AppShell.tsx`, `frontend/src/app/AuthGate.tsx`, `frontend/src/app/theme.ts`, `frontend/src/app/PlaceholderPage.tsx`
  - `frontend/src/api/client.test.ts`
  - `frontend/nginx.conf`, `frontend/Dockerfile`, `backend/Dockerfile`, `backend/.dockerignore`, `frontend/.dockerignore`
- Modify: `docker-compose.yml` (add `api` and `nginx`), `frontend/vite.config.ts` (proxy `/api` → `http://localhost:8000`; Vitest jsdom), `CLAUDE.md` (Commands and layout), `PROGRESS.md`

**Interfaces:**
- Produces (`client.ts`; S4 extends it):
  - `class ApiError extends Error { status: number; code: string; details: unknown }`
  - `apiGet<T>(path: string): Promise<T>`
  - `apiSend<T>(method: "POST" | "PATCH" | "DELETE", path: string, body?: unknown): Promise<T>`
  - Every request goes to `/api…` with `credentials: "same-origin"`. Non-2xx responses are parsed into `ApiError` from the error shape.
- `AppShell` has a left nav (Chat, Upload, Dataset, Settings) and shows `display_name` from `/api/me`. `AuthGate` renders its children. Routes `/chat`, `/upload`, `/dataset`, `/settings` all render `PlaceholderPage`; `/` redirects to `/chat`.

- [ ] **Step 1: Scaffold.** Run `npm create vite@latest frontend -- --template react-ts`, then `npm i @mui/material @mui/icons-material @emotion/react @emotion/styled @tanstack/react-query react-router` and `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom`.

- [ ] **Step 2: Write the failing test.**

```ts
it("parses the error shape into ApiError", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(
    { error: { code: "import_not_found", message: "Not found", details: null } }), { status: 404 })));
  await expect(apiGet("/api/imports/9")).rejects.toMatchObject({ status: 404, code: "import_not_found" });
});
```

- [ ] **Step 3: Run `npm test -- --run`.** Expected: FAIL.

- [ ] **Step 4: Implement the client, shell, gate, and routes** (react-router `createBrowserRouter`; TanStack `QueryClientProvider`).

- [ ] **Step 5: Run `npm test -- --run && npm run build`.** Expected: PASS and the build succeeds.

- [ ] **Step 6: Docker.**
  - `backend/Dockerfile`: `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`, `uv sync --frozen --no-dev`, CMD `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`.
  - `frontend/Dockerfile`: multi-stage, `node:24-alpine` build → `nginx:stable-alpine` with `nginx.conf`.
  - `nginx.conf`: SPA fallback to `index.html`; `location /api/` proxies to `http://api:8000` with `proxy_buffering off`, `proxy_read_timeout 120s`, and `client_max_body_size 50m`.
  - Compose: `nginx` publishes `127.0.0.1:8080:80` and depends on `api`, which depends on `db` (healthy). `api` gets `DATABASE_URL=postgresql+psycopg://hub_app:${HUB_APP_PASSWORD}@db:5432/hub` and the chatbot equivalent.

- [ ] **Step 7: Verify.** Run `docker compose up --build -d && curl -s 127.0.0.1:8080/api/health && curl -s 127.0.0.1:8080/ | grep -c '<div id="root">'`. Expected: `{"status":"ok"}` and `1`. Then run `docker compose down`.

- [ ] **Step 8: Docs.**
  - Fill in the `CLAUDE.md` "Commands" section: start the app, start the dev DB, backend dev server, `uv run pytest`, `uv run pytest -m acceptance`, `uv run ruff check .`, frontend dev and test, and loading the samples.
  - Update the planned layout.
  - Update `PROGRESS.md` for the end of S2.

- [ ] **Step 9: Commit** in two commits:
  - `feat(frontend): add app shell, API client, and Docker full stack`
  - `docs(progress): end of S2`
