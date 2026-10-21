# User stories

Every user story for the GPSRC Data Hub, written in S6 so that each one can be walked by hand in
the running app. The walk records what passes and what does not, and the failures become fixes.

| File | Page | Stories |
|---|---|---|
| [shell.md](shell.md) | side nav, page header, app-wide states | SH-01 … SH-07 |
| [chat.md](chat.md) | Chat | CH-01 … CH-22 |
| [upload.md](upload.md) | Upload | UP-01 … UP-19 |
| [dataset.md](dataset.md) | Dataset | DS-01 … DS-05 |
| [settings.md](settings.md) | Settings | ST-01 … ST-10 |
| `walkthrough-<date>.md` | the recorded walks (see "Recording a walk") | |
| `screenshots/` | screenshots the walk records refer to | |

## Story format

Each story is a `###` heading `<ID> <title>` followed by five parts:

```markdown
### UP-15 A file lists the same person twice
- **Who:** a GPSRC student worker entering an event
- **Story:** As a student worker, I want the preview to tell me when a file lists someone twice, so that the imported count does not surprise me.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - The preview card shows "Duplicate in this event: 1".
  - After Commit, the summary shows "18 rows imported" and "Duplicates in event 1": one row fewer imported than previewed.
- **Walk:**
  1. Run `scripts/story_files.py` and upload `Duplicate Person.csv`.
  2. ...
```

- **Acceptance criteria** say what a user should get, taken from the spec
  (`docs/specs/2026-10-20-data-hub-design.md`) and the design doc
  (`docs/design/2026-10-21-ui-redesign.md`), not what the code happens to do today. Text in
  double quotes is the exact text on screen. A criterion the app misses is a finding for the walk
  to record. It is not a reason to edit the story.
- **(expected; spec silent)** marks a criterion that neither document states, but that a
  reasonable user clearly expects. A failure of such a criterion is still recorded. Its finding
  says so, because the fix may need a design decision first.
- **Stack** names where the story is walked: **replay (Demo)**, **main (DeepSeek)** or both. Most
  stories also say what the stack must hold first (samples loaded, no profile yet, an api
  restarted with other limits).
- **Walk** is a numbered list of concrete steps. Unless the story says otherwise, the browser
  window is 1440×900, the replay stack is at `http://127.0.0.1:8083`, and the main stack is at
  `http://127.0.0.1:8080`.

## Story files

Several Upload stories need edge-case files that the samples do not cover. Generate them, from
`project/`, into a folder outside the repo (they are never committed):

```bash
uv run --project backend python scripts/story_files.py /tmp/story-files
```

The script uses only the Python standard library, so `python3 scripts/story_files.py <out_dir>`
works too. It reads `backend/sample_data/exports/` and writes:

| File | What it is | Used by |
|---|---|---|
| `Header Only.csv` | the header row of `Bagel Breakfast - October.csv`, nothing else | UP-08, UP-09, SH-03 |
| `Unknown Format.csv` | headers `Name,Mail,Event` and two made-up rows | UP-03, UP-07, UP-09 |
| `Notes.txt` | one line of text | UP-09 |
| `Bagel Breakfast - October (copy).csv` | the October CSV with CRLF line endings switched to LF: new bytes, same cells | UP-05, UP-10 |
| `Duplicate Person.csv` | `Postdoc Wellness Lunch.csv` with its first attendee row appended again | UP-15 |
| `Pending Then Broken.csv` | `Cover Letters for Academic Jobs.csv` renamed (same bytes); its stored copy is damaged in UP-14 | UP-14, UP-19 |
| `Over Size Limit.csv` | the October CSV with its attendee rows repeated to 21,804 bytes, over a 20,000-byte limit | UP-10 |
| `Edwards Site Visit - No Shows.xlsx` | `Edwards Life Science Site Visit.xlsx` with "Attended?" set to NO in rows 3 and 5 | UP-02, SH-07 |

The stories call this folder `<story-files>`. The ten sample exports themselves are in
`backend/sample_data/exports/`.

## Stack: replay (Demo)

A disposable Compose project, `hub-replay`, on port 8083, with the scripted "Demo" model and no
real API key. Everything below runs from `project/`. Nothing here touches the dev database.

**Bring it up** (it starts empty: no imports and no AI model):

```bash
HUB_HTTP_PORT=8083 HUB_ENABLE_FAKE_LLM=true LLM_SEED_NAME= LLM_SEED_PRESET= LLM_SEED_BASE_URL= LLM_SEED_MODEL= LLM_SEED_API_KEY= LLM_SEED_SHARE_RESULTS= docker compose -p hub-replay -f docker-compose.yml up -d --build
until curl -sf http://127.0.0.1:8083/api/health >/dev/null; do sleep 2; done
```

**Create the Demo profile** (skip this for CH-17 and ST-01, which need no profile; ST-01 creates
it through the form). The first profile becomes the default automatically:

```bash
curl -s -X POST http://127.0.0.1:8083/api/llm-profiles -H 'Content-Type: application/json' -d '{"name":"Demo","preset":"fake","model":"scripted"}'
curl -s http://127.0.0.1:8083/api/llm-profiles    # "Demo" with "is_default":true
```

