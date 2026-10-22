# Progress

Read this after `CLAUDE.md` at the start of every session (see "Rule #2" there).

## Current status

- **Sessions:** S1–S6 are complete. S6 (2026-10-21) finished the planned build.
- **Phase:** the MVP meets its acceptance criteria. Every row of `bash scripts/acceptance.sh` passes except A7 (login, deferred). The UI has the approved redesign, every user story has a recorded walkthrough result, and every problem the walk found is fixed or left with a reason.
- **After S6 (2026-10-21):** the user approved a revision of the shell and Chat page, artboard "A2" on the design canvas (`docs/design/2026-10-21-ui-redesign.md`, "Revision"). Built and checked in a browser:
  - "Recent questions" with "New chat" moved into a 280 px side nav, on every page;
  - Chat lost its conversation column and header for a slim "Answering with" row;
  - every summary has a caution line, and the line under the question box is gone;
  - the shell fills the window, so the nav, the model row and the question box stay put and the page never rubber-bands.
- **Sponsor walkthrough (2026-10-22):** the sponsor's requests from the 2026-10-21 meeting were walked as SP-01 … SP-14 (`docs/user-stories/walkthrough-2026-10-22.md`): 8 Pass, 5 Pass with a caveat, 1 Gap. The benchmark scored 20/20 again and question to Excel took 4–7 s. Nothing was fixed; the findings are under "Open issues".
- **Next:** no session is planned. The work left is the sponsor demo and the open issues below.

## Done in S6

- **Plan:** `docs/plans/2026-10-21-s6-ui-user-stories.md`. It ran subagent-driven: 17 tasks, each reviewed, then a final whole-branch review and one fix wave. That is 60 commits from `c3bc35e` to `e897787`.
- **Redesign (Tasks 1–6):** "Campus blue and gold" is on every page:
  - theme tokens (`src/app/theme.ts`) and Source Sans 3 (self-hosted, `@fontsource/source-sans-3` 5.3.0);
  - a navy side nav that collapses to a 72 px rail, and `PageHeader`;
  - the share switch inside the question box, with the On/Off helper texts;
  - restyled answer cards ("Show the SQL query", "Download Excel (.xlsx)", "Download CSV (.csv)");
  - Upload, Dataset and Settings restyled.
- **S5 carry-overs (Tasks 7–9):**
  - a pending import that no longer loads shows its file name and Discard;
  - the preview counts "Duplicate in this event" and "Email/NetID unavailable";
  - a dropped stream no longer shows two cards.
- **Demo questions (Task 10):** "Demo slow question", "Demo refused query", "Demo repaired query" and "Demo all columns" in the scripted model.
- **User stories (Task 11):** 63 stories in `docs/user-stories/` (shell, chat, upload, dataset, settings), each with who, the story, acceptance criteria and walk steps. `scripts/story_files.py` makes the edge-case upload files.
- **Walkthrough (Tasks 12–15):** `docs/user-stories/walkthrough-2026-10-21.md`, with screenshots.
  - The first walk gave 67 rows, 32 findings. Fix groups G1–G10 fixed them, and a re-walk confirmed it and found W-33…W-37, which were fixed too.
  - **Final:** 67 rows: 65 Pass, 2 Fail. Both Fails are left on purpose.
  - **Findings:** 37 in all. 34 are fixed and 3 are left:
    - W-3: text fields show focus with their field border.
    - W-10: a question is lost if the Hub server itself stops mid-answer.
    - W-32: "How I read your question" can name a column.

    W-10 and W-32 are in `docs/known-limitations.md`.
  - **Main fixes:**
    - a "Page not found" page;
    - nginx fails fast (5 s) when the api is down, instead of 60 s;
    - the question box stays typeable while answering;
    - a sent question scrolls to the top with room for its answer;
    - "Copied" and "More than N rows";
    - saved AI errors keep their message;
    - the Dataset list shows one line with "…", and narrow columns sort on click;
    - grid focus rings;
    - Upload: Dismiss, "Already imported as …", `.xls` refused in the browser, "To commit, fill in: …", the size limit in KB/MB;
    - commit summary links count only existing people;
    - `imported_rows` on `GET /api/imports`;
    - Settings: a credentials-in-URL message, and the model list after a Test.
