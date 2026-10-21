# Dataset stories

The list of imported files and the full-dataset download. Format, stacks and recording:
[README.md](README.md). Window 1440×900 unless a story says otherwise.

### DS-01 See what has been imported
- **Who:** the GPSRC director checking which events are in the Hub
- **Story:** As the director, I want one list of every imported file with its event, platform and counts, so that I can see at a glance what the dataset covers.
- **Stack:** replay (Demo), samples loaded
- **Acceptance criteria:**
  - The page header reads "Dataset", with "Download full dataset (.xlsx)" (filled) and "Download full dataset (.csv)" (outlined) on the right, each with a download icon.
  - The list has the columns "File", "Event", "Term", "Platform", "Rows", "Flags", "Uploaded by", "Uploaded at" and "Status".
  - With the 10 samples:
    - there are 10 rows, all with Status "Committed", Term "Fall 2026" and Uploaded by "GPSRC Staff";
    - Platform is "CampusGroups" for the five `.csv` files and `Bagel Breakfast - December.xlsx`, and "12twenty" for the other four;
    - the Rows column adds up to 293.
  - The newest upload is listed first. Clicking a column header sorts by it, and "Uploaded at" sorts by time.
  - Rows and Flags are right-aligned numbers.
  - At 1440×900, all nine columns fit without a sideways scrollbar in the list.
  - A file or event name too long for its column ends with "…", and its full text shows on hover.
- **Walk:**
  1. On the replay stack with the samples loaded, open Dataset. Read the header and the columns.
  2. Check the 10 rows and add up Rows.
  3. Click "Uploaded at" and "Rows" to sort, then "File".
  4. Check the list has no sideways scrollbar. Narrow the File column, or use 1280×720, until a name is cut, and hover it.
  5. Take a screenshot at 1440×900.

### DS-02 Download the full dataset (19 columns, Notes)
- **Who:** the GPSRC director preparing the term report in the sponsor's spreadsheet
- **Story:** As the director, I want the whole dataset in the GPSRC Data Project layout, so that it drops straight into the sheet I already use.
- **Stack:** replay (Demo), with only the 10 samples imported
- **Acceptance criteria:**
  - "Download full dataset (.xlsx)" saves `hub-dataset-<YYYYMMDD-HHMM>.xlsx`, and "Download full dataset (.csv)" saves `hub-dataset-<YYYYMMDD-HHMM>.csv`, with the current local date and time. Both buttons are disabled while a download runs.
  - Both files have the 19 columns of the GPSRC Data Project template, with the template's exact header text, from "Student Worker" to "Notes" (including its spellings, such as "Sponsor/Host/Parnters").
  - Both files have 293 data rows and 79 distinct NetIDs.
  - "On Campus Groups?" is "Yes" for CampusGroups rows and "No" for 12twenty rows. The Student ID column is filled for CampusGroups rows.
  - Every row's Notes starts with its source:
    - "Source: CampusGroups export";
    - or "Source: 12twenty export; 12twenty does not supply Student/Employee ID or domestic/international status".
  - Rows with missing data add "INCOMPLETE: …". The November Bagel Breakfast row without a NetID reads "Source: CampusGroups export; INCOMPLETE: NetID missing".
  - The Excel file opens without a repair warning.
- **Walk:**
  1. Use a stack where only the samples are imported: Task 12's stack before any upload, or a fresh replay stack with `app.samples` loaded.
  2. Click "Download full dataset (.xlsx)", then "Download full dataset (.csv)". Note the names.
  3. Open both. Compare the headers with `../data/GPSRC Data Project Template.xlsx` (outside `project/`).
  4. Count the data rows and the distinct NetIDs (for example a pivot or `cut` on the CSV), and read a few Notes, including the November row without a NetID.

### DS-03 Nothing imported yet
- **Who:** a GPSRC staff member on a freshly installed Hub
- **Story:** As a new user, I want an empty Dataset page to tell me nothing is imported and where to start, so that I know what to do first.
- **Stack:** replay (Demo), nothing imported
- **Acceptance criteria:**
  - The page shows "No files imported yet." and an "Upload" link instead of an empty list.
  - "Upload" opens the Upload page.
  - The download buttons still work and save a file with the 19 template headers and no data rows (expected; spec silent).
- **Walk:**
  1. On a fresh replay stack with no samples and no uploads, open Dataset. Read the page.
  2. Click "Download full dataset (.csv)" and "Download full dataset (.xlsx)", and open both files.
  3. Click "Upload".

### DS-04 A pending import links to Upload
- **Who:** a GPSRC student worker who left an upload unfinished
- **Story:** As a student worker, I want the Dataset page to show uploads that are still waiting and take me to finish them, so that none is forgotten.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - A file uploaded but not committed is listed with Status "Pending", shown as a link. Its Event and Term are empty.
  - Clicking "Pending" opens Upload, where that file's card waits with "Ready to commit", even after a full reload.
  - The full dataset download has none of its rows.
  - After it is committed on Upload, Dataset shows it as "Committed", with its Event and Term.
- **Walk:**
  1. Drop a file that is not imported yet on Upload (`Teaching Statements for Academic Jobs.csv` if it is free) and leave it pending.
  2. Reload, then open Dataset. Read its row.
  3. Download the full dataset (.csv) and search for the file's event name.
  4. Click "Pending". Check the card. Commit it, then open Dataset again.

### DS-05 A download fails
- **Who:** a GPSRC staff member downloading while the Hub is restarting
- **Story:** As a staff member, I want a failed download to say so, so that I don't believe a file was saved when it wasn't.
- **Stack:** replay (Demo)
- **Acceptance criteria:**
  - With the api stopped, "Download full dataset (.xlsx)" shows the red alert "The Hub server isn't responding. Check that it is running, then try again.". No file is saved, and both buttons work again.
  - The same happens for "Download full dataset (.csv)".
  - After the api is started, the next download saves the file and the alert disappears.
- **Walk:**
  1. Open Dataset while the api runs.
  2. Run `docker compose -p hub-replay stop api`. Click both download buttons in turn. Read the alert and check the browser's downloads.
  3. Run `docker compose -p hub-replay start api` and wait for `/api/health`. Click "Download full dataset (.xlsx)".
