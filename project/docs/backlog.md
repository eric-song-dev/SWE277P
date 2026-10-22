# Backlog: requested features and known bugs

Items the user asked to keep for later (2026-10-22). Each one gets a design draft for the user to review before any code is written. The older backlog (login, CI, P1 features and so on) is in the [handoff guide](handoff.md#backlog).

| ID | Kind | Item | Priority |
|---|---|---|---|
| B1 | Feature | Delete a conversation, and a retention setting | Medium (privacy) |
| B2 | Feature | A "Downloads" (or "Library") page for AI results | Medium |
| B3 | Feature | An "Insights" button on the Dataset page | Low |
| B4 | Bug | A second download of an imported event is recorded as a new event | High |

## B1. Delete a conversation, and a retention setting

**Request:**
- Each conversation can be deleted by hand.
- Settings gets a choice for how long conversations are kept: Never delete, 6 months, 3 months, 1 month.

**Today:**
- Conversations are kept forever. There is no delete API (`/api/conversations` only creates, lists, opens and asks), no delete button and no cleanup job.
- "Recent questions" lists every conversation, newest first, with no limit.
- Deleting a conversation in the database already deletes its turns (`chat_turn.conversation_id` is `ON DELETE CASCADE`).
- There is no store for app-wide settings yet. Settings only holds AI models.

**Points for the design:**
- A turn stores the question, the SQL, the reading, the AI summary and the title. It does not store result rows. With "Let AI see the results" on, the AI summary can contain names and emails, so retention is also a privacy question.
- `chat_turn` is the query log (spec section 13, safety layer 5). Deleting a conversation deletes its log. Decide whether to keep the question and SQL after the summary is removed.
- Before login, all staff share one user, so a deletion removes the conversation for everyone.
- The default should stay "Never delete", which is today's behavior, until the sponsor sets a policy.
- **Ask the sponsor:** does UCI set a retention period for records with student information, and does the office want a query log at all?

## B2. A "Downloads" (or "Library") page for AI results

**Request:** a page in the side nav that lists the AI results that can be downloaded as Excel or CSV, so staff do not have to find the right conversation first.

**Today:**
- Files are not stored. "Download Excel (.xlsx)" and "Download CSV (.csv)" call `GET /api/chat/turns/{id}/export`, which re-runs the turn's saved SQL on the current data.
- So a page like this would list answer turns (question, conversation, date, row count) with download buttons. Each file shows today's data, as "Show results" does.

**Points for the design:**
- Should the list hold every answer, or only the ones someone downloaded? The second needs a record of downloads.
- Is today's data right, or does staff need the exact file from the day of the answer? Keeping files means storing result rows, names and emails included, which ties in with B1's retention.
- Name: "Downloads" or "Library". It sits in the side nav after Dataset, with an icon, and also in the collapsed rail.

## B3. An "Insights" button on the Dataset page

**Request:** an "Insights" button on the Dataset page. Clicking it opens a new chat and sends a preset question, such as "What are the insights of this dataset?".

**Today:** the chatbot turns one question into one SQL query. An open question like this will probably get a clarifying question or one narrow query, not an overview. Check what it does before designing.

**Points for the design:**
- Option: the button sends a short, fixed set of questions one after another, for example attendance by event, unique people by school, people who came to several events, and the term-by-term count. Each gets its own answer card.
- Option: a separate "overview" mode with its own prompt. That is a prompt change, so re-run the benchmark (`benchmark.run`, `--set holdout` too).
- With result sharing off, answers have no AI summary, only the tables.

## B4. A second download of an imported event is recorded as a new event

This is a hole in the upload step. If the same event's attendee list is downloaded at two different times, the two files differ, so the Hub doesn't recognize them as one event and records it twice. It was found in the sponsor walkthrough as SF-1 (`docs/user-stories/walkthrough-2026-10-22.md`, with two screenshots).

**A concrete scenario:**

1. Right after the Bagel Breakfast on October 7, student worker A downloads the check-in list from CampusGroups. Only 35 people have checked in so far, and A uploads that file.
2. A few days later, 3 more check-ins are added. Student worker B doesn't know A already uploaded the list, downloads it again (38 people) and uploads it.

Both files come from the same event, but the Hub records them as two events:

| Event in the Hub | Term | Date | People |
|---|---|---|---|
| Bagel Breakfast, October | Fall 2026 | 10/07 | 35 |
| Bagel Breakfast, October | Fall 2026 | 10/07 | 38 |

The first 35 people appear in both, so they are counted twice.

**Why the current duplicate check doesn't catch it:**
- The check compares the file's contents (every cell in the table):
  - The same file uploaded twice: same contents, blocked.
  - A copy saved under a new name: same cells, blocked.
  - A fresh download a few days later: 3 more rows, so the contents differ and the Hub treats it as a new file.
- Every committed file creates a new event. The Hub never checks whether "Fall 2026 already has an event called Bagel Breakfast, October".
- The rule that a person counts once per event only works inside one event, not across two events with the same name.

**What goes wrong:**
- The event's head count doubles. Asked how many people attended the October Bagel Breakfast, Chat answered 73 (really 38).
- Rankings come out wrong. Asked which event had the most attendees this term, Chat said the October Bagel Breakfast with 73. The right answer is Health Careers Mixer with 45.
- The full dataset export has 35 duplicate rows, so it no longer matches the sponsor's compiled sheet.
- What stays correct: the total number of distinct people, because the Hub still recognizes each person as the same person.

The Hub gives no warning at any point. The upload result says "35 rows imported" and "Duplicates in event 0".

**Why it can't be undone:** a committed import can't be deleted in the UI. Only files that have not been committed can be discarded. Once someone notices the double upload, the only fix is for a developer to edit the database directly.

**How likely it is:** that depends on how the sponsor's office works: whether staff download the list before all check-ins are in, and whether two student workers ever handle the same event. The sponsor said clearly in the 2026-10-21 meeting that duplicate uploads must not happen, so this is worth asking the sponsor about.

**Repro:** upload a CampusGroups export, then a copy of it with a few rows removed, and keep the prefilled name and term. Ask "Which event had the most attendees this term?".

**How it could be fixed:**

1. **Warn in the upload preview.** If an event with the same name and term already exists, or most of the people in the file are already in one event, show a warning. The person uploading then chooses to replace the old one, add it as a new event anyway, or cancel.
2. **Allow deleting a committed import,** so a wrong upload can be undone.

Until it is fixed, staff are warned in `docs/known-limitations.md` ("One file per event").
