# S5: Benchmark Tuning, Acceptance, Hardening, and Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Meet the MOV:

- the benchmark reaches at least 18/20 on the primary profile (A3) and runs on a second profile (A4);
- question → Excel takes under 60 s (A10);
- every other acceptance test is green.

Then close the hardening carry-overs from S2–S4 and write the handoff documentation.

**Architecture:** No new subsystems. Tuning changes only `app/chat/graph/prompts.py` (rules, view description, few-shot) and, if a test shows it is needed, the controlled values in `chat/context.py`. The benchmark questions and reference SQL are frozen.

**Tech Stack:** As in S2–S4.

**Spec:** `project/docs/specs/2026-10-20-data-hub-design.md` (Sections 1, 14, 16). Commands are in `CLAUDE.md`. The carry-over lists are in `PROGRESS.md` ("Carry into S5" and "Deferred to S5").

## Revision at the start of S5 (2026-10-21)

The plan was written in S1, before S3 and S4 existed. It was checked against the S4 code at the start of S5 and revised:

| Change | Why |
|---|---|
| Task 1 is split: Task 1 builds the holdout and tooling, Task 2 tunes. | The holdout must exist and be committed before any tuning. |
| The second profile (A4) is "DeepSeek Pro" (`deepseek-v4-pro`), created by copying the stored DeepSeek key server-side. | The user's choice. No second provider key is available yet; ZotGPT is unverified. |
| The S2–S4 carry-overs become Tasks 4–7. | `PROGRESS.md` assigns them to S5's hardening sweep; the old Task 4 had no room for them. |
| A10 runs from its own Playwright config (`npm run e2e:timing`) against the main stack, not `npm run e2e`. | `npm run e2e` is pinned to the happy path, and its global setup builds the `hub-e2e` stack and refuses any real profile. |
| The log scan follows the A10 run, not a benchmark run. | The benchmark runs on the host, so it writes nothing to the container logs. |
| The fresh install uses its own Compose project and port. | A clone in another folder would otherwise collide with the main stack on port 8080. |
| No UI screenshots in the README or user guide. | S6 restyles every page (`PROGRESS.md`). |
| Benchmark reports are gitignored from now on; `docs/benchmark-results.md` is the record. | The S1 plan already said so; S3 had committed one report, which stays. |
| Task 11 leaves the project pointing at S6, not "MVP complete". | S6 was added after this plan was written. |

## Global Constraints

- Never edit `benchmark/questions.yaml` questions, `reference_sql`, or the scorer to raise a score. If a question really is ambiguous, record it in `PROGRESS.md` and ask the user.
- Few-shot examples stay disjoint from the benchmark and the holdout: no example may be a paraphrase of a benchmark or holdout question.
- Every prompt change bumps `PROMPT_VERSION` by its suffix (`2026-10-29.2` → `2026-10-29.3`). Every benchmark report stays under `benchmark/reports/` (gitignored). Copy the score lines into `docs/benchmark-results.md`.
- A real API key comes only from the user, through Settings or `LLM_SEED_*`, or from the key already stored in the database. Never print it, write it to a file, or commit it. Never read `project/.env`.
- The generate prompt must never gain row values. A6 must stay green after every tuning change.
- Commit on `main` (the current branch), staging files by path, as `CLAUDE.md` Rule #1 says.
- A behavior decision made while fixing a carry-over goes into the matching spec section, marked "(Decided in S5.)", in the same commit.

## Review Focus

1. **The prompt is overfit to the 20 questions.** Expected: real staff phrasings still work. Test: a 10-question holdout (`benchmark/holdout.yaml`, written before tuning starts, run but never tuned on) is reported next to the main score (Tasks 1 and 2).
2. **The benchmark result is not stable across runs** (temperature 0 still varies). Expected: at least 18/20 on two consecutive runs. The test is in Task 2.
3. **A fresh install fails.** On a clean clone with only `.env` created, the steps in `docs/setup-guide.md` must start the app. The tests are in Tasks 7 and 10.
4. **Secrets or row values in logs.** Expected: `docker compose logs` contains no API key and no sample email after questions are asked through the UI. The test is in Task 8.
5. **The cold-start first question is slow** (model warm-up, first DB connection). Expected: under 60 s even as the first question after startup. The test is in Task 8.

