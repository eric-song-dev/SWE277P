# Handoff guide

For whoever takes over the code. The design and its reasons are in the [spec](specs/2026-10-20-data-hub-design.md), which is the source of truth. This page is the map: what is where, how to run and test it, where to extend it, and what is left.

Read next to this: [`CLAUDE.md`](../CLAUDE.md) (commands, rules, non-negotiables), [`PROGRESS.md`](../PROGRESS.md) (current state and open issues), [known limitations](known-limitations.md), [benchmark results](benchmark-results.md).

## Architecture in brief

Three Docker containers, started with `docker compose up --build -d`:

| Container | Role |
|---|---|
| `nginx` | Serves the built React app and proxies `/api/*` to `api`. The only published port, `127.0.0.1:8080`. |
| `api` | FastAPI (Python 3.12). Runs the Alembic migrations on start, then serves the API. Runs as a non-root user and has a health check. |
| `db` | PostgreSQL 16, one database `hub`, with a named volume. |

**Backend** (`backend/app/`), a modular monolith. Routers are thin and call services, and services take an explicit database session and the current user.

| Module | Does |
|---|---|
| `imports/` | Adapters per platform (`adapters/`), file reading, detection, normalization, identity linking, the pending to committed flow. |
| `events/`, `dataset/` | Events. The dataset query service and the full-dataset export. |
| `chat/` | The LangGraph `StateGraph` (`graph/`), the SQL guard (`guard.py`), the executor (`executor.py`), the error sanitizer, conversations, and the streaming (SSE) router. |
| `llm/` | AI models: encrypted storage, presets, the chat model factory, the connection test. |
| `export/` | The XLSX and CSV writers with the formula guard. |
| `auth/` | `get_current_user`. Today it returns the one local user. |
| `quality/` | The data-quality flag model. |

**Frontend** (`frontend/src/`): React 19, TypeScript, Vite, MUI 9. `api/client.ts` is the only place that calls `fetch`, and a lint rule enforces it. `features/` has `upload`, `chat`, `settings` and `dataset`. `app/` has the shell, `AuthGate` and the routes.

**Two database roles.** `hub_app` reads and writes. `chatbot_ro` can read only `hub.attendance_view`, is read-only by default, and has a 5 second statement timeout. Only the chat executor and the chat export use the `chatbot_ro` connection. Generated SQL never runs on the app connection.

