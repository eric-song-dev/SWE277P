# Chat stories

Asking questions, reading and downloading answers, and what happens when something fails.
Format, stacks, helper profiles and recording: [README.md](README.md). Window 1440×900 unless a
story says otherwise.

Unless a story says otherwise, the replay stack has the 10 samples loaded and the "Demo" profile
as its default. The Demo profile may receive results, so the "Let AI see the results" switch
starts on. The Demo questions it knows (matched anywhere in the question, any case):

| Question | Answer |
|---|---|
| How many unique people attended Bagel Breakfast, October? | 1 row: `unique_people` 38 |
| Of those, how many are international? | 1 row: `international_people` 8 |
| Emails of everyone who attended any Bagel Breakfast | 55 rows: `email` |
| … this year … | clarifying question "Do you mean the 2026-27 academic year or calendar year 2026?" |
| Demo slow question | about 10 s on "Writing SQL", then 38 |
| Demo refused query | a `DELETE` refused three times, then an error |
| Demo repaired query | a failed query, one repair, then `n` 293 |
| Demo all columns | 38 rows × 17 columns |
| anything else | clarifying question "The demo model only knows its scripted questions." |

### CH-01 First question in a new chat
- **Who:** the GPSRC director, Kayleigh, preparing numbers for a report
- **Story:** As the director, I want to type a question in plain English and get the number with an explanation, so that I don't need SQL or a spreadsheet to answer it.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `/chat` shows "Ask a question about your data to start." above an empty thread. The "Answering with" select at the top right shows "Demo".
  - The question box shows the placeholder "Ask a question about your data". Inside the box are the "Let AI see the results" switch (on) with "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI." and a "Send" button. Nothing is below the box.
  - "Send" is disabled while the box is empty.
  - Pressing Enter sends the question:
    - the box empties;
    - the question appears as a right-aligned blue bubble;
    - the start text disappears;
    - a step line shows the progress ("Writing SQL", "Checking the query", "Running the query", "Analyzing results"; with the Demo model some pass too fast to read).
  - The answer card shows, top to bottom:
    - "AI-generated summary. Check it against the table." and "38 unique people attended the October Bagel Breakfast.";
    - a table with the column `unique_people` and the value 38, right-aligned;
    - "How I read your question" with "Count the distinct people who attended the October Bagel Breakfast.";
    - a closed "Show the SQL query" bar;
    - a footer with "1 row" on the left, and "Download Excel (.xlsx)" (filled) and "Download CSV (.csv)" (outlined) on the right, each with a download icon.
  - The address changes to `/chat/<number>`. "Recent questions" in the side nav gains one item at the top, titled with the question and highlighted.
  - The whole answer arrives within 5 seconds.
- **Walk:**
  1. Open `/chat` (or click "New chat"). Check the start text, the header, the box, the switch text and the line below the box. Check that Send is disabled.
  2. Type "How many unique people attended Bagel Breakfast, October?" and press Enter. Watch the box, the bubble and the step line.
  3. When the answer arrives, check each part of the card in order, and the address and "Recent questions".
  4. Take a screenshot of the answer.

### CH-02 Follow-up
- **Who:** the GPSRC director narrowing an answer
- **Story:** As the director, I want to ask a follow-up in plain words, so that I can drill into an answer without repeating the whole question.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - The follow-up appears below the first answer in the same conversation, and the address does not change.
  - Its card shows `international_people` 8, and "How I read your question" lists "Of the October Bagel Breakfast attendees, count the international people." and "Those means the attendees of the previous question.".
  - "Recent questions" still has one item for this conversation, and it is still highlighted.
  - The first answer is unchanged above it.
- **Walk:**
  1. Continue from CH-01 (or ask its question in a new chat first).
  2. Ask "Of those, how many are international?".
  3. Check the new card, the address, the list and the first card.