If another profile is already the default, make Demo the default with
`curl -s -X POST http://127.0.0.1:8083/api/llm-profiles/<Demo's id>/default`.

**Helper profiles**, only for the stories that name them:

```bash
# CH-08, CH-10, ST-06: a second model that may receive results
curl -s -X POST http://127.0.0.1:8083/api/llm-profiles -H 'Content-Type: application/json' -d '{"name":"Demo B","preset":"fake","model":"scripted"}'
# CH-09: a model that may not receive results
curl -s -X POST http://127.0.0.1:8083/api/llm-profiles -H 'Content-Type: application/json' -d '{"name":"Demo No Share","preset":"fake","model":"scripted","share_results_with_llm":false}'
```

**Load the samples** when a story says "samples loaded" (10 files, 293 rows; files already
imported are skipped):

```bash
docker compose -p hub-replay exec api python -m app.samples
```

**Restart the api with other limits** (CH-06, CH-22, UP-10, ST-10). Repeat the bring-up variables
and add the story's limits. Only the api container is recreated, and the data stays:

```bash
# CH-06 and UP-10
HUB_HTTP_PORT=8083 HUB_ENABLE_FAKE_LLM=true LLM_SEED_NAME= LLM_SEED_PRESET= LLM_SEED_BASE_URL= LLM_SEED_MODEL= LLM_SEED_API_KEY= LLM_SEED_SHARE_RESULTS= DISPLAY_ROW_CAP=20 EXPORT_ROW_CAP=30 MAX_UPLOAD_BYTES=20000 docker compose -p hub-replay -f docker-compose.yml up -d api
# CH-22: use TURN_TIMEOUT_S=5 instead of the three caps. ST-10: use HUB_SECRET_KEY=<new key> instead.

# Back to the default limits (and the .env secret key)
HUB_HTTP_PORT=8083 HUB_ENABLE_FAKE_LLM=true LLM_SEED_NAME= LLM_SEED_PRESET= LLM_SEED_BASE_URL= LLM_SEED_MODEL= LLM_SEED_API_KEY= LLM_SEED_SHARE_RESULTS= docker compose -p hub-replay -f docker-compose.yml up -d api
```

After each restart, wait for `/api/health` (as above) and reload the browser.

**Simulate "server down"** (SH-04, CH-14, CH-15, UP-17, UP-18, DS-05):

```bash
docker compose -p hub-replay stop api
docker compose -p hub-replay start api    # then wait for /api/health
```

**Damage a pending import** (UP-14). The database's owner role is `hub_app`
(`db/init/01-roles.sh`):

```bash
docker compose -p hub-replay exec db psql -U hub_app -d hub -c "UPDATE hub.import_file SET content = 'not a spreadsheet' WHERE file_name = 'Pending Then Broken.csv' AND status = 'pending'"
# prints UPDATE 1
```

**Make many conversations** (CH-19). This creates 20 conversations with the default (Demo) model:

```bash
for i in $(seq 1 20); do
  id=$(curl -s -X POST http://127.0.0.1:8083/api/conversations | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
  curl -s -N -X POST "http://127.0.0.1:8083/api/conversations/$id/messages" -H 'Content-Type: application/json' \
    -d "{\"question\":\"How many unique people attended Bagel Breakfast, October? Conversation number $i, asked to fill the list with long titles\"}" >/dev/null
done
```

**Tear it down** at the end of a walk (removes the containers and the volume):

```bash
docker compose -p hub-replay down -v
```

## Stack: main (DeepSeek)

The main stack runs on the dev database with the 10 committed samples (293 rows), which the A1
acceptance test and the benchmark depend on. Rebuild it with the current code, from `project/`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

It serves `http://127.0.0.1:8080`. Use the AI model "DeepSeek".

- **Never upload or commit a file there,** and do not load the samples again. Before and after
  the walk, `curl -s http://127.0.0.1:8080/api/imports` must list the same 10 committed files.
- Asking questions is fine. Conversations do not change the dataset.
- Undo any temporary change: delete the "Bad key" profile (CH-21), and turn off sharing on
  "DeepSeek" again if CH-20 turned it on. At the end, `curl -s http://127.0.0.1:8080/api/llm-profiles`
  lists only "DeepSeek" and "DeepSeek Pro".
- Leave the stack running afterwards.

## Walk order

The stories share stacks and files, so this order keeps each one in the state it needs.

1. **Shell and Chat, replay.** Bring up a fresh replay stack.
   - Walk CH-17 first, before any profile exists.
   - Create the Demo profile and load the samples. DS-02 can be walked now, on a samples-only stack.
   - Walk SH-01 … SH-07, then CH-01 … CH-16, CH-18, CH-19, the replay part of CH-21 and CH-22. CH-06 and CH-22 restart the api and restore it.
   - Tear the stack down.
2. **Upload, Dataset and Settings, replay.** Bring up a fresh replay stack and do not load the samples.
   - Walk DS-03, then ST-01 (it creates "Demo").
   - Walk UP-01 … UP-19 in ID order (table below), then DS-04 and DS-05, then ST-02 … ST-10.
   - Tear the stack down. Bring up a fresh one, create Demo, load the samples, and walk DS-01 (and DS-02 if step 1 did not), then tear it down.
