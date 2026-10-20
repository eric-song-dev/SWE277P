# S5: Benchmark Tuning, Acceptance, and Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Meet the MOV:

- the benchmark reaches at least 18/20 on the primary profile (A3) and runs on a second profile (A4);
- question → Excel takes under 60 s (A10);
- every other acceptance test is green.

Then write the handoff documentation.

**Architecture:** No new subsystems. Tuning changes only `app/chat/graph/prompts.py` (rules, view description, few-shot) and, if a test shows it is needed, the controlled values in `chat/context.py`. The benchmark questions and reference SQL are frozen.

**Tech Stack:** As in S2–S4.

**Spec:** `project/docs/specs/2026-10-20-data-hub-design.md` (Sections 1, 14, 16). Commands are in `CLAUDE.md`.

## Global Constraints

- Never edit `benchmark/questions.yaml` questions, `reference_sql`, or the scorer to raise a score. If a question really is ambiguous, record it in `PROGRESS.md` and ask the user.
- Few-shot examples stay disjoint from the benchmark: no example may be a paraphrase of a benchmark question.
- Every prompt change bumps `PROMPT_VERSION`. Every benchmark report is kept under `benchmark/reports/` (gitignored). Copy the score lines into `docs/benchmark-results.md`.
- A real API key comes only from the user, through Settings or `LLM_SEED_*`. Never write it to files or commits.
- The generate prompt must never gain row values. A6 must stay green after every tuning change.

## Review Focus

1. **The prompt is overfit to the 20 questions.** Expected: real staff phrasings still work. Test: a 10-question holdout (`benchmark/holdout.yaml`, written before tuning starts, run but never tuned on) is reported next to the main score (Task 1).
2. **The benchmark result is not stable across runs** (temperature 0 still varies). Expected: at least 18/20 on two consecutive runs. The test is in Task 1.
3. **A fresh install fails.** On a clean clone with only `.env` created, the steps in `docs/setup-guide.md` must start the app. The test is in Task 4.
4. **Secrets or row values in logs.** Expected: `docker compose logs` contains no API key and no sample email after a benchmark run. The test is in Task 4.
5. **The cold-start first question is slow** (model warm-up, first DB connection). Expected: under 60 s even as the first question after startup. The test is in Task 3.

---

### Task 1: Benchmark tuning to at least 18/20

**Files:**
- Create: `backend/benchmark/holdout.yaml`, `docs/benchmark-results.md`
- Modify: `backend/app/chat/graph/prompts.py`, possibly `backend/app/chat/context.py`, `backend/benchmark/run.py` (`--set holdout`)

- [ ] **Step 1: Write the holdout before any tuning.** `holdout.yaml` has 10 new sponsor-style questions in the same format, with reference SQL. Add them to `test_reference_answers.py` with pandas cross-checks. Run `uv run pytest tests/benchmark -m acceptance -v`. Expected: PASS. Commit `test(benchmark): add 10-question holdout set`.

- [ ] **Step 2: Get a baseline.** Run `uv run python -m app.samples` (if the DB is empty) and `uv run python -m benchmark.run --profile "<primary>"`. Record the score, the holdout score, and the failing ids in `docs/benchmark-results.md`.

- [ ] **Step 3: Classify each failure** in `docs/benchmark-results.md` as one of:
  - missing domain rule
  - controlled-value gap
  - few-shot gap
  - JSON or format failure
  - question ambiguity

- [ ] **Step 4: Fix one class at a time.** Edit the prompt, bump `PROMPT_VERSION`, rerun the benchmark and holdout, and run `uv run pytest -m acceptance -v` (A6 must pass). Keep the change only if the main score does not drop and the holdout does not drop by more than 1. Commit each kept change as `feat(chat): <what changed> (benchmark N/20, holdout M/10)`.

- [ ] **Step 5: Confirm stability.** Repeat until two consecutive runs score at least 18/20, then record both runs. Expected: `Score: 18/20` or better, twice.

---

### Task 2: Second provider (A4)

- [ ] **Step 1:** The user creates a second profile on another provider (for example DeepSeek, or ZotGPT if it has been verified).

- [ ] **Step 2:** Run `uv run python -m benchmark.run --profile "<second>"`. Expected: it completes with no code change. Record the score in `docs/benchmark-results.md`. Only the primary profile has to reach at least 18/20. Note any provider-specific failures in the known limitations.

- [ ] **Step 3: Commit** `docs(benchmark): record second-provider run (A4)`.

---

