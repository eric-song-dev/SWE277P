# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S3 of 5 (2026-10-20 to 10-21) is complete.
  - Tasks 0–11 are done. Task 0 was the S2 carry-overs.
  - Every task passed its task review; several needed fix rounds.
  - A final whole-branch review and one fix wave followed. The fix wave's re-review is clean.
- **Phase:** the backend chatbot is done. Next is the frontend (S4).

## Done

- **S2 (foundation and import):** settings and error shape, the core schema and `attendance_view`, the `chatbot_ro` role, the login seam, the import pipeline with identity linking, the dataset export, the samples, and the frontend skeleton. Docker runs the full stack. See the S2 line in the session log.
- **LLM profiles** (`app/llm/`):
  - Fernet-encrypted keys, presets (`fake` only with `HUB_ENABLE_FAKE_LLM=true`), and CRUD with a default profile.
  - `POST /api/llm-profiles/{id}/test`: the probe detects `json_mode` and lists `/models`.
  - `LLM_SEED_*` seeds one profile at startup.
  - A PATCH that changes the provider settings clears the probe results.
  - Each LLM call gets one 30 s timeout and no client retry.
  - LangChain/LangSmith tracing is forced off in every code path.
- **SQL safety:**
  - `chat/guard.py` (sqlglot) uses a fail-closed node allow-list, the spec's function allow-list, built-in cast types only, CTE scoping, and PostgreSQL identifier folding. It sets or tightens the limit (including `FETCH FIRST`) and re-validates its own rendered SQL.
  - `chat/executor.py` runs on `chatbot_ro` as one prepared statement in a read-only transaction, always rolls back, and resets the pool.
  - The error sanitizer passes through only identifier-only SQLSTATEs, including `42P10`.
- **Chatbot** (`chat/context.py`, `chat/graph/`):
  - Controlled values, including event names with their terms.
  - Prompts at version `2026-10-29.2`.
  - The LangGraph `StateGraph` with clarify, repair (at most 3 generations), JSON-mode fallback, and analyze. Analyze only runs when the profile and the request both share; otherwise a local summary is used.
- **Chat API** (`chat/service.py`, `chat/router.py`):
  - Conversations, the `POST /api/conversations/{id}/messages` SSE stream, rerun, and XLSX/CSV export.
  - Turns are logged in `chat_turn`, once each, including partial state on a timeout. Migration `0004` makes `conversation.title` nullable.
- **Acceptance:** A1, A2, A5, A6, A8 and A9 pass, as do the 20 benchmark reference checks.
- **Benchmark** (`backend/benchmark/`):
  - `questions.yaml` holds 20 questions with reference SQL, cross-checked by independent pandas computations over the compiled sheet.
  - The scorer (ignores column names, numeric tolerance, ties in ordered results can be in any order) and the runner CLI.
  - **First real run: 20/20** on DeepSeek `deepseek-flash` (JSON mode unsupported, so plain calls are used). Report: `backend/benchmark/reports/20261021-0059-deepseek.md`.
- **Spec updated** with this session's design decisions (§7.1, §7.5, §7.6, §8.2, §9, §13, §14, each marked "S3").

## State of the code

- **How to run:** see `CLAUDE.md` "Commands", which now includes the benchmark command.
- **Dev database (`hub`):**
  - At migration `0004`, with the 10 sample imports.
  - Has LLM profile id 1, "DeepSeek" (preset `deepseek`, model `deepseek-flash`, sharing on, `json_mode` false), seeded from `.env`. The user chose the model in S3, because `/models` does not list the configured `deepseek-v4-flash`.
  - `project/.env` still says `LLM_SEED_MODEL=deepseek-v4-flash`. Change it to `deepseek-flash` so a fresh database seeds the right model; this doesn't affect the existing profile.