---

### Task 1: Holdout set and benchmark tooling

**Files:**
- Create: `backend/benchmark/holdout.yaml`, `docs/benchmark-results.md`
- Modify: `backend/benchmark/__init__.py`, `backend/benchmark/run.py`, `backend/tests/benchmark/` (`pandas_expected.py`, `test_reference_answers.py`, `test_questions.py`, `test_run.py`), `.gitignore`

- [ ] **Step 1: Write the holdout before any tuning.** `holdout.yaml` has 10 new sponsor-style questions (ids `h01`–`h10`) in the same format as `questions.yaml`, with reference SQL and notes. They are questions GPSRC staff would plausibly ask, phrased differently from the benchmark (not paraphrases of it or of the few-shot examples in `prompts.py`). Cover the readings most likely to flip: records vs. people, blank emails or schools, "students", term and academic-year wording, event-name matching, ranking with ties, and one follow-up-free comparison across platforms. Each answer on the sample data must be non-trivial (not empty, not the whole table).
- [ ] **Step 2: Cross-check the holdout.** Add an independent pandas computation per holdout id to `tests/benchmark/pandas_expected.py`, and run the holdout through the same reference test and format test as the benchmark. Run `uv run pytest tests/benchmark -m acceptance -v`. Expected: PASS. Commit `test(benchmark): add 10-question holdout set`.
- [ ] **Step 3: Add `--set main|holdout`** (default `main`) to `benchmark/run.py`. The report title and file name say which set ran (`<YYYYMMDD-HHMM>-<slug>-holdout.md` for the holdout), and the printed line is `Score: N/10` for the holdout. `--only` works within the chosen set. Add unit tests in `test_run.py`. Commit `feat(benchmark): run the holdout set with --set holdout`.
- [ ] **Step 4: Reports and the results document.** Add `project/backend/benchmark/reports/*.md` to `.gitignore` (the committed S3 report stays tracked). Create `docs/benchmark-results.md` with:
  - an **Acceptance summary** table, `| Acceptance | Status | Evidence |`, with rows `A3`, `A4` and `A10`, each `PENDING` for now. Task 11's script reads these rows; the status cell is exactly `PASS`, `FAIL` or `PENDING`.
  - a **Runs** table: date, profile (preset, model), prompt version, set, score, failing ids;
  - **Failure classes** and **Timings** sections, empty for now.

  Commit `docs(benchmark): add the results record`.

---

### Task 2: Benchmark tuning to at least 18/20

**Files:**
- Modify: `backend/app/chat/graph/prompts.py`, possibly `backend/app/chat/context.py`, `docs/benchmark-results.md`, `backend/tests/chat/` where a prompt test pins the changed text

The primary profile is `DeepSeek` (id 1, `deepseek-flash`). Use `--today 2026-11-02` (the default).

- [ ] **Step 1: Get a baseline.** Run `uv run python -m benchmark.run --profile "DeepSeek"` and `--set holdout` three times each. Record every score and the failing ids in `docs/benchmark-results.md`.
- [ ] **Step 2: Classify each failure** (main and holdout) in `docs/benchmark-results.md` as one of: missing domain rule, controlled-value gap, few-shot gap, JSON or format failure, question ambiguity.
- [ ] **Step 3: Fix one class at a time.** Also make the prompt carry-overs from `PROGRESS.md`:
  - state the "students" reading (everyone GPSRC serves unless an affiliation is named) and NULL-grouping (records with no school or department are not a group) as assumptions in the answer, rather than silently;
  - the latest-term wording ("last term", "most recent term", "this term").

  For each change: edit the prompt, bump `PROMPT_VERSION`, rerun the main set and the holdout, and run `uv run pytest -m acceptance -v` (A6 must pass). Keep the change only if the main score does not drop and the holdout does not drop by more than 1. Tune on main-set failures only; the holdout is never used to choose wording. Commit each kept change as `feat(chat): <what changed> (benchmark N/20, holdout M/10)`.
