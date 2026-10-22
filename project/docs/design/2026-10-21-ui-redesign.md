# UI redesign: "Campus blue and gold"

- **Date:** 2026-10-21. Approved by the user after S4 and built in **S6**.
- **Mockup:** https://claude.ai/artifact/Xbq6MdmGMZdmT39wnmBQfs. The first artboard, "A. Campus blue and gold", is the approved design. Press Play on it to try the nav collapse, the hover states and the share switch.
- **Revision (2026-10-21, after S6):** the artboard "A2. Conversations in the nav" on the same canvas is approved and supersedes A for the shell and the Chat page: recent questions in a 280 px side nav whose first link is "New chat", a slim "Answering with" row instead of the Chat page header, a caution line on every summary, no line under the question box, and a shell that fills the window so the nav and the question box never move. The sections below describe A2 where it differs from A.
- **Revision (2026-10-22):** the model row became a white bar with a bottom border (artboard "D2. White bar with a line, like the other page headers", chosen over a bare line and a line shown only after scrolling). Before, the conversation scrolled under a row of the same color, so text was cut at an invisible edge.
- **Mockup source:** `2026-10-21-chat-mockup-a.dc.html` (A) and `2026-10-21-chat-mockup-a2.dc.html` (A2) in this folder. They render only inside the Design artifact, but every exact value (color, size, spacing, copy) is written in its inline styles, so read it as the reference when a value below is unclear.
- **Scope:** visual design and copy only. Every behavior, API call and test-relevant role stays as built in S4 (spec §4.3 "Details settled in S4").

## Why this direction

Three directions were mocked on the chat screen:

- **A. Campus blue and gold:** chosen.
- **B. Calm reading column:** a single centered column with Atkinson Hyperlegible.
- **C. Split data desk:** chat on the left and a large results pane on the right.

A was chosen because it reads like uci.edu, so the sponsor recognizes it as a UCI tool, and because it changes the S4 layout the least.

Three layouts for the question box were then compared:

1. **Toolbar inside the question box:** chosen.
2. **Warning on each answer.**
3. **Compact left-aligned lines.**

Option 1 was chosen because the switch only affects the next question, so it belongs inside the question box, and it is the most compact.

## Color