- **Tests at the last S3 commit:**
  - backend: 784 passed, 54 of them acceptance;
  - ruff: check and format clean;
  - frontend: unchanged since S2 (Vitest 5 passed, build and lint clean).
- **Versions added:** langgraph 1.2.16, langchain-core 1.6.12, langchain-openai 1.7.2, sqlglot 30.24, pytest-asyncio 1.4 (`asyncio_mode = "auto"`), plus pandas and pyyaml (dev).
- **Patterns to keep:**
  - Routes take `SessionDep`, and services never commit.
  - Streaming code opens its own short sessions through `asyncio.to_thread`.
  - The chatbot engine comes from `make_chatbot_engine` (the pool reset lives there).
  - Logs record exception types only.
  - Tests blank `LLM_SEED_*`, so the real key is never read.

## Next session: S4

- **Start:** open a new Claude Code conversation in the repo root (`SWE277P/`) and say: "Read project/CLAUDE.md, then follow Rule #2 and start S4."
- **Read:** `CLAUDE.md`, this file, the spec, and `docs/plans/2026-10-20-s4-frontend.md`. Don't read the other plans.
- **Do:** execute the S4 plan with `superpowers:subagent-driven-development`. Before Task 1, check the plan against the S3 API, because the plan was written before S3:
  - SSE (spec §7.6, "Details settled in S3"):
    - `sql` can arrive once per attempt; show the latest.
    - `analysis` replaces the streamed `analysis_delta` text, even when its `source` is `local`.
    - `done.turn_id` can be null.
    - Error codes include `internal_error`, `turn_timeout`, `profile_not_found` and `profile_missing_key`.
    - Payloads are valid JSON (non-finite numbers arrive as strings).
  - REST:
    - 404 `conversation_not_found`;
    - 409 `turn_has_no_result` for rerun/export of turns that are not answers;
    - 409 `profile_name_taken`;
    - 422 for questions over 2,000 characters;
    - `share_results` defaults to false;
    - the chat export file is named `hub-turn-<id>-<ts>.<ext>`.
  - Profiles: `/test` returns `ProbeResultOut`; upstream failures give HTTP 502; `fake` appears in `/presets` only with the flag. The fake script answers "How many unique people attended Bagel Breakfast, October?" (38), "Of those, how many are international?", "…emails of everyone who attended any Bagel Breakfast", and clarifies on "this year".
- **Carry into S4:**
  - The S2 items still open (below).
  - When the user aborts a turn or starts a new conversation, the backend logs no `chat_turn` if the client disconnects before `finalize`. Record a partial turn on disconnect.
  - Chat export does not report truncation at 100,000 rows. Add a header or a note.
  - Reject `base_url` with userinfo; add a test that an empty `api_key` on PATCH keeps the key.
  - Strip whitespace-only questions (API and UI).
  - With ZotGPT: widen `response_format` rejection detection, and merge consecutive human messages if the gateway needs alternation.
  - A one-line fix in `app/llm/__init__.py`: also force the legacy `LANGCHAIN_TRACING` to `false`. Today a shell with `LANGCHAIN_TRACING=true` makes every chat turn fail closed with `internal_error` (no leak). Also make `tests/llm/test_tracing.py` clear langsmith's env cache in a `finally`.
- **Exit:** Vitest passes, and the Playwright happy path passes with the fake preset.
- **Midterm due 10/26:** S4 Task 7 produces the screenshots. If S4 isn't done by then, screenshot the S2 import flow plus the S3 API and benchmark report.

## Open issues and blockers

- D1 (the LLM sees query results) is provisional and must be confirmed with the sponsor. Sharing can be switched off per profile.
- The ZotGPT Gateway base URL, JSON-mode support and model names are unknown. Verify by 10/28.
- The sponsor's two separate dummy export files have not arrived.
- **The benchmark likely overstates generalization.** 20/20 was one run of one model, and several prompt rules match the benchmark's own readings: one-event `COUNT(*)`, ties for most/fewest, the latest-term rule, and "students" meaning everyone. S5 should add a hold-out set of about 10 new sponsor-style questions and run several times per profile. q15 (records vs people) and q04 (null email) are the readings most likely to flip.
- Sponsor questions:
  - Should waitlisted CampusGroups registrants count as attendees?
  - Is the Notes wording acceptable?
  - Do "students" include postdocs?
