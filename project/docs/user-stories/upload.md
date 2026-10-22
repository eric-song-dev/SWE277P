# Upload stories

Adding an event's attendee export, and every way an upload can go wrong. Format, stacks, the
story files and recording: [README.md](README.md). Window 1440×900 unless a story says otherwise.

Walk these in ID order on one fresh replay stack with **no samples loaded** and the Demo profile
created (ST-01 or the README's `curl`). Several stories share files, and the order keeps each
file in the state its story needs (README, "Upload walk order"). `<story-files>` is the folder
`scripts/story_files.py` wrote.

### UP-01 CampusGroups export
- **Who:** a GPSRC student worker entering an event
- **Story:** As a student worker, I want to drop the CampusGroups export as it is and confirm the event details, so that the attendees join the dataset without any hand-cleaning.
- **Stack:** replay (Demo), nothing imported yet
- **Acceptance criteria:**
  - The Upload page shows a drop zone reading "Drop CSV or Excel files here, or click to choose. (.csv, .xlsx, .xlsm)".
  - Dropping `Bagel Breakfast - October.csv` shows a progress bar while it uploads, then one card with:
    - the file name "Bagel Breakfast - October.csv" and the tag "Ready to commit";
    - "CampusGroups" and "38 rows";
    - no "rows skipped" line and no flag tags.
  - The form is prefilled:
    - Event name "Bagel Breakfast, October";
    - Event date 2026-10-07 (in the browser's date format);
    - Term "Fall 2026";
    - Entered by (student worker) "GPSRC Staff".

    Format, Sponsor/Host/Partners, Event type and Attendance source note are empty.
  - Event type offers "Professional Development", "Wellness/Mental Health" and "Fellowships", and accepts other text. Format offers "In Person", "Virtual" and "Hybrid".
  - "Commit" is disabled until Format and Event type are filled.
  - After Commit:
    - the tag reads "Committed";
    - the form and "Discard" are replaced by "38 rows imported" and "Linked by NetID 0", "Linked by email 0", "New people 38", "Unlinked 0", "Flagged rows 0", "Skipped 0", "Duplicates in event 0".
  - Dataset lists the file: Event "Bagel Breakfast, October", Term "Fall 2026", Platform "CampusGroups", Rows 38, Flags 0, Uploaded by "GPSRC Staff", Status "Committed".
  - In Chat, "How many unique people attended Bagel Breakfast, October?" answers 38.
- **Walk:**
  1. Open Upload. Read the drop zone.
  2. Drag `backend/sample_data/exports/Bagel Breakfast - October.csv` onto it. Check the bar, the card and each prefilled field.
  3. Open Event type and Format and read the choices. Check Commit is disabled.
  4. Choose Format "In Person" and Event type "Wellness/Mental Health", type Sponsor/Host/Partners "GPSRC", and click Commit.
  5. Read the summary. Take a screenshot.
  6. Open Dataset and read the row. Ask the question in Chat.

### UP-02 12twenty export with skipped rows
- **Who:** a GPSRC student worker entering an employer event tracked in 12twenty
- **Story:** As a student worker, I want the Hub to leave out people who registered but did not attend, and tell me which rows it left out, so that the dataset counts real attendance only.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `Edwards Site Visit - No Shows.xlsx` gives a card with "12twenty", "19 rows" and "2 rows skipped".
  - Clicking "2 rows skipped" lists "Row 3: Not marked as attended" and "Row 5: Not marked as attended".
  - The flag tags read "Department missing: 1" and "Skipped, not attended: 2".
  - The form is prefilled with Event name "Edwards Site Visit, No Shows", Attendance source note "12twenty attendance export" and Entered by "GPSRC Staff". Event date and Term are empty, because 12twenty exports do not hold them.
  - After Commit (Term "Fall 2026", Format "In Person", Event type "Professional Development"), the summary shows "19 rows imported" and "Skipped 2".
  - Dataset lists the file with Platform "12twenty" and Rows 19.
- **Walk:**
  1. Drop `<story-files>/Edwards Site Visit - No Shows.xlsx`.
  2. Check the counts. Click "2 rows skipped" and read the list. Read the tags and the form.
  3. Fill Term, Format and Event type, and click Commit. Read the summary.
  4. Open Dataset and read the row.

### UP-03 Several files at once
- **Who:** a GPSRC student worker catching up on a week of events
- **Story:** As a student worker, I want to drop several exports together and handle each one on its own card, so that I can catch up in one go.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Dropping `Bagel Breakfast - December.xlsx`, `Health Careers Mixer.xlsx` and `Unknown Format.csv` together shows one progress bar, then three cards:
    - "Bagel Breakfast - December.xlsx": "Ready to commit", "CampusGroups", "24 rows", "Email missing: 1";
    - "Health Careers Mixer.xlsx": "Ready to commit", "12twenty", "45 rows";
    - "Unknown Format.csv": "Rejected", with its reason.
  - Each card has its own form. Typing in one does not change another.
  - Committing the December card changes only that card. The Health Careers Mixer card keeps what was typed in it.
  - Both valid files can be committed, and Dataset lists both as Committed.
- **Walk:**
  1. Select the three files together (from `backend/sample_data/exports/` and `<story-files>`) and drop them on the zone, or choose them together in the file chooser.
  2. Check the three cards.
  3. Type Sponsor/Host/Partners "GPSRC / GPS-STEM" on the Health Careers Mixer card.
  4. Fill and commit the December card (Format "In Person", Event type "Wellness/Mental Health"). Check the Health Careers Mixer card still has its text.
  5. Fill and commit the Health Careers Mixer card (Term "Fall 2026", Format "In Person", Event type "Professional Development"). Open Dataset.

### UP-04 A file already imported
- **Who:** a GPSRC student worker who is not sure whether a colleague already uploaded an event
- **Story:** As a student worker, I want uploading an already imported file to be harmless and to say so, so that I can't create duplicate rows by mistake.
- **Stack:** replay (Demo), after UP-01
- **Acceptance criteria:**
  - Dropping `Bagel Breakfast - October.csv` again gives a card named "Bagel Breakfast - October.csv" with the tag "Duplicate", the text "Already imported" and the link "View it on the Dataset page". It has no form, Commit or Discard.
  - The link opens Dataset, which still lists the October file once and has no new row.
  - In Chat, the October question still answers 38.
  - The Duplicate card can be dismissed from the page (expected; spec silent).
- **Walk:**
  1. Drop `Bagel Breakfast - October.csv` on Upload. Read the card.
  2. Click "View it on the Dataset page". Count the October rows.
  3. Ask the October question in Chat.
  4. Back on Upload, look for a way to dismiss the Duplicate card.

### UP-05 A re-saved copy
- **Who:** a GPSRC student worker who opened an export in Excel and saved it under a new name
- **Story:** As a student worker, I want a copy of an imported export to be recognized even when its bytes changed, so that re-saving a file never doubles an event.
- **Stack:** replay (Demo), after UP-01
- **Acceptance criteria:**
  - `Bagel Breakfast - October (copy).csv` (the same cells, different line endings) gives a card named "Bagel Breakfast - October (copy).csv" with "Duplicate" and "Already imported".
  - The card names the file or event it duplicates ("Bagel Breakfast - October.csv" or "Bagel Breakfast, October"), so the student worker knows which import it matches (expected; spec silent).
  - Dataset has no new row.
- **Walk:**
  1. Drop `<story-files>/Bagel Breakfast - October (copy).csv`. Read the card.
  2. Open Dataset and count the rows.

### UP-06 The same pending file again
- **Who:** a GPSRC student worker who uploads a file, gets distracted, and uploads it again
- **Story:** As a student worker, I want a second upload of a file that is still waiting to bring me back to the same card, so that I don't end up with two pending copies.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Dropping `Teaching Statements for Academic Jobs.csv` gives a "Ready to commit" card ("CampusGroups", "26 rows", "Department missing: 1").
  - Dropping it again leaves exactly one card for it, with no error, and the text typed in the form is still there.
  - Dataset lists the file once, with Status "Pending".
  - After a reload, the page shows the card once. Dropping the file again still leaves one card.
- **Walk:**
  1. Drop `Teaching Statements for Academic Jobs.csv`. Type Sponsor/Host/Partners "GPSRC / Graduate Writing Hub".
  2. Drop the same file again. Count the cards and check the typed text.
  3. Open Dataset and count its rows.
  4. Back on Upload, reload. Count the cards. Drop the file again and count again. Leave it pending for UP-13.

### UP-07 An unknown format
- **Who:** a GPSRC student worker who picked the wrong spreadsheet
- **Story:** As a student worker, I want the Hub to reject a file that is not an attendee export and tell me why, so that I can find the right file.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `Unknown Format.csv` (headers `Name,Mail,Event`) gives a card with the tag "Rejected", the red text "File does not match a known export format; closest is CampusGroups.", and "Missing columns: First Name, Last Name, Email, Net ID, Event Registration UID". It has no form.
  - Nothing is stored: Dataset has no row for it, and after a reload the card is gone.
  - The Rejected card can be dismissed from the page (expected; spec silent).
- **Walk:**
  1. Drop `<story-files>/Unknown Format.csv`. Read the card.
  2. Look for a way to dismiss it.
  3. Open Dataset. Reload Upload.

### UP-08 A header-only export
- **Who:** a GPSRC student worker who exported an event before anyone checked in
- **Story:** As a student worker, I want an export with no attendees to be refused with a clear reason, so that I don't create an empty event.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `Header Only.csv` (the October header row and nothing else) gives a "Rejected" card with "This file has a header row but no attendee rows." and no "Missing columns" line.
  - It is not reported as a Duplicate, even though another header-only file would have the same cells.
  - Nothing is stored: Dataset has no row for it.
- **Walk:**
  1. Drop `<story-files>/Header Only.csv`. Read the card.
  2. Open Dataset.

### UP-09 An unsupported file type
- **Who:** a GPSRC student worker who grabbed a notes file instead of the export
- **Story:** As a student worker, I want the Hub to refuse files it cannot read before uploading them, so that I see the mistake at once.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - Dropping `Notes.txt` shows the warning "Unsupported file type, not uploaded: Notes.txt" and no card. Nothing is sent to the server.
  - Dropping `Notes.txt` together with `Header Only.csv` shows the same warning, and a card for `Header Only.csv` only.
  - The file chooser opened from the drop zone offers only `.csv`, `.xlsx` and `.xlsm` files.
  - The warning clears on the next upload that has no unsupported file.
- **Walk:**
  1. Drop `<story-files>/Notes.txt`. Read the page. In DevTools → Network, check no `imports` request was sent.
  2. Drop `Notes.txt` and `Header Only.csv` together.
  3. Click the drop zone and look at which files the chooser lets you pick. Cancel.
  4. Drop `Unknown Format.csv` and check the warning is gone.

### UP-10 A file over the size limit (`MAX_UPLOAD_BYTES=20000`)
- **Who:** a GPSRC student worker with an unusually large export
- **Story:** As a student worker, I want a file that is too big to be refused with the limit stated, so that I know what to do instead.
- **Stack:** replay (Demo), api restarted with `MAX_UPLOAD_BYTES=20000`
- **Acceptance criteria:**
  - `Over Size Limit.csv` (21,804 bytes) gives a "Rejected" card that says the file is too large.
  - The message names the real limit in a readable unit (about 20 KB here), never "0 MB" (expected; spec silent).
  - Nothing is stored: Dataset has no row for it.
  - A file under the limit is handled as usual: `Bagel Breakfast - October (copy).csv` (7,553 bytes) is reported as "Duplicate", not as too large.
- **Walk:**
  1. Restart the api with `MAX_UPLOAD_BYTES=20000` (README, "Restart the api with other limits"). Reload Upload.
  2. Drop `<story-files>/Over Size Limit.csv`. Read the card.
  3. Drop `<story-files>/Bagel Breakfast - October (copy).csv`. Read its card.
  4. Open Dataset. Restart the api with the default limits.

### UP-11 Fix event details before Commit (term, required fields)
- **Who:** a GPSRC student worker typing event details quickly
- **Story:** As a student worker, I want the form to stop me from committing incomplete or badly formatted details and show me what to fix, so that every event in the dataset is complete.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `Building your Brand Workshop.xlsx` gives "12twenty", "27 rows", "School missing: 1" and "Degree missing: 1". Term and Event date are empty, and Commit is disabled.
  - The required fields are marked with "*": "Event name", "Term", "Format" and "Event type".
  - Term shows the hint "e.g. Fall 2026". Typing "fall 2026", "Fall 26", "Autumn 2026" or "Fall ２０２６" (full-width digits) turns it red with "Use a season and year, like Fall 2026", and Commit stays disabled. "Fall 2026" clears the error.
  - An Event name of only spaces counts as empty, and Commit stays disabled.
  - While Commit is disabled, the form makes clear which required field still needs a value (expected; spec silent).
  - Event type accepts text that is not in the list ("Career Workshop").
  - With Event date left empty and every required field valid, Commit works: "27 rows imported". Dataset shows Event "Building your Brand Workshop" and Term "Fall 2026".
- **Walk:**
  1. Drop `Building your Brand Workshop.xlsx`. Read the card and the form. Check Commit.
  2. Type each wrong term in turn and read the field. Type "Fall 2026".
  3. Replace Event name with spaces and check Commit. Restore "Building your Brand Workshop".
  4. Choose Format "Hybrid". Leave Event type empty and look for what tells you it is missing. Type "Career Workshop".
  5. Click Commit. Read the summary and the Dataset row.

### UP-12 Leave the page mid-form and come back, then reload
- **Who:** a GPSRC student worker who is interrupted while entering details
- **Story:** As a student worker, I want my half-typed event details to survive a trip to another page, and the pending file to survive a reload, so that an interruption doesn't lose the upload.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - After typing into the form of `Edwards Life Science Site Visit.xlsx` and visiting Chat and Dataset, Upload shows the same card with everything typed still there.
  - Dataset lists the file with Status "Pending" while it waits.
  - After a full reload, the card comes back ("Ready to commit", "12twenty", "21 rows", "Department missing: 1"). The form shows the prefilled values again: Term and Format empty, Attendance source note "12twenty attendance export". Typed text is gone after a reload, as the user guide says.
  - The restored card can be committed: "21 rows imported".
- **Walk:**
  1. Drop `Edwards Life Science Site Visit.xlsx`. Type Term "Fall 2026", choose Format "In Person", type Sponsor/Host/Partners "GPSRC / Edwards Lifesciences", choose Event type "Professional Development".
  2. Click Chat, then Dataset (read the Status), then Upload. Check every field.
  3. Reload. Check the card and the form.
  4. Fill the form again and commit.

### UP-13 Discard a pending import
- **Who:** a GPSRC student worker who uploaded the wrong event
- **Story:** As a student worker, I want to throw away an upload before committing it, so that nothing from it reaches the dataset.
- **Stack:** replay (Demo), after UP-06
- **Acceptance criteria:**
  - "Discard" on the `Teaching Statements for Academic Jobs.csv` card removes the card.
  - Dataset no longer lists the file, and the dataset has none of its rows.
  - After a reload, the card does not come back.
  - Dropping the file again gives a fresh "Ready to commit" card with the prefilled form, not "Duplicate".
- **Walk:**
  1. If the card from UP-06 is not on the page, drop `Teaching Statements for Academic Jobs.csv` first.
  2. Click "Discard". Open Dataset. Reload Upload.
  3. Drop the file again. Read the card, then click "Discard" again.

### UP-14 A pending import that no longer loads
- **Who:** a GPSRC student worker whose waiting upload was damaged on the server
- **Story:** As a student worker, I want a waiting upload that cannot be shown to say so and let me retry or throw it away, so that it doesn't silently block the file.
- **Stack:** replay (Demo). `Cover Letters for Academic Jobs.csv` must not be imported or pending yet, because `Pending Then Broken.csv` has the same bytes.
- **Acceptance criteria:**
  - After the stored file is damaged and Upload is reloaded, a card shows the file name "Pending Then Broken.csv", "Could not load this pending import. Try again, or discard it and upload the file again.", and the buttons "Try again" and "Discard".
  - "Try again" disables both buttons while it runs, then shows the same card again (the file is still damaged).
  - "Discard" removes the card, and Dataset no longer lists the file.
  - After the discard, dropping `Pending Then Broken.csv` again gives a normal "Ready to commit" card.
- **Walk:**
  1. Drop `<story-files>/Pending Then Broken.csv`. Check its card ("CampusGroups", "29 rows") and leave it pending.
  2. Damage the stored bytes (README, "Damage a pending import").
  3. Reload Upload. Read the card.
  4. Click "Try again". Watch the buttons.
  5. Click "Discard". Open Dataset.
  6. Drop `Pending Then Broken.csv` again, read the card, then click "Discard" (UP-18 and UP-19 need the file free).

### UP-15 A file lists the same person twice
- **Who:** a GPSRC student worker entering an event
- **Story:** As a student worker, I want the preview to tell me when a file lists someone twice, so that the imported count does not surprise me.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - `Duplicate Person.csv` gives "CampusGroups" and "19 rows", with the tags "Domestic/international missing: 1" and "Duplicate in this event: 1".
  - After Commit, the summary shows "18 rows imported" and "Duplicates in event 1": one row fewer imported than previewed.
  - Dataset's Rows column for `Duplicate Person.csv` shows 18, the rows that are in the dataset (expected; spec silent).
  - The full dataset download has 18 rows for the event "Duplicate Person", one per person.
- **Walk:**
  1. Run `scripts/story_files.py` (README) and drop `<story-files>/Duplicate Person.csv`.
  2. Read the card's tags.
  3. Fill Format "In Person" and Event type "Wellness/Mental Health", and click Commit. Read the summary.
  4. Open Dataset and read the file's Rows. Download the full dataset (.csv) and count the "Duplicate Person" rows.

### UP-16 Rows missing NetID or email (flags)
- **Who:** a GPSRC student worker entering exports with incomplete attendee details
- **Story:** As a student worker, I want the preview to point out rows with a missing NetID or email, and the Hub to link people by email when the NetID is missing, so that I know which rows need checking and nobody is double-counted.
- **Stack:** replay (Demo), after UP-01 (the October Bagel Breakfast is committed)
- **Acceptance criteria:**
  - `LinkedIn Info Session.xlsx` gives "12twenty", "34 rows", "NetID missing: 1" and "Email missing: 1".
  - The preview tells that one row has neither a NetID nor an email, so the person cannot be matched (for example "Email/NetID unavailable: 1"), not only the two separate counts (expected; spec §6, `missing_identity`).
  - After Commit, the summary shows "34 rows imported", "Unlinked 1" and "Flagged rows" of at least 1.
  - `Bagel Breakfast - November.csv` gives "CampusGroups", "31 rows" and "NetID missing: 1". After Commit, the summary shows "31 rows imported" and "Linked by email 1": the row without a NetID was matched to an October attendee by email.
  - In the full dataset download:
    - the LinkedIn row's Notes read "Source: 12twenty export; 12twenty does not supply Student/Employee ID or domestic/international status; INCOMPLETE: email/NetID unavailable";
    - the November row's Notes read "Source: CampusGroups export; INCOMPLETE: NetID missing".
- **Walk:**
  1. Drop `LinkedIn Info Session.xlsx`. Read the tags.
  2. Commit it (Term "Fall 2026", Format "Virtual", Event type "Professional Development"). Read the summary.
  3. Drop `Bagel Breakfast - November.csv`, read the tags, commit it (Format "In Person", Event type "Wellness/Mental Health"), and read the summary.
  4. Download the full dataset (.csv) and find both rows' Notes.

### UP-17 The server is down at Commit
- **Who:** a GPSRC student worker whose Hub stopped while they filled in the form
- **Story:** As a student worker, I want a failed Commit to keep my details and let me try again, so that I don't retype them or commit twice.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - With the api stopped, Commit on the `Postdoc Wellness Lunch.csv` card shows "The Hub server isn't responding. Check that it is running, then try again." under the form.
  - The card stays "Ready to commit", everything typed is still there, and Commit is enabled again.
  - After the api is started, Commit succeeds once: "18 rows imported".
  - Dataset lists `Postdoc Wellness Lunch.csv` exactly once, as Committed.
- **Walk:**
  1. Drop `Postdoc Wellness Lunch.csv`. Choose Format "In Person", type Event type "Wellness/Mental Health" and Sponsor/Host/Partners "Postdoctoral Affairs".
  2. Run `docker compose -p hub-replay stop api`. Click Commit. Read the card.
  3. Run `docker compose -p hub-replay start api` and wait for `/api/health`. Click Commit.
  4. Open Dataset and count the file's rows.

### UP-18 The server is down while uploading
- **Who:** a GPSRC student worker whose Hub is not running
- **Story:** As a student worker, I want an upload that cannot reach the server to say so, so that I know to start the Hub and try again.
- **Stack:** replay (Demo), after UP-14 (`Cover Letters for Academic Jobs.csv` free)
- **Acceptance criteria:**
  - With the api stopped, dropping `Cover Letters for Academic Jobs.csv` shows the progress bar, then the error "Upload failed for Cover Letters for Academic Jobs.csv: The Hub server isn't responding. Check that it is running, then try again." with a close button. No card appears.
  - The close button removes the error.
  - After the api is started, dropping the file again gives one "Ready to commit" card, and Dataset lists the file once as Pending.
- **Walk:**
  1. Run `docker compose -p hub-replay stop api`. Drop `Cover Letters for Academic Jobs.csv`. Read the page, then close the error.
  2. Run `docker compose -p hub-replay start api` and wait for `/api/health`. Drop the file again. Read the card and the Dataset row.
  3. Click "Discard" on the card (UP-19 needs the file free).

### UP-19 The same export twice in one batch
- **Who:** a GPSRC student worker who selected an export and its renamed copy together
- **Story:** As a student worker, I want two copies of one export dropped together to give one card, so that I can't import the event twice.
- **Stack:** replay (Demo), after UP-18 (`Cover Letters for Academic Jobs.csv` free)
- **Acceptance criteria:**
  - Dropping `Cover Letters for Academic Jobs.csv` and `Pending Then Broken.csv` (the same bytes) together gives exactly one "Ready to commit" card ("CampusGroups", "29 rows"), named after one of the two files.
  - Dataset lists one Pending row for them.
  - Committing that card gives "29 rows imported". A later drop of either file gives "Duplicate".
- **Walk:**
  1. Select both files together and drop them. Count the cards.
  2. Open Dataset and count the rows.
  3. Commit the card (Format "Virtual", Event type "Professional Development"). Drop `Pending Then Broken.csv` again and read the card.