- **Docs (Task 16):**
  - seven screenshots in `docs/screenshots/` (01–07), as window-sized captures;
  - one screenshot in the README;
  - the user guide updated for the new labels and the fixes, with screenshots;
  - spec §4.3 notes the walkthrough fixes.

## State of the code

- **How to run:** see `CLAUDE.md` "Commands".
- **Dev database (`hub`):**
  - at migration `0005`, with the 10 sample imports (293 rows, 79 NetIDs);
  - profiles: id 1 "DeepSeek" (`deepseek-flash`, default, sharing on) and id 2 "DeepSeek Pro" (`deepseek-v4-pro`, sharing off, the same stored key);
  - chat turns from the walks and the timing runs.
- **Main stack:** it was left running at the final code (after the A2 revision) on 127.0.0.1:8080. It was started with `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d`.
- **Tests at the end of S6** (`bash scripts/acceptance.sh`, exit 0):
  - ruff check and format: clean;
  - pytest: 917 passed, 65 of them acceptance;
  - Vitest: 218 passed (21 files), also under a `zh_CN` locale; 222 after the A2 revision;
  - oxlint and build: clean;
  - Playwright e2e: 5 passed;
  - `npm run e2e:screenshots`: passed;
  - timing spec (`HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing`, main stack): 3 passed, 3.9–5.9 s from question to Excel.
- **Benchmark (S5, unchanged):** DeepSeek 20/20 and holdout 10/10; DeepSeek Pro 19/20. See `docs/benchmark-results.md`.
- **Patterns to keep:**
  - Upload cards live in `UploadProvider`, above the routes, in memory only.
  - The chat's live turn belongs to one conversation (`useChatStream` owner `{id, created, reached}`). The sent turn gets a min-height from the measured conversation pane (`--thread-height`).
  - The shell fills the window (`100dvh`): the side nav and the main area scroll on their own, and on Chat only the conversation pane scrolls. A layout check in e2e must measure the pane, not the window.
  - Grid styles are shared in `gridSx`. Header, cell and scroll-area focus rings are inset (offset −2 px).
  - Unhandled errors go through `_UnhandledErrorMiddleware`. Client mocks keep the real `ApiError`. MUI 9 `Stack` layout props go in `sx`.
  - Screenshots use `shoot()` in `e2e/screenshots.spec.ts`. It grows the window until no pane scrolls, then captures the window.

## Before the sponsor demo (week 7)

1. Rebuild the main stack and click through every page with a real profile.
2. Try one export in Safari. Testing so far is Chromium only.
3. Walk the README story walk order on a replay stack if the UI changed since 2026-10-21.

## Open issues and blockers

- **Sponsor walkthrough findings** (`docs/user-stories/walkthrough-2026-10-22.md`):
  - SF-1 (high): a second download of an imported event commits as a new event with no warning, and Chat then double-counts it. Committed imports cannot be removed. Needs a design.
  - SF-2: event date is optional, so date-range answers silently leave undated events out (main has no dates at all).
  - SF-3: main's four 12twenty events lack the attendance-source note that `events.json` now sets. Fix the dev DB before the demo.
  - SF-4: with result sharing off, summaries are "unique_people: 79", not sentences. It depends on D1.
  - SF-5 … SF-9 are minor or for discussion: gendered readings, one summary over-claim, no roster for service gaps, no row filter on Dataset, raw column names in chat downloads.
