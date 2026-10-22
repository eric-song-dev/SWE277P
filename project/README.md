# Program Registration & Attendance Data Hub

A web app that runs on one computer at UCI's Graduate & Postdoctoral Scholar Resource Center (GPSRC). Staff upload attendee exports from CampusGroups and 12twenty without editing them. The Hub combines them into one dataset and recognizes the same person across events. Staff then ask questions in plain English, such as "How many unique postdocs came to any wellness event?". An AI writes the database query, the Hub runs it read-only and shows both the query and the result table, and any answer can be downloaded as Excel or CSV.

SWE 277P capstone, UC Irvine, Fall 2026. Sponsor: Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development, GPSRC.

![A question, its answer, the SQL and the download buttons](docs/screenshots/03-chat-answer.png)

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Development](#development)
- [Testing](#testing)
- [Configuration](#configuration)
- [Project structure](#project-structure)
- [API overview](#api-overview)
- [Security and privacy](#security-and-privacy)
- [Documentation](#documentation)
- [Project status](#project-status)
- [Contributing](#contributing)
- [Team](#team)
- [License](#license)

## Features

- **Native exports, unchanged.** Upload a CampusGroups export (CSV or XLSX) or a 12twenty export (XLSX) exactly as the platform produced it. The Hub recognizes the platform from the column headers, normalizes every row into the GPSRC Data Project layout, and shows a preview with flags before anything is saved.
- **Event details at upload.** A short form records the event name, date, term, format, host and type. Values are filled in from the file where possible.
- **One dataset, no duplicates.** The Hub hashes both the file's bytes and its parsed cells. Uploading the same file again, or a copy re-saved in Excel, adds nothing.
- **People linked across events.** The Hub matches people by NetID first, then by email, and never by name. Uncertain matches are flagged for staff instead of merged.
- **Plain-English questions.** An AI turns each question into one SQL query. The Hub checks the query, runs it read-only, and shows the SQL, a "How I read your question" note and the result table. It handles follow-up questions, asks back when a question is ambiguous, retries a failed query automatically (up to 3 attempts), and shows progress as it goes.
- **Optional AI summary.** If you allow it, the AI also reads the rows its own query returned and writes a short summary. Two switches control this (see [Security and privacy](#security-and-privacy)).
- **AI models managed in the app.** Staff add any OpenAI-compatible provider (ZotGPT Gateway, OpenAI, DeepSeek or a custom address) in Settings, then pick one for each question. API keys are stored encrypted.
- **Excel and CSV downloads.** Every answer can be downloaded as `.xlsx` or `.csv`, and so can the full dataset, in the sponsor's 19-column template layout. Values that look like spreadsheet formulas are saved as plain text.

## How it works

Three Docker containers, started with one command:

```
  Staff browser (on the same computer)
           │
           │  http://127.0.0.1:8080
           ▼
  ┌──────────────────┐
  │ nginx            │  serves the React build and passes /api/* to the api
  └────────┬─────────┘
           ▼
  ┌──────────────────┐         HTTPS, the only outbound traffic
  │ api (FastAPI)    │ ──────────────────────────────────────────► AI provider (OpenAI-compatible)
  └────────┬─────────┘
           │  hub_app     read/write, every table
           │  chatbot_ro  read-only, attendance_view only, 5 s statement timeout
           ▼
  ┌──────────────────┐
  │ db (PostgreSQL)  │  database "hub", Docker volume hub-pgdata
  └──────────────────┘
```

**Import.** `POST /api/imports` hashes the file and refuses one that was already imported. It then picks the adapter (CampusGroups or 12twenty) whose required headers are present, normalizes the rows, and stores the file as *pending* with a preview. When staff click **Commit**, one transaction creates the event, links identities, and inserts the attendance rows and flags.

**Chat.** Each question runs through a custom LangGraph `StateGraph`:

```
load_context ─► generate ─► route ─┬─► clarify ─────────────────────────────► finalize
                   ▲               └─► guard ─► execute ─► analyze ─► finalize
                   │                    │          │
                   └──── repair ◄───────┴──────────┘   (guard or execution error,
                                                        attempts < 3; else finalize as error)
```

`generate` asks the AI for a JSON draft: either SQL or a clarifying question. `guard` checks the SQL with sqlglot. `execute` runs it as the read-only `chatbot_ro` role. `repair` sends a cleaned-up error back to the AI for another attempt. `analyze` writes the summary: the AI writes it when sharing is on, and the Hub builds a plain one itself when it is off. The steps stream to the browser as server-sent events, and each question is recorded in `chat_turn`.

The full design and the reasons behind it are in the [design spec](docs/specs/2026-10-20-data-hub-design.md).

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, MUI 9, MUI X DataGrid 9, TanStack Query, React Router |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, managed with uv |
| Chatbot | LangGraph (custom `StateGraph`), `langchain-openai` `ChatOpenAI` with a `base_url`, sqlglot |
| Database | PostgreSQL 16 |
| Packaging | Docker Compose (nginx, api, db) |
| Quality | pytest, Vitest and Testing Library, Playwright, ruff, oxlint |

## Quick start

This section is for running the Hub on a staff computer. The [setup guide](docs/setup-guide.md) covers each step in more detail for Mac and Windows, including backups and upgrades.

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/), installed and running. Run every command from this folder (`project/`).

1. **Create `.env`** from the template:

   ```
   cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
   ```

2. **Fill in four values** in `.env`: `POSTGRES_PASSWORD`, `HUB_APP_PASSWORD` and `CHATBOT_RO_PASSWORD` (letters and digits only), and `HUB_SECRET_KEY`. Docker can generate them:

   ```
   # a password (run once for each of the three)
   docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_hex(24))"
   # HUB_SECRET_KEY
   docker run --rm python:3.12-slim python -c "import base64,os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
   ```

   Keep a private copy of `.env`. If `HUB_SECRET_KEY` is lost, the saved API keys cannot be read and must be entered again.

3. **Start the Hub**, and optionally load the synthetic sample data (10 events, 293 attendance records):

   ```
   docker compose up --build -d
   docker compose exec api python -m app.samples
   ```

4. **Open http://127.0.0.1:8080.** In **Settings**, click **Add AI model**, save it, and click **Test**. Then click **New chat** and ask a question, for example "Which event had the most attendees?".

`docker compose down` stops the Hub and keeps the data. `docker compose down -v` deletes all data.

## Development

You need Docker, [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you) and Node.js 24 (the version the frontend image builds with).

1. Create `project/.env` as in the [Quick start](#quick-start). Also update the passwords in `DATABASE_URL`, `CHATBOT_DATABASE_URL` and `TEST_ADMIN_DATABASE_URL` to match the ones you set. The backend and the tests read these URLs. Docker ignores them.

2. Start only the database, published on `127.0.0.1:5432`:

   ```
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d db
   ```

3. Backend, from `backend/`:

   ```
   uv run alembic upgrade head
   uv run python -m app.samples             # optional: load the synthetic samples
   uv run uvicorn app.main:app --reload     # http://127.0.0.1:8000, API docs at /docs
   ```

4. Frontend, from `frontend/`:

   ```
   npm install
   npm run dev                              # http://127.0.0.1:5173, proxies /api to :8000
   ```

**Working without an AI key.** Set `HUB_ENABLE_FAKE_LLM=true` to add the "Demo (scripted)" preset. It answers the questions in `backend/app/llm/fake_script.json` without any network calls. The tests, the Playwright runs and offline demos all use it.

| Port | Used by |
|---|---|
| 8080 | The full stack (nginx), set by `HUB_HTTP_PORT` |
| 8081 | The Playwright e2e stack (`hub-e2e`), started and removed by `npm run e2e` |
| 8000 | The backend dev server |
| 5173 | The Vite dev server |
| 5432 | The dev database (with `docker-compose.dev.yml`) |

If you work on the code with Claude Code, read [`CLAUDE.md`](CLAUDE.md) (rules and commands) and [`PROGRESS.md`](PROGRESS.md) (current state) first.

## Testing

| What | Command | Run from | Needs |
|---|---|---|---|
| Backend lint | `uv run ruff check .` and `uv run ruff format --check .` | `backend/` | |
| Backend tests | `uv run pytest` | `backend/` | The dev database. Tests create and use their own `hub_test` database. |
| Acceptance tests | `uv run pytest -m acceptance` | `backend/` | The dev database |
| Frontend tests | `npm test -- --run` | `frontend/` | |
| Frontend lint and build | `npm run lint` and `npm run build` | `frontend/` | |
| End-to-end | `npm run e2e` | `frontend/` | Docker. Runs on its own stack with the Demo model, then removes it. |
| Screenshots | `npm run e2e:screenshots` | `frontend/` | Docker. Regenerates `docs/screenshots/`. |
| Timing (A10) | `HUB_E2E_PROFILE="<name>" npm run e2e:timing` | `frontend/` | The main stack running with the samples loaded, and a real AI model |
| Everything | `bash scripts/acceptance.sh` | `project/` | The dev database and Docker. Stops at the first failure. |

The first time you use Playwright, run `npx playwright install chromium`.

### Acceptance criteria

These come from the project's measures of value (spec section 14).

| ID | Check | How | Status |
|---|---|---|---|
| A1 | Importing the 10 sample files reproduces the sponsor's compiled sheet: 293 rows, 79 unique NetIDs | pytest | Pass |
| A2 | Uploading each file again adds nothing | pytest | Pass |
| A3 | The chatbot answers at least 18 of 20 benchmark questions correctly | benchmark, real AI | Pass, 20/20 |
| A4 | The benchmark runs against two AI models with no code change | benchmark, real AI | Pass, 20/20 and 19/20 |
| A5 | Every chat result and the full dataset export to XLSX and CSV | pytest | Pass |
| A6 | With sharing off, no attendee value reaches the AI. With sharing on, only the capped rows of the checked query do, and never a Student ID. | pytest | Pass |
| A7 | No data without signing in | | Deferred with login |
| A8 | Harmful SQL is refused by the guard, and again by the read-only role when the guard is bypassed | pytest | Pass |
| A9 | An exported value starting with `=` is a text cell | pytest | Pass |
| A10 | Question to downloaded Excel file in under 60 seconds | Playwright, real AI | Pass, 4–7 s |

### Chatbot benchmark

From `backend/`, with a saved AI model and the sample data loaded:

```
uv run python -m benchmark.run --profile "<name>" [--set main|holdout] [--only q01,q05] [--min-score 18]
```

The main set is 20 sponsor-style questions (`benchmark/questions.yaml`). Each reference answer is cross-checked against an independent pandas computation over the compiled sheet. The holdout set is 10 questions written before any prompt tuning (`benchmark/holdout.yaml`). Never tune prompts on the holdout set. Reports go to `backend/benchmark/reports/` and are not committed. Copy the results that matter into [benchmark-results.md](docs/benchmark-results.md). Run both sets again after every change to a prompt or a model.

## Configuration

All settings live in `project/.env`, and [`.env.example`](.env.example) explains each one. The api container only receives the variables listed under `environment:` in `docker-compose.yml`.

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_PASSWORD`, `HUB_APP_PASSWORD`, `CHATBOT_RO_PASSWORD` | required | Database passwords, letters and digits only. They take effect only when the database volume is first created. |
| `HUB_SECRET_KEY` | required | Fernet key that encrypts saved API keys. The api refuses to start without a valid one. |
| `DATABASE_URL`, `CHATBOT_DATABASE_URL`, `TEST_ADMIN_DATABASE_URL` | localhost URLs | For development and tests only. Docker builds its own. |
| `HUB_HTTP_PORT` | `8080` | Host port for the web app, bound to `127.0.0.1` |
| `AUTH_MODE` | `none` | Only `none` is supported until login exists |
| `DISPLAY_ROW_CAP` | `1000` | Rows shown in a result table |
| `EXPORT_ROW_CAP` | `100000` | Rows in a chat-result download (the full-dataset download has no cap) |
| `LLM_RESULT_MAX_ROWS`, `LLM_RESULT_MAX_CHARS` | `200`, `20000` | Most rows and characters of a result sent to the AI for its summary |
| `LLM_TIMEOUT_S` | `30` | Timeout for one AI call, in seconds |
| `STATEMENT_TIMEOUT_MS` | `5000` | Timeout for one chatbot query, in milliseconds |
| `TURN_TIMEOUT_S` | `90` | Timeout for one whole question, in seconds |
| `MAX_GENERATIONS` | `3` | SQL attempts per question |
| `MAX_UPLOAD_BYTES` | `10485760` | Upload size limit (10 MB) |
| `HUB_ENABLE_FAKE_LLM` | `false` | Turns on the scripted Demo model |
| `LLM_SEED_*` | empty | Developers only: creates one AI model at startup. Leave empty on the GPSRC computer. |

## Project structure

```
project/
├── docker-compose.yml        nginx + api + db
├── docker-compose.dev.yml    publishes Postgres on 127.0.0.1:5432 for development
├── .env.example              every setting, with comments; copy it to .env
├── db/init/01-roles.sh       creates the hub database and the hub_app and chatbot_ro roles
├── scripts/
│   ├── acceptance.sh         lint, all tests, build, e2e, then the A1–A10 table
│   └── story_files.py        edge-case upload files for the user-story walkthroughs
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI app, routers, startup
│   │   ├── config.py         settings from the environment (pydantic-settings)
│   │   ├── db.py             two engines: the app role and the read-only chatbot role
│   │   ├── auth/             get_current_user, the single login seam
│   │   ├── imports/          platform adapters, file reader, normalization, identity linking
│   │   ├── events/           events
│   │   ├── dataset/          dataset queries and the full-dataset export
│   │   ├── chat/             LangGraph graph and prompts, SQL guard, executor, sanitizer, streaming
│   │   ├── llm/              AI model profiles, key encryption, presets, connection test, Demo model
│   │   ├── export/           XLSX and CSV writers with the formula guard
│   │   ├── quality/          data-quality flags
│   │   └── samples.py        loads the synthetic sample exports
│   ├── alembic/              database migrations
│   ├── benchmark/            benchmark questions, holdout questions, runner and scorer
│   ├── sample_data/          synthetic exports, their event details, the sponsor's compiled sheet
│   └── tests/                unit, integration and acceptance tests
├── frontend/
│   ├── src/
│   │   ├── api/              client.ts (the only code that calls fetch), SSE parser, types
│   │   ├── app/              shell, side nav, AuthGate, routes, theme
│   │   └── features/         upload, chat, dataset, settings
│   ├── e2e/                  Playwright: happy path, screenshots, timing
│   └── nginx.conf            static files and the /api proxy
└── docs/                     guides, spec, plans, design, user stories, screenshots
```

## API overview

Every route except `GET /api/health` depends on `get_current_user`. Errors share one shape: `{"error": {"code", "message", "details"}}`. When the backend dev server is running, interactive docs are at http://127.0.0.1:8000/docs.

| Area | Routes |
|---|---|
| Health | `GET /api/health` |
| Current user | `GET /api/me` |
| Imports | `POST /api/imports` (upload and preview), `GET /api/imports`, `GET /api/imports/{id}`, `GET /api/imports/{id}/preview`, `POST /api/imports/{id}/commit`, `DELETE /api/imports/{id}` (pending imports only) |
| Events | `GET /api/events` |
| Dataset | `GET /api/dataset/export?format=xlsx\|csv` |
| Chat | `POST /api/conversations`, `GET /api/conversations`, `GET /api/conversations/{id}`, `POST /api/conversations/{id}/messages` (server-sent events), `GET /api/chat/turns/{id}/rerun`, `GET /api/chat/turns/{id}/export?format=xlsx\|csv` |
| AI models | `GET` and `POST /api/llm-profiles`, `GET /api/llm-profiles/presets`, `PATCH` and `DELETE /api/llm-profiles/{id}`, `POST /api/llm-profiles/{id}/default`, `POST /api/llm-profiles/{id}/test` |

## Security and privacy

The Hub holds attendee names and emails, so keep the computer and its backups protected.

- **Local only.** nginx listens on `127.0.0.1`, so only the computer the Hub runs on can open it. The only outbound traffic is HTTPS to the AI provider you choose.
- **What the AI sees when writing SQL:** the schema, column descriptions, allowed values (such as school and event names), earlier questions and their SQL, and your question. It never sees attendee rows or Student IDs.
- **What the AI sees when summarizing:** results are shared only when two switches are both on. The first is per model, "Allow sending query results to this AI" in Settings (on by default for the ZotGPT preset, off for the rest). The second is per question, "Let AI see the results" in Chat. When both are on, the AI receives the rows its own query returned, up to 200 rows and 20,000 characters. These rows come only from `attendance_view` and never include Student IDs. **The sponsor has not confirmed this yet (decision D1).** Sharing can be turned off for each model in Settings without changing any code. See the [user guide](docs/user-guide.md#4-who-sees-the-data-the-two-switches).
- **SQL safety, in layers.** The guard accepts only a single `SELECT` over `attendance_view` that uses allow-listed functions. The `chatbot_ro` role can read only that view, is read-only by default, and has a 5 s statement timeout. The executor runs the query as one prepared statement in a read-only transaction that is always rolled back. Before an error goes back to the AI, the sanitizer removes any data values from it. Every question, with its SQL, is logged in `chat_turn`.
- **Secrets.** API keys are encrypted with Fernet (`HUB_SECRET_KEY`), never returned by the API and never logged. LangSmith tracing is forced off. `.env` is gitignored and must never be committed or shared.
- **No login yet.** Anyone who can use the computer can open the Hub. The code is ready for login to be added later (see the [handoff guide](docs/handoff.md#moving-it-to-oit-and-adding-login)).
- **Synthetic data only.** All sample and test data in this repository is synthetic.

## Documentation

| Read this | If you are |
|---|---|
| [Setup guide](docs/setup-guide.md) | Installing or upgrading the Hub, adding an AI model, backing up |
| [User guide](docs/user-guide.md) | Staff using the Hub: uploads, flags, questions, answers, downloads, the privacy switches |
| [Data dictionary](docs/data-dictionary.md) | Looking up what a column means or how an export maps into the dataset |
| [Known limitations](docs/known-limitations.md) | Deciding how far to trust an answer, or checking what is not done yet |
| [Handoff guide](docs/handoff.md) | Taking over the code: architecture, tests, extension points, moving to OIT |
| [Backlog](docs/backlog.md) | Planning the next work: requested features and known bugs |
| [Design spec](docs/specs/2026-10-20-data-hub-design.md) | Looking for the full design and its reasons (the source of truth) |
| [Benchmark results](docs/benchmark-results.md) | Checking how well the chatbot answered the benchmark questions |
| [UI design](docs/design/2026-10-21-ui-redesign.md) | Changing the look: colors, type, layout and on-screen text |
| [User stories](docs/user-stories/README.md) | Testing the app by hand: 63 stories and their walkthrough results |
| [Implementation plans](docs/plans/) | Looking up how each build session (S2–S6) was planned |
| [`CLAUDE.md`](CLAUDE.md), [`PROGRESS.md`](PROGRESS.md) | Working on the code with Claude Code: rules, commands, current state |

## Project status

The MVP is complete: build sessions S1–S6 ran from 2026-10-20 to 2026-10-21, with follow-up fixes on 2026-10-22. It meets the project's measures of value, which are due 2026-12-04:

| Goal | Target | Result |
|---|---|---|
| Import matches the compiled sheet | 293 rows, 79 unique NetIDs, no duplicates after a re-upload | Met (A1, A2) |
| Chatbot accuracy | At least 18 of 20 benchmark questions | 20/20 on DeepSeek `deepseek-flash`, 10/10 on the holdout set |
| Question to Excel file | Under 1 minute | 4–7 seconds |

Still open:

- The sponsor must confirm result sharing (D1), whether waitlisted registrants count as attendees, and whether "students" includes postdocs.
- ZotGPT's base URL, JSON support and model names have not been checked. Only DeepSeek models have been benchmarked.
- Backlog items B1–B4 in [backlog.md](docs/backlog.md). B4 is a high-priority bug: a second download of an event that was already imported is recorded as a new event, so its attendees are counted twice.
- Not built yet: login, and the P1 features (filter table, data-quality view, saved queries, historical import, multiple accounts). The code already has a hook for each one (see the [handoff guide](docs/handoff.md#extension-points-for-the-p1-features)).

See [known limitations](docs/known-limitations.md) for the full list.

## Contributing

Every developer on the team must follow these two rules.

### 1. Follow the rules in `CLAUDE.md`

All development follows the rules in [`CLAUDE.md`](CLAUDE.md), whether you write the code yourself or with an AI coding agent. Read it and [`PROGRESS.md`](PROGRESS.md) before you start. Where the [spec](docs/specs/2026-10-20-data-hub-design.md) disagrees with other documents, the spec wins. The rules you will meet most often:

- Make one commit per logical change, using [Conventional Commits](https://www.conventionalcommits.org/) in English with an imperative subject, for example `fix(chat): reject non-SELECT SQL`.
- Run the lint and tests for the code you changed before committing. `bash scripts/acceptance.sh` runs everything.
- Stage files by path. The current git root is the course folder above `project/`, so never use `git add -A` there.
- Add every new environment variable to `.env.example`. If the api needs it, also add it to the api `environment:` list in `docker-compose.yml`.
- Never commit `.env`, API keys or real student data. Tests, fixtures and prompts use synthetic data only.
- After any change to a prompt or a model, run the benchmark again, holdout set included.

### 2. Install the team's plugins in your AI coding agent

Install these plugins in your AI coding agent. **superpowers** matters most: it sets the team's way of working (brainstorm, write a plan, test first, review, verify before saying a task is done). In Claude Code, install each plugin with the `/plugin` command. When all of them are installed, the `enabledPlugins` block in `~/.claude/settings.json` looks like this:

```json
{
  "enabledPlugins": {
    "frontend-design@anthropic-plugin-directory": true,
    "context7@anthropic-plugin-directory": true,
    "skill-creator@anthropic-plugin-directory": true,
    "code-review-anthropics@anthropic-plugin-directory": true,
    "claude-md-management@anthropic-plugin-directory": true,
    "code-simplifier@anthropic-plugin-directory": true,
    "playwright@anthropic-plugin-directory": true,
    "vercel@anthropic-plugin-directory": true,
    "typescript-lsp@claude-plugins-official": true,
    "superpowers@anthropic-plugin-directory": true
  }
}
```

## Team

| Name | Role |
|---|---|
| Brandon Y Lau | Database schema and import pipeline |
| Jennifer Sun | Frontend UI and chat screen |
| Zhenyu (Eric) Song | AI chatbot integration |
| Molly Tran | Project management |

Sponsor: Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development, GPSRC, UC Irvine.

## License

No license has been chosen yet. This is a course project, and the code is shared only through the team's private repository.