### CH-03 Clarifying question
- **Who:** a GPSRC staff member asking a question that can be read two ways
- **Story:** As a staff member, I want the Hub to ask me what I mean when my question is ambiguous, so that I don't get a confident answer to the wrong question.
- **Stack:** replay (Demo) and main (DeepSeek)
- **Acceptance criteria:**
  - An ambiguous question gets a left-aligned white bubble with a border that asks a question back. There is no answer card, table, "Show the SQL query" bar, row count or download button for that turn.
  - The question box is ready for the reply, and the reply is sent as the next turn of the same conversation.
  - Replay: "How many people came this year?" gets "Do you mean the 2026-27 academic year or calendar year 2026?".
  - Main: "How many people attended the event?" gets a question asking which event is meant.
  - Main: replying "The Health Careers Mixer" gets an answer card with 45. Its "How I read your question" names the Health Careers Mixer.
  - After a reload, the clarifying bubble is still shown as a bubble, not as an answer or an error.
- **Walk:**
  1. Replay: in a new chat ask "How many people came this year?". Check the bubble and that nothing else appears for that turn.
  2. Reply "The academic year" (the Demo model then says it only knows its scripted questions; that is expected). Check the reply joined the same conversation.
  3. Reload and check the bubbles.
  4. Main (`http://127.0.0.1:8080`, profile "DeepSeek"): in a new chat ask "How many people attended the event?". Check the bubble.
  5. Reply "The Health Careers Mixer". Check the answer and its reading.

### CH-04 Read and copy the SQL
- **Who:** a GPSRC staff member who hands a query to the team's analyst
- **Story:** As a staff member, I want to see and copy the exact query behind an answer, so that I or someone technical can check how the number was made.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - "Show the SQL query" is a full-width bar, closed by default, and the SQL is not on screen until it is opened.
  - Clicking the bar opens it, turns its chevron, and shows `SELECT COUNT(DISTINCT person_key) AS unique_people FROM attendance_view WHERE event_name = 'Bagel Breakfast, October'` in a monospace box, with a "Copy" button. Long SQL wraps inside the box.
  - Clicking "Copy" puts exactly that SQL on the clipboard.
  - After "Copy", the screen confirms the copy (for example "Copied") (expected; spec silent).
  - Clicking the bar again closes it.
- **Walk:**
  1. In the CH-01 answer, check the bar is closed. Click it.
  2. Read the SQL. Click "Copy" and watch for a confirmation.
  3. Paste into the question box (Ctrl/Cmd+V) and compare with the shown SQL, then clear the box.
  4. Ask "Demo all columns", open its SQL bar at 1024×768, and check the SQL wraps.
  5. Click the bar to close it.

### CH-05 Download Excel and CSV
- **Who:** the GPSRC director who sends results to a partner office
- **Story:** As the director, I want to download any answer as Excel or CSV, so that I can share it or keep working on it in a spreadsheet.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - "Download Excel (.xlsx)" saves `hub-turn-<turn id>-<YYYYMMDD-HHMM>.xlsx` and "Download CSV (.csv)" saves `hub-turn-<turn id>-<YYYYMMDD-HHMM>.csv`, with the current local date and time.
  - For the CH-01 answer, both files hold the header `unique_people` and the value 38.
  - For "Emails of everyone who attended any Bagel Breakfast", both files hold the header `email` and 55 rows, the same emails as the table.
  - The Excel file opens in Excel or LibreOffice without a repair warning.
  - Both buttons are disabled while a download is running. No "This file stops at" notice appears with the default caps.
  - Going from the question to a saved Excel file takes under a minute.
- **Walk:**
  1. In the CH-01 answer, click "Download Excel (.xlsx)", then "Download CSV (.csv)". Note the file names and open both files.
  2. Ask "Emails of everyone who attended any Bagel Breakfast". Download both formats and count the data rows (`wc -l` on the CSV gives 56 with the header).
  3. Time one run from typing a question to the saved Excel file.

