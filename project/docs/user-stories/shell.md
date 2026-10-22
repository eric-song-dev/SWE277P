# Shell stories

The side nav, the page header and the app-wide states (wrong address, broken page, small screen).
Format, stacks and recording: [README.md](README.md). Window 1440×900 unless a story says otherwise.

### SH-01 Move between pages
- **Who:** a GPSRC staff member using the Hub for the first time
- **Story:** As a staff member, I want to see the four pages in one place and always know which one I am on, so that I can get to Upload, Chat, Dataset or Settings without hunting.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - The navy side nav shows "GPSRC Data Hub", below it "Graduate & Postdoctoral Scholar Resource Center", and the links "Chat", "Upload", "Dataset" and "Settings", each with an icon.
  - Opening `http://127.0.0.1:8083/` lands on `/chat`.
  - Clicking a link changes the address to `/chat`, `/upload`, `/dataset` or `/settings`, and the page shows a white header whose h1 is "Chat", "Upload", "Dataset" or "Settings".
  - Only the current page's link has the 3 px gold bar on its left, a lighter background and white bold text, and only it has `aria-current="page"`.
  - Hovering any link lightens its background.
  - The browser's Back and Forward buttons move between the visited pages, and the highlighted link follows.
  - Opening `/chat/<id>` of an existing conversation highlights "Chat".
  - The browser tab reads "GPSRC Data Hub".
- **Walk:**
  1. On the replay stack with the samples loaded, open `http://127.0.0.1:8083/`. Check the address is `/chat`, the brand text, and the four links.
  2. Click Upload, Dataset, Settings, then Chat. After each click check the address, the h1 and the gold bar.
  3. Hover each link and watch the background.
  4. In DevTools Elements, check that only the current link has `aria-current="page"`.
  5. Press Back three times and Forward once. Check the address, h1 and highlighted link each time.
  6. Ask "How many unique people attended Bagel Breakfast, October?" so the address becomes `/chat/<id>`. Check that "Chat" is still highlighted.

### SH-02 Collapse and expand the nav
- **Who:** a GPSRC staff member who wants more room for a wide result table
- **Story:** As a staff member, I want to shrink the side nav to icons, so that the page has more room while I can still move between pages.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - A borderless icon button to the right of "GPSRC Data Hub" has the tooltip and accessible name "Collapse navigation" and `aria-expanded="true"`.
  - Clicking it shrinks the nav to a 72 px rail of icons only. The brand text and the "Signed in as …" line are hidden, and the button now reads "Expand navigation" with `aria-expanded="false"`.
  - In the rail, hovering an icon shows its page name ("Chat", "Upload", "Dataset", "Settings") as a tooltip. Each icon link keeps its accessible name, and the current page keeps its gold bar and `aria-current="page"`.
  - The page content moves left and gets the extra width. Nothing overlaps, and no horizontal scrollbar appears.
  - The nav stays collapsed while moving between pages.
  - After a full reload the nav is expanded again (the state is kept in memory only).
  - "Expand navigation" restores the 248 px nav with all text.
- **Walk:**
  1. Open `/chat`. Hover the button next to the brand and read the tooltip. Check `aria-expanded` in DevTools.
  2. Click it. Check the rail, the hidden texts, the new label and `aria-expanded`.
  3. Hover each icon and read its tooltip. Check `aria-label` and `aria-current` on the Chat link in DevTools.
  4. Click the Upload, Dataset and Settings icons in turn. Check the rail stays collapsed and the gold bar follows.
  5. Reload the page and check that the nav is expanded.
  6. Collapse it again, then click "Expand navigation". Check the full nav is back.

### SH-03 Keyboard only (focus ring everywhere, including the nav)
- **Who:** a GPSRC staff member who works with the keyboard, or cannot use a mouse
- **Story:** As a keyboard user, I want every control to be reachable with Tab and to show clearly where I am, so that I can do everything without a mouse.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - From a fresh page load, Tab reaches "Collapse navigation" first, then Chat, Upload, Dataset and Settings, then the page's own controls in reading order.
  - Every focused element in the nav shows a 2 px white focus ring. Every focused element outside the nav shows a 2 px `#255799` ring with a 2 px offset. No control is focused without a visible ring.
  - Enter on a nav link opens its page. Enter or Space on "Collapse navigation" collapses and expands the nav.
  - On Chat, the order is: "AI model" select, "New chat", the conversation links, the controls inside the answer cards (if any), then Question, then "Let AI see the results", then Send. The question box shows the ring while typing, and the switch and Send each show their own ring.
  - On Chat, Space toggles the switch, Enter in the question box sends, and Enter or Space on "Show the SQL query" opens and closes the SQL. "Copy", "Download Excel (.xlsx)" and "Download CSV (.csv)" are reachable and work with Enter.
  - On Upload, the drop zone is focusable, and Enter or Space opens the file chooser. Every field of the event form, "Commit" and "Discard" are reachable in order.
  - On Settings, "Add AI model" opens a dialog that keeps focus inside it. Escape closes it and focus returns to the button that opened it.
  - On Dataset, both download buttons and the "Pending" link (when there is one) are reachable.
  - Nothing traps focus: Shift+Tab walks back the same way.
- **Walk:**
  1. Open `/chat` with the samples loaded and click the address bar, so focus starts outside the page. Press Tab repeatedly. Write down the order and check the ring on each stop (DevTools Elements → Computed → `outline` to confirm color and width).
  2. Press Enter on "Collapse navigation", Tab to a rail icon, press Enter. Press Shift+Tab back to the toggle and press Space to expand.
  3. On Chat, Tab to Question, type "How many unique people attended Bagel Breakfast, October?", Tab to the switch, press Space twice, Tab to Send, press Enter.
  4. Tab into the answer card: open "Show the SQL query" with Enter, press Enter on "Copy", then on "Download CSV (.csv)".
  5. Go to Upload with the keyboard. Tab to the drop zone, press Enter, and check the file chooser opens. Cancel it. Upload `Edwards Site Visit - No Shows.xlsx` (any way), then Tab through the page.
  6. Go to Settings. Press Enter on "Add AI model", Tab through the dialog to the end and on. Check focus stays in the dialog. Press Escape and check where focus lands.
  7. Go to Dataset and Tab through the downloads and the grid.