### Task 3: Timing acceptance (A10)

**Files:**
- Create: `frontend/e2e/timing.spec.ts`

**Interfaces:**
- The spec runs only when `HUB_E2E_PROFILE` (a profile name) is set; otherwise it skips. It uses the dev stack at `HUB_E2E_BASE_URL` (default `http://127.0.0.1:8080`) with samples loaded.

- [ ] **Step 1: Write the test.**
  - Restart the `api` container first, so the first question is a cold start.
  - For benchmark questions q01, q04, and q14: start a timer at the Enter press, wait for the `.xlsx` download event, and assert the elapsed time is under 60,000 ms.
  - Print the timings.

- [ ] **Step 2: Run** `HUB_E2E_PROFILE="<primary>" npm run e2e -- timing.spec.ts`. Expected: 3 passed. Add the timings to `docs/benchmark-results.md`.

- [ ] **Step 3: Commit** `test(e2e): add question-to-Excel timing acceptance (A10)`.

---

### Task 4: Hardening sweep

- [ ] **Step 1: Fresh install.** In a temporary clone, run `cp .env.example .env`, set the passwords and key, then `docker compose up --build -d` and `docker compose exec api uv run python -m app.samples`. Expected: the app works at `127.0.0.1:8080`. Fix any setup-guide gap that turns up.

- [ ] **Step 2: Log scan.** After a benchmark run, run `docker compose logs api | grep -E "sk-|@uci\.edu" | wc -l`. Expected: `0`. Fix any log line that leaks.

- [ ] **Step 3: Replay the Review Focus lists.** Replay the Review Focus items from S2, S3, and S4 by hand in the running app, and record the results in `PROGRESS.md`. Each real bug gets a failing test first (superpowers:systematic-debugging), then the fix. Commit each fix as `fix(<area>): ...`.

---

### Task 5: Handoff documentation

**Files:**
- Create: `README.md` (in `project/`), `docs/setup-guide.md`, `docs/user-guide.md`, `docs/data-dictionary.md`, `docs/known-limitations.md`, `docs/handoff.md`

- [ ] **Step 1: Write each document.**
  - **README:** what the Hub is, a screenshot, a quick start, and links to the other docs.
  - **Setup guide:** Docker Desktop on Mac or Windows, `.env` fields, generating `HUB_SECRET_KEY`, first start, loading samples, adding a profile, backup (`pg_dump` from the `db` container), upgrade.
  - **User guide:**
    - uploading and event details, and what each flag means;
    - asking good questions and follow-ups;
    - reading an answer card (analysis vs. table, interpretation, SQL);
    - exports;
    - Settings and the result-sharing switch, with the privacy explanation.
  - **Data dictionary:** the `attendance_view` columns, the GPSRC layout mapping per platform, and the flag codes.
  - **Known limitations:**
    - D1 is pending with the sponsor;
    - identity edge cases (dot-name and `@hs.uci.edu` addresses);
    - no login;
    - committed imports cannot be edited;
    - LLM answers can be wrong;
    - ZotGPT status.
  - **Handoff:** architecture summary, the P1 extension points table (spec §12), the backlog, notes on moving to OIT (HTTPS at nginx, `AUTH_MODE=password`), and how to run all tests.

- [ ] **Step 2: Check every command** in the docs by running it.

- [ ] **Step 3: Commit** `docs: add setup, user, data dictionary, limitations, and handoff guides`.

---

### Task 6: Final acceptance run and wrap-up

**Files:**
- Create: `scripts/acceptance.sh`

- [ ] **Step 1: Write `scripts/acceptance.sh`.** It runs, in order:
  1. `uv run ruff check .`
  2. `uv run pytest -v`
  3. `uv run pytest -m acceptance -v`
  4. `npm test -- --run`
  5. `npm run lint`
  6. `npm run e2e`

  It stops on the first failure and ends with a table of A1–A10 and their status. A3, A4, and A10 are read from `docs/benchmark-results.md`; A7 shows "deferred (login in backlog)".

- [ ] **Step 2: Run `bash scripts/acceptance.sh`.** Expected: every automated row is PASS.

- [ ] **Step 3: Final docs.** Make `CLAUDE.md` final: Commands, layout, and a note that the S1–S5 sessions are complete. Make `PROGRESS.md` final: MVP complete, scores, what's next (P1 order suggestion: F11 → F12 → F14 → F16 → F15).

- [ ] **Step 4: Commit** `docs(progress): MVP complete (end of S5)`.