- [ ] **Step 4: Confirm stability.** Repeat until two consecutive main runs score at least 18/20, then record both runs and set the `A3` row to `PASS`. Also record three holdout runs on the final prompt.

---

### Task 3: Second profile (A4)

- [ ] **Step 1: Create the profile.** Write a one-off script in the session scratchpad (never in the repo) that, in one DB session, reads profile `DeepSeek`'s key with `app.llm.service.get_profile_with_key` and creates profile `DeepSeek Pro` (preset `deepseek`, the same base URL, model `deepseek-v4-pro`, `share_results_with_llm` off) with `create_profile`. The script prints only the new profile's id and name, never the key. Skip creation if the profile exists.
- [ ] **Step 2:** Run `uv run python -m benchmark.run --profile "DeepSeek Pro"` and `--set holdout`. Expected: it completes with no code change. Record the scores in `docs/benchmark-results.md` and set `A4` to `PASS` with the two profiles as evidence. Only the primary profile has to reach at least 18/20. Note any provider-specific failures for the known limitations.
- [ ] **Step 3: Commit** `docs(benchmark): record second-profile run (A4)`.

---

### Task 4: Backend hardening (correctness and security)

Carry-overs from `PROGRESS.md`. Each real bug gets a failing test first (superpowers:systematic-debugging), then the fix. Commit each fix separately as `fix(<area>): ...`. Use `git log --grep` and the spec to recover the context of a terse item.

- [ ] **Imports:** two simultaneous uploads of the same new file return 500. Expected: neither request fails; both get the same pending import (or `duplicate` once committed), and one row exists.
- [ ] **Database:** CHECK constraints on the enumerated text columns (`kind`, `preset`, `source`, `status`, `match_method`, `modality` and the like) in a new migration. Deleting a profile while a turn using it is in flight must not make the turn fail with an FK error when it is recorded.
- [ ] **Executor:** the pool reset also releases advisory locks (`pg_advisory_unlock_all()` or equivalent), with a test.
- [ ] **Guard:** clear repair messages, safe to send to the LLM, for `COLLATE`, the `^` operator, and schema-qualified function calls.
- [ ] **Security (IDOR before login):** conversation and chat-turn routes (`GET /api/conversations/{id}`, messages, rerun, export) return 404 for a conversation or turn whose `created_by` is not the current user, and `GET /api/conversations` lists only the current user's. Imports, the dataset and LLM profiles stay shared office resources. Record this in spec §11.
- [ ] **ZotGPT readiness:** widen the detection of a provider rejecting `response_format` (other status codes and message wordings that OpenAI-compatible gateways use), so the plain-call fallback still triggers. Merging consecutive human messages waits until ZotGPT is verified (known limitation).

Run `uv run pytest`, `uv run ruff check .` and `uv run ruff format --check .`.

---

### Task 5: Backend logs and test hygiene

- [ ] **Logs and warnings:** the httpx warning; the cp1252 comment; failure logs without tracebacks (a logged failure carries the exception type only, never a message or traceback that could hold row values or a key).
- [ ] **Test tightening:** A6 asserts `== 50` with a case-insensitive regex; a shared fixtures conftest where fixtures are duplicated; 42501-specific asserts where a test only expects "some DB error".
- [ ] **Test hygiene:** tests for key stripping on profile create; an anyio re-delivered-cancel disconnect test; a bounded busy-wait in `test_chat_api.py`.

Commit as `test(...)`, `fix(logging): ...` or `chore(...)` per logical change. Run the full backend suite, ruff check and ruff format.

---

### Task 6: Frontend hardening

Each item gets a Vitest test first, then the fix. Copy and behavior only: S6 restyles every page, so add no new visual style.

