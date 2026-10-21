# S6: UI Redesign and User-Story Walkthrough Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the approved "Campus blue and gold" redesign on every page, close the three S5 carry-overs, then write every user story and walk each one in the running app, fixing what the walk finds.

**Architecture:** Visual and copy changes only on the existing S4/S5 React app: a token-based MUI theme, a collapsible navy side nav, and a `PageHeader` each page renders. Behavior, routes, API calls and test-relevant roles stay as built. Three small behavior fixes (an unloadable pending import, in-file duplicate people in the preview, the dropped-stream double card) land before the walk so the walk verifies them. The walk runs on a disposable "Demo" stack and, where answer quality matters, on the main stack with DeepSeek.

**Tech Stack:** React 19, TypeScript, MUI 9, MUI X DataGrid 9, TanStack Query, Vitest, Playwright; FastAPI, pytest; Docker Compose.

**Spec:** `docs/specs/2026-10-20-data-hub-design.md` (§4.3, §6, §8.2, §15) and the binding visual spec `docs/design/2026-10-21-ui-redesign.md` with its mockup source `docs/design/2026-10-21-chat-mockup-a.dc.html`. Every implementer reads the design doc in full; the plan does not repeat its values.

## Global Constraints

- Colors come only from the design doc's token table. Never use `#0064A4`, `#0064a4` or `#FFD200`. Gold `#FECC07` appears only as the 3 px active-page bar in the side nav.
- Font: Source Sans 3, weights 400/600/700, self-hosted with `@fontsource/source-sans-3` pinned to exactly `5.3.0` (5.3.1 is under two weeks old). No Google Fonts link, no external URL of any kind in `index.html`, CSS or code.
- Behavior stays as built: routes, API calls, query keys, localStorage key `hub.chat.profileId`, and every role and accessible name a test relies on, unless a task below changes it and updates the test in the same commit.
- Buttons: `textTransform: "none"`, weight 600, at least 40 px tall, 44 px for the main ones. Corner radii, sizes and spacing exactly as the design doc's "Type and shape" section.
- Every clickable element has a hover state and a visible keyboard focus ring: 2 px `#255799`, 2 px offset. On the navy side nav, UCI Blue is not visible, so the nav's ring is 2 px `#FFFFFF` (Task 2 records this clarification in the design doc).
- Exact copy (no paraphrase):
  - placeholder `Ask a question about your data`
  - empty conversation `Ask a question about your data to start.`
  - switch label `Let AI see the results`
  - helper on `On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI.`
  - helper off `Off: the AI sees only your question. You get the results without an AI summary.`
  - disabled tooltip `This AI model isn't allowed to receive results. Change it in Settings.`
  - below the box `AI can make mistakes. Double-check important answers.`
  - SQL bar `Show the SQL query`; downloads `Download Excel (.xlsx)` and `Download CSV (.csv)`; nav toggle `Collapse navigation` / `Expand navigation`; nav footer `Signed in as {display_name}` or `Not connected`.
- S4/S5 patterns: MUI 9 `Stack` layout props go in `sx`; `fetch` only inside `src/api/` (oxlint enforces it); Vitest client mocks keep the real `ApiError` (`importOriginal`); upload cards live in `UploadProvider`.
- Never commit an import into the dev DB (`hub`, port 5432): A1 and the benchmark depend on its 293 rows. Anything that imports or needs an empty database runs on the disposable `hub-replay` stack.
- Synthetic data only. Screenshots come from the sample exports and the Demo profile or the dev DB's synthetic rows.
- Never read or print `project/.env`. Check a variable with `grep -c '^NAME=.' .env`.
- Commits: one per task (more if a task touches unrelated things), staged by path, Conventional Commits, ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Run the task's tests plus `npm run lint` and `npm run build` (frontend) or `uv run ruff check . && uv run ruff format --check .` (backend) before committing.

## Review Focus

1. **Narrow windows and long unbroken text.** At 1024×768, with a 300-character question that has no spaces, the chat page has no horizontal page scroll and the bubble wraps. Owner: Task 3 (Playwright check in `e2e/happy-path.spec.ts`).
2. **Keyboard-only use of the question box.** Tab goes Question → "Let AI see the results" → Send, and each shows the focus ring. Owner: Task 5 (Vitest tab-order test).
3. **Collapsed nav.** In the 72 px rail every link keeps its accessible name and `title`, and the current page keeps `aria-current="page"`. Owner: Task 2 (Vitest).
4. **A profile that disallows sharing.** The switch is off and disabled, and the helper shows the Off text even if the previous profile had it on. Owner: Task 5 (Vitest).
5. **Failed turns in the new card.** A live and a saved failed turn both keep the alert, Retry (disabled while streaming) and the "Show the SQL query" bar. Owner: Task 4 (Vitest).

---

## Part 1: The redesign

### Task 1: Theme, tokens and the self-hosted font

**Files:**
- Modify: `frontend/package.json`, `frontend/package-lock.json` (add `@fontsource/source-sans-3@5.3.0`, exact)
- Modify: `frontend/src/main.tsx` (import `@fontsource/source-sans-3/400.css`, `600.css`, `700.css`)
- Modify: `frontend/src/app/theme.ts`
- Create: `frontend/src/app/theme.test.ts`