### CH-06 More rows than the screen shows, and an export cap
- **Who:** a GPSRC staff member pulling a long list
- **Story:** As a staff member, I want to be told when the table or the file holds only part of the result, so that I never send someone a list I think is complete when it is not.
- **Stack:** replay (Demo), api restarted with `DISPLAY_ROW_CAP=20 EXPORT_ROW_CAP=30`
- **Acceptance criteria:**
  - "Emails of everyone who attended any Bagel Breakfast" (55 rows) shows 20 rows in the table and the notice "Showing the first 20 rows. Download the file to get all rows.".
  - The footer does not claim the result has exactly 20 rows; it says there are more (for example "More than 20 rows") (expected; spec silent).
  - With "Let AI see the results" off, the summary reads "More than 20 rows (showing the first 20)".
  - "Download CSV (.csv)" saves a file with 30 data rows, and the card then shows "This file stops at 30 rows.". The same holds for "Download Excel (.xlsx)".
  - "Demo all columns" (38 rows) behaves the same: 20 rows in the table, 30 in each file, and both notices.
  - After the api is restarted with the default caps, the email list shows all 55 rows, no notice, and its files hold 55 rows.
- **Walk:**
  1. Restart the api with the caps (README, "Restart the api with other limits").
  2. Reload `/chat`, start a new chat, ask "Emails of everyone who attended any Bagel Breakfast". Check the table, notice and footer.
  3. Turn the switch off and ask the same question again. Read the summary.
  4. Download the CSV and the Excel file. Count rows and read the notice.
  5. Ask "Demo all columns" and repeat steps 2 and 4.
  6. Restart the api with the default limits, ask the email question again, and check there is no notice and the files hold 55 rows.

### CH-07 A wide result (`Demo all columns`)
- **Who:** a GPSRC staff member who asks for every detail of an event's attendees
- **Story:** As a staff member, I want a wide result to stay readable inside the answer, so that I can scan all columns without the page breaking.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - The table has 17 columns in this order: `person_key`, `event_name`, `event_date`, `term`, `academic_year`, `modality`, `sponsors_hosts`, `event_type`, `platform`, `first_name`, `last_name`, `email`, `netid`, `affiliation`, `domestic_international`, `school`, `department`. The footer says "38 rows".
  - The table scrolls sideways inside its own frame. The page does not scroll sideways, and the card's other parts stay in the card.
  - The header row stays visible while the rows scroll up and down inside the table.
  - Every column header can be read in full, because the column is wide enough, it can be widened, or its full name shows on hover (expected; spec silent).
  - `person_key` values are right-aligned. Text columns are left-aligned.
- **Walk:**
  1. In a new chat ask "Demo all columns".
  2. Scroll the table sideways and down. Check the page itself does not scroll sideways (`document.documentElement.scrollWidth - innerWidth` is `0`).
  3. Try to read `domestic_international` and `sponsors_hosts` in full: hover, or drag the column edge.
  4. Repeat at 1024×768. Take a screenshot.

### CH-08 "Let AI see the results" on and off, kept for follow-ups, reset on new chat and profile change
- **Who:** a GPSRC staff member asking about a list of names and emails
- **Story:** As a staff member, I want to keep results away from the AI for a question and the follow-ups after it, so that personal data is shared only when I choose.
- **Stack:** replay (Demo), with the helper profile "Demo B" (README)
- **Acceptance criteria:**
  - The switch starts on for "Demo", with "On: the AI reads the results to summarize them. PII (such as emails and names) may be shared with the AI.".
  - Turned off, it reads "Off: the AI sees only your question. You get the results without an AI summary.".
  - A question asked with the switch off gets a summary built on this computer, under the line "The AI wrote the SQL, so check it." instead of "AI-generated summary. Check it against the table.": "unique_people: 38" for the CH-01 question.
  - The switch stays off when the first question turns `/chat` into `/chat/<id>`, and stays off for the follow-up. "Of those, how many are international?" gets "international_people: 8".
  - "New chat" resets the switch to on.
  - Opening another conversation from the list resets it to on.
  - Choosing another AI model resets it to that model's setting: off on "Demo", then choosing "Demo B" shows it on.
  - Clicking the label "Let AI see the results" toggles the switch too.