The colors come from the official UCI palette (https://brand.uci.edu/identity/colors.php, checked 2026-10-21). UCI Blue and Gold are `#255799` and `#FECC07`. The older `#0064A4` / `#FFD200` values are outdated; do not use them.

The guide's rules:

- UCI Blue is the main color and Gold is the complement.
- Secondary colors are always paired with a primary color.
- Accent colors (orange, magenta, green, …) are not used.

| Token | Hex | Official name | Use |
|---|---|---|---|
| primary | `#255799` | UCI Blue | primary buttons, user question bubbles, switch on, links, focus ring, the A design's "New chat" hover fill |
| gold | `#FECC07` | UCI Gold | **only** the 3 px active-page bar in the side nav |
| navy | `#1B3D6D` | Dark Blue | side nav background, page titles, section headings, table header text, selected conversation text |
| ink | `#002244` | Darkest Blue | body text, text on light buttons |
| muted | `#555759` | Dark Gray | secondary text, helper text, row counts, switch off track |
| page | `#F3F6FA` | tint of UCI Blue | page background behind the thread |
| selected | `#E4ECF6` | tint | selected conversation |
| tableHead | `#EDF2F8` | tint | table header row |
| border | `#D3DCE8` | tint | card, header and column borders |
| divider | `#E3E9F1` | tint | table row lines, card footer line |
| subtle | `#F6F8FB` | tint | the "Show the SQL query" bar |
| control | `#7B8FAE` | tint | input, select and outlined-button borders |
| navMuted | `#C9D6E8` | tint | subtitle, "Signed in as", collapse icon |
| navText | `#DCE5F1` | tint | inactive nav links |

The tints are lightened UCI Blue. The palette has no tints, and the guide allows lightening for web contrast.

Contrast is checked:

- white on `#255799`: 7.2:1;
- `#002244` on white and on `#FECC07`: about 10:1 or more;
- `#555759` on white: 7.3:1;
- `#7B8FAE` borders on white: 3.3:1, which passes the 3:1 rule for UI components;
- `#C9D6E8` on `#1B3D6D`: 7.3:1.

## Type and shape

- **Typeface:** Source Sans 3 at weights 400, 600 and 700. Self-host it with `@fontsource/source-sans-3`. Never load it from Google Fonts: the app runs locally and must not call outside sites.
- **Sizes:**

  | Text | Size and weight |
  |---|---|
  | body | 16 px |
  | page title | 28 px / 700, navy |
  | wordmark | 19 px / 700, one line |
  | answer summary | 18 px |
  | table | 15 px |
  | recent questions | 15 px |
  | helper | 13–14 px |

  Text uses `text-wrap: pretty` (no orphan words). Table numbers are right-aligned and use `tabular-nums`.
- **Corner radius:** 8 px for buttons, inputs, selects and list items; 10 px for the table container and the SQL bar; 12 px for cards and the question box; 18 px for chat bubbles, with a 4 px corner on the speaker's side.
- **Buttons:** no all-caps (MUI `textTransform: "none"`). Buttons are 600 weight, at least 40 px tall, and 44 px for the main ones.
- **Interaction states:** every clickable element has a hover state and a visible keyboard focus ring (2 px UCI Blue, 2 px offset). The side nav uses a 2 px white ring instead, because UCI Blue is not visible on navy. Text fields and selects show focus with their 2 px UCI Blue field border instead of the offset ring (decided in S6, W-3).

## Shell (`AppShell`)

- **Top bar:** none. The left nav carries the brand.
- **Window:** the shell fills the window (`100dvh`) and the page itself never scrolls or rubber-bands (`overscroll-behavior: none` on `html` and `body`). The side nav runs the full height; the main area scrolls on its own (on Chat, only the conversation pane does).
- **Side nav:** 280 px wide, navy background.
  - **Brand block:** 88 px tall, the same height as the page header. It holds "GPSRC Data Hub" (19 px / 700, never wraps) and below it "Graduate & Postdoctoral Scholar Resource Center" (13 px, navMuted).
  - **Collapse button:** to the right of the wordmark. It is a 40×40 icon button with **no border**: icon navMuted at rest; on hover or focus, a `rgba(255,255,255,0.12)` background and a white icon. Its `aria-label` and title are "Collapse navigation" or "Expand navigation", with `aria-expanded` set.
  - **Collapsed state:** a 72 px rail with icons only. Each link keeps an `aria-label` and a hover title. The state is kept in memory only, not in localStorage (localStorage holds only the last selected profile id).
  - **Nav links:** New chat, Upload, Dataset and Settings, each icon plus label (New chat keeps the chat icon). "New chat" opens the `/chat` draft and is the current page only there; an open conversation `/chat/:id` is marked in Recent questions instead, so no page link is current then.
    - Active: a 3 px gold left border, a `rgba(255,255,255,0.10)` background, white 600 text.
    - Inactive: navText.
  - **Recent questions:** below the nav links (28 px gap), on every page.
    - **Heading:** "Recent questions" (15 px / 600, navMuted), on one line. There is no button beside it; "New chat" is the first nav link.
    - **Items:** one link per conversation, most recently updated first: 15 px, line height 1.4, padding 8/12, radius 8, navText; at most two lines, then "…", with the full title as the hover title. Hover `rgba(255,255,255,0.08)`. The open conversation has a `rgba(255,255,255,0.14)` background with white 600 text and `aria-current="page"`; the gold bar stays for the current page only.
    - The list fills the nav's free height and scrolls inside it, with a thin `rgba(255,255,255,0.3)` scrollbar. It is a `nav` landmark named by its heading. Empty: "No conversations yet."; failed: "Could not load your conversations." (14 px, navMuted).
    - **Collapsed rail:** the list is hidden; the "New chat" icon is the first link.
  - **Bottom:** "Signed in as {display_name}", or "Not connected" when `/api/me` fails, above a `rgba(255,255,255,0.14)` divider.
- **Page header (Upload, Dataset, Settings, Page not found):** white, 88 px tall, with a bottom border. The title (h1) is on the left and the page actions on the right. Chat has no page header, only a slimmer white model row (below).

## Chat page

- **Layout:** the page fills the main area as three rows: the model row and the question box stay put, and only the conversation pane between them scrolls (`overscroll-behavior: contain`). The conversations are in the side nav (Shell above); there is no conversation column.
- **Model row:** no page header and no visible title. A slim white bar holds, on the right, an "Answering with" label (15 px / 600, muted) and a select styled to match: native arrow hidden, a chevron icon inside on the right, 600 weight, at least 160 px wide, 6 px vertical padding, control border. The bar has padding 12/32, at least 58 px height (so it does not jump while the models load or when there are none) and a 1 px border at the bottom, like the page header on other pages and mirroring the question box band's top border. The conversation scrolls under that edge. An `h1` "Chat" stays for screen readers only.
- **Thread:**
  - centered, at most 880 px wide, padding 20/40/32;
  - a question and its answer sit 12 px apart, and two question–answer pairs sit 32 px apart;
  - **user question:** a right-aligned UCI Blue bubble with white text, at most 75% wide;
  - **clarifying question:** a left-aligned white bubble with a border.
- **Answer card:** white, 1 px border, radius 12, padding 24, sections 20 px apart, in this order:
  1. a caution line (13 px, muted) above every summary: "AI-generated summary. Check it against the table." when the AI wrote it (`source == "llm"`), else "The AI wrote the SQL, so check it."; then the summary at 18 px;
  2. the result table, inside a bordered container with radius 10: header row tableHead with navy 600 text, rows divided by divider lines;
  3. "How I read your question" (16 px / 700 navy) with bullet points;
  4. a full-width "Show the SQL query" bar (44 px, subtle background, chevron), collapsed by default, with Copy inside;
  5. a footer with a top divider: "{n} rows" on the left; on the right "Download Excel (.xlsx)" (filled UCI Blue) and "Download CSV (.csv)" (outlined), both with a download icon.

  Failed turns keep the alert, Retry and the SQL bar (S4 rule: always show the SQL).
- **Composer:** a white band with a top border at the bottom of the page, padding 16/40/20, centered at 880 px.
  - **Question box:** 1 px control border, radius 12, padding 12/12/10/16. Inside it:
    - a borderless 2-row textarea with the placeholder **"Ask a question about your data"**;
    - a toolbar row. On the left is the switch (40×22; track UCI Blue when on and `#555759` when off; white 16 px knob; `role="switch"`), next to a column with the label **"Let AI see the results"** (600) and the helper text (14 px, muted), which changes with the state. On the right is "Send" (40 px, filled UCI Blue).
  - **Below the box:** nothing. The caution lives on each answer card.
- **Copy:**

  | Place | Text |
  |---|---|
  | Helper, switch on | "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI." |
  | Helper, switch off | "Off: the AI sees only your question. You get the results without an AI summary." |
  | Disabled tooltip | "This AI model isn't allowed to receive results. Change it in Settings." (unchanged) |
  | Empty conversation | "Ask a question about your data to start." |

## Upload, Dataset, Settings

These pages use the same shell, header, card (radius 12, border), button, input and table styles. Their structure stays as built in S4. S6's user-story walkthrough decides any further changes to them.

- **Settings model cards (after S6):** besides "Default", each card shows the model's result-sharing setting (D2) as an outlined tag, in both states: "AI can see results" (ink) or "AI never sees results" (muted). The tag is focusable; on hover or focus a tooltip explains it:
  - on: "This AI may read query results, such as names and emails, to summarize them. You can turn it off for a question with "Let AI see the results" in Chat."
  - off: "This AI only writes the SQL. Query results stay on this computer."

## What S6 must update along with the code

- **Spec:**
  - §8.2 (Selection), which quotes the old helper text "Off: AI only writes the SQL. Results stay on this computer.";
  - §4.3: point to this file.
- **Tests:**
  - Vitest assertions on the changed copy: helper text, placeholder, download button names, "Show the SQL query".
  - Playwright: `.xlsx` still matches "Download Excel (.xlsx)"; "New chat" and `getByLabel("Let AI see the results")` must keep resolving to exactly one element.
- **Screenshots:** regenerate `docs/screenshots/` with `npm run e2e:screenshots`.
