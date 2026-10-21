# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S2 of 5 (2026-10-20) is complete. All 11 S2 tasks passed their task reviews. A final whole-branch review and one fix wave followed, and the fix wave's re-review is clean.
- **Phase:** foundation and import done. Next is the chatbot (S3).

## Done

- **Backend skeleton:** settings, the error shape `{"error": {code, message, details}}` (422 details never echo request input), and `GET /api/health`.
- **Database:** PostgreSQL 16 through Compose. Alembic `0001` creates the core schema in `hub` plus `attendance_view` (17 columns). `0002` adds `import_file.content_sha256`. The `hub_app` and `chatbot_ro` roles exist, and `chatbot_ro` may only SELECT the view; a test checks every relation in `hub`.
- **Login seam:** `get_current_user` returns the seeded `local` user, with `GET /api/me`. A route-walker test (now including routes on included routers) enforces that every route except `/api/health` depends on it.
- **Import pipeline:**
  - `read_grid` reads CSV in utf-8-sig with a cp1252 fallback, and XLSX/XLSM. It drops blank rows and XLSX-illegal control characters.
  - Adapters: CampusGroups and 12twenty, detected by a small identifying header set. All other columns are optional.
  - Identity linking: NetID first, then email.
  - `POST /api/imports` previews each file. It rejects bad files one by one and catches duplicates by file hash and by content hash.
  - `POST /api/imports/{id}/commit` runs in one locked transaction.
  - Also `GET /api/imports[/{id}]`, `DELETE /api/imports/{id}` and `GET /api/events`.
- **Export:** formula-safe XLSX/CSV writers and `GET /api/dataset/export?format=xlsx|csv` (the 19 GPSRC headers, Notes built from flags). `dataset.service.query_dataset` is the F11 seam.
- **Samples and acceptance:** `backend/sample_data/` holds the 10 synthetic exports, the compiled sheet and `events.json`. `uv run python -m app.samples` loads them. A1 (every non-Notes column matches the compiled sheet: 293 rows, 79 NetIDs, plus the identity edge rows), A2 and A9 pass.
- **Frontend skeleton:** Vite, React 19, MUI 9, TanStack Query and react-router 8. `src/api/client.ts` is the only `fetch` caller. `AppShell` has the nav and the current user, `AuthGate` passes through, and the four routes show placeholders.
- **Docker:** nginx (127.0.0.1:8080), api (runs migrations, then uvicorn, TZ America/Los_Angeles) and db, with restart policies. The api gets an explicit environment list with no superuser password. Smoke-tested on a fresh volume.
- **Spec updated** with this session's design decisions (see "Decisions").

## State of the code

- How to run: see `CLAUDE.md` "Commands". The whole app starts with `docker compose up --build -d` from `project/`. Dev mode is the dev-override db plus `uv run uvicorn …` and `npm run dev`.
- `project/.env` exists on this machine. It was generated in S2 with random URL-safe passwords and a Fernet key, and is gitignored. A new machine needs `cp .env.example .env`, then fill it in.
- The dev `hub` database is at migration 0002 and holds the 10 sample imports, loaded once with `python -m app.samples`. Tests use a separate `hub_test` DB that they recreate.
- Test results at the last S2 commit:
  - backend: 158 passed, 5 of them acceptance;
  - ruff: check and format clean;
  - frontend: Vitest 5 passed, `npm run build` and `npm run lint` clean.
  - The only warning is Starlette's `httpx` deprecation notice.
- Installed versions are newer than the plans assumed: FastAPI 0.156.4, MUI 9.5, react-router 8.5, Vite 8, Vitest 5, TypeScript 6. The DB session dependency must be used as `SessionDep` (`app/db.py`, `Depends(get_session, scope="function")`), so the commit happens before the response is sent. Never write `Depends(get_session)` directly.

## Next session: S3

