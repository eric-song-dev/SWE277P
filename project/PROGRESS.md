# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S4 of 5 (2026-10-21) is complete.
  - Task 0 (backend carry-overs) and plan Tasks 1–7 are done. Every task passed its task review; Tasks 0, 2, 3 and 5 needed fix rounds.
  - A final whole-branch review and one fix wave followed. The fix wave's re-review is clean.
- **Phase:** the MVP is feature-complete. Next is S5: benchmark tuning, timing, hardening, and handoff docs.

## Done

- **S2 (foundation and import)** and **S3 (backend chatbot)**: see the session log. Their design decisions are in the spec.
- **S4 backend carry-overs** (spec §6, §7.6, §8.2, §9, §12, each marked "S4"):
  - A partial `chat_turn` is recorded when the client disconnects (`client_disconnected`).
  - Chat export sends `X-Hub-Truncated` and `X-Hub-Row-Cap`.
  - Questions are stripped, so a whitespace-only one is a 422. A `base_url` with credentials is a 422. An empty `api_key` on PATCH keeps the key.
  - Legacy `LANGCHAIN_TRACING` is forced off.
  - Terms use fullmatch and ASCII digits.
  - `query_dataset` has a total order and rejects null `eq`/`ilike`.
  - `source_row` is the real file row.
  - Header-only files are rejected (`no_data_rows`).
  - 12twenty drafts prefill `attendance_source_note`.
- **S4 frontend** (`frontend/src/`, spec §4.3 "Details settled in S4"):
  - **API layer:** `client.ts` (one `hubFetch` seam, upload, download with truncation info) and `sse.ts` (stream parser and `streamSse`). `types.ts` mirrors the backend schemas. oxlint forbids `fetch` elsewhere.
  - **Settings:** LLM profiles. The key is write-only, PATCH sends only changed fields, Test connection gives model suggestions.
  - **Upload:**
    - a dropzone with one card per file;
    - the event form, prefilled and validated;
    - Commit and Discard;
    - the commit summary;
    - plain-language flag labels.
  - **Chat:**
    - conversations, the profile drop-down, and the "Let AI see the results" switch (D2);
    - streamed steps;
    - answer cards: analysis, result grid, interpretation, SQL, exports;
    - clarifications, Retry (with the current profile and switch), and "Show results" re-run for old turns.
  - **Dataset:** import history and full-dataset export.
  - **Shell:** lazy-loaded pages with vendor chunks (no chunk-size warning), a root error page, and "Not connected" when `/api/me` fails.
  - **E2E (Playwright):** `npm run e2e` is the happy path (upload, commit, ask, Excel download, follow-up). `npm run e2e:screenshots` regenerates `docs/screenshots/01–05*.png`, which are the **midterm screenshots** (synthetic data).

## State of the code

- **How to run:** see `CLAUDE.md` "Commands", which now includes the e2e commands.
- **Dev database (`hub`):** unchanged since S3. It is at migration `0004`, with the 10 sample imports and profile id 1 "DeepSeek" (`deepseek-flash`).
  - `project/.env` now has `LLM_SEED_MODEL=deepseek-flash` (changed 2026-10-21). DeepSeek's `/models` lists `deepseek-flash` and `deepseek-v4-pro`. It also accepts `deepseek-v4-flash`, but only as an alias that it answers as `deepseek-flash`.
- **Tests at the last S4 commit:**
  - backend: 815 passed, 54 of them acceptance; ruff check and format are clean;
  - frontend: Vitest 132 passed (13 files); lint and build are clean;
  - Playwright happy path: 1 passed on the `hub-e2e` stack, which leaves no containers or volumes behind.
- **Versions added:** react-dropzone, `@mui/x-data-grid` 9, `@testing-library/user-event`, `@playwright/test` 1.64 (Chromium via `npx playwright install chromium`).
- **Patterns to keep:**
  - Feature tests mock `../../api/client` with a factory that keeps the real `ApiError`.
  - `src/test/setup.ts` registers jest-dom and cleanup.
  - MUI 9 `Stack` layout props go in `sx`.
  - Backend patterns are unchanged from S3.

## Next session: S5

- **Start:** open a new Claude Code conversation in the repo root (`SWE277P/`) and say: "Read project/CLAUDE.md, then follow Rule #2 and start S5."
- **Read:** `CLAUDE.md`, this file, the spec, and `docs/plans/2026-10-20-s5-benchmark-handoff.md`. Don't read the other plans.
- **Do:** execute the S5 plan with `superpowers:subagent-driven-development`:
  - Task 1: benchmark to at least 18/20;
  - Task 2: a second provider (A4);
  - Task 3: A10 timing;
  - Task 4: hardening;
  - Task 5: handoff docs;
  - Task 6: the final acceptance run.
  Before Task 1, check the plan against S4: the UI exists now, so A10 can drive the real UI with Playwright and a real profile. The plan predates S3 and S4.
