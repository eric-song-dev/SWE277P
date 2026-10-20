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

## What we are building

**Program Registration & Attendance Data Hub** for UCI's Graduate & Postdoctoral Scholar Resource Center (GPSRC). SWE 277P capstone, Fall 2026. Sponsor and main user: Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development.

The app is a web app that runs locally on one GPSRC computer:

1. Staff upload one event's attendee export (CampusGroups or 12twenty) exactly as the platform produced it, and enter the event details in a form.
2. The app normalizes the rows into one permanent dataset in the GPSRC Data Project format and links the same person across events.
3. Staff ask questions in plain English. An LLM turns the question into SQL, the app runs it locally, then shows both the SQL and the result table.
4. Staff can download any result as Excel or CSV.

## Tech stack

- Frontend: React
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Packaging: Docker Compose. The whole app must start with one command on the sponsor's machine.
- LLM: ZotGPT Gateway (UCI OIT) as the main provider, with OpenAI or DeepSeek as alternatives. Keep providers behind one interface and select the provider through config or env vars.

Planned layout (update this once the scaffold exists):

```
project/
  backend/             FastAPI app, import pipeline, text-to-SQL
  frontend/            React UI: upload, chat, results and export
  docker-compose.yml
```

## Non-negotiables

- **Privacy:** the LLM only receives the schema, column descriptions, and the user's question. Never send row values (names, emails, NetIDs, student IDs) to the LLM: not in prompts, few-shot examples, or error-retry messages. Don't log them to external services either.
- **SQL safety:** generated SQL must be a single read-only `SELECT`, run through a read-only database role with a statement timeout and a row limit. Always show the SQL to the user.
- **Imports:** accept native export files unmodified. Staff must not have to clean files by hand. Uploading the same file twice must not create duplicates.
- **Identity matching:** match people by NetID first, then by email (12twenty exports have no NetID). Flag uncertain matches for staff instead of silently merging them.
- **Synthetic data only.** Never add real student data to the repo, fixtures, or prompts.

## Scope

In scope: importing 12twenty and CampusGroups exports, entering event details at upload, one unified dataset, cross-event identity matching, a chatbot that shows its SQL, and Excel/CSV export.

Out of scope (don't build these unless the user changes scope): registration/attendance reconciliation, certificates and multi-session programs, charts and dashboards, multiple accounts or roles, cloud or UCI server hosting, UCI SSO, live connections to 12twenty, CampusGroups, or Zoom.

Login: the charter (Oct 18) lists one staff login, but the team removed login from scope in the Oct 19 meeting. Ask before building auth.

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

Not set up yet. When you add the scaffold, record here how to start the app, run backend and frontend tests, lint, and run the benchmark.

## Conventions

- Keep secrets in `project/.env` (gitignored) and commit a `.env.example` alongside it.
- Keep this file current. When you change the stack, layout, commands, or a scope decision, update CLAUDE.md in the same commit.
