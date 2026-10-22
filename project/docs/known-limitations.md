# Known limitations

What the Hub does not do yet, what is not confirmed, and where it can be wrong. Read this before you rely on an answer or an import. Items marked **Open** wait for a decision or a task. The test results behind the chatbot items are in [benchmark-results.md](benchmark-results.md).

## Decisions waiting for the sponsor

- **D1: the AI seeing query results is provisional. Open.** With "Let AI see the results" on, the AI receives the rows its query returned (up to 200 rows, 20,000 characters). That can include names and emails. It never receives Student IDs or other tables. The sponsor has not confirmed this. Each AI model has a setting, "Allow sending query results to this AI". Turn it off and no results leave the computer. No code change is needed. All presets except ZotGPT start off. See the [user guide](user-guide.md#4-who-sees-the-data-the-two-switches).
- **Waitlisted CampusGroups registrants. Open.** The Hub keeps every row of a CampusGroups export as an attendee. Whether waitlisted people should count is a question for the sponsor.
- **Does "students" include postdocs? Open.** The AI reads "students" with no named affiliation as everyone GPSRC serves, postdocs included. The sponsor has not confirmed that.
- **The Notes wording in the full download. Open.** The sponsor has not confirmed it.
- **The sponsor's two dummy export files have not arrived. Open.** All tests use the team's synthetic samples, which were modeled on the sponsor's compiled sheet. That sheet may itself be AI-generated, so real exports may differ from what was tested.

## Database logs can hold values

PostgreSQL logs a failing statement and its error message in the `db` container log. A generated query that fails can therefore put a value from the question or the data into `docker compose logs db`. These logs stay on the machine; check them before sharing. The fix, a superuser-only per-role log setting, is backlog.

## Chat answers can be wrong

The AI writes the SQL, so an answer can be wrong even when it looks reasonable. The table is the authority. The Hub shows the SQL and a "How I read your question" note so you can check.

- **Benchmark.** On the main model (DeepSeek, `deepseek-flash`) the AI answered 20 of 20 benchmark questions correctly on two runs in a row, and 10 of 10 on three runs of a set of 10 held-out questions written before tuning. A second model (DeepSeek Pro, `deepseek-v4-pro`) scored 19 of 20 and 10 of 10. The target is 18 of 20. Both benchmarked profiles are DeepSeek models on one provider. No second provider has been benchmarked, and ZotGPT is unverified.
- **The benchmark likely overstates how well it handles new wording.** All runs used one model family, 293 sample rows, and one term (Fall 2026). Several prompt rules match the benchmark's own readings. The held-out questions help, but they are only 10. Expect misses on new kinds of questions.
- **The second profile's q15 reading (records vs people).** The question is "What percentage of attendees at virtual events were doctoral students?". The main model counts attendance records, like the reference answer. DeepSeek Pro counted unique people instead. Both readings are sensible, and the question does not say which. Say "unique people" or "attendance records" when it matters. The "How I read your question" note shows which reading was used.
- **The "students" assumption is stated in most answers, not all.** In a spot check of nine answers, eight stated it. When an answer says "students", check the note, or name the affiliation (doctoral students, Master's students, postdocs).
- **Sharing analysis can only be checked for numbers present in the data.** The AI summary is told to use only numbers that are in the results. You can check a summary only against numbers that appear in the table. A figure the AI works out itself (a percentage, a difference, a ranking) has no row to check it against, and the Hub does not verify it. Compare every summary with the table.
- **Blank values.** Grouping by a column that can be blank (school, department, affiliation) leaves out the records where it is blank. The AI is asked to say so; check the note.
- **"Last term" needs more than one term.** The sample data has one term, so "last term" gives a clarifying question there. This was checked outside the benchmark only.
- **Large results.** The table shows at most 1,000 rows. A single-answer export holds up to 100,000 rows (`EXPORT_ROW_CAP`), and a notice appears when it is cut. A query that takes more than 5 seconds is stopped.
- The "How I read your question" note can sometimes use a database column name, such as person_key, instead of plain words. The answer itself is not affected.
- **Prompt text in data.** Free-text fields such as Department could contain text that tries to steer the AI summary. The summary is display-only and never used to write SQL, and the table shows the real data, but a summary could be misled.

## AI providers

- **ZotGPT is unverified. Open.** Its base URL, whether it supports JSON output, and its model names have not been confirmed (target 10/28). The ZotGPT preset takes any address you type. "Test" detects JSON support.
- **Message merging waits until the gateway is verified.** Some gateways reject two consecutive messages from the user. The Hub does not merge them yet. If ZotGPT turns out to need it, the fix is small, and the S5 detection of a rejected `response_format` is already in place.
- Only providers with an OpenAI-style API are supported. Native Anthropic and Gemini connectors are in the backlog.
- If `HUB_SECRET_KEY` changes, saved API keys cannot be decrypted. Enter them again in Settings. There is no key-rotation tool.

## Imports and identity

- **A person listed twice in one file.** The preview shows how many rows are "Duplicate in this event". The commit is the final check, so its "N rows imported" count can still differ from the preview.
- **Committed imports cannot be edited or deleted.** If you commit the wrong event name, term or date, the Hub cannot fix it. Check the form before you click Commit. You can only discard a file before committing. Editing event details and deleting a committed import are in the backlog. Until then, the team must correct the database directly.
- **Dot-name and `@hs.uci.edu` addresses (12twenty).** 12twenty exports have no NetID, so the Hub derives one only from emails that look exactly like `netid@uci.edu`. `first.last@uci.edu` or `name@hs.uci.edu` get no NetID and the flag "Non-standard email, NetID not derived". The same person then matches CampusGroups records only if the email is identical. Otherwise they appear as two people, which makes "unique people" counts too high. This is why uncertain cases are flagged and not merged.
- **Matching is exact.** Misspelled names or a person using two different emails and no NetID in either file are counted as two people. Names are never used to match.
- **Pending files.** The form text you typed is lost when you reload the browser page. The file stays on the Upload page.
- **One file per event.** A second file for the same event is a new event. Attaching a file to an existing event is in the backlog.
- **Upload the native export.** A file opened and re-saved in Excel without changes is still recognized as a duplicate. A file with edits is a different file, and it is rejected if the column names no longer match.
- The 12twenty `Registration Date` is never used as the event date, because it is the date people signed up.

## No login

The Hub has **no login** and no passwords. Anyone who can open `http://127.0.0.1:8080` on the computer sees all data, imports, AI models and conversations. The page is reachable only from the computer it runs on (the port is bound to `127.0.0.1`), and the only outgoing traffic is to the selected AI provider. Protect the computer itself with its normal login, screen lock and disk encryption. Login is in the backlog and the code has the seams for it (see the [handoff guide](handoff.md#moving-it-to-oit-and-adding-login)). The test that checks "no data without signing in" (A7) is deferred with it.

All staff share one built-in user, so everyone sees the same conversations.

## Other

- **Tested in Chromium (Playwright).** One export in Safari has not been tried yet.
- If the Hub server itself stops while it is answering a question, that question is not saved. The page shows "Connection lost. Retry."; retry it once the Hub is running again.
- **Pages are plain HTTP on localhost.** There is no HTTPS, because nothing leaves the computer.
- **No CI** and **no automatic backups**. See the [setup guide](setup-guide.md#7-back-up-and-restore).
- **Not built** (out of scope or backlog): reconciling registration with attendance, certificates, charts and dashboards, multiple accounts, hosting on a UCI server, UCI single sign-on, live links to CampusGroups, 12twenty or Zoom. See the backlog in the [handoff guide](handoff.md#backlog).
