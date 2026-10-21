# UI redesign: "Campus blue and gold"

- **Date:** 2026-10-21. Approved by the user after S4 and built in **S6**.
- **Mockup:** https://claude.ai/artifact/Xbq6MdmGMZdmT39wnmBQfs. The first artboard, "A. Campus blue and gold", is the approved design. Press Play on it to try the nav collapse, the hover states and the share switch.
- **Mockup source:** `2026-10-21-chat-mockup-a.dc.html` in this folder. It renders only inside the Design artifact, but every exact value (color, size, spacing, copy) is written in its inline styles, so read it as the reference when a value below is unclear.
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
| primary | `#255799` | UCI Blue | primary buttons, user question bubbles, switch on, links, focus ring, the "New chat" hover fill |
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
  | conversation list | 15 px |
  | helper | 13–14 px |

  Text uses `text-wrap: pretty` (no orphan words). Table numbers are right-aligned and use `tabular-nums`.
- **Corner radius:** 8 px for buttons, inputs, selects and list items; 10 px for the table container and the SQL bar; 12 px for cards and the question box; 18 px for chat bubbles, with a 4 px corner on the speaker's side.
- **Buttons:** no all-caps (MUI `textTransform: "none"`). Buttons are 600 weight, at least 40 px tall, and 44 px for the main ones.
- **Interaction states:** every clickable element has a hover state and a visible keyboard focus ring (2 px UCI Blue, 2 px offset). The side nav uses a 2 px white ring instead, because UCI Blue is not visible on navy.

## Shell (`AppShell`)

- **Top bar:** none. The left nav carries the brand.
- **Side nav:** 248 px wide, navy background.
  - **Brand block:** 88 px tall, the same height as the page header. It holds "GPSRC Data Hub" (19 px / 700, never wraps) and below it "Graduate & Postdoctoral Scholar Resource Center" (13 px, navMuted).
  - **Collapse button:** to the right of the wordmark. It is a 40×40 icon button with **no border**: icon navMuted at rest; on hover or focus, a `rgba(255,255,255,0.12)` background and a white icon. Its `aria-label` and title are "Collapse navigation" or "Expand navigation", with `aria-expanded` set.
  - **Collapsed state:** a 72 px rail with icons only. Each link keeps an `aria-label` and a hover title. The state is kept in memory only, not in localStorage (localStorage holds only the last selected profile id).
  - **Nav links:** Chat, Upload, Dataset and Settings, each icon plus label.
    - Active: a 3 px gold left border, a `rgba(255,255,255,0.10)` background, white 600 text.
    - Inactive: navText.
  - **Bottom:** "Signed in as {display_name}", or "Not connected" when `/api/me` fails.
- **Page header:** white, 88 px tall, with a bottom border. The title (h1) is on the left and the page actions on the right.

## Chat page

- **Header actions:** an "AI model" label (15 px / 600, muted) and a select styled to match: native arrow hidden, a chevron icon inside on the right, 600 weight, at least 200 px wide, control border.
- **Conversation column:** 256 px wide, white, with a right border.
  - **New chat:** a full-width button, 44 px tall, outlined UCI Blue, radius 8, with a "+" icon. On hover or focus it fills UCI Blue with white text (120 ms). There is **no** "Conversations" heading.
  - **Items:** radius 8, padding 10/12. The selected item has the `selected` background and navy 600 text.
- **Thread:**
  - centered, at most 880 px wide, padding 28/40;
  - a question and its answer sit 12 px apart, and two question–answer pairs sit 32 px apart;
  - **user question:** a right-aligned UCI Blue bubble with white text, at most 75% wide;
  - **clarifying question:** a left-aligned white bubble with a border.
- **Answer card:** white, 1 px border, radius 12, padding 24, sections 20 px apart, in this order:
  1. "AI-generated summary. Check it against the table." (13 px, muted; only when `source == "llm"`), then the summary at 18 px;
  2. the result table, inside a bordered container with radius 10: header row tableHead with navy 600 text, rows divided by divider lines;
  3. "How I read your question" (16 px / 700 navy) with bullet points;
  4. a full-width "Show the SQL query" bar (44 px, subtle background, chevron), collapsed by default, with Copy inside;
  5. a footer with a top divider: "{n} rows" on the left; on the right "Download Excel (.xlsx)" (filled UCI Blue) and "Download CSV (.csv)" (outlined), both with a download icon.

  Failed turns keep the alert, Retry and the SQL bar (S4 rule: always show the SQL).
- **Composer:** a white band with a top border, padding 16/40/12, centered at 880 px.
  - **Question box:** 1 px control border, radius 12, padding 12/12/10/16. Inside it:
    - a borderless 2-row textarea with the placeholder **"Ask a question about your data"**;
    - a toolbar row. On the left is the switch (40×22; track UCI Blue when on and `#555759` when off; white 16 px knob; `role="switch"`), next to a column with the label **"Let AI see the results"** (600) and the helper text (14 px, muted), which changes with the state. On the right is "Send" (40 px, filled UCI Blue).
  - **Below the box:** centered, 13 px, muted: **"AI can make mistakes. Double-check important answers."**
- **Copy:**

  | Place | Text |
  |---|---|
  | Helper, switch on | "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI." |
  | Helper, switch off | "Off: the AI sees only your question. You get the results without an AI summary." |
  | Disabled tooltip | "This AI model isn't allowed to receive results. Change it in Settings." (unchanged) |
  | Empty conversation | "Ask a question about your data to start." |

## Upload, Dataset, Settings

These pages use the same shell, header, card (radius 12, border), button, input and table styles. Their structure stays as built in S4. S6's user-story walkthrough decides any further changes to them.

## What S6 must update along with the code

- **Spec:**
  - §8.2 (Selection), which quotes the old helper text "Off: AI only writes the SQL. Results stay on this computer.";
  - §4.3: point to this file.
- **Tests:**
  - Vitest assertions on the changed copy: helper text, placeholder, download button names, "Show the SQL query".
  - Playwright: `.xlsx` still matches "Download Excel (.xlsx)"; "New chat" and `getByLabel("Let AI see the results")` must keep resolving to exactly one element.
- **Screenshots:** regenerate `docs/screenshots/` with `npm run e2e:screenshots`.