**Chat safety, in layers.** The SQL guard (sqlglot) allows one `SELECT` over `attendance_view` with an allow-list of functions. The executor runs it as one prepared statement in a read-only transaction that is always rolled back. The sanitizer strips row values from error messages before they go back to the AI. The prompts never contain attendee rows, except the optional result summary (see the [user guide](user-guide.md#4-who-sees-the-data-the-two-switches)). Every question is logged in `chat_turn`. Details: spec sections 7 and 13.

**Secrets.** API keys are encrypted with a Fernet key (`HUB_SECRET_KEY`, in `.env`), never returned by the API, never logged. Never read, print or commit `.env`.

## Run it and test it

Full list: `CLAUDE.md`, "Commands". The short version, from `project/`:

```
# Whole app at http://127.0.0.1:8080
docker compose up --build -d

# Dev: database only, published on 127.0.0.1:5432
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
```

Backend, from `project/backend` (needs [uv](https://docs.astral.sh/uv/) and the dev database running; copy `.env.example` to `project/.env` first and fill it in, as in the [setup guide](setup-guide.md#2-create-the-env-file)):

```
uv run alembic upgrade head
uv run uvicorn app.main:app --reload     # :8000
uv run pytest                            # all backend tests
uv run pytest -m acceptance              # A1/A2/A9 import, A5/A6/A8 chat, benchmark reference checks
uv run ruff check .
uv run ruff format --check .
uv run python -m app.samples             # load the synthetic samples into the dev database
```

Frontend, from `project/frontend`:

```
npm install
npm run dev                              # :5173, proxies /api to :8000
npm test -- --run                        # Vitest
npm run lint                             # oxlint
npm run build                            # type-check and production build
npm run e2e                              # Playwright happy path on its own stack (needs Docker)
npm run e2e:screenshots                  # regenerate docs/screenshots/
HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing   # A10, real AI model, main stack
```

First time for Playwright: `npx playwright install chromium`. `npm run e2e` starts its own Compose project (`hub-e2e`, port 8081) with the scripted "Demo" profile and removes it afterwards, so it needs no API key. `e2e:timing` makes real AI calls against the main stack with the samples loaded. See `CLAUDE.md` for how to start that stack.

The chatbot benchmark needs a saved AI model and the sample data:

```
cd backend
uv run python -m benchmark.run --profile "<name>" [--set main|holdout] [--only q01,q05] [--min-score 18]
```

It writes a report to `backend/benchmark/reports/` (not committed) and prints `Score: N/20`. Run it after every change to the prompt or the AI model. `--set holdout` runs the 10 held-out questions; never tune prompts on those. Results so far: [benchmark-results.md](benchmark-results.md).

Acceptance tests A1 to A10 are in spec section 14. A7 (login) is deferred. A3, A4 and A10 need a real AI key and are run by hand; the rest are automated.

## Extension points for the P1 features

These features are not built, but the code has a seam for each (spec section 12). Do not add stub endpoints in advance.

| Feature | Seam already in the code | What to add |
|---|---|---|
| F11 filter table | `dataset/service.py::query_dataset(filters, sort, limit, offset)` over `attendance_view`, with an allow-listed column set and bound parameters. Pages are stable. | A route and a DataGrid page. |
| F12 data quality | The `data_quality_flag` table with `resolved_at` and `resolved_by`. Flags are written at import. | A list or resolve UI and an "edit blank field" endpoint. |
| F14 saved queries | `chat_turn` keeps the question, SQL and interpretation. | A `saved_query` table referencing a turn, and a one-click run that reuses the export and re-run path. |
| F15 historical import | The adapter registry (`imports/adapters/__init__.py`). | A `gpsrc_sheet` adapter plus one migration (see below). Its event details come from the rows, so the form is skipped. |
| F16 multiple accounts | `app_user`, `get_current_user`, and `created_by` columns everywhere. | An auth mode, an admin page, and per-user filtering if wanted. |

To add a platform adapter: add one module under `imports/adapters/` that declares its `source`, its identifying headers, `parse(rows)` and `prefill(file_name, rows)`, and register it. Also add one Alembic migration that widens the `ck_import_file_source` CHECK to accept the new `source` and adds that source to the `platform` CASE in `attendance_view` (otherwise it is labelled 12twenty). Without the migration, every upload of the new format returns 500. New flag codes need no migration.

## Backlog

From spec section 3, plus what the S5 and S6 plans left:

- Login (see below).
- The P1 features above: F11, F12, F14, F15, F16.
- CI. The git root is the course folder, so CI waits for the team's own repository.
- Native Anthropic or Gemini connectors.
- Editing event details of a committed import, and deleting a committed import.
- Attaching a second file to an existing event.
- API key rotation (changing `HUB_SECRET_KEY`).
- S6, the UI redesign and the user-story walkthrough (`docs/design/2026-10-21-ui-redesign.md`). It also refreshes the screenshots and the label names in the user guide.
- Verify ZotGPT (base URL, JSON output, model names), then widen the response-format detection or merge consecutive user messages if the gateway needs it.
- Confirm with the sponsor: result sharing (D1), waitlisted registrants, whether "students" includes postdocs, the Notes wording. Add the sponsor's own dummy exports as test files when they arrive.

Out of scope unless the sponsor changes it: reconciling registration with attendance, certificates, charts and dashboards, live links to the platforms, UCI single sign-on.

## Moving it to OIT and adding login

The Hub is built to run on one staff computer. Moving it to a UCI server needs decisions that are not made yet (data classification, hosting, authentication), so treat this as a checklist, not a recipe.

1. **Ask OIT first** whether attendee names, emails and NetIDs may live on the server, and which AI providers may receive data. Result sharing (D1) must be settled before any provider other than the university's own sees rows.
2. **HTTPS at nginx.** Today nginx listens on plain HTTP and is bound to `127.0.0.1` (`docker-compose.yml`, `ports`). On a shared server, terminate TLS in `frontend/nginx.conf` (or in a reverse proxy in front) and publish only the HTTPS port. Do not bind the plain HTTP port to the network.
3. **Turn on login before exposing it.** The code is prepared (spec section 11):
   - Every data route depends on `auth/dependencies.py::get_current_user`. A test walks the route table to enforce it. Implement `AUTH_MODE=password` (or an SSO mode) by changing that dependency: add `password_hash` and `is_active` to `app_user`, login and logout routes, and an httpOnly session cookie. No other route should need to change.
   - Conversations and chat turns are already per user (other users get 404). Imports, the dataset, events and AI models are shared office resources. Decide if that stays.
   - In the frontend, `api/client.ts` is the one place to attach credentials and handle a 401. `AuthGate` wraps the routes, and a login page goes behind it. The acceptance test A7 ("no data without signing in") then needs writing.
4. **Secrets.** Use real secret storage for `HUB_SECRET_KEY` and the three database passwords. Back up the key apart from the database.
5. **Backups and updates.** Schedule `pg_dump` (see the [setup guide](setup-guide.md#7-back-up-and-restore)) and plan how the images are rebuilt and the host patched.
6. **Network.** Today the only outgoing traffic is HTTPS to the chosen AI provider. Keep it that way, and allow only that destination if the server has an egress firewall.

## Rules the code follows (keep them)

From `CLAUDE.md`:

- Accept native exports without edits. Uploading the same file twice never creates duplicates.
- Match people by NetID, then email. Flag uncertain matches. Never merge on names.
- Generated SQL is a single read-only `SELECT`, run through the read-only role with a timeout and a row limit. Always show the SQL.
- Synthetic data only in the repository, tests and prompts.
- Every new environment variable goes into `.env.example`, and into the api `environment:` list in `docker-compose.yml` if the api needs it.
- Commit after every change, with a Conventional Commit message. Update `PROGRESS.md` and `CLAUDE.md` when the state or layout changes.