- [ ] **Pending imports:** a pending import has a home after leaving `/upload`. The Upload page shows the server's pending imports as cards when it opens (so a pending import can be committed or discarded later), and the Dataset page's "Pending" rows link to it. Typed form edits survive in-app navigation; after a full reload the form starts from the prefilled draft.
- [ ] **Chat:**
  - a question sent between `done` and the end of the body is not lost (the composer clears only when the question is accepted);
  - errors that are not `ApiError` are logged to the console before being mapped;
  - `sse.ts` no longer turns an exception thrown by `onEvent` into "Connection lost";
  - "Show results" shows a pending state;
  - `/chat` with no profiles shows one first-run hint that links to Settings.
- [ ] **Upload:** two copies of one export dropped in one batch give one card (no duplicate React keys).
- [ ] **Client:** a connection drop while reading a response body maps to `network_error`, not a raw `TypeError`; a render error inside `AuthGate` reaches the error page; `sse.test.ts` uses the current route path; a split multi-byte UTF-8 character in an SSE chunk decodes correctly (test).
- [ ] **E2E setup:** a failing teardown no longer masks the original error, and the health fetch has a per-request timeout.

Run `npm test -- --run`, `npm run lint`, `npm run build`, and `npm run e2e`.

---

### Task 7: Docker, nginx, and a fresh install