- **D1 is provisional.** The LLM sees query results, and the sponsor must confirm this. Sharing can be switched off per profile.
- **ZotGPT is unknown.** Its base URL, JSON-mode support and model names must be verified by 10/28.
- **Only one provider is benchmarked.** Both profiles are DeepSeek models.
- **Missing sponsor files.** The two separate dummy exports have not arrived. When they do, add them as fixtures and check "last term" on data with more than one term.
- **Sponsor questions:** Should waitlisted CampusGroups registrants count as attendees? Is the Notes wording acceptable? Do "students" include postdocs?
- **Known limitations:** `docs/known-limitations.md`.
- **Backlog (minor):**
  - The term order is defined in three places.
  - The upload store re-renders on every keystroke.
  - The timing spec fails slowly on an unknown profile name.
  - Committed upload cards have no Dismiss; they clear on reload.
  - Grid ring values repeat in `gridSx`.
  - The size text rounds odd limits oddly ("1024 KB" just under 1 MiB).

## Decisions

- **Spec decisions:** D1–D10 (spec Section 2). Later decisions are in the spec sections marked with their session ("Decided in S6", "S6 walkthrough fixes").
- **Execution method:** S2–S6 were subagent-driven. The controller ruled on plan conflicts and findings, and recorded each ruling.
- **S6 decisions:**
  - Nav links use a white inset focus ring, because the navy background hides the blue one. Text fields and selects keep MUI's 2 px field border (W-3).
  - The preview counts in-file duplicates and rows with no NetID or email. The commit stays authoritative.
  - Dropped stream: a live error turn takes the place of the first saved turn after the `seq` it started from, and the client refetches after a lost connection.
  - The Demo questions are scripted entries with optional `delay_seconds`.
  - A blank Student ID in a source export stays blank, and no flag is added (W-18).
  - W-10 and W-32 are left and documented. Removing column names from readings needs a prompt change and a benchmark re-run.
  - Screenshots are window-sized captures of a reopened conversation.

## Session log

- S1 (2026-10-20): explored the course materials, brainstormed, wrote and got approval for the spec, wrote the S2–S5 plans, and chose subagent-driven execution.
- S2 (2026-10-20): built the foundation and import pipeline (11 tasks, each reviewed), then a final review and one fix wave. A1/A2/A9 pass and Docker serves the placeholder UI.
- S3 (2026-10-20/21): built the backend chatbot (Task 0 plus 11 tasks, each reviewed), then a final review and one fix wave. A5/A6/A8 pass, and the first real benchmark scored 20/20 on DeepSeek.
- S4 (2026-10-21): built the whole staff UI (Task 0 plus 7 tasks, each reviewed), then a final review and one fix wave. Vitest has 132 tests, the Playwright happy path passes, and the midterm screenshots are in `docs/screenshots/`.
- S4 follow-up (2026-10-21): verified the DeepSeek seed model, designed and approved the UI redesign, and added S6.
- S5 (2026-10-21): revised the plan against the S3/S4 code, then ran 11 tasks plus 10b, each reviewed. Added the holdout; the benchmark scored 20/20 and 10/10, the second profile 19/20, and A10 took about 5 s. Did the hardening sweep, the replay (no bugs) and the handoff docs. `acceptance.sh` is green.
- S6 (2026-10-21): built the redesign, fixed the S5 carry-overs, wrote 63 user stories and walked them (67 rows, 37 findings), fixed 34 findings and left 3 with reasons, re-walked, regenerated the screenshots and guides, then a final review and one fix wave. `acceptance.sh` is green: pytest 917, Vitest 218, e2e 5, timing 3.
- After S6 (2026-10-21): built the approved A2 revision (recent questions in the side nav, the "Answering with" row, a caution line on every summary, a fixed window-filling shell), tested it in a browser on a replay stack and on main, and refreshed the design doc, spec, guide, stories and screenshots. Vitest 222, e2e 5.
- Sponsor walkthrough (2026-10-22): walked the 10/21 meeting's requests on main (read-only) and a throwaway DeepSeek stack. 14 stories, 9 findings recorded, nothing fixed. Benchmark 20/20, acceptance 65, timing 3.