- **Deferred to S4 (from S2):**
  - `validate_term` should use fullmatch and ASCII digits;
  - a test with not-attended rows;
  - `query_dataset` needs a default ORDER BY and should reject None for eq/ilike;
  - `client.ts` must handle an empty 2xx body;
  - `AppShell` needs a fallback when `/api/me` fails;
  - the 505 kB bundle should be code-split;
  - `source_row` drifts after blank rows;
  - show the commit summary, because preview `flag_counts` leave out linker outcomes;
  - prefill `attendance_source_note` for 12twenty;
  - header-only files from different events share a content hash.
- **Deferred to S5:**
  - From S2:
    - the httpx warning;
    - the cp1252 comment;
    - nginx: resolve `api` once, no-cache on `index.html`, and wait for a healthy api;
    - non-root containers and a backend HEALTHCHECK;
    - `frontend/.dockerignore` should cover `.env.*`;
    - simultaneous uploads of the same new file return 500.
  - From S3 (the final review's S5 items):
    - prompt tuning: state "students" and NULL-grouping as assumptions; latest-term wording;
    - guard repair messages for COLLATE, `^` and qualified functions;
    - an advisory-lock unlock in the pool reset;
    - test tightening: A6 `== 50` with a case-insensitive regex, a fixtures conftest, 42501-specific asserts;
    - CHECK constraints on kind/preset;
    - traceback-free failure logs;
    - ownership checks before login (IDOR);
    - the FK error when a profile is deleted mid-turn.

## Decisions

- Spec D1–D10 (spec Section 2). The execution method for S2–S5 is subagent-driven, with the controller ruling on plan conflicts and recording them.
- **Per-question result sharing (spec D2):** a "Let AI see the results" switch, capped by the profile. The server sends rows only when both are on.
- **S2 decisions** are in spec §5, §6, §9 and §12.
- **S3 decisions, now in the spec:**
  - The executor sends one prepared statement and always rolls back, with a pool reset (§7.1, §13).
  - `42P10` passes through the sanitizer (§7.5).
  - The SSE details: un-limited SQL in the log, `internal_error`, partial turns on timeout, `results_shared` erring toward true, and answers-only rerun/export (§7.6).
  - PATCH clears probe results; one timeout per call; 502 for upstream failures; an unreadable key gives `profile_missing_key` (§8.2).
  - Chat export file names (§9).
  - Logs carry types only, `hide_parameters`, and tracing is off (§13).
  - Ties in ordered benchmark results (§14).
  - Events are identified by name and term in prompts; the current term is computed from the month (§7.1).
- **S3 execution choices:**
  - Migration `0004` was added rather than editing `0003`.
  - q15 is scored as attendance records (58.4%).
  - Benchmark reports are committed.
  - Provider error HTTP statuses are 502/400, never 401.
  - The user picked `deepseek-flash`.

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
- S2 (2026-10-20): built the foundation and import pipeline (11 tasks, each reviewed), then a final review and one fix wave (7 Important issues fixed). A1/A2/A9 pass and Docker serves the placeholder UI.
- S3 (2026-10-20/21): built the backend chatbot (Task 0 carry-overs plus 11 tasks, each reviewed). Fix rounds closed guard bypasses (AND/OR, catalog casts, a dropped WITH, Kelvin-sign folding), executor multi-statement and pool-leak gaps, and turn-logging races. A final review and one fix wave followed (tracing kill switch, stale probe fields). A5/A6/A8 pass, and the first real benchmark scored 20/20 on DeepSeek.