- **Carry into S5 (the hardening sweep):**
  - **Benchmark:** add the hold-out set (see Open issues).
  - **Pending imports:** they have no home after leaving `/upload`. The Dataset page shows them as "Pending" rows with no way to discard them. Dropping the file again brings back the card, but typed edits are lost.
  - **Chat:**
    - If the user sends a question in the few milliseconds after `done` and before the body closes, it is ignored and the composer is already cleared (`useChatStream` `streamingRef`).
    - Errors that aren't `ApiError` are mapped without logging. `sse.ts` also wraps `onEvent`, so a frontend bug shows up as "Connection lost".
    - "Show results" has no pending state.
    - `/chat` with no profiles shows two hints. This is the sponsor's first-run screen.
  - **Upload:** two copies of one export dropped together give duplicate React keys (no dedupe within a batch).
  - **Client:** a connection drop while reading a response body still shows a raw `TypeError`. A render error inside `AuthGate` is outside the error page. `sse.test.ts` uses a stale route path.
  - **Test hygiene:**
    - tests for key stripping on create;
    - an anyio re-delivered-cancel disconnect test;
    - a bounded busy-wait in `test_chat_api.py`;
    - a split multi-byte UTF-8 SSE test;
    - the e2e teardown error masking and the health-fetch timeout.
  - **With ZotGPT (verify by 10/28):** widen `response_format` rejection detection, and merge consecutive human messages if the gateway needs alternation.
- **Exit:** all acceptance tests green except A7, benchmark at least 18/20, A10 under 60 s, docs done.
- **Before the sponsor demo (week 7):**
  - Run `docker compose up --build -d` on the main stack.
  - Click through with a real profile.
  - Try one export in Safari.

## Open issues and blockers

- **D1 is provisional.** The LLM sees query results, which must be confirmed with the sponsor. Sharing can be switched off per profile.
- **ZotGPT is unknown.** Its base URL, JSON-mode support and model names must be verified by 10/28.
- **Missing sponsor files.** The sponsor's two separate dummy export files have not arrived.
- **The benchmark likely overstates generalization.** 20/20 was one run of one model, and several prompt rules match the benchmark's own readings. S5 should add a hold-out set of about 10 new sponsor-style questions and run it several times per profile. q15 (records vs people) and q04 (null email) are the readings most likely to flip.
- **Known UI gap (spec §4.3):** after a dropped stream and a refetch, both the saved `client_disconnected` turn and the live "Connection lost" card can show.
- **Sponsor questions:**
  - Should waitlisted CampusGroups registrants count as attendees?
  - Is the Notes wording acceptable?
  - Do "students" include postdocs?
- **Deferred to S5 (from S2 and S3):**
  - **Logs and warnings:** the httpx warning; the cp1252 comment; traceback-free failure logs.
  - **nginx:** resolve `api` once, no-cache on `index.html`, and wait for a healthy api.
  - **Docker:** non-root containers and a backend HEALTHCHECK; `frontend/.dockerignore` should cover `.env.*`.
  - **Imports:** simultaneous uploads of the same new file return 500.
  - **Prompt tuning:** state "students" and NULL-grouping as assumptions; latest-term wording.
  - **Guard:** repair messages for COLLATE, `^` and qualified functions.
  - **Executor:** an advisory-lock unlock in the pool reset.
  - **Test tightening:** A6 `== 50` with a case-insensitive regex, a fixtures conftest, and 42501-specific asserts.
  - **Database:** CHECK constraints on kind/preset; the FK error when a profile is deleted mid-turn.
  - **Security:** ownership checks before login (IDOR).

## Decisions

- **Spec decisions:** D1–D10 (spec Section 2). S2, S3 and S4 decisions are in the spec sections marked with their session.
  - S4 frontend decisions are in §4.3: the `/chat` draft conversation, one chat route, no router transitions, one card per question, Retry with the current settings, the SQL on failed turns, plain error texts, and the e2e isolation.
- **Execution method:** S2–S5 are subagent-driven. The controller rules on plan conflicts and records the rulings.
- **S4 execution choices:**
  - Added Task 0 for backend carry-overs.
  - Lint with oxlint `no-restricted-globals`, not ESLint.
  - `apiDownload` returns `{fileName, truncated, rowCap}`.
  - Header-only files are rejected, not fingerprinted by name.
  - `attendance_source_note` prefill is "12twenty attendance export".
  - PATCH sends only changed fields, plus `base_url` whenever the preset changes.
  - The e2e and screenshot runs each use a fresh stack.
  - Vendor chunks are split in `vite.config.ts`.

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
- S2 (2026-10-20): built the foundation and import pipeline (11 tasks, each reviewed), then a final review and one fix wave (7 Important issues fixed). A1/A2/A9 pass and Docker serves the placeholder UI.
- S3 (2026-10-20/21): built the backend chatbot (Task 0 carry-overs plus 11 tasks, each reviewed). Fix rounds closed guard bypasses, executor gaps, and turn-logging races. A final review and one fix wave followed. A5/A6/A8 pass, and the first real benchmark scored 20/20 on DeepSeek.
- S4 (2026-10-21): built the whole staff UI (Task 0 backend carry-overs plus 7 tasks, each reviewed). Fix rounds:
  - a total order for `query_dataset`;
  - the base URL kept on a preset change;
  - every upload batch's cards and errors kept;
  - the SQL shown on failed turns.
  The e2e caught a router transition race. The final review's fix wave covered Retry with the current settings, kept the conversation on a failed refetch, added one fetch seam, plain error texts, and an error page. Vitest has 132 tests, the Playwright happy path passes, and the midterm screenshots are in `docs/screenshots/`.