**Interfaces:**
- Produces: `tokens` (a `const` object whose keys are exactly the design doc's token names: `primary`, `gold`, `navy`, `ink`, `muted`, `page`, `selected`, `tableHead`, `border`, `divider`, `subtle`, `control`, `navMuted`, `navText`, each a hex string); `theme` (MUI theme); `gridSx: SxProps<Theme>` (the shared DataGrid look: bordered container radius 10, header row `tableHead` with `navy` 600 text, `divider` row lines, 15 px).

- [ ] **Step 1: Write the failing test** `theme.test.ts`:
  - `tokens.primary === "#255799"`, `tokens.gold === "#FECC07"`, `tokens.navy === "#1B3D6D"`, `tokens.ink === "#002244"`, `tokens.muted === "#555759"`.
  - `theme.palette.primary.main === tokens.primary`, `theme.palette.text.primary === tokens.ink`, `theme.palette.background.default === tokens.page`.
  - `theme.typography.fontFamily` starts with `"Source Sans 3"`; `theme.typography.fontSize === 16` (body 16 px; `htmlFontSize` stays 16).
  - `JSON.stringify(theme).toLowerCase()` contains neither `#0064a4` nor `#ffd200`.
- [ ] **Step 2:** `npm test -- --run src/app/theme.test.ts` fails (no `tokens` export).
- [ ] **Step 3: Implement** `theme.ts`: palette from `tokens` (primary, text primary `ink`, text secondary `muted`, background default `page`, divider `divider`); typography (Source Sans 3 stack, body 16 px, `h1` 28/700 `navy`, `button` 600 no transform); `shape.borderRadius: 8`; component overrides for `MuiButton` (min height 40, radius 8), `MuiCard`/`MuiPaper` outlined (radius 12, `border` color), `MuiOutlinedInput` (radius 8, `control` border), `MuiButtonBase` and `MuiCssBaseline` focus ring (`&.Mui-focusVisible` and `:focus-visible`: `outline: 2px solid #255799; outline-offset: 2px`), `text-wrap: pretty` on `p, li, h1, h2, h3, span, a`. Install the font with `npm install --save-exact @fontsource/source-sans-3@5.3.0` and import the three weights in `main.tsx`.
- [ ] **Step 4:** the theme test passes; `npm test -- --run` passes in full (no copy changed yet); `npm run build` passes and `dist/assets/` contains `source-sans-3` `.woff2` files; `grep -ri "fonts.googleapis\|fonts.gstatic" src index.html dist` prints nothing.
- [ ] **Step 5: Commit** `feat(ui): add the UCI palette tokens and self-hosted Source Sans 3`

### Task 2: Side nav that collapses, and a page header on every page

**Files:**
- Modify: `frontend/src/app/AppShell.tsx`, `frontend/src/app/AppShell.test.tsx`
- Create: `frontend/src/app/PageHeader.tsx`, `frontend/src/app/PageHeader.test.tsx`
- Modify: `frontend/src/features/chat/ChatPage.tsx`, `frontend/src/features/upload/UploadPage.tsx`, `frontend/src/features/dataset/DatasetPage.tsx`, `frontend/src/features/settings/SettingsPage.tsx` (each renders `PageHeader`; their old `h5` titles go)
- Modify: `docs/design/2026-10-21-ui-redesign.md` ("Interaction states": the nav's ring is white)

**Interfaces:**
- Consumes: `tokens`, `theme` (Task 1).
- Produces: `PageHeader({ title, actions }: { title: string; actions?: ReactNode })`, default export of `src/app/PageHeader.tsx`: a white 88 px `header` element with a bottom `border` line, an `h1` with `title` on the left and `actions` on the right, padding 16/40, wrapping on narrow widths. Pages put their body below it with padding 28/40 (Chat has its own layout, Task 3). Chat's actions are the AI model select; Dataset's are the two full-dataset downloads; Settings' is "Add AI model" (only when profiles exist, as now); Upload has none.

- [ ] **Step 1: Write the failing tests** in `AppShell.test.tsx` (keep the two existing cases, changing the first to expect `Signed in as Ada Lovelace`):
  - `"collapses to an icon rail and expands again"`: the button `Collapse navigation` has `aria-expanded="true"`; after a click the button is named `Expand navigation` with `aria-expanded="false"`; the text `GPSRC Data Hub` and `Signed in as Ada Lovelace` are no longer visible; `getByRole("link", { name })` still resolves for `Chat`, `Upload`, `Dataset`, `Settings`, each with `title` equal to its name; clicking `Expand navigation` restores the labels.
  - `"marks the current page"`: rendered at `/upload` (memory router with the four child paths), the `Upload` link has `aria-current="page"` and the `Chat` link has none, in both the expanded and the collapsed state.
  - `PageHeader.test.tsx`: `render(<PageHeader title="Dataset" actions={<button>Go</button>} />)` gives `getByRole("heading", { level: 1, name: "Dataset" })` and the `Go` button.
- [ ] **Step 2:** `npm test -- --run src/app` fails.
- [ ] **Step 3: Implement** per the design doc's "Shell (`AppShell`)" section: no `AppBar`; a 248 px navy nav (`aria-label="Main navigation"`, sticky, full viewport height) with the 88 px brand block, the borderless 40×40 toggle, icon+label `NavLink`s (active: 3 px gold left border, `rgba(255,255,255,0.10)` background, white 600; inactive `navText`), and the bottom line; collapsed is a 72 px rail with icons only, each link keeping `aria-label` and `title`. Collapse state is `useState` in `AppShell` (memory only). The nav's focus ring is white. Main area: `flex: 1, minWidth: 0`, `bgcolor: tokens.page`, the `Suspense` fallback kept. Move each page's title and actions into `PageHeader`. Edit the design doc's "Interaction states" line to say the side nav uses a 2 px white ring because UCI Blue is not visible on navy.
- [ ] **Step 4:** `npm test -- --run` passes in full (fix any page test that looked for the old `h5` by role; titles keep their text); `npm run lint`, `npm run build` pass.
- [ ] **Step 5: Commit** `feat(ui): add the collapsible navy side nav and page headers`

### Task 3: Chat layout, conversation column and question bubbles

**Files:**
- Modify: `frontend/src/features/chat/ChatPage.tsx`, `ConversationList.tsx`, `Thread.tsx`, `ProfileSelect.tsx`
- Test: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `frontend/e2e/happy-path.spec.ts` (Review Focus 1)

**Interfaces:**
- Consumes: `PageHeader` (Task 2), `tokens`.
- Produces: no new exports. `ProfileSelect` keeps its props; `ChatPage` keeps `Composer`/`ShareResultsSwitch` wiring for Task 5.

- [ ] **Step 1: Write the failing tests** (`ChatPage.test.tsx`):
  - the draft with a profile shows `Ask a question about your data to start.` (replaces the old text; update the existing assertion at the "no profiles" case to the new text too);
  - the header shows a visible `AI model` label and `getByRole("combobox", { name: "AI model" })` still resolves to exactly one element;
  - the selected conversation link (`/chat/7` with conversation 7 in the list) has `aria-current="page"`; the list has no heading named `Conversations` (`queryByRole("heading", { name: "Conversations" })` is null) while `getByRole("navigation", { name: "Conversations" })` still resolves.
- [ ] **Step 2:** the new assertions fail.
- [ ] **Step 3: Implement** per the design doc's "Chat page": `PageHeader title="Chat"` with the `AI model` label (15/600 `muted`) and the select (MUI select kept for behavior; chevron icon via `IconComponent`, 600 weight, min width 200, `control` border); body is a row of the 256 px white conversation column (`nav aria-label="Conversations"`, sticky at the top with its own scroll, "New chat" 44 px outlined that fills UCI Blue on hover and focus in 120 ms, items radius 8 padding 10/12, selected `selected` background with navy 600 text, 15 px) and the thread section. The thread is centered at max 880 px, padding 28/40, 12 px inside a question–answer pair and 32 px between pairs. User bubble: right-aligned, UCI Blue, white text, max 75%, radius `18px 18px 4px 18px`, `overflowWrap: "anywhere"`; clarification bubble: left-aligned, white with a `border` line, radius `18px 18px 18px 4px`. The whole page scrolls (window), so full-page screenshots keep the whole thread.
- [ ] **Step 4: Add the Review Focus 1 check** to the end of `e2e/happy-path.spec.ts`: `await page.setViewportSize({ width: 1024, height: 768 })`, send `"x".repeat(300)` (the Demo model answers with its "only knows its scripted questions" clarification), wait for that text, then `expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)`.
- [ ] **Step 5:** `npm test -- --run`, `npm run lint`, `npm run build` pass; `npm run e2e` passes (needs Docker; it builds its own stack).
- [ ] **Step 6: Commit** `feat(chat): restyle the chat layout, conversation list and bubbles`

### Task 4: Answer card, result table and the SQL bar

**Files:**
- Modify: `frontend/src/features/chat/AnswerCard.tsx`, `SqlAccordion.tsx`, `ResultGrid.tsx`, `Thread.tsx` (failed-turn layout), `StepIndicator.tsx` (styling only)
- Test: `frontend/src/features/chat/AnswerCard.test.tsx`, `ChatPage.test.tsx` (button names), create `frontend/src/features/chat/ResultGrid.test.ts`
- Modify: `frontend/e2e/screenshots.spec.ts` (`{ name: "SQL", exact: true }` becomes `{ name: "Show the SQL query" }`)

**Interfaces:**
- Consumes: `tokens`, `gridSx` (Task 1).
- Produces: `columnsFor(result: QueryResultOut): GridColDef[]` exported from `ResultGrid.tsx`. A column is numeric when it has at least one non-null value and every non-null value is a `number`; numeric columns get `align: "right"`, `headerAlign: "right"` and a class that sets `font-variant-numeric: tabular-nums`. Values are not reformatted (a year stays `2026`, not `2,026`), so do not use `type: "number"`.

- [ ] **Step 1: Write the failing tests:**
  - `ResultGrid.test.ts`: `columnsFor({ columns: ["school", "people"], rows: [["Eng", 7], [null, 3]], row_count: 2, truncated: false })` gives `align` `undefined`/left for `school` and `"right"` for `people`; a column of all `null` is not numeric; a column mixing `"7"` and `7` is not numeric.
  - `AnswerCard.test.tsx`: replace `.xlsx`/`.csv` names with `Download Excel (.xlsx)` and `Download CSV (.csv)` (the existing click → `apiDownload("/api/chat/turns/4/export?format=xlsx")` assertions stay); replace `{ name: "SQL" }` with `{ name: "Show the SQL query" }`, which has `aria-expanded="false"` and no SQL text in the DOM until clicked, then shows the SQL and `Copy`; the truncated notice reads `Showing the first 1000 rows. Download the file to get all rows.`; `"orders the sections"`: for an LLM answer with result, interpretation and SQL, the caption `AI-generated summary. Check it against the table.` precedes the grid, which precedes the heading `How I read your question`, which precedes the SQL bar, which precedes `1 row`, which precedes `Download Excel (.xlsx)` (`compareDocumentPosition`).
  - Review Focus 5 (`ChatPage.test.tsx` or `AnswerCard.test.tsx`, where the existing failed-turn cases live): a saved `kind: "error"` turn with SQL and a live turn ending in an `error` event each show the error text, a `Retry` button and a `Show the SQL query` button; while another question streams, both `Retry` buttons are disabled.
  - Update `ChatPage.test.tsx` uses of `{ name: "SQL" }` to the new name.
- [ ] **Step 2:** the new assertions fail.
- [ ] **Step 3: Implement** per the design doc's "Answer card": white card, `border` line, radius 12, padding 24, sections 20 px apart, in the doc's order; summary 18 px with the 13 px `muted` caption only when the analysis is the LLM's; the grid wrapped with `gridSx`; "How I read your question" as an `h2` at 16/700 navy with bullets; the SQL bar as a full-width 44 px `subtle` bar, radius 10, chevron, collapsed by default (keep `unmountOnExit`), `Copy` inside; footer with a top `divider` line: `{n} rows` (`1 row`) left, the two download buttons right (Excel filled, CSV outlined, both with a download icon, no "Export" label). "Show results", "Loading results…", "Re-run on current data" and the result-error alert stay in the table's slot. Failed turns: the alert with `Retry`, then the SQL bar.
- [ ] **Step 4:** `npm test -- --run`, `npm run lint`, `npm run build` pass. `npm run e2e` passes (its `.xlsx` lookup is a substring match, so `Download Excel (.xlsx)` resolves).
- [ ] **Step 5: Commit** `feat(chat): restyle the answer card, result table and SQL bar`

### Task 5: Question box with the share switch inside it

**Files:**
- Modify: `frontend/src/features/chat/Composer.tsx`, `ShareResultsSwitch.tsx`, `ChatPage.tsx`
- Create: `frontend/src/features/chat/Composer.test.tsx`
- Test: `frontend/src/features/chat/ChatPage.test.tsx`
- Modify: `docs/specs/2026-10-20-data-hub-design.md` §8.2 "Selection" (drop the sentence "Until S6 ships, the S4 text … is shown.")

**Interfaces:**
- Consumes: `tokens`.
- Produces: `Composer({ disabled, onSend, toolbar }: { disabled: boolean; onSend: (question: string) => boolean; toolbar?: ReactNode })`. `toolbar` renders at the left of the row under the textarea; Send is at its right. `ShareResultsSwitch` keeps its props (`checked`, `allowed`, `onChange`).

- [ ] **Step 1: Write the failing tests:**
  - `Composer.test.tsx`: the textbox `Question` has placeholder `Ask a question about your data`; `AI can make mistakes. Double-check important answers.` is shown; Enter sends the trimmed text and clears it; Shift+Enter adds a newline; a 2,001-character question shows `2,001 / 2,000 characters. Shorten your question.` and disables Send; `onSend` returning `false` keeps the text; the textbox, the `toolbar` content and `Send` are inside one element with `data-testid="question-box"`.
  - Review Focus 2 (`ChatPage.test.tsx`): with a sharing profile, focus the textbox, then `user.tab()` focuses `getByRole("switch", { name: "Let AI see the results" })`, and another `user.tab()` focuses `Send`.
  - `ChatPage.test.tsx`: the switch on shows the On helper text and its `aria-describedby` element holds that text; after a click the Off helper text shows; `getAllByLabelText("Let AI see the results")` has length 1; replace the old helper assertion (`Off: AI only writes the SQL…`) with the new Off text.
  - Review Focus 4 (`ChatPage.test.tsx`): select a sharing profile and leave the switch on, then pick a profile with `share_results_with_llm: false`: the switch is disabled and not checked, the Off helper text shows, and hovering shows the unchanged tooltip.
- [ ] **Step 2:** the new assertions fail.
- [ ] **Step 3: Implement** per the design doc's "Composer": a white band with a top `border` line, padding 16/40/12, sticky at the bottom, centered at 880 px; the question box (`data-testid="question-box"`, 1 px `control` border, radius 12, padding 12/12/10/16; focus-within shows the UCI Blue ring) holds a borderless 2-row textarea (keep `aria-label="Question"`, max 8 rows) and the toolbar row (switch block left, 40 px filled Send right). `ShareResultsSwitch`: a restyled MUI `Switch` (40×22 track, UCI Blue on, `#555759` off, 16 px white knob; MUI 9 renders `role="switch"`), labeled `Let AI see the results` (600), with the helper (14 px, `muted`) chosen by the effective state (`allowed && checked`) and wired by `aria-describedby`; the disabled tooltip wrapper stays. The disclaimer line sits under the box, centered, 13 px `muted`. In `ChatPage`, pass `<ShareResultsSwitch …/>` as `toolbar`. Update spec §8.2.
- [ ] **Step 4:** `npm test -- --run`, `npm run lint`, `npm run build` pass; `npm run e2e` passes (`getByLabel("Let AI see the results")` resolves to one element and is checked after the follow-up).
- [ ] **Step 5: Commit** `feat(chat): put the share switch inside the question box with the new copy`

### Task 6: Upload, Dataset and Settings in the new style

**Files:**
- Modify: `frontend/src/features/upload/UploadPage.tsx`, `FilePreviewCard.tsx`, `CommitSummaryView.tsx`, `EventDetailsForm.tsx`
- Modify: `frontend/src/features/dataset/DatasetPage.tsx`
- Modify: `frontend/src/features/settings/SettingsPage.tsx`, `ProfileList.tsx`, `ProfileForm.tsx`
- Test: `UploadPage.test.tsx`, `DatasetPage.test.tsx`, `ProfileList.test.tsx` (only where names change)

**Interfaces:**
- Consumes: `PageHeader`, `tokens`, `gridSx`. No new exports.

- [ ] **Step 1: Write the failing tests:** `DatasetPage.test.tsx`: `getByRole("heading", { level: 1, name: "Dataset" })`; the buttons `Download full dataset (.xlsx)` and `Download full dataset (.csv)` each have a download icon (`svg[data-testid="DownloadIcon"]` inside). `UploadPage.test.tsx`: `heading level 1 "Upload"`; the drop zone text `Drop CSV or Excel files here, or click to choose. (.csv, .xlsx, .xlsm)` is unchanged. Settings: `heading level 1 "Settings"`.
- [ ] **Step 2:** the icon assertion fails (the others may already pass after Task 2; that is fine).
- [ ] **Step 3: Implement** with the same shell, card (radius 12, `border` line, padding 24), button, input and table styles; structure stays as built. Upload: body max 720 px; drop zone with a 2 px dashed `control` border, radius 12, white, UCI Blue border and `selected` fill while dragging; status chips keep their labels. Dataset: the history grid uses `gridSx`; downloads in the header (xlsx filled, csv outlined, download icons). Settings: profile cards in the card style; "Default" chip in UCI Blue; the dialog keeps its fields and copy.
- [ ] **Step 4:** `npm test -- --run`, `npm run lint`, `npm run build`, `npm run e2e` pass.
- [ ] **Step 5: Commit** `feat(ui): restyle the Upload, Dataset and Settings pages`

## Part 2: S5 carry-overs

### Task 7: A pending import that no longer loads gets its file name, Try again and Discard

**Files:**
- Modify: `frontend/src/features/upload/useImports.ts` (`usePendingPreviews`)
- Create: `frontend/src/features/upload/UnloadableImportCard.tsx`
- Modify: `frontend/src/features/upload/UploadPage.tsx`
- Test: `frontend/src/features/upload/UploadPage.test.tsx`

**Interfaces:**
- Produces: `usePendingPreviews(ids: number[]): { previews: ImportPreview[]; failedIds: number[]; retry: (id: number) => void }`; `UnloadableImportCard({ importId, fileName, onRetry }: { importId: number; fileName: string; onRetry: () => void })`, which discards through `useDiscardImport` itself; `UploadPage` passes `onRetry={() => retry(id)}`.

- [ ] **Step 1: Write the failing tests** (`UploadPage.test.tsx`): history holds pending import 9, `Old.csv`, whose `GET /api/imports/9/preview` rejects with `new ApiError(422, "unknown_format", "…")`:
  - a card shows `Old.csv` and `Could not load this pending import. Try again, or discard it and upload the file again.`, with `Try again` and `Discard`; the old alert `Could not load a pending import. Reload the page to try again.` is gone;
  - `Discard` calls `apiSend("DELETE", "/api/imports/9")`; when the refetched history no longer lists 9, the card is gone;
  - `Try again` refetches the preview; when it now resolves, the normal preview card for `Old.csv` replaces the error card.
- [ ] **Step 2:** the tests fail.
- [ ] **Step 3: Implement.** The file name comes from the history row (`ImportFileOut.file_name`). The error card uses the card style with an error-colored message, `Try again` (outlined) and `Discard` (`color="inherit"`), and shows the discard error if DELETE fails.
- [ ] **Step 4:** `npm test -- --run`, lint, build pass.
- [ ] **Step 5: Commit** `fix(upload): give an unloadable pending import its file name, Try again and Discard`

### Task 8: The preview counts a person listed twice in one file

**Decision (S6):** yes, the preview says so. Staff confirm the event details while reading the preview; a row that silently disappears between "38 rows" and "37 rows imported" looks like data loss. The commit stays authoritative, because it also knows people already in the database.

**Files:**
- Modify: `backend/app/imports/identity.py` (new pure function), `backend/app/imports/service.py` (`_preview_from`)
- Test: `backend/tests/imports/test_in_file_duplicates.py` (create), plus a preview case in the existing import service/API tests
- Modify: `docs/specs/2026-10-20-data-hub-design.md` §6 (after the `duplicate_in_event` sentence: "The preview's flag counts include `duplicate_in_event` for rows that repeat a person within the file under the same rules restricted to the file (NetID, then email, including the NetID-attach case), so staff see them before commit; the commit, which also knows people already in the database, is authoritative. (Decided in S6.)")

**Interfaces:**
- Produces: `count_in_file_duplicates(keys: Iterable[tuple[str | None, str | None]]) -> int` in `app/imports/identity.py`; `keys` are the parsed rows' normalized `(netid, email)` in file order. It applies `IdentityLinker`'s rules 1–4 to the file alone: a row repeats a person when its NetID was seen; or it has a NetID not seen and its email belongs to an in-file person with no NetID (attach); or it has no NetID and its email was seen. A row with neither is never a duplicate. Two rows with different NetIDs and one email are two people (the conflict case).

- [ ] **Step 1: Write the failing tests** (`test_in_file_duplicates.py`):
  - `[("ab1", "a@uci.edu"), ("ab1", "x@gmail.com")]` → 1
  - `[("ab1", "a@uci.edu"), (None, "a@uci.edu")]` → 1
  - `[(None, "a@uci.edu"), ("ab1", "a@uci.edu")]` → 1 (attach)
  - `[("ab1", "a@uci.edu"), ("cd2", "a@uci.edu")]` → 0 (conflict: two people)
  - `[(None, None), (None, None)]` → 0
  - `[("ab1", None), ("ab1", None), ("ab1", None)]` → 2
  - service/API: a CampusGroups CSV built from `sample_data/exports/Bagel Breakfast - October.csv` with its first attendee row appended again (renamed so it is a new file): the preview has `row_count` = original + 1 and `flag_counts["duplicate_in_event"] == 1`; committing it gives `duplicates_in_event == 1` and `inserted` = original. The original sample's preview has no `duplicate_in_event` key.
- [ ] **Step 2:** `uv run pytest tests/imports -q` fails.
- [ ] **Step 3: Implement** the function and, in `_preview_from`, `if n := count_in_file_duplicates((r.netid, r.email) for r in result.rows): counts["duplicate_in_event"] = n`. The frontend already labels the chip "Duplicate in this event".
- [ ] **Step 4:** `uv run pytest -q` passes in full; ruff check and format pass. Commits are unchanged, so A1/A2 must pass as they are. If an existing test asserts a sample's exact preview `flag_counts` and that sample repeats a person, update that expectation and say why in the commit body.
- [ ] **Step 5: Commit** `feat(import): count people listed twice in one file in the preview` (code, tests and the spec line together)

### Task 9: A dropped stream shows one card, not two

**Files:**
- Modify: `frontend/src/features/chat/chatStream.ts` (`LiveTurn`, `startTurn`), `useChatStream.ts`, `Thread.tsx`
- Test: `frontend/src/features/chat/chatStream.test.ts`, `useChatStream.test.tsx`, `ChatPage.test.tsx` (or a new `Thread.test.tsx`)
- Modify: `docs/specs/2026-10-20-data-hub-design.md` §4.3 (replace the "Known gap" sentence with the rule below, marked "(Fixed in S6.)")

**Interfaces:**
- Produces: `LiveTurn.afterSeq: number` (the highest saved `seq` in the cached conversation when the turn started; 0 for a new conversation); `startTurn(question: string, afterSeq: number): LiveTurn`.
- Rule: a live turn that ended in error **without** a `done` (`turnId === undefined`) takes the place of the first saved turn with `seq > afterSeq` and the same `question`; with no such saved turn it is appended last, as now. After a lost connection (`stream_interrupted`, `network_error`, `server_unavailable`) the hook invalidates `["conversation", id]` and `["conversations"]`, so the saved `client_disconnected` copy arrives and is absorbed.

- [ ] **Step 1: Write the failing tests:**
  - Thread: saved turns seq 1 (`"Q1"`), 2 (`"Q2"`) and 3 (`"Q3"`, `kind: "error"`, `error_code: "client_disconnected"`), live `{ question: "Q3", status: "error", error: { code: "stream_interrupted", message: "Connection lost. Retry." }, afterSeq: 2 }`: exactly one bubble `Q3`, `Connection lost. Retry.` shown once, and `This answer was interrupted before it finished.` absent.
  - Same, but saved seq 3 has question `"Other"`: both cards show (no adoption).
  - Same, but `afterSeq: 3` and saved seq 3 is `"Q3"` (an earlier identical question): no adoption; the live card is appended after it.
  - A live error turn with `turnId: null` (done arrived, turn not recorded) is appended, never adopted.
  - `useChatStream`: with `["conversation", 5]` cached holding seqs 1–4, `send` creates a live turn with `afterSeq: 4`; when `streamSse` rejects with `new ApiError(0, "network_error", …)`, `invalidateQueries` is called with `{ queryKey: ["conversation", 5] }` and `{ queryKey: ["conversations"] }`.
- [ ] **Step 2:** the tests fail.
- [ ] **Step 3: Implement** the rule. `afterSeq` is read in `run` from `queryClient.getQueryData<ConversationDetail>(["conversation", id])` (0 when the conversation is created by this send or not cached).
- [ ] **Step 4:** `npm test -- --run`, lint, build pass.
- [ ] **Step 5: Commit** `fix(chat): absorb a dropped answer's saved copy into its live card` (code, tests and the spec change together)

## Part 3: User stories and the walkthrough

### Task 10: Demo script entries the walkthrough needs

The Demo model knows four questions, which cannot show a slow answer, a refused query, a repair or a wide result. Add four entries.

**Files:**
- Modify: `backend/app/llm/fake.py` (`ScriptEntry.delay_seconds: float = 0`, applied before a `generate` reply, `asyncio.sleep` in `_agenerate`, `time.sleep` in `_generate`; analyze replies are not delayed)
- Modify: `backend/app/llm/fake_script.json`
- Test: the existing fake-model and fake-graph tests under `backend/tests/` (find them with `grep -rln ScriptedChatModel tests`)
- Modify: wherever the docs list the Demo questions (`grep -rn "fake_script\|scripted" ../docs ../README.md`)

**Interfaces:**
- Produces these Demo questions (matched case-insensitively as substrings), used by Tasks 12–13:

  | Question to type | Script | Expected outcome |
  |---|---|---|
  | `Demo slow question` | `delay_seconds: 10`, then the Bagel October count SQL | the step line shows for 10 s, then 38 |
  | `Demo refused query` | always `DELETE FROM attendance_view` | after 3 attempts, error `sql_rejected` with the SQL shown |
  | `Demo repaired query` | first `SELECT COUNT(*) AS n FROM attendance_view WHERE campus = 'UCI'`, then `SELECT COUNT(*) AS n FROM attendance_view` | "Fixing the query (attempt 2)", then an answer (`attempts == 2`) |
  | `Demo all columns` | `SELECT * FROM attendance_view WHERE event_name = 'Bagel Breakfast, October'` | 17 columns, 38 rows |

- [ ] **Step 1: Write the failing tests:** a fake-model unit test that a `delay_seconds: 2` entry awaits `asyncio.sleep(2)` once for generate and not for analyze (monkeypatch `asyncio.sleep`); graph tests with the fake on the sample data: `Demo refused query` → `kind == "error"`, `error_code == "sql_rejected"`, `sql` contains `DELETE`, `attempts == 3`; `Demo repaired query` → `kind == "answer"`, `attempts == 2`; `Demo all columns` → 17 columns, `row_count == 38`. If a test checks that Demo questions stay disjoint from the benchmark, it must still pass.
- [ ] **Step 2:** the tests fail.
- [ ] **Step 3: Implement.** If the guard refuses `SELECT *` or the repair path does not take the unknown-column error, change the scripted SQL, not the guard or the graph.
- [ ] **Step 4:** `uv run pytest -q`, ruff check and format pass.
- [ ] **Step 5: Commit** `feat(llm): add Demo questions for slow, refused, repaired and wide answers`

### Task 11: Write every user story

**Files:**
- Create: `docs/user-stories/README.md` (format, the two stacks and their recipes, how to record a walk), `shell.md`, `chat.md`, `upload.md`, `dataset.md`, `settings.md`
- Create: `scripts/story_files.py` (writes the synthetic edge-case files into a directory given as its only argument; nothing it writes is committed)
- Modify: `CLAUDE.md` (layout line for `scripts/`, and the command `uv run --project backend python scripts/story_files.py <out_dir>`)

**Story format** (each story is a `###` heading `<ID> <title>`):

```markdown
### UP-15 A file lists the same person twice
- **Who:** a GPSRC student worker entering an event
- **Story:** As a student worker, I want the preview to tell me when a file lists someone twice, so that the imported count does not surprise me.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - The preview card shows "Duplicate in this event: 1".
  - After Commit, the summary shows "Duplicates in event 1" and one row fewer imported than previewed.
- **Walk:**
  1. Run `scripts/story_files.py` and upload `Duplicate Person.csv`.
  2. ...
```

Acceptance criteria describe the behavior a user should get, from the spec and the design doc, not whatever the code does today; the walk finds the gaps.

**`scripts/story_files.py <out_dir>`** writes, from `backend/sample_data/exports/`:
- `Header Only.csv`: the header row of `Bagel Breakfast - October.csv`;
- `Unknown Format.csv`: a CSV with headers `Name,Mail,Event`;
- `Notes.txt`: one line of text;
- `Bagel Breakfast - October (copy).csv`: the October CSV with its line endings switched (new bytes, same grid);
- `Duplicate Person.csv`: `Postdoc Wellness Lunch.csv` with its first attendee row appended again;
- `Pending Then Broken.csv`: `Cover Letters for Academic Jobs.csv` renamed, for UP-14 (its stored bytes are overwritten in the replay db after upload; see the story).

**Stories to write** (IDs fixed; add more if the spec implies a state none of these covers):

| Page | IDs and titles | Stack |
|---|---|---|
| Shell | SH-01 move between pages; SH-02 collapse and expand the nav; SH-03 keyboard only (focus ring everywhere, including the nav); SH-04 signed-in name, and "Not connected" when the API is down; SH-05 an address that does not exist (`/foo`); SH-06 a page that fails to load after a rebuild; SH-07 a small laptop screen (1280×720 and 1024×768) | replay |
| Chat | CH-01 first question in a new chat; CH-02 follow-up; CH-03 clarifying question; CH-04 read and copy the SQL; CH-05 download Excel and CSV; CH-06 more rows than the screen shows, and an export cap (`DISPLAY_ROW_CAP=20`, `EXPORT_ROW_CAP=30`); CH-07 a wide result (`Demo all columns`); CH-08 "Let AI see the results" on and off, kept for follow-ups, reset on new chat and profile change; CH-09 a profile that may not receive results; CH-10 switch AI model, remembered after reload; CH-11 reopen an old conversation and show its results again; CH-12 a refused query; CH-13 a repaired query; CH-14 the connection drops mid-answer (`Demo slow question`, then go offline or stop `api`); CH-15 the server is down when asking; CH-16 long, multi-line and too-long questions, Enter vs Shift+Enter, sending while an answer streams; CH-17 no AI model yet; CH-18 a conversation link that no longer exists (`/chat/99999`, `/chat/abc`); CH-19 many conversations and a long thread; CH-20 answer quality on five sponsor-style questions with a follow-up and "last term", sharing on and off; CH-21 the AI provider rejects the key | CH-03, CH-20, CH-21 also main; the rest replay |
| Upload | UP-01 CampusGroups export; UP-02 12twenty export with skipped rows; UP-03 several files at once; UP-04 a file already imported; UP-05 a re-saved copy; UP-06 the same pending file again; UP-07 an unknown format; UP-08 a header-only export; UP-09 an unsupported file type; UP-10 a file over the size limit (`MAX_UPLOAD_BYTES=20000`); UP-11 fix event details before Commit (term, required fields); UP-12 leave the page mid-form and come back, then reload; UP-13 discard a pending import; UP-14 a pending import that no longer loads; UP-15 a person listed twice; UP-16 rows missing NetID or email (flags); UP-17 the server is down at Commit; UP-18 the server is down while uploading | replay |
| Dataset | DS-01 see what has been imported; DS-02 download the full dataset (19 columns, Notes); DS-03 nothing imported yet; DS-04 a pending import links to Upload; DS-05 a download fails | replay |
| Settings | ST-01 add the first AI model; ST-02 each provider preset (URL prefill, sharing default); ST-03 test a connection (pass, fail); ST-04 edit without re-entering the key, then change it; ST-05 a name already used; ST-06 make another model the default; ST-07 delete a model, the default, and the last one; ST-08 turn result sharing off; ST-09 a base URL with a username and password | replay; ST-03 pass on main |

- [ ] **Step 1:** Write `scripts/story_files.py` and run it into the scratchpad; check `Header Only.csv` has one line and `Duplicate Person.csv` has one more line than its source.
- [ ] **Step 2:** Write `README.md` and the five story files. The README holds both stack recipes:
  - **replay (Demo):** from `project/`, `HUB_HTTP_PORT=8083 HUB_ENABLE_FAKE_LLM=true LLM_SEED_NAME= LLM_SEED_PRESET= LLM_SEED_BASE_URL= LLM_SEED_MODEL= LLM_SEED_API_KEY= LLM_SEED_SHARE_RESULTS= docker compose -p hub-replay -f docker-compose.yml up -d --build`; create the Demo profile with `POST /api/llm-profiles {"name":"Demo","preset":"fake","model":"scripted"}` and make it the default; load samples when a story needs them with `docker compose -p hub-replay exec api python -m app.samples`; restart only `api` with changed caps for CH-06 and UP-10; `docker compose -p hub-replay down -v` at the end.
  - **main (DeepSeek):** `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d` at 127.0.0.1:8080, profile "DeepSeek"; no uploads committed there.
- [ ] **Step 3:** Check every ID in the table has a story, and every story has who, story, stack, acceptance criteria and walk steps (`grep -c '^### ' docs/user-stories/*.md`).
- [ ] **Step 4: Commit** `docs(stories): write the S6 user stories and the edge-file script`

### Task 12: Walk the Shell and Chat stories on the replay stack

**Files:**
- Create: `docs/user-stories/walkthrough-2026-10-21.md`
- Create: `docs/user-stories/screenshots/` (PNG, 1440×900 unless the story is about size; only where a picture shows something the text cannot)

**Record format:** one table per page, `| ID | Result | Notes | Screenshot |`, Result one of `Pass`, `Fail → W-n`, `Covered by <test file>` (only when the state cannot be produced in the running app, with the reason). Then a "Findings" list: `W-n (<story IDs>) <severity: blocker | major | minor | cosmetic>: what happened; expected; status`. Status is filled in by Task 15.

- [ ] **Step 1:** Bring up the replay stack (README recipe) and load the samples (chat stories need Bagel Breakfast, October).
- [ ] **Step 2:** Walk SH-01…SH-07 and every Chat story marked replay, step by step, in a real browser (the Playwright MCP tools, or a throwaway Playwright script in the scratchpad). Do not fix anything; record.
- [ ] **Step 3:** `docker compose -p hub-replay down -v`.
- [ ] **Step 4: Commit** `docs(stories): record the shell and chat walkthrough`

### Task 13: Walk the Upload, Dataset and Settings stories on the replay stack

**Files:** Modify `docs/user-stories/walkthrough-2026-10-21.md`, add screenshots.

- [ ] **Step 1:** Fresh replay stack, **no samples** at first (DS-03, ST-01 and UP-01 need empty tables); load the samples only when a story says so.
- [ ] **Step 2:** Walk every Upload, Dataset and Settings story marked replay, with the files from `scripts/story_files.py`. UP-14: upload `Pending Then Broken.csv`, leave it pending, overwrite its stored bytes (`UPDATE hub.import_file SET content = 'not a spreadsheet' WHERE file_name = 'Pending Then Broken.csv'` through `psql` in the replay `db` container), then reload `/upload`.
- [ ] **Step 3:** `docker compose -p hub-replay down -v`.
- [ ] **Step 4: Commit** `docs(stories): record the upload, dataset and settings walkthrough`

### Task 14: Walk the main-stack stories with DeepSeek

**Files:** Modify `docs/user-stories/walkthrough-2026-10-21.md`, add screenshots.

- [ ] **Step 1:** Rebuild the main stack with the current code (README recipe). Check `GET /api/imports` still reports the 10 committed sample files, and commit nothing.
- [ ] **Step 2:** Walk CH-03, CH-20, CH-21 and ST-03 (pass) with "DeepSeek". CH-21 uses a temporary profile "Bad key" (preset DeepSeek, key `sk-invalid`), deleted at the end. For CH-20, record each question, the SQL's reading, the summary and whether the table supports the summary.
- [ ] **Step 3:** Leave the main stack running. Check `GET /api/llm-profiles` lists only "DeepSeek" and "DeepSeek Pro" again.
- [ ] **Step 4: Commit** `docs(stories): record the main-stack walkthrough`

### Task 15: Fix the walkthrough findings

The controller turns each finding into a fix (grouping findings that share code), ordered by severity. Each fix follows TDD where the behavior is testable (a failing Vitest or pytest case first), keeps the Global Constraints, and is its own commit (`fix(<area>): …`). A finding not fixed gets a reason (out of scope, needs a sponsor decision, backlog) in the walkthrough's Findings list and, if it affects users, a line in `docs/known-limitations.md`.

- [ ] **Step 1:** For each fix: failing test, fix, `npm test -- --run` / `uv run pytest -q`, lint, build, commit.
- [ ] **Step 2:** Re-walk every story a fix touched (replay or main as the story says), update its row and the finding's status (`Fixed in <short sha>` or `Left: <reason>`).
- [ ] **Step 3:** `npm run e2e` passes.
- [ ] **Step 4: Commit** the walkthrough record update: `docs(stories): record the re-walk after the fixes`

## Part 4: Docs, screenshots and exit

### Task 16: Regenerate the screenshots and refresh the guides

**Files:**
- Modify: `frontend/e2e/screenshots.spec.ts` (keep `01-upload-preview.png` … `05-settings.png`; add `06-dataset.png` after the commit step and `07-nav-collapsed.png` on `/chat` with the nav collapsed)
- Modify: `docs/screenshots/*.png` (regenerated by `npm run e2e:screenshots`)
- Modify: `README.md` (one screenshot, `docs/screenshots/03-chat-answer.png`, under the intro)
- Modify: `docs/user-guide.md`: screenshots in the Upload, Chat, Dataset and Settings sections; the placeholder text; "SQL" → "Show the SQL query"; the Export paragraph → **Download Excel (.xlsx)** and **Download CSV (.csv)** (drop the "(The redesign relabels …)" note); "Export to get them all" → "Download the file to get them all"; the switch helper texts (On and Off, exact copy); the collapsible nav; the "AI can make mistakes" line.
- Modify: `docs/specs/2026-10-20-data-hub-design.md` §4.3 if the walkthrough fixes changed a behavior the spec states.

- [ ] **Step 1:** Update the screenshots spec; run `npm run e2e:screenshots`; open each PNG and check it shows the new design with synthetic data only.
- [ ] **Step 2:** Update README and the user guide; `grep -n "\.xlsx\`\|Export\*\*\|attendance data\|Off: AI only" docs/user-guide.md README.md` prints nothing stale.
- [ ] **Step 3: Commit** `docs: regenerate the screenshots and refresh the guides for the redesign`

### Task 17: Final verification and PROGRESS

Run after the controller's final whole-branch review and its fix wave.

- [ ] **Step 1:** From `project/`: `bash scripts/acceptance.sh` exits 0 (every row PASS except A7 deferred).
- [ ] **Step 2:** With the main stack up: `HUB_E2E_PROFILE="DeepSeek" npm run e2e:timing` passes (both Playwright runs green, as the S6 exit requires).
- [ ] **Step 3:** Rewrite `PROGRESS.md` per Rule #2 (S6 done; state of the code and test counts; next steps: the sponsor demo checklist, the open issues; the S6 decisions: the nav's white focus ring, the preview's in-file duplicates, the dropped-stream rule, the Demo questions; one log line). Update `CLAUDE.md` if any command or layout changed.
- [ ] **Step 4: Commit** `docs(progress): end of S6`