- **Walk:**
  1. Create "Demo B" (README). Open `/chat`, click "New chat", read the switch text.
  2. Turn the switch off and read the helper.
  3. Ask "How many unique people attended Bagel Breakfast, October?". Check the address changed, the switch is still off, and the summary is "unique_people: 38" with no AI label.
  4. Ask "Of those, how many are international?". Check the switch and the summary.
  5. Click "New chat" and check the switch. Turn it off, then click the CH-01 conversation in the list and check the switch.
  6. Turn it off again, choose "Demo B" in "Answering with" and check the switch. Click the label text and check it toggles.

### CH-09 A profile that may not receive results
- **Who:** a GPSRC staff member using a model the office has not approved for personal data
- **Story:** As a staff member, I want the Hub to stop me from sharing results with a model that may not receive them, so that I cannot send personal data there by accident.
- **Stack:** replay (Demo), with the helper profile "Demo No Share" (README)
- **Acceptance criteria:**
  - With "Demo No Share" selected, the switch is off and greyed out, and the helper reads "Off: the AI sees only your question. You get the results without an AI summary.". This holds even right after "Demo" had the switch on.
  - Hovering the switch or its label shows "This AI model isn't allowed to receive results. Change it in Settings.".
  - Clicking the switch or the label does not turn it on.
  - A question asked with "Demo No Share" gets a summary built on this computer, under the line "The AI wrote the SQL, so check it.": "unique_people: 38".
  - Choosing "Demo" again turns the switch back on and enables it.
- **Walk:**
  1. Create "Demo No Share" (README). On `/chat` with "Demo" selected, check the switch is on.
  2. Choose "Demo No Share". Check the switch, its helper and its greyed look.
  3. Hover the switch and read the tooltip. Click the switch and the label.
  4. Ask "How many unique people attended Bagel Breakfast, October?". Read the summary.
  5. Choose "Demo" and check the switch.

### CH-10 Switch AI model, remembered after reload
- **Who:** a GPSRC staff member who prefers a particular AI model
- **Story:** As a staff member, I want the Hub to remember the AI model I picked, so that I don't have to choose it again every time I open Chat.
- **Stack:** replay (Demo), with the helper profile "Demo B" (README)
- **Acceptance criteria:**
  - "Answering with" lists every saved model by name; "Demo" (the default) is selected on a first visit.
  - Choosing "Demo B" sends the next question with "Demo B". The answer arrives as usual.
  - After a reload, and in a new tab, "Demo B" is still selected.
  - After "Demo B" is deleted in Settings, Chat selects the default ("Demo") with no error.
  - On a browser that never picked a model (for example a private window), the default is selected.
- **Walk:**
  1. Open `/chat` in a private window and check "Demo" is selected. Close it.
  2. In the normal window choose "Demo B" and ask "How many unique people attended Bagel Breakfast, October?". In DevTools → Network, check the `messages` request body carries Demo B's id as `llm_profile_id` (the ids are in `GET /api/llm-profiles`).
  3. Reload. Open `/chat` in a new tab. Check the selection in both.
  4. In Settings, delete "Demo B". Back on Chat, check the selection and ask the question again. (Recreate "Demo B" afterwards if later stories need it.)

### CH-11 Reopen an old conversation and show its results again
- **Who:** the GPSRC director returning to last week's numbers
- **Story:** As the director, I want to reopen an earlier conversation and see its results again, so that I can reuse an answer without asking again.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - After a reload, clicking a conversation in the list opens `/chat/<id>`. The item is highlighted, and every question and answer shows in order, oldest first.
  - Each saved answer card shows its summary, "How I read your question", the "Show the SQL query" bar, the row count ("1 row") and both download buttons, plus a "Show results" button instead of the table.
  - "Show results" changes to "Loading results…", then shows the table, labeled "Re-run on current data", with the current values (38 and 8 for the CH-01 and CH-02 turns).
  - The downloads on a saved card work without "Show results" first and hold the current data.
  - A saved clarifying question shows as a bubble. A saved failed answer shows its error, "Retry" and the "Show the SQL query" bar (when it had SQL).
  - A follow-up asked in the reopened conversation is answered in it.
