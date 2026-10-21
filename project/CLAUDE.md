# CLAUDE.md

Guidance for Claude Code when working on the capstone project. All project files live under `project/`.

## Rule #1: commit after every change

Every time you finish a change, commit it before ending your turn. Never leave uncommitted work behind.

- One commit per logical change (a feature, a fix, a doc update). If a task touched unrelated things, split it into several commits.
- Stage files by path (`git add backend/app/importer.py`). Never run `git add -A` or `git add .` from the repo root: the git root is `SWE277P/`, which also holds course materials outside `project/`.
- Run the relevant tests and lint before committing (see Commands). Fix failures first. If you can't fix them, still commit, prefix the subject with `WIP:`, and tell the user what is failing.
- Use Conventional Commits in English with an imperative subject, e.g. `feat(import): parse 12twenty xlsx exports` or `fix(chat): reject non-SELECT SQL`. Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`. Don't use `first commit` style messages.
- Commit on the current branch. Don't push, create branches, rebase, amend, or force-push unless the user asks.
- Never commit secrets (`.env`, API keys) or real student data.

## Rule #2: work in sessions, keep state in PROGRESS.md

The MVP is built over six separate Claude Code conversations, S1–S6 (S6, the UI redesign and user-story walkthrough, was added on 2026-10-21). Spec Section 15 lists what each one covers. S1–S5 are complete; S6 is next. Each session starts as a new conversation on purpose: one long conversation fills the context window and makes the AI worse. So anything that must carry over goes into files, not the chat.

At the start of a session:

1. Read this file, then `PROGRESS.md`, then the spec (`docs/specs/`) and the current plan (`docs/plans/`).
2. Work on what `PROGRESS.md` lists under "Next session", unless the user says otherwise.
3. Don't re-read large reference material (assignments, meeting notes, sample data) unless the task needs it. The spec already summarizes it.

Before the session ends, or as soon as the user says they are about to start a new conversation:

1. Update `PROGRESS.md`. Cover what was done, the state of the code (what works, how to run it, test results), the next session's scope and first steps, open issues and blockers, and any decisions made this session.
2. A decision that changes the design goes into the spec too, in the same commit.
3. Commit (`docs(progress): ...`). `PROGRESS.md` must always describe the committed state, so the next session can start from it alone.

Keep `PROGRESS.md` short. Rewrite the status sections each time instead of appending, and keep only a one-line-per-session log at the bottom.

## What we are building

**Program Registration & Attendance Data Hub** for UCI's Graduate & Postdoctoral Scholar Resource Center (GPSRC). SWE 277P capstone, Fall 2026. Sponsor and main user: Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development.

The app is a web app that runs locally on one GPSRC computer:

1. Staff upload one event's attendee export (CampusGroups or 12twenty) exactly as the platform produced it, and enter the event details in a form.
2. The app normalizes the rows into one permanent dataset in the GPSRC Data Project format and links the same person across events.
3. Staff ask questions in plain English, with follow-ups. An LLM turns the question into SQL, the app runs it locally, then shows the SQL and the result table. If the selected LLM profile allows it, the LLM also analyzes the query result.
4. Staff can download any result as Excel or CSV.

The full design is in `docs/specs/2026-10-20-data-hub-design.md`. It is the source of truth for the build; where it differs from assignment1 or the charter, the spec wins.

## Tech stack

- Frontend: React 19 + TypeScript (Vite), MUI 9 + MUI X DataGrid 9, TanStack Query
- Backend: FastAPI (Python 3.12, uv), SQLAlchemy 2, Alembic, Pydantic v2
- Database: PostgreSQL 16
- Packaging: Docker Compose (nginx, api, db). The whole app must start with one command on the sponsor's machine.
- Chatbot: a custom LangGraph `StateGraph` (not LangChain's prebuilt SQL agent), sqlglot for the SQL guard.
- LLM: OpenAI-compatible providers only, through `langchain-openai` `ChatOpenAI` with a `base_url`. Presets: ZotGPT Gateway, OpenAI, DeepSeek, Custom. Staff manage LLM profiles (base URL, model, API key) in the web UI and pick one per question. API keys are stored encrypted in PostgreSQL (Fernet, master key `HUB_SECRET_KEY` in `.env`) and never returned to the browser.

Layout:

```
project/
  README.md  CLAUDE.md  PROGRESS.md  docker-compose.yml  docker-compose.dev.yml  .env.example
  scripts/             acceptance.sh (final acceptance run), story_files.py (edge-case upload files for the user stories)
  db/init/             Postgres init scripts (app and read-only roles)
  docs/*.md            handoff guides (setup, user, data dictionary, known limitations, handoff) and benchmark-results.md
  docs/specs/          design specs
  docs/plans/          implementation plans
  docs/design/         approved visual design and its mockup source (UI redesign, built in S6)
  docs/user-stories/   user stories and their walkthrough results (written in S6)
  docs/screenshots/    UI screenshots from the Playwright e2e run (synthetic data)
  backend/             FastAPI app (app/), Alembic (alembic/), sample_data/, tests/, Dockerfile
  frontend/            React + Vite app (src/api client, src/app shell), nginx.conf, Dockerfile
```

## Non-negotiables

- **Privacy (provisional, pending sponsor confirmation):** the SQL-generation prompt only gets the schema, column descriptions, controlled values, prior questions and SQL, and the user's question. It never gets row values. The only exception is the analysis step: when the selected LLM profile allows it (`share_results_with_llm`) and the user leaves the "Let AI see the results" switch on for that question, the LLM receives the rows returned by its own guarded query against `attendance_view`, capped by `LLM_RESULT_MAX_ROWS` and `LLM_RESULT_MAX_CHARS`. The LLM must never see Student IDs, other tables, or the rest of the database. Error-retry messages go through the error sanitizer and never carry row values. Never log row values to external services. If the sponsor rejects result sharing, it is switched off per profile, not by changing code.
- **Secrets:** API keys are encrypted at rest, never returned by the API, and never logged. Never read, print, or `cat` `project/.env`. It holds the DB passwords and API keys, and anything you read ends up in the conversation. To check that a variable is set, run `grep -c '^NAME=.' .env`, which prints only a count. You may append non-secret lines to `.env` when the user asks. The user fills in secret values.
- **SQL safety:** generated SQL must be a single read-only `SELECT`, run through a read-only database role with a statement timeout and a row limit. Always show the SQL to the user.
- **Imports:** accept native export files unmodified. Staff must not have to clean files by hand. Uploading the same file twice must not create duplicates.
- **Identity matching:** match people by NetID first, then by email (12twenty exports have no NetID). Flag uncertain matches for staff instead of silently merging them.
- **Synthetic data only.** Never add real student data to the repo, fixtures, or prompts.

## Scope

In scope (P0): importing 12twenty and CampusGroups exports, entering event details at upload, one unified dataset, cross-event identity matching, a chatbot that shows its SQL (multi-turn follow-ups, clarifying questions, automatic repair retries, streamed progress, optional result analysis), LLM profiles managed in the UI, and Excel/CSV export.

P1 features (F11 filter table, F12 data quality, F14 saved queries, F15 historical import, F16 multiple accounts) are not built, but the P0 code must keep the extension points listed in spec Section 12. Don't add stub endpoints for them.

Out of scope (don't build these unless the user changes scope): registration/attendance reconciliation, certificates and multi-session programs, charts and dashboards, multiple accounts or roles, cloud or UCI server hosting, UCI SSO, live connections to 12twenty, CampusGroups, or Zoom.

### Login: in the backlog, but design for it now

Login is not part of the MVP. The charter (Oct 18) lists one staff login, but the team moved it to the backlog, so acceptance criterion 7 ("no data without signing in") is deferred too. Don't build login screens, password storage, or sessions yet.

The code must still make login easy to add later, ideally without editing every endpoint or page:

- **Backend:** every API route that touches data depends on a single `get_current_user` FastAPI dependency. For now it returns a fixed local user. Adding auth should mean changing only that dependency (plus adding login routes). Don't add any route that bypasses it.
- **Who did what:** write records that come from user actions, such as uploads, with the acting user's id (e.g. `uploaded_by`), taken from `get_current_user`.
- **Frontend:** send every API call through one shared API client, so auth headers or tokens can be attached in one place. Keep one top-level wrapper around the routes where a login gate can go later.
- **Config:** keep auth settings in env/config so login can be switched on without code changes elsewhere.

## Success criteria (MOV, due 2026-12-04)

- The chatbot answers at least 18 of 20 sponsor-style benchmark questions correctly.
- Importing the sample files reproduces the sponsor's compiled sheet: 293 rows and 79 unique NetIDs, with no duplicates after a re-upload.
- Going from question to downloaded Excel file takes under 1 minute.

Treat these as acceptance tests and automate them.

## Reference material (read-only, outside `project/`)

Read these freely, but don't modify them unless the user asks.

- `../assignment/assignment4/assignment4.md`: project charter (scope, MOV, schedule, costs). This is the source of truth for scope unless later meeting notes override it.
- `../assignment/assignment3/assignment3.md`: business case.
- `../data/GPSRC Data Project Template.xlsx`: the target unified format. Columns: Student Worker, Event Date, Event Term, Event Name, Virtual/In-Person/Hybrid, Sponsor/Host/Partners, Event type, On Campus Groups?, attendance source if not on CampusGroups, First Name, Last Name, Email, Affiliation, Student or Employee ID, NetID, Domestic or International, School, Department, Notes.
- `../data/Example Data/Campus Groups Files/`: CampusGroups exports (CSV and XLSX). The headers repeat field names (`First Name`/`First name`, `Email` twice) because the registration-form answers duplicate the profile fields. The NetID column is `Net ID`, and affiliation sits under a long question-text header.
- `../data/Example Data/12twenty Data Files/`: 12twenty exports (XLSX, no NetID).
- `../data/Example Data/GSPRC Compiled Dataset.xlsm`: the sponsor's compiled sheet, used as the import benchmark. The team suspects it is AI-generated dummy data and has asked the sponsor for two separate dummy export files to compare against.
- `../data/GPSRC Data Process 10_5_26.docx`: the current manual process.
- `../data/Meeting Notes/`, `../weekly_meeting/`: sponsor and team meeting notes.

## Team

- Brandon Y Lau: database schema and import pipeline
- Jennifer Sun: frontend UI and chat screen
- Zhenyu (Eric) Song: AI chatbot integration
- Molly Tran: project management

The code will be shared with the team through a private GitHub repo, so write code, comments, docs, and commit messages in English.

## Schedule

| Week | Dates | Work |
|---|---|---|
| 5 | Oct 22 – Oct 28 | Database and file import |
| 6 | Oct 29 – Nov 4 | Chatbot |
| 7 | Nov 5 – Nov 11 | Chat screen and export; mid-project demo to sponsor |
| 8–9 | Nov 12 – Nov 25 | Feedback fixes, testing, benchmark; MVP complete |
| 10 | Nov 26 – Dec 4 | Documentation, handoff, final demo |

The midterm report and presentation are due Oct 26, 11:59 PM. Screenshots are enough; no live demo is needed.

## Commands

Run from `project/` unless noted. Copy `.env.example` to `.env` and fill it in first.

```
# Whole app (nginx + api + db) at http://127.0.0.1:8080
docker compose up --build -d
docker compose down                      # keeps the hub-pgdata volume
docker compose exec api python -m app.samples   # load the synthetic samples into the running stack

# Dev database only (published on 127.0.0.1:5432)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db

# Backend (from project/backend)
uv run uvicorn app.main:app --reload     # dev server on :8000
# HUB_ENABLE_FAKE_LLM=true enables the scripted "Demo" preset (tests, Playwright, offline demos)
uv run alembic upgrade head
uv run pytest                            # all tests (needs the dev db)
uv run pytest -m acceptance              # A1/A2/A9 import, A5/A6/A8 chat, benchmark reference checks
uv run ruff check .
uv run ruff format --check .
uv run python -m app.samples             # load the synthetic sample files

# Everything: lint, all tests, build, e2e, then the A1-A10 table (stops on first failure)
bash scripts/acceptance.sh               # from project/; needs the dev db and Docker

# Edge-case upload files for the user-story walks (docs/user-stories/README.md); never commit them
uv run --project backend python scripts/story_files.py <out_dir>   # from project/; out_dir outside the repo

# Frontend (from project/frontend)
npm install
npm run dev                              # :5173, proxies /api to :8000
npm test -- --run                        # Vitest
npm run build                            # type-check + production build
npm run lint                             # oxlint
npm run e2e                              # Playwright happy path on its own stack (needs Docker)
npm run e2e:screenshots                  # regenerate docs/screenshots/ (midterm report)
HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing   # A10: question to Excel under 60 s, real LLM, main stack
```

Each e2e run starts a separate `hub-e2e` Compose project on 127.0.0.1:8081 (`HUB_HTTP_PORT`) with the scripted "Demo" profile, blanks every `LLM_SEED_*` so no real API key is used, and removes the stack and its volume afterwards. First time: `npx playwright install chromium`.

`e2e:timing` is different: it uses `playwright.timing.config.ts` (no global setup), runs against the main stack at `HUB_E2E_BASE_URL` (default `http://127.0.0.1:8080`) with the samples loaded, and makes real LLM calls. Start that stack first from `project/` with `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`. `HUB_E2E_PROFILE` is the name of the AI profile to select; without it the spec skips. The spec restarts the `api` container first (cold start).

Chatbot benchmark (from `project/backend`, needs a saved LLM profile and the sample data loaded):

```bash
uv run python -m benchmark.run --profile "<name>" [--set main|holdout] [--only q01,q05] [--today 2026-11-02] [--min-score 18]
```

It writes `backend/benchmark/reports/<YYYYMMDD-HHMM>-<slug>.md` and prints `Score: N/20` (`Score: N/10` for `--set holdout`). `--set holdout` runs the 10 held-out questions (`holdout.yaml`, ids h01-h10; never tune prompts on them) and writes `...-<slug>-holdout.md`. Exit code 0 = ok, 1 = below `--min-score`, 2 = could not run.

## Conventions

- Keep secrets in `project/.env` (gitignored) and commit a `.env.example` alongside it. Every new env var goes into `.env.example`. If the api container needs it, also add it to the api `environment:` list in `docker-compose.yml`. The container gets only the variables listed there, not the whole `.env`.
- Keep this file current. When you change the stack, layout, commands, or a scope decision, update CLAUDE.md in the same commit.