3. **Main.** Walk CH-03 (main part), CH-20, CH-21 (main part), ST-02's last step and ST-03's main part.

**Upload walk order.** The state each story leaves its files in:

| Story | Files | Left as |
|---|---|---|
| UP-01 | `Bagel Breakfast - October.csv` | committed |
| UP-02 | `Edwards Site Visit - No Shows.xlsx` | committed |
| UP-03 | `Bagel Breakfast - December.xlsx`, `Health Careers Mixer.xlsx`, `Unknown Format.csv` | the first two committed |
| UP-04 | `Bagel Breakfast - October.csv` | (duplicate, nothing stored) |
| UP-05 | `Bagel Breakfast - October (copy).csv` | (duplicate, nothing stored) |
| UP-06 | `Teaching Statements for Academic Jobs.csv` | pending |
| UP-07 | `Unknown Format.csv` | (rejected, nothing stored) |
| UP-08 | `Header Only.csv` | (rejected, nothing stored) |
| UP-09 | `Notes.txt`, `Header Only.csv`, `Unknown Format.csv` | (nothing stored) |
| UP-10 | `Over Size Limit.csv`, `Bagel Breakfast - October (copy).csv` | (nothing stored) |
| UP-11 | `Building your Brand Workshop.xlsx` | committed |
| UP-12 | `Edwards Life Science Site Visit.xlsx` | committed |
| UP-13 | `Teaching Statements for Academic Jobs.csv` | discarded |
| UP-14 | `Pending Then Broken.csv` | discarded |
| UP-15 | `Duplicate Person.csv` | committed |
| UP-16 | `LinkedIn Info Session.xlsx`, `Bagel Breakfast - November.csv` | committed |
| UP-17 | `Postdoc Wellness Lunch.csv` | committed |
| UP-18 | `Cover Letters for Academic Jobs.csv` | discarded |
| UP-19 | `Cover Letters for Academic Jobs.csv`, `Pending Then Broken.csv` | committed |
| DS-04 | `Teaching Statements for Academic Jobs.csv` | committed |

## Recording a walk

Record each walk in `docs/user-stories/walkthrough-<YYYY-MM-DD>.md` (the S6 walk is
`walkthrough-2026-10-21.md`). Walk; do not fix anything while walking.

1. **Header:** the date, the commit walked (`git rev-parse --short HEAD`), the stacks, and the
   browser and window size.
2. **One table per page** (Shell, Chat, Upload, Dataset, Settings), one row per story, and one row
   per stack for a story walked on both (`CH-03 (replay)`, `CH-03 (main)`):

   ```markdown
   | ID | Result | Notes | Screenshot |
   |---|---|---|---|
   | UP-15 | Fail → W-3 | Dataset's Rows shows 19 for Duplicate Person.csv | [UP-15](screenshots/UP-15-dataset-rows.png) |
   | CH-04 | Pass | | |
   ```

   - **Result** is one of:
     - `Pass`: every criterion holds;
     - `Fail → W-n`: at least one criterion fails, with a link to the finding;
     - `Covered by <test file>`: only when the state cannot be produced in the running app. Give the reason in Notes.
   - **Notes:** short. For a Fail, name the criterion that failed.
   - **Screenshot:** a link into `screenshots/`. Name the file `<ID>-<what>.png`. Use PNG at 1440×900 unless the story is about window size. Take one only where a picture shows something the text cannot.
3. **Findings** after the tables, one line each:

   ```markdown
   - W-3 (UP-15, DS-01) minor: Dataset's Rows column shows 19 for Duplicate Person.csv, which imported 18 rows; expected the rows in the dataset (expected; spec silent); open
   ```

   The format is `W-n (<story IDs>) <severity>: what happened; expected; status`.
   - **Severity:**
     - `blocker`: a core task cannot be done;
     - `major`: the task needs a workaround, or the screen misleads, or data or privacy is at risk;
     - `minor`: it works but is confusing or inconsistent;
     - `cosmetic`: looks only.
   - **Status:** the walk writes `open`. Task 15 replaces it with `Fixed in <short sha>` or `Left: <reason>`.

## Browser tips

- **Window size:** use the DevTools device toolbar, or Playwright's `page.setViewportSize`.
- **Sideways scroll:** in the console, `document.documentElement.scrollWidth - innerWidth` is `0` when the page does not scroll sideways.
- **Long text:** in the console, `copy("x".repeat(300))` puts 300 characters on the clipboard.
- **Go offline:** DevTools → Network → throttling "Offline", or Playwright's `context.setOffline(true)`.
- **Block a page's code (SH-06):** DevTools → More tools → Network request blocking. With Playwright, use `page.route(..., r => r.abort())`.
- **Read a chat answer's stream:** DevTools → Network → the `messages` request → EventStream.
- **Forget the remembered AI model:** delete `hub.chat.profileId` under DevTools → Application → Local Storage, or use a private window.