- **Start:** open a new Claude Code conversation in the repo root (`SWE277P/`) and say: "Read project/CLAUDE.md, then follow Rule #2 and start S3."
- **Read:** `CLAUDE.md`, this file, the spec, and `docs/plans/2026-10-20-s3-chatbot.md`. Don't read the other plans.
- **Do:** execute the S3 plan with `superpowers:subagent-driven-development`. Before Task 1, check the plan against the S2 interfaces it consumes, because the plan was written before S2 changed some of them:
  - `SessionDep`;
  - `HubError` and the 422 detail shape;
  - `export.writers` (`to_xlsx`, `to_csv`, `export_response`, `guard_cell`);
  - `get_chatbot_engine`;
  - the `settings` caps;
  - `tests/conftest.py` fixtures (`app`, `client`, `db_session`, `user`, `committed_october`).
- **Carry into S3:**
  - make `POST /api/imports` a plain `def` route (it currently blocks the event loop, which SSE will share);
  - rename or redocument `guard_cell` (it is CSV-only; XLSX uses `data_type = "s"`) before the chat export reuses it;
  - add tests for `chatbot_ro`'s `default_transaction_read_only` and `statement_timeout`, and include sequences in the grant test;
  - fix the `thread`-before-`try` slip in the double-commit test;
  - add a timezone regression test for the ORM timestamps.
- **Exit:** A6 and A8 pass, the graph passes integration tests with the fake model, and a first benchmark run works on a real profile.

## Open issues and blockers

- D1 (the LLM sees query results) is provisional and must be confirmed with the sponsor.
- ZotGPT Gateway base URL, JSON-mode support and model names are unknown. Verify by 10/28; S3 needs them.
- The sponsor's two separate dummy export files have not arrived. When they do, add them as import fixtures and check that detection with the small header sets accepts them.
- Midterm due 10/26: S4 Task 7 produces the screenshots. If S4 isn't done by then, screenshot the S2 import flow and API results instead.
- Sponsor questions:
  - Should waitlisted CampusGroups registrants count as attendees? They are currently kept.
  - Is the Notes wording acceptable?
- **Deferred to S4:**
  - `validate_term` should use fullmatch and ASCII digits;
  - a test with not-attended rows;
  - `query_dataset` needs a default ORDER BY and should reject None values for eq/ilike;
  - `client.ts` must handle an empty 2xx body;
  - `AppShell` needs a fallback when `/api/me` fails;
  - the 505 kB bundle should be code-split;
  - `source_row` drifts after blank rows;
  - preview `flag_counts` leave out linker outcomes, so show the commit summary;
  - prefill `attendance_source_note` for 12twenty;
  - header-only files from different events share a content hash.
- **Deferred to S5:**
  - the httpx warning;
  - a comment on the cp1252 replacement character;
  - nginx resolves `api` only once and doesn't set no-cache on `index.html`;
  - nginx should wait for a healthy api (it returns 502 during migration);
  - containers should run as non-root, and the backend needs a HEALTHCHECK;
  - `frontend/.dockerignore` should cover `.env.*`;
  - two simultaneous uploads of the same new file return 500.

## Decisions

- Spec D1–D10 (spec Section 2). Execution method for S2–S5: subagent-driven, with the controller generating `.env` when asked.
- **Per-question result sharing (added after S2, spec D2):** a "Let AI see the results" switch sits next to the question box, capped by the profile's `share_results_with_llm`. The server sends rows only when both are on. There is no global env flag. The S3, S4 and S5 plans already include it.
- **S2 design decisions, now in the spec:**
  - 12twenty affiliation falls back to `Degree Level` and flags `missing_degree` (§6).
  - Linker: rule 2's attach case is `match_method = email`, and a NetID/email conflict gets only `netid_email_conflict` (§6).
  - Duplicate detection also uses a content hash of the parsed grid (§5, §6).
  - Adapters require only a small identifying header set (§6).
  - Notes format (§9) and the F11 seam wording (§12).
- **S2 implementation rules:**
  - Services never call `commit()`; the request session does, and CLIs commit themselves.
  - The commit endpoint locks the import row.
  - Commit trailers name the model that wrote the commit.
  - The db container gets only the three Postgres passwords.

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
- S2 (2026-10-20): built the foundation and import pipeline (11 tasks, each reviewed), then a final review and one fix wave (7 Important issues fixed). A1/A2/A9 pass and Docker serves the placeholder UI.