- [ ] **nginx:** resolve `api` at request time (Docker's resolver), so an api restart does not leave nginx on a stale address; `Cache-Control: no-cache` on `index.html` (hashed assets keep long caching).
- [ ] **Containers:** the api runs as a non-root user; a backend `HEALTHCHECK` on `/api/health`; nginx waits for a healthy api (`depends_on: condition: service_healthy`). `frontend/.dockerignore` covers `.env.*`. Run nginx unprivileged only if it needs no change to the published port mapping.
- [ ] **Samples in the container:** make sure the documented way to load the samples into the running stack works (`docker compose exec api python -m app.samples` or the `uv run` form; the image has no dev dependencies).
- [ ] **Fresh install:** clone the repo at `HEAD` into the scratchpad, create its `.env` from `.env.example` with newly generated passwords and `HUB_SECRET_KEY` (never copy the real `.env`), and start it as Compose project `hub-fresh` on `HUB_HTTP_PORT=8082`. Load the samples, open the app, check `/api/health` and that the Dataset page lists 10 imports. Then `docker compose -p hub-fresh down -v`. Write the exact working command sequence into the task report; Task 10 turns it into the setup guide. Fix any gap found.

Run `npm run e2e` afterwards (the e2e stack uses the same Dockerfiles). Commit as `fix(docker): ...` / `fix(nginx): ...`.

---

### Task 8: Timing acceptance (A10) and the log scan

**Files:**
- Create: `frontend/e2e/timing.spec.ts`, `frontend/playwright.timing.config.ts`
- Modify: `frontend/package.json` (`e2e:timing`), `docs/benchmark-results.md`, `CLAUDE.md` (Commands)

**Interfaces:**
- `npm run e2e:timing` uses `playwright.timing.config.ts`: no global setup, `baseURL` from `HUB_E2E_BASE_URL` (default `http://127.0.0.1:8080`). The spec skips unless `HUB_E2E_PROFILE` (a profile name) is set. It runs against the main stack with the samples loaded. Start that stack with the dev override, `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`, so the dev database keeps its published port.

- [ ] **Step 1: Write the test.**
  - Restart the `api` container first (`docker compose restart api`, then wait for `/api/health`), so the first question is a cold start.
  - Select the profile named by `HUB_E2E_PROFILE` in the chat page's drop-down.
  - For benchmark questions q01, q04 and q14, each in a new chat: start a timer at the Enter press, click the answer card's Excel download, wait for the `.xlsx` download event, and assert the elapsed time is under 60,000 ms.
  - Print the timings.
- [ ] **Step 2: Run** `HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing`. Expected: 3 passed. Add the timings to `docs/benchmark-results.md` and set `A10` to `PASS`.
- [ ] **Step 3: Log scan.** Run `docker compose logs api nginx db | grep -E "sk-|@uci\.edu" | wc -l`. Expected: `0`. Fix any log line that leaks (failing test first).
- [ ] **Step 4: Commit** `test(e2e): add question-to-Excel timing acceptance (A10)`.

---

### Task 9: Review Focus replay

- [ ] Replay the Review Focus items from the S2, S3 and S4 plans by hand in the running app (main stack; the "Demo" profile is not available there, so use `DeepSeek` where a model is needed). The items are extracted for you in the task's dispatch. Record each item's result (pass, or the bug found and its fix commit) in the task report; the controller copies the summary into `PROGRESS.md`.
- [ ] Each real bug gets a failing test first (superpowers:systematic-debugging), then the fix. Commit each fix as `fix(<area>): ...`.

---

### Task 10: Handoff documentation

**Files:**
- Create: `README.md` (in `project/`), `docs/setup-guide.md`, `docs/user-guide.md`, `docs/data-dictionary.md`, `docs/known-limitations.md`, `docs/handoff.md`

- [ ] **Step 1: Write each document.** No UI screenshots: describe screens by their labels ("Let AI see the results", "New chat" and "Download Excel (.xlsx)" survive the S6 redesign). Leave a one-line note in the README and user guide that screenshots arrive with the S6 redesign.
  - **README:** what the Hub is, a quick start, and links to the other docs.
  - **Setup guide:** Docker Desktop on Mac or Windows, `.env` fields, generating `HUB_SECRET_KEY`, first start, loading samples, adding a profile, backup (`pg_dump` from the `db` container), upgrade. Built from Task 7's verified command sequence.
  - **User guide:**
    - uploading and event details, and what each flag means;
    - asking good questions and follow-ups;
    - reading an answer card (analysis vs. table, interpretation, SQL);
    - exports;
    - the two result-sharing switches (per model in Settings, per question next to the question box), with the privacy explanation.
  - **Data dictionary:** the `attendance_view` columns, the GPSRC layout mapping per platform, and the flag codes.
  - **Known limitations:**
    - D1 is pending with the sponsor;
    - identity edge cases (dot-name and `@hs.uci.edu` addresses);
    - no login;
    - committed imports cannot be edited;
    - LLM answers can be wrong;
    - ZotGPT status;
    - the second-profile and holdout results from `docs/benchmark-results.md`.
  - **Handoff:** architecture summary, the P1 extension points table (spec §12), the backlog, notes on moving to OIT (HTTPS at nginx, `AUTH_MODE=password`), and how to run all tests.
- [ ] **Step 2: Check every command** in the docs by running it. For the setup guide, follow it verbatim on a fresh clone as in Task 7 (project `hub-fresh`, port 8082, generated secrets), then tear it down.
- [ ] **Step 3: Commit** `docs: add setup, user, data dictionary, limitations, and handoff guides`.

---

### Task 11: Final acceptance run and wrap-up

**Files:**
- Create: `scripts/acceptance.sh` (in `project/`)

- [ ] **Step 1: Write `scripts/acceptance.sh`.** It runs, in order:
  1. `uv run ruff check .` and `uv run ruff format --check .`
  2. `uv run pytest -v`
  3. `uv run pytest -m acceptance -v`
  4. `npm test -- --run`
  5. `npm run lint` and `npm run build`
  6. `npm run e2e`

  It stops on the first failure and ends with a table of A1–A10 and their status. A3, A4 and A10 are read from the Acceptance summary in `docs/benchmark-results.md`; A7 shows "deferred (login in backlog)".
- [ ] **Step 2: Run `bash scripts/acceptance.sh`.** Expected: every automated row is PASS.
- [ ] **Step 3: Final docs.** `CLAUDE.md`: Commands and layout current, and a note that S1–S5 are complete and S6 is next. `PROGRESS.md`: S5 complete, scores, and S6 as the next session (P1 order suggestion after S6: F11 → F12 → F14 → F16 → F15).
- [ ] **Step 4: Commit** `docs(progress): end of S5`.