- **Walk:**
  1. Have the CH-01/CH-02 conversation and the CH-03 replay conversation. Reload the page.
  2. Click the CH-01 conversation. Check each card.
  3. Click "Show results" on both cards. Watch the label and the tables.
  4. Click "Download CSV (.csv)" on the second card and open the file.
  5. Open the CH-03 conversation and check its bubbles. Open the CH-12 conversation (after walking it) and check its error card.
  6. Back in the CH-01 conversation, ask "Of those, how many are international?" and check it is added there.

### CH-12 A refused query
- **Who:** a GPSRC staff member whose question leads the AI to write something unsafe
- **Story:** As a staff member, I want the Hub to refuse any query that would change data, and to show me what was refused, so that the dataset can never be damaged by a question.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - "Demo refused query" ends with an error alert: "The AI model's SQL was not allowed, even after retrying (only SELECT statements are allowed). Try rephrasing the question.", with a "Retry" button.
  - The card still shows the "Show the SQL query" bar, and it holds `DELETE FROM attendance_view`.
  - There is no table, row count or download button for this turn.
  - Nothing was deleted: "How many unique people attended Bagel Breakfast, October?" still answers 38, and the Dataset page is unchanged.
  - After a reload, the saved turn shows "The AI wrote a query the Hub doesn't allow.", "Retry" and the SQL bar with the same SQL.
  - "Retry" is disabled while another answer is streaming.
- **Walk:**
  1. In a new chat ask "Demo refused query". Read the alert and open the SQL bar.
  2. Ask "How many unique people attended Bagel Breakfast, October?" and check the answer. Visit Dataset and check the rows.
  3. Reload the conversation. Read the saved card.
  4. Ask "Demo slow question" and, while it runs, check the refused card's "Retry" is disabled. After it finishes, click "Retry" and check a new turn with the same refusal is added.

### CH-13 A repaired query
- **Who:** a GPSRC staff member whose question first produced a broken query
- **Story:** As a staff member, I want the Hub to fix a failed query by itself and show me the query that worked, so that a small AI mistake does not cost me an answer.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - While "Demo repaired query" runs, the step line reads "Fixing the query (attempt 2)" during the repair: the number is the attempt now being made, so the first repair says 2 (expected; spec silent).
  - The answer is a normal card with no error. Its table shows `n` 293, "How I read your question" reads "Count all attendance rows.", and the summary reads "The result is the number of attendance rows.".
  - "Show the SQL query" holds the query that worked, `SELECT COUNT(*) AS n FROM attendance_view`, not the failed one (which used a `campus` column).
  - The downloads hold `n` 293.
- **Walk:**
  1. Open DevTools → Network. In a new chat ask "Demo repaired query".
  2. Watch the step line. It may pass too fast to read, so also open the `messages` request → EventStream and read the `step` events: note the `attempt` of the `repairing` event, which the screen shows as "Fixing the query (attempt N)".
  3. Check the card, open the SQL bar and download the CSV.

### CH-14 The connection drops mid-answer (`Demo slow question`, then go offline or stop `api`)
- **Who:** a GPSRC staff member on flaky Wi-Fi, or whose Hub restarts while answering
- **Story:** As a staff member, I want a dropped answer to tell me plainly and let me retry, so that I never wait forever or see the same question twice.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - When the connection drops while "Writing SQL" is showing, the card shows "Connection lost. Retry." with a "Retry" button, within a few seconds of the drop.
  - The thread shows exactly one card for that question: the lost answer is not shown again as a second card, now or after the connection returns.
  - After the connection returns and the page is reloaded, the turn shows "This answer was interrupted before it finished." with "Retry", still as one card.
  - "Retry" (with the connection back) sends "Demo slow question" again, and about 10 s later shows 38.
  - The question box works again after the drop.