### SH-04 Signed-in name, and "Not connected" when the API is down
- **Who:** a GPSRC staff member checking that the Hub is running
- **Story:** As a staff member, I want the nav to show who I am, or that the Hub cannot be reached, so that I know at a glance whether my work will be saved.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - With the api running, the bottom of the expanded nav reads "Signed in as GPSRC Staff".
  - With the api stopped, after a reload the bottom of the nav reads "Not connected", and the shell still renders: nav, page header and the page.
  - With the api stopped, each page says it cannot load its data instead of spinning forever (after a short wait for retries):
    - Chat: "Could not load your AI models." and "Could not load your conversations.";
    - Upload: "Could not check for pending imports.";
    - Dataset: "The Hub server isn't responding. Check that it is running, then try again.";
    - Settings: "Could not load your AI models.".
  - After the api is started again, a reload shows "Signed in as GPSRC Staff" and every page works again.
- **Walk:**
  1. Open `/chat` and read the nav footer.
  2. Run `docker compose -p hub-replay stop api`.
  3. Reload `/chat`. Wait about 10 seconds. Read the footer and the page's alerts.
  4. Visit Upload, Dataset and Settings, waiting about 10 seconds on each, and read each alert.
  5. Run `docker compose -p hub-replay start api` and wait until `curl -s http://127.0.0.1:8083/api/health` answers.
  6. Reload and check the footer and each page.

### SH-05 An address that does not exist (`/foo`)
- **Who:** a GPSRC staff member who followed an old bookmark or mistyped an address
- **Story:** As a staff member, I want a wrong address to tell me the page does not exist and take me back, so that I am not left on an error I cannot act on.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `/foo` shows a message that the page was not found (for example "Page not found"). It does not show the generic "Something went wrong. Reload the page to continue." (expected; spec silent).
  - The page offers a way back: the side nav stays visible, or there is a link to Chat (expected; spec silent).
  - The same happens for `/upload/extra` and `/settings/foo` (expected; spec silent).
  - Following the way back opens a working page.
- **Walk:**
  1. Open `http://127.0.0.1:8083/foo`. Read the page and note whether the nav is there.
  2. Use the way back the page offers. Check you land on a working page.
  3. Repeat with `/upload/extra` and `/settings/foo`.

### SH-06 A page that fails to load after a rebuild
- **Who:** a GPSRC staff member who left the Hub open in a tab while it was updated
- **Story:** As a staff member, I want a page that can no longer load to tell me to reload, so that an update never leaves me on a blank or frozen screen.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - When a page's code file cannot be loaded (as after a rebuild that renamed it), the screen shows "Something went wrong. Reload the page to continue." with a "Reload" button, not a blank page or an endless spinner.
  - "Reload" reloads the page. Once the file can be loaded again, the page appears and works.
- **Walk:**
  1. Open `/chat` in a fresh tab, so the Dataset page's code is not loaded yet.
  2. In DevTools, open the Network request blocking panel (More tools → Network request blocking) and block the pattern `*DatasetPage-*`. With Playwright, `page.route("**/assets/DatasetPage-*", r => r.abort())` does the same.
  3. Click Dataset in the nav. Read the screen.
  4. Remove the block and click "Reload". Check the Dataset page loads.

### SH-07 A small laptop screen (1280×720 and 1024×768)
- **Who:** a GPSRC staff member on a 13-inch laptop or a projector
- **Story:** As a staff member on a small screen, I want every page to fit the window, so that I never scroll sideways to reach a button or read an answer.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - At 1280×720 and at 1024×768, with the nav expanded and collapsed, no page scrolls sideways: `document.documentElement.scrollWidth - innerWidth` is `0` on `/chat`, `/upload`, `/dataset` and `/settings`.
  - Chat: the question box, the "Let AI see the results" switch with its helper text, Send and "AI can make mistakes. Double-check important answers." stay visible at the bottom without scrolling. The header's "AI model" select stays inside the header, wrapping under the title if needed.
  - Chat: an answer card's buttons ("Download Excel (.xlsx)", "Download CSV (.csv)") wrap instead of running off the card, and a result table wider than the card scrolls inside its own frame.
  - Chat: a 300-character question with no spaces wraps inside its blue bubble.
  - Upload: the drop zone, the cards and every form field fit the width.
  - Dataset: the header buttons wrap if needed, and the file list scrolls inside its own frame.
  - Settings: the model cards and the Add/Edit dialog fit. The dialog's Save and Cancel are reachable without scrolling the page sideways.
  - At 720 px tall, the nav footer ("Signed in as GPSRC Staff") stays visible.
- **Walk:**
  1. In DevTools device mode (or `page.setViewportSize`), set 1280×720.
  2. On `/chat`, ask "Demo all columns", then paste a 300-character question with no spaces: run `copy("x".repeat(300))` in the console, paste into the box and press Enter.
  3. On each of the four pages, run `document.documentElement.scrollWidth - innerWidth` in the console and look over the layout. Collapse the nav and repeat.
  4. On Upload, upload `Edwards Site Visit - No Shows.xlsx` and look at the card and form. On Settings, open "Add AI model".
  5. Repeat steps 2–4 at 1024×768. Take a screenshot of Chat at 1024×768.
