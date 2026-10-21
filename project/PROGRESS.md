# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Session:** S6 (2026-10-21) is **in progress, paused after Task 11** (the user stopped for the day).
  - Plan: `docs/plans/2026-10-21-s6-ui-user-stories.md`, run subagent-driven.
  - Tasks 1–11 are done and committed (`0005498`..`131d609`), each with a passing task review:
    - the redesign on every page (Tasks 1–6);
    - the three S5 carry-overs (Tasks 7–9);
    - four new Demo questions (Task 10);
    - 63 user stories in `docs/user-stories/` plus `scripts/story_files.py` (Task 11).
  - Task 12 (walk the Shell and Chat stories) was started and stopped before it recorded anything. Its partial output was deleted and the `hub-replay` stack removed.
  - **Resume at Task 12.** The controller's ledger, with every ruling and the deferred minors for the final review, is `SWE277P/.superpowers/sdd/2026-10-21-s6-ui-user-stories/progress.md` (git-ignored, on this machine only).
  - One early observation for the re-walk: with the api stopped, requests through nginx hung about 40 s before returning 502 (SH-04, CH-15).
- **Phase:** the MVP meets its acceptance criteria; S6 is UI and UX work on top. `bash scripts/acceptance.sh` has not been re-run since S5 (Task 17 does it).
- **Next:** Tasks 12–17 of the S6 plan (walkthrough, fixes, screenshots and docs, final verification).

## Done in S5

- **Plan:** revised against the S3/S4 code at the start of the session. The revision table is at the top of `docs/plans/2026-10-20-s5-benchmark-handoff.md`.
- **Benchmark** (`docs/benchmark-results.md`):
  - **Holdout:** 10 questions (`benchmark/holdout.yaml`, h01–h10), each cross-checked with pandas. Run them with `--set holdout`. They were committed before any tuning.
  - **Prompt:** version `2026-10-29.4`. It states the "students" reading and that blank schools or departments are not a group as assumptions, and reads "last term", "most recent term" and "this term".
  - **A3:** DeepSeek (`deepseek-flash`) scored 20/20 on every run, including two consecutive runs on the final prompt, and the holdout scored 10/10 three times.
  - **A4:** DeepSeek Pro (`deepseek-v4-pro`) scored 19/20 and 10/10 on the holdout. Its one miss is q15, which reads records as people.
  - **A10:** about 4–6 s from question to Excel on DeepSeek with a cold-started api, and 5–16 s on DeepSeek Pro. Run it with `npm run e2e:timing`.
- **Backend hardening:**
  - simultaneous uploads of one file are serialized;
  - CHECK constraints (migration `0005`);
  - a turn whose profile is deleted mid-run is still recorded;
  - the pool reset releases advisory locks;
  - guard repair messages for COLLATE, `^` and qualified functions;
  - conversations and turns are per-user, returning 404 (IDOR);
  - wider detection of a rejected `response_format`;
  - logs record the exception type only, including under uvicorn;
  - settings errors never echo values;
  - tighter A6 and SQLSTATE tests.
- **Frontend hardening:**
  - pending imports come back as cards on `/upload` through the new `GET /api/imports/{id}/preview`, and typed edits survive in-app navigation;
  - a question sent between `done` and the end of the body is kept;
  - "Show results" has a pending state;
  - one first-run hint when there are no profiles;
  - batch dedupe;
  - a body-read drop maps to `network_error`;
  - `AuthGate` sits inside the error page;
  - the e2e setup no longer masks errors.
- **Docker and nginx:**
  - nginx resolves `api` on each request;
  - `index.html` is no-cache and assets are immutable;
  - the api runs as non-root, with a HEALTHCHECK;
  - nginx waits for a healthy api.
- **Review Focus replay (S2–S4):** 14 items passed by hand and 1 is covered by its tests. No bugs.
- **Docs:** `README.md`, `docs/setup-guide.md` (followed verbatim on a fresh clone, including backup, restore and upgrade), `docs/user-guide.md`, `docs/data-dictionary.md`, `docs/known-limitations.md`, `docs/handoff.md`. None of them has screenshots; those arrive with S6.