- **Walk:**
  1. In a new chat ask "How many unique people attended Bagel Breakfast, October?" (so the conversation has a saved turn), then ask "Demo slow question".
  2. While "Writing SQL" shows, cut the connection: DevTools → Network → throttling "Offline" (Playwright: `context.setOffline(true)`). If the card keeps waiting, use `docker compose -p hub-replay stop api` instead (the api can take up to 10 s to stop, and the answer may finish first; if so, repeat).
  3. Read the card. Count the cards for "Demo slow question".
  4. Go back online (or `docker compose -p hub-replay start api` and wait for `/api/health`). Wait 10 seconds and count the cards again.
  5. Reload. Read the saved card and count again.
  6. Click "Retry" and wait for 38.

### CH-15 The server is down when asking
- **Who:** a GPSRC staff member whose computer restarted Docker in the background
- **Story:** As a staff member, I want a question sent while the Hub is down to fail clearly and be easy to resend, so that I don't lose what I typed.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - With the api stopped, sending a question from an open Chat page shows the question bubble and a card with "Connection lost. Retry." and a "Retry" button, within a few seconds.
  - The question text stays visible in the bubble, so nothing typed is lost.
  - After the api is started again, "Retry" answers the question (38) in that card's place. The conversation then appears in the list once.
  - The same holds in an existing conversation: the failed question is the last card and "Retry" answers it.
- **Walk:**
  1. Open `/chat` and click "New chat" while the api runs, so the page has loaded the models.
  2. Run `docker compose -p hub-replay stop api`.
  3. Ask "How many unique people attended Bagel Breakfast, October?". Read the card.
  4. Run `docker compose -p hub-replay start api` and wait for `/api/health`. Click "Retry". Check the answer and "Recent questions".
  5. Stop the api again and ask "Of those, how many are international?" in the same conversation. Start the api, then click "Retry".

### CH-16 Long, multi-line and too-long questions, Enter vs Shift+Enter, sending while an answer streams
- **Who:** a GPSRC staff member who writes detailed questions
- **Story:** As a staff member, I want the question box to handle long and multi-line questions predictably, so that I know what will be sent and when.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Shift+Enter adds a new line. Enter sends.
  - A two-line question shows in its bubble with the line break kept, and is answered as usual. The box grows with the text up to about 8 lines, then scrolls inside.
  - A 300-character question with no spaces wraps inside the bubble, and the page does not scroll sideways (also at 1024×768).
  - A question of exactly 2,000 characters (after trimming spaces at both ends) can be sent.
  - At 2,001 characters the box shows "2,001 / 2,000 characters. Shorten your question." in red. Send is disabled and Enter does nothing. Deleting one character removes the message and enables Send.
  - A box holding only spaces or new lines cannot be sent.
  - While an answer is streaming ("Demo slow question"), Send is disabled and Enter does not send a second question.
  - While an answer is streaming, the next question can still be typed into the box, and it is kept until it is sent (expected; spec silent).
  - A question sent right as the previous answer finishes is either sent or stays in the box; it is never lost.
- **Walk:**
  1. Type "How many unique people attended Bagel Breakfast, October?", press Shift+Enter, type "Thanks", press Enter. Check the bubble and the answer.
  2. Type 10 lines with Shift+Enter and watch the box grow, then scroll. Clear it.
  3. In the console run `copy("x".repeat(300))`, paste, press Enter. Check the bubble. Repeat at 1024×768.
  4. Run `copy("a".repeat(2000))`, paste and check Send is enabled. Type one more character and check the message, Send and Enter. Delete it.
  5. Clear the box, type a few spaces and new lines, and check Send.
  6. Ask "Demo slow question". While it runs, try to type "Of those, how many are international?", press Enter, and check Send.
  7. When the answer arrives, press Enter at once on the typed question and check where it went.