## State of the code

- **How to run:** see `CLAUDE.md` "Commands". It now covers `npm run e2e:timing`, loading samples into the running stack, and `scripts/acceptance.sh`.
- **Dev database (`hub`):**
  - at migration `0005`, with the 10 sample imports (293 rows, 79 NetIDs);
  - profiles: id 1 "DeepSeek" (`deepseek-flash`, default, sharing on) and id 2 "DeepSeek Pro" (`deepseek-v4-pro`, sharing off, the same stored key);
  - a few chat turns from the timing and replay runs.
- **Main stack:** it was left running (`project-api-1`, `project-nginx-1` on 127.0.0.1:8080) at the final code. It was started with the dev override so the db keeps port 5432: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`.
- **Tests at the last S5 commit** (one run of `scripts/acceptance.sh`, exit 0, 2:37):
  - ruff check and format: clean;
  - pytest: 889 passed, 65 of them acceptance;
  - Vitest: 147 passed (14 files);
  - lint and build: clean;
  - Playwright happy path: 1 passed;
  - timing spec (run separately, real profile): 3 passed.
- **Patterns to keep:**
  - The upload cards live in `UploadProvider`, above the routes, in memory only.
  - Unhandled errors go through `_UnhandledErrorMiddleware` (`app/errors.py`), never a re-raise.
  - The S4 patterns still apply: client mocks keep the real `ApiError`, and MUI 9 `Stack` layout props go in `sx`.

## Next session: S6 (UI and user experience)

- **Start:** open a new conversation in `SWE277P/` and say: "Read project/CLAUDE.md, then follow Rule #2 and start S6."
- **Read:** `CLAUDE.md`, this file, the spec, and `docs/design/2026-10-21-ui-redesign.md`. There is no S6 plan yet; S6 writes it. Don't read the S2–S5 plans.
- **Scope (the user's request, 2026-10-21):**
  1. **Build the approved redesign on every page.** It is "Campus blue and gold":
     - the official UCI palette and Source Sans 3, self-hosted;
     - a navy side nav that can collapse;
     - the share switch inside the question box, plus the new copy.

     The design doc has every value and lists what must change with it: the spec §8.2 text, Vitest copy assertions, and the screenshots. Its mockup is https://claude.ai/artifact/Xbq6MdmGMZdmT39wnmBQfs, with the source in `docs/design/`.
  2. **Write every user story** to `docs/user-stories/`: who, the story, acceptance criteria, and the steps to walk it. Cover every page and the empty, error and edge states, not only happy paths. Examples: a duplicate upload, a rejected file, a clarifying question, a dropped stream, no profiles, sharing off.
  3. **Walk through every story in the running app.**
     - Use a disposable stack with the "Demo" profile for anything that imports or needs an empty database. The Task 9 recipe: `docker compose -p hub-replay` on port 8083, `HUB_ENABLE_FAKE_LLM=true`, blank `LLM_SEED_*`, and `down -v` afterwards.
     - Use the main stack and "DeepSeek" where answer quality matters. Never commit an import into the dev DB: A1 and the benchmark depend on its 293 rows.
     - Record each result in `docs/user-stories/walkthrough-<date>.md`, with screenshots where useful.
     - Fix the problems found, and list anything left with a reason.
- **Carry into S6:**
  - **Pending imports:** a pending import whose stored file no longer parses (only possible after an adapter change) shows "Could not load a pending import", which has no file name and no Discard. Give it both.
  - **Duplicate person in one file:** it is flagged `duplicate_in_event` only at commit, so the preview count includes the second row. Write a story for it, and decide whether the preview should say so.
  - **Doc refresh after the redesign:**
    - add screenshots to the README and user guide;
    - update the user guide's export labels (".xlsx" and ".csv" under "Export"), which S6 renames;
    - regenerate `docs/screenshots/`.
  - **Dropped stream:** after a drop and a refetch, both the saved `client_disconnected` turn and the live "Connection lost" card can show (spec §4.3).
- **Exit:** see the S6 row in spec §15.
- **Before the sponsor demo (week 7):** rebuild the main stack, click through with a real profile, and try one export in Safari.

## Open issues and blockers

- **D1 is provisional.** The LLM sees query results, which must be confirmed with the sponsor. Sharing can be switched off per profile.
- **ZotGPT is unknown.** Its base URL, JSON-mode support and model names must be verified by 10/28. Rejection detection is already wider. If the gateway needs alternating roles, merge consecutive human messages.
- **Only one provider is benchmarked.** Both profiles are DeepSeek models. Benchmark ZotGPT or another provider once a key exists.
- **Missing sponsor files.** The sponsor's two separate dummy export files have not arrived. When they do, add them as fixtures, and check "last term" on data with more than one term.
- **Sponsor questions:**
  - Should waitlisted CampusGroups registrants count as attendees?
  - Is the Notes wording acceptable?
  - Do "students" include postdocs?
- **Known limitations** are in `docs/known-limitations.md`, including that the `db` container log can hold values from a failing statement. Fixing that needs a superuser per-role log setting (backlog).
- **Backlog from the S5 reviews** (all minor):
  - the term order is defined in three places (`context.py`, `prompts.py`);
  - `acceptance.sh` A7 text formatting;
  - test cosmetics: migration test gaps, the concurrent FOR KEY SHARE path, and no test for discarding a restored card;
  - the upload store re-renders on every keystroke;
  - the timing spec fails slowly on an unknown profile name.

## Decisions

- **Spec decisions:** D1–D10 (spec Section 2). S2–S5 decisions are in the spec sections marked with their session ("Decided in S5" for this one).
- **Execution method:** S2–S6 are subagent-driven. The controller rules on plan conflicts and records the rulings.
- **UI redesign (2026-10-21):**
  - The user approved direction A, "Campus blue and gold", with the toolbar-inside-the-box question layout and their own switch copy.
  - It is recorded in `docs/design/` and spec §4.3, §8.2 and §15.
- **S5 rulings:**
  - Work on `main` (Rule #1).
  - A4 uses "DeepSeek Pro", made by copying the stored key server-side (the user's choice).
  - A10 has its own Playwright config against the main stack.
  - IDOR covers conversations and turns only; imports, the dataset and profiles stay shared.
  - Benchmark reports are gitignored, and `docs/benchmark-results.md` is the record.
  - `PROMPT_VERSION` bumps its suffix.
  - No UI screenshots until S6.
  - A new import adapter needs one module plus one migration (the source CHECK and the view's `platform` CASE).

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
- S2 (2026-10-20): built the foundation and import pipeline (11 tasks, each reviewed), then a final review and one fix wave. A1/A2/A9 pass and Docker serves the placeholder UI.
- S3 (2026-10-20/21): built the backend chatbot (Task 0 plus 11 tasks, each reviewed), then a final review and one fix wave. A5/A6/A8 pass, and the first real benchmark scored 20/20 on DeepSeek.
- S4 (2026-10-21): built the whole staff UI (Task 0 plus 7 tasks, each reviewed), then a final review and one fix wave. Vitest has 132 tests, the Playwright happy path passes, and the midterm screenshots are in `docs/screenshots/`.
- S4 follow-up (2026-10-21): verified the DeepSeek seed model, designed and approved the UI redesign, and added S6.
- S5 (2026-10-21): revised the plan against the S3/S4 code, then ran 11 tasks plus 10b, each reviewed. Added the holdout; the benchmark scored 20/20 and 10/10, the second profile 19/20, and A10 took about 5 s. Did the hardening sweep, the replay (no bugs) and the handoff docs. The final review's fix wave closed a traceback leak under uvicorn. `acceptance.sh` is green.
- S6 part 1 (2026-10-21): wrote the S6 plan, then ran Tasks 1–11, each reviewed: the redesign, the three S5 carry-overs, the Demo questions and 63 user stories. Vitest has 185 tests and pytest 906. Paused before the walkthrough (Task 12).