### CH-17 No AI model yet
- **Who:** a GPSRC staff member on a freshly installed Hub
- **Story:** As a new user, I want Chat to tell me to add an AI model first and take me there, so that I know why I can't ask anything yet.
- **Stack:** replay (Demo), before any profile exists
- **Acceptance criteria:**
  - `/chat` shows "Add an AI model in Settings to start." with a "Go to Settings" link.
  - There is no question box and no "Answering with" select. "Recent questions" in the side nav shows "New chat" and "No conversations yet.".
  - "Go to Settings" opens `/settings`, which shows "No AI models yet. Add one to start asking questions." and "Add AI model".
  - After a model is added (ST-01), Chat shows the question box with that model selected, without a reload.
- **Walk:**
  1. On a fresh replay stack, before creating the Demo profile, open `/chat`. Read the page.
  2. Click "Go to Settings". Read the page.
  3. Add the Demo model through the form (ST-01, or the README's `curl`), go back to Chat with the nav, and check the box and selection.

### CH-18 A conversation link that no longer exists (`/chat/99999`, `/chat/abc`)
- **Who:** a GPSRC staff member opening a link a colleague pasted, or an old bookmark
- **Story:** As a staff member, I want a dead conversation link to say so and offer a new chat, so that I'm not stuck on an error.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `/chat/99999` shows "This conversation no longer exists." with a "Start a new chat" link, and no question box under it (expected; spec silent).
  - `/chat/abc` and `/chat/0` show the same (expected; spec silent).
  - No conversation in the list is highlighted.
  - "Start a new chat" opens `/chat` with "Ask a question about your data to start." and a working question box.
- **Walk:**
  1. Open `http://127.0.0.1:8083/chat/99999`. Read the page and the list.
  2. Click "Start a new chat". Ask the CH-01 question to check it works.
  3. Repeat steps 1–2 with `/chat/abc` and `/chat/0`.

### CH-19 Many conversations and a long thread
- **Who:** the GPSRC director after a term of daily use
- **Story:** As the director, I want a long conversation list and a long thread to stay easy to move through, so that I can find an old answer and keep working in a long conversation.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - With 20 or more conversations, "Recent questions" in the side nav shows them all, most recently used first. Each title takes at most two lines, cut with "…" when longer.
  - Hovering a cut-off title shows the full title (expected; spec silent).
  - The list scrolls inside the nav while the page links above it and "Signed in as …" below it stay in place.
  - "Recent questions" and "New chat" stay visible above the list while it scrolls (expected; spec silent).
  - In a thread of 12 or more questions, only the conversation pane scrolls; the "Answering with" row and the question box stay in place, and the page itself never scrolls or bounces.
  - After a question is sent in a long thread, the new question and its answer are scrolled into view without manual scrolling (expected; spec silent).
  - Reopening the long conversation shows all its questions in order.
- **Walk:**
  1. Create 20 conversations with the README's loop ("Make many conversations").
  2. Reload `/chat`. Check the order, the titles and the hover. Scroll the list hard and watch "New chat", the page links and "Signed in as …".
  3. In one conversation, ask 12 questions, cycling through the Demo questions (the "Show the SQL query" bars stay closed). Watch where the view is after each send, and scroll the thread hard both ways while watching the question box and the "Answering with" row.
  4. Open another conversation, then reopen the long one, and check its order.

### CH-20 Answer quality on five sponsor-style questions with a follow-up and "last term", sharing on and off
- **Who:** the GPSRC director deciding whether to trust the Hub
- **Story:** As the director, I want correct answers to the questions I actually ask, with the reading stated, so that I can use the numbers in reports.
- **Stack:** main (DeepSeek). Not walked on replay: the Demo model only knows its scripted questions.
- **Acceptance criteria:**
  - "How many unique people attended at least one event in Fall 2026?", asked with the switch off: 79. The summary is built on this computer, under "The AI wrote the SQL, so check it."
  - Its follow-up "Break that down by school, highest first.": School of Engineering 16 first; Biological Sciences, Social Sciences, Social Ecology, Humanities, Physical Sciences, Medicine and Paul Merage School of Business 8 each; School of Information and Computer Sciences 7. The one attendee with a blank school is left out (as the stated assumption says) or shown as a blank row with 1.
  - "Which event had the fewest attendees?": Postdoc Wellness Lunch, 18.
  - "List the names and emails of the postdocs who attended the Postdoc Wellness Lunch.", asked with the switch on: 8 rows of names and emails. The summary starts with "AI-generated summary. Check it against the table.", and every number in it matches the table.
  - "How many unique people attended an event last term?": a clarifying question saying no earlier term than Fall 2026 has events (or a stated assumption naming the term used). Never a silent answer for Fall 2026.
  - Every answer's "How I read your question" states its reading and assumptions (for example that "students" includes postdocs, or which term is meant).
  - Each answer arrives within 60 seconds.
- **Walk:**
  1. On main (`http://127.0.0.1:8080`), select "DeepSeek". If its Settings card has no "Can receive results" tag, edit it, turn on "Allow sending query results to this AI" for this story, and turn it off again at the end (the data is synthetic).
  2. In a new chat, switch off "Let AI see the results" and ask the first question, then the follow-up. Record the reading, the SQL, the summary and the table.
  3. Ask the third question.
  4. Switch on "Let AI see the results" and ask the fourth question. Compare the summary with the table.
  5. Ask the "last term" question.
  6. For each turn, record whether the table supports the summary and whether the answer matches the expected value.

### CH-21 The AI provider rejects the key
- **Who:** a GPSRC staff member whose API key was revoked or mistyped
- **Story:** As a staff member, I want a rejected key to be explained and fixable, so that I know to update Settings and can retry with another model.
- **Stack:** replay (Demo) and main (DeepSeek), with a temporary profile "Bad key" (preset DeepSeek, key `sk-invalid`), deleted at the end
- **Acceptance criteria:**
  - Asking with "Bad key" ends with the alert "The AI provider rejected the API key. Check this profile in Settings." and a "Retry" button. No SQL bar or table is shown (no SQL was written).
  - Choosing a working model in "Answering with" and clicking "Retry" sends the same question with that model, and its answer appears as the newest turn.
  - After a reload, the saved failed turn still says the key was rejected and points to Settings (expected; spec silent).
  - "Test" on the "Bad key" card in Settings shows "The AI provider rejected the API key. Check this profile in Settings.".
  - The key is never shown: the card shows only "…" (a key under 12 characters shows no part of itself).
- **Walk:**
  1. In Settings, click "Add AI model". Name "Bad key", Provider "DeepSeek" (Base URL fills in), Model `deepseek-chat`, API key `sk-invalid`. Save.
  2. Replay: in Chat choose "Bad key" and ask "How many unique people attended Bagel Breakfast, October?". Main: ask "How many unique people attended at least one event in Fall 2026?".
  3. Read the alert. Choose "Demo" (replay) or "DeepSeek" (main) and click "Retry".
  4. Reload and read the saved failed turn.
  5. In Settings, click "Test" on "Bad key" and read the result. Check the key hint.
  6. Delete "Bad key". On main, check `curl -s http://127.0.0.1:8080/api/llm-profiles` lists only "DeepSeek" and "DeepSeek Pro".

### CH-22 An answer that takes too long
- **Who:** a GPSRC staff member whose AI provider is very slow
- **Story:** As a staff member, I want a question that takes too long to stop with a clear message, so that I'm not left waiting with no end.
- **Stack:** replay (Demo), api restarted with `TURN_TIMEOUT_S=5`
- **Acceptance criteria:**
  - "Demo slow question" stops after about 5 seconds with "The question took too long to answer. Try a simpler question." and a "Retry" button.
  - After a reload, the saved turn shows "This question took too long to answer." with "Retry".
  - After the api is restarted with the default limits, "Retry" answers 38 after about 10 seconds.
- **Walk:**
  1. Restart the api with `TURN_TIMEOUT_S=5` (README, "Restart the api with other limits").
  2. In a new chat ask "Demo slow question". Time it and read the alert.
  3. Reload and read the saved turn.
  4. Restart the api with the default limits, then click "Retry" on the saved turn.
