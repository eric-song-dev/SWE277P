# Project Charter

## Program Registration & Attendance Data Hub

| | |
|---|---|
| **Course** | SWE 277P Capstone Project in Software Engineering, Assignment 4 |
| **Authors** | Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song |
| **Date** | October 18, 2026 |
| **Version** | 1.0. Adapted from our Business Case (Assignment 3) and our Project Scope and High-Level Design (v2.0, October 16, 2026) |
| **Sponsor** | Kayleigh Anderson-Natale, PhD, UCI Graduate Division |

### Project Stakeholders

| Name | Title | Role in this project |
|---|---|---|
| Kayleigh Anderson-Natale, PhD | Director of Postdoc and Professional Development, UCI Graduate Division (GPSRC) | Project sponsor and primary user. Sets priorities and accepts deliverables |
| Rosie Victor | GPSRC staff | User and subject-matter expert on the current data process; provides sample data |
| Karen Friedlander | GPSRC staff | User and subject-matter expert; checks that the sample files match real 12twenty and CampusGroups exports |
| GPSRC student assistants | Front-desk student employees | Users who download event exports and upload them to the Hub |
| Graduate Division dean and leadership; partner schools | Report recipients | Receive counts and lists from GPSRC staff; no access to the system |
| Graduate students and postdocs | Event attendees | Data subjects; their records are protected under FERPA |
| UCI Office of Information Technology (OIT) | Provider of the ZotGPT Gateway AI service | Supplies AI access and test credits; would review any future real-data use or server hosting |
| Prof. Emily Navarro | Instructor, SWE 277P | Project-management guidance; weekly team meetings; course evaluation |
| Rakib Hossain | Teaching Assistant, SWE 277P | Weekly team meetings; course evaluation |
| Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song | MSWE students | Project team: plan, design, build, test, document, and hand off the prototype |

---

## 1. Project Description

### 1.1 Background and current situation

The Graduate & Postdoctoral Scholar Resource Center (GPSRC) in UCI Graduate Division runs professional development, wellness, and fellowship events for graduate students and postdocs throughout the year. Each event produces its own attendance file. Today the data moves like this:

1. Students and postdocs register for an event on **CampusGroups/ZotSpot** or **12twenty**.
2. At the event they check in on a GPSRC iPad or laptop (a Google Form), or they join on Zoom.
3. Student assistants compare check-ins with registrations and mark attendance on the platform.
4. They download that event's attendee list and paste it into a year-long "GPSRC Data Project" Google Sheet, typing in the event details by hand.

### 1.2 Problem: the sponsor's pains and frustrations

Step 3 is routine front-desk work, and the sponsor told us it is not a pain point. The pain starts after step 4, when someone needs an answer from the data:

- **The data is scattered.** There is one attendee file per event and one large sheet per academic year. Excel becomes hard to filter and combine across terms and years.
- **The two platforms export different fields.** CampusGroups includes NetID, Student ID, and domestic/international status. 12twenty includes none of these, identifies people only by email, and says "Major/Academic Program" where CampusGroups says "Department".
- **Common reporting questions take manual work.** A new dean asked for a full year of programming data. A school asked how many of its students attended. Staff want to invite past Bagel Breakfast attendees to a new Donut Breakfast. Because the sheet counts rows rather than people, even "how many *unique* students came?" means cleaning data by hand.
- **There is no easy query tool.** The sponsor has some SQL experience but has not used it in years, and other staff should not need SQL at all.

> "Every once [in a] while I am asked to do reporting and I have to get out a ton of Excel sheets … I have to work across different documents, I have to compile documents."
> — Kayleigh Anderson-Natale, sponsor meeting, October 14, 2026

### 1.3 How the scope changed

The sponsor's original proposal, a "Registration & Attendance Reconciliation Hub", centered on matching registrations to Zoom and sign-in records and on tracking certificate programs. In the October 7 and October 14 meetings the sponsor narrowed it:

- Reconciliation stays with the student assistants.
- Certificate programs are deferred.
- Inputs are limited to the two platforms' attendee exports.
- The tool runs locally on one computer instead of in a public cloud.

On October 16 the course instructor advised us to deliver the sponsor's core request first and to add features sprint by sprint only after it works. This charter records the narrowed scope and **replaces the scope in the original proposal**.

### 1.4 Proposed solution

We will build **the Hub**, a web application that runs on one GPSRC computer:

- Staff drag in each event's attendee export, unchanged, and confirm the event details.
- Every upload is added to **one permanent dataset** that grows across academic years. The Hub recognizes the same person across events by NetID or email.
- Staff ask questions in plain English through an **AI chatbot** and get exact numbers, student lists, and email lists, each downloadable as an Excel file.
- The AI only writes SQL from a *description* of the data. The Hub runs that SQL locally under a read-only database account, so student records never leave the computer.

### 1.5 Desired impact

- **Show the GPSRC's reach** to the dean, Graduate Division leadership, and partner schools: by school, by program, and by unique student.
- **Find gaps in service**, such as schools or programs whose students rarely attend (the sponsor's example was humanities students).
- **Answer ad hoc requests quickly.** Counts and outreach lists come from one tool instead of several spreadsheets.
- **Leave a foundation** that UCI could later move to an OIT server, with handoff documentation.

The sponsor was clear that the main value is **better reporting**, not staff time saved.

---

## 2. Measurable Organizational Value (MOV)

### 2.1 MOV statement

> **This project will be successful if**, by December 4, 2026, GPSRC staff can load the sponsor's sample 12twenty and CampusGroups exports into one unified dataset that matches the sponsor's compiled sheet, and can get correct, Excel-exportable answers to at least 90% (18 of 20) of a benchmark of sponsor-style reporting questions through the chatbot, each in under one minute.

### 2.2 MOV details

| Area of impact | Value | Metric and target | How we will verify it |
|---|---|---|---|
| **Strategic** | *Do more:* answer reporting questions that are hard or impossible to answer from the spreadsheets today, such as unique students per school across events | At least **18 of 20** benchmark questions answered correctly by the chatbot | Benchmark run at the final demo. Expected answers are computed from the sponsor's `GSPRC Compiled Dataset.xlsm` |
| **Operational** | *Better:* one consistent dataset with each person counted once | The 10 sample files import into **293 rows and 79 unique NetIDs**, matching the compiled sheet, and uploading a file a second time adds **0 rows** | Automated import test at the end of Sprint 1 (October 28), repeated at the final demo |
| **Operational** | *Faster:* quick turnaround for reports and outreach lists | **Under 1 minute** from typing a question to downloading its Excel result. Today the same answer means opening and combining several spreadsheets by hand | Timed with the sponsor during the final demo |

**How a benchmark answer is scored.** An answer is correct when the result of the chatbot's SQL equals the expected result, even if the SQL is written differently. The 20 benchmark questions are based on the sponsor's real examples and are kept separate from the worked examples given to the AI. Three examples, with answers verified on the sample data:

| Question | Expected answer |
|---|---|
| How many unique Biological Sciences students came to a Bagel Breakfast in Fall 2026? | 6 |
| Which school had the fewest unique attendees in Fall 2026? | School of Information and Computer Sciences (7) |
| List the emails of everyone who attended any Bagel Breakfast. | 55 unique addresses |

### 2.3 How the MOV supports the GPSRC's goals

The GPSRC wants to show leadership how graduate students and postdocs engage with its programs and to find where access falls short. The MOV measures exactly that capability: correct answers to the questions leadership and partner schools actually ask, drawn from one dataset that covers every event instead of one spreadsheet per year. Exact counts matter because these numbers go into reports to the dean, which is why the database computes every answer and the AI only writes the query. Because each result exports to Excel, staff can keep building charts and reports the way they do today.

### 2.4 Changes since the Business Case

- "Merging the sample files" now has a precise, testable target: 293 rows, 79 unique NetIDs, and no duplicate rows on re-upload.
- We defined how a benchmark answer is scored.
- We added the under-one-minute turnaround target.
- **Status:** we will ask the sponsor to confirm the MOV and its targets at the October 21 weekly meeting.

---

## 3. Project Scope

### 3.1 In scope: the MVP (committed)

| # | Capability | What it includes |
|---|---|---|
| 1 | Import platform exports | 12twenty (.xlsx) and CampusGroups (.csv or .xlsx) attendee exports, used exactly as downloaded. The source is detected from the header row. Unknown layouts are rejected with the missing columns listed. Rows with blank fields are kept and flagged |
| 2 | Event details at upload | Staff enter or confirm event name, date, term, in-person/virtual/hybrid, host/partners, event type, and who entered the data, since the exports do not contain these |
| 3 | One common layout | Every row is converted to the 19 columns of the sponsor's GPSRC Data Project template. Fields a platform does not provide stay blank and are never guessed. Each row keeps its source file and row number |
| 4 | Permanent, growing dataset | A local database that is not split by academic year. Uploading the same file twice is blocked |
| 5 | One person across events | Records are linked by exact NetID, then by exact email. Rows with neither are kept and flagged. There is no fuzzy merging |
| 6 | AI chatbot | A plain-English question returns a number, table, or list, together with a one-line summary, the filters used, the generated SQL, and any assumption made (for example, academic year versus calendar year) |
| 7 | Privacy and SQL safety | The AI receives only the question and a description of the data, never student records or results. Generated SQL must be a single read-only query on one approved view, and it runs under a read-only database account. Every query is logged |
| 8 | Switchable AI provider | ZotGPT Gateway (UCI OIT) by default. OpenAI or DeepSeek can be selected in a settings file with no code change |
| 9 | Excel and CSV export | Every result and the full dataset can be downloaded. Values that Excel would run as formulas are written as plain text |
| 10 | Local install and login | One-command install with Docker Compose on one computer, reachable only from that computer. One staff account; no data can be viewed without signing in |

### 3.2 Deliverables (due December 4, 2026)

- The working prototype with a setup guide
- The database schema and a data dictionary
- Import mappings for both exports, plus the synthetic sample files used for testing
- The chatbot benchmark (20 questions with expected answers) and its results for each provider
- Automated tests, including the security tests
- A user guide, a known-limitations list, and handoff notes for a possible later move to an OIT server

### 3.3 Acceptance criteria

The sponsor accepts the MVP when, on the synthetic sample data:

1. The 10 sample files import into the same data as the compiled sheet (293 rows, 79 unique NetIDs), and re-uploading a file adds no rows.
2. The chatbot answers at least 18 of the 20 benchmark questions correctly, and still works after the provider is switched in the settings file.
3. Every table or list result downloads as Excel, and no exported cell runs as a formula.
4. The log of AI requests contains no student rows or query results.
5. Harmful SQL (for example DROP, DELETE, multiple statements, or reading the user-account table) is refused by the SQL check and, tested separately, by the read-only database account.
6. No data can be viewed or exported without signing in.

### 3.4 Stretch goals (not committed)

We will start these only after the sponsor accepts the MVP (planned for week 8), and only if sprint capacity allows:

- **Filter table without AI.** Filter the dataset by column and export the result. This gives staff a fallback when the AI is wrong or offline.
- **Data-quality view.** List rows missing a NetID, email, or school, and let staff fill in blanks by hand, as the sponsor asked on October 7.

### 3.5 Out of scope

| Item | Reason | Future path |
|---|---|---|
| Registration–attendance reconciliation, including Zoom, Google Form, and paper sign-in files | Student assistants already do it at the front desk; the sponsor said it is not a pain point (October 14) | A change request after the MVP, if the sponsor asks for it |
| Certificate and multi-session program tracking | Deferred by the sponsor (October 7) | Later phase |
| Charts and dashboards | The sponsor builds charts in Excel from exported data (October 14) | Later phase |
| Proactive AI insights, chatbot follow-up questions, saved queries | Not requested by the sponsor; they add AI risk | Later phase |
| Multiple staff accounts and permission roles | One staff login is enough for a single-computer prototype (October 14) | Needed only if the Hub moves to a shared server |
| Import of last year's GPSRC Data Project sheet | Not yet confirmed by the sponsor | A change request, if confirmed on October 21 |
| Public cloud hosting, OIT server deployment, UCI single sign-on, production use | The sponsor ruled out public cloud for privacy (October 14); hosting at UCI needs an OIT review | Later phase with OIT |
| Student information system integration; live 12twenty, CampusGroups, or Zoom APIs; writing back to these platforms | Outside the proposal's boundary; the platforms remain the system of record | None planned |
| Arbitrary spreadsheet formats; automatic fuzzy merging of people | Keeps imports predictable; the sponsor does not want the system to guess | None planned |
| Real student data | The capstone uses synthetic data only | After a UCI privacy and security review |

---

## 4. Project Schedule Summary

**Start date:** September 24, 2026 &nbsp;·&nbsp; **End date:** December 4, 2026 &nbsp;·&nbsp; **Duration:** 10 weeks

After initiation and planning, we work in one-week sprints. Sponsor check-ins are on Wednesdays, and instructor meetings are during Tuesday class.

| Week | Dates | Phase | Main work | Milestone or checkpoint |
|---|---|---|---|---|
| 1 | Sep 24–30 | Initiation | Team formation; review of the sponsor's proposal | Team statement submitted (Oct 6) ✓ |
| 2 | Oct 1–7 | Initiation | First sponsor meeting: current data process, templates, identifiers | Sponsor kickoff (Oct 7) ✓ |
| 3 | Oct 8–14 | Initiation | MOV draft; review of sample data; scope discussion with the sponsor | Scope narrowed to compile-and-query with local deployment (Oct 14) ✓ |
| 4 | Oct 15–21 | Planning | Instructor consultation (Oct 16); scope and design document; business case; this charter; repository, Docker Compose skeleton, and CI | **Sponsor confirms scope and MOV (Oct 21)** |
| 5 | Oct 22–28 | Sprint 1 | Database schema; import of both exports; event-details form; identity linking; check ZotGPT Gateway compatibility | Sample files reproduce the compiled sheet (293 rows, 79 NetIDs) |
| 6 | Oct 29–Nov 4 | Sprint 2 | Chatbot pipeline: prompt, provider adapters, SQL check, read-only account; draft the 20-question benchmark with the sponsor | First chatbot answers on sample data |
| 7 | Nov 5–11 | Sprint 3 | Chat screen, answer view, Excel/CSV export, login; security tests | **Mid-project demo of the end-to-end MVP to the sponsor.** Nov 11 is Veterans Day, so the check-in will be rescheduled that week |
| 8 | Nov 12–18 | Sprint 4 | Fixes from sponsor feedback; benchmark tuning; stretch goals only if the MVP is accepted | MVP feature-complete |
| 9 | Nov 19–25 | Sprint 5 | Feature freeze; full benchmark on each provider; end-to-end tests; bug fixes | Benchmark at 90% or better |
| 10 | Nov 26–Dec 4 | Closing | Setup guide, user guide, data dictionary, known limitations, handoff notes; final presentation. Thanksgiving falls on Nov 26–27 | **Final demo and handoff (by Dec 4)** |

Weeks 8 and 9 are deliberately light. They absorb schedule slips before any stretch work begins.

---

## 5. Resources Required

### 5.1 People

| Role | Who | Responsibilities | Estimated time |
|---|---|---|---|
| Project sponsor (product owner) | Kayleigh Anderson-Natale | Sets priorities, answers workflow questions, supplies example questions for the benchmark, reviews demos, accepts deliverables | Weekly 1-hour check-in (about 9 hours) plus the final demo |
| Subject-matter experts | Rosie Victor, Karen Friedlander | Provide synthetic sample data; confirm that sample files match real exports | About 6 hours in total |
| Project team | Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song | Plan, design, build, test, document, and hand off. All four develop; tasks are assigned at each sprint planning based on strengths and availability | About 10 hours per person per week for 10 weeks (about 400 hours) |
| Course instructor and TA | Prof. Emily Navarro, Rakib Hossain | Project-management guidance, weekly team meetings, review of deliverables | Provided by the course |
| UCI OIT | ZotGPT Gateway service | Provides AI access and test credits | No project time expected |

### 5.2 Technology

| Category | Resource | Purpose |
|---|---|---|
| Application stack | React with TypeScript, Python FastAPI, pandas and openpyxl, PostgreSQL, Nginx (all open source) | Web interface, API, file import and export, database, local web server |
| AI | ZotGPT Gateway (default; $100 of OIT test credits); OpenAI and DeepSeek developer keys | Turning questions into SQL; testing provider switching |
| Packaging | Docker Compose, run with Docker Desktop or a free compatible runtime | One-command install on the GPSRC computer or a team laptop |
| Development | GitHub repository, GitHub Actions, project board (free tiers) | Version control, automated tests, sprint tracking and burndown |
| Hardware | Team laptops; one existing GPSRC computer for the delivered prototype (Mac or Windows, to be confirmed on Oct 21) | Development, demos, final installation |
| Collaboration | Google Drive (course documents), Zoom (sponsor meetings), Discord and text messages (team) | Communication and document management |

### 5.3 Other resources

- **Sample data from the sponsor (received):** 4 12twenty exports, 6 CampusGroups exports, the compiled dataset for these 10 Fall 2026 events, and the platform templates. All data is synthetic.
- **Sponsor time:** a weekly 1-hour check-in on Wednesdays, with the last 20 minutes available for our internal team sync.
- **Example questions** from the sponsor for the chatbot benchmark.
- **Workspace:** ISEB 1310 during Tuesday class; remote work otherwise.

---

## 6. Cost of Resources

Students are not paid for capstone work, and the software is free, so the GPSRC's cash cost is essentially zero. To show the real size of the investment, we value people's time at an **assumed blended rate of $50 per hour**, roughly the rate for a junior software developer. This rate is for estimation only.

| Resource | Basis of estimate | Estimated value | Cash cost |
|---|---|---|---|
| Project team labor | 4 people × about 10 h/week × 10 weeks = 400 h × $50/h | $20,000 | $0 (capstone course) |
| Sponsor and GPSRC staff time | About 9 weekly check-ins, about 6 h of data support, and the final demo: about 20 h × $50/h | $1,000 | $0 (existing staff) |
| Instructor and TA | Part of the course | Not charged | $0 |
| ZotGPT Gateway usage | Development and benchmark runs (about 2,000 test questions × about 3,500 tokens each) | $100 (OIT test credits) | $0 |
| OpenAI and DeepSeek usage | Provider-switch testing, with hard spending limits on each account | Up to $20 | Up to $20 (team developer accounts) |
| Software and tools | Open-source stack; free tiers of GitHub, GitHub Actions, and the project board; UCI Google Drive and Zoom | $0 | $0 |
| Hardware | Existing team laptops and an existing GPSRC computer | $0 | $0 |
| **Total** | | **About $21,120** | **Up to $20, none of it paid by the GPSRC** |

**Contingency.** We hold contingency as time rather than money: the buffer in weeks 8 and 9, plus stretch goals that can be dropped. Spending limits on every AI account cap the cash risk.

**Ongoing costs after December 4** (not part of the project budget):

- **AI usage:** each question uses about 3,500 tokens. A few hundred questions a month costs a few dollars at current API prices for small models.
- **Hosting:** $0 on the existing GPSRC computer. Moving to an OIT server is a later-phase decision.
- **Container runtime:** Docker Desktop's free terms cover our student development work. Before staff use the Hub long term, the GPSRC should check with OIT whether UCI needs a paid Docker subscription, or use a free runtime such as Rancher Desktop or Podman Desktop.

---

## 7. Assumptions, Constraints, and Risks

**Assumptions**

- The sample files are synthetic but use the same headers as the real exports. Karen is double-checking the 12twenty format.
- Each input file is already reconciled and lists only the people who attended.
- A NetID uniquely identifies a person. 12twenty emails are usually `netid@uci.edu`, and exceptions are flagged rather than guessed.
- ZotGPT Gateway works with the same API call as OpenAI (to be verified by October 28). Using real student data with any AI provider requires approval from the sponsor and OIT.

**Constraints**

- 10 weeks, ending December 4, 2026, with four part-time developers, several of whom also work full time.
- No public cloud hosting, synthetic data only, and no student information system, single sign-on, or live platform APIs.

**Key risks**

| Risk | Likelihood / Impact | Response |
|---|---|---|
| Scope creep: the scope has already changed twice, and adding features for course complexity is tempting | Medium / High | Change control (Section 8). Stretch goals start only after the sponsor accepts the MVP |
| The chatbot gives a wrong answer that looks right | Medium / High | Show the SQL, filters, and assumptions with every answer; hold the 90% benchmark target; the stretch filter table offers a fallback |
| The sponsor does not accept the chatbot-first plan on October 21 | Low / Medium | Import, the dataset, and export are useful on their own; the filter table would become the main query screen |
| Team capacity, since several members work full time | Medium / Medium | One-week sprints, buffer in weeks 8 and 9, and stretch goals dropped first |
| Docker cannot be installed on the GPSRC computer | Medium / Low | Ask on October 21; demo on a team laptop; use a free runtime |
| Real 12twenty exports differ from the sample files | Low / Medium | Staff are verifying the format; imports fail loudly and name the missing columns |

**Open items for the October 21 sponsor meeting**

- Confirm the MOV targets and that the AI chatbot is part of the MVP.
- Which computer will run the Hub (Mac or Windows), and whether Docker can be installed on it.
- Whether ZotGPT may later be used with real data, since a question may contain a student's name.
- Whether last year's GPSRC Data Project sheet should be imported.
- Who enters event details at upload: student assistants or staff.

---

## 8. Project Governance and Change Control

- **Weekly sponsor check-in** (Wednesdays, up to 1 hour, Zoom): demo progress and confirm priorities for the next sprint.
- **Weekly instructor and TA meeting** during Tuesday class.
- **One-week sprints:** planning at the start, a demo at the sponsor check-in, and a short retrospective.
- **Team norms** (from our ground rules): Discord or text for updates, with a reply within 24 hours on weekdays. At least one other member reviews every major deliverable before it is submitted.
- **Change control:** any new feature request, whether it comes from the sponsor, the instructors, or the team, goes into the backlog first. It enters a sprint only when the sponsor agrees it is worth more than the work it would displace, and either an item of similar size moves out or there is spare capacity after the MVP is accepted. Changes to the MOV, the out-of-scope list, or the end date need agreement from both the sponsor and the team, and are recorded as a new version of this charter.

---

## 9. Acceptance and Approval

| Name | Role | Signature | Date |
|---|---|---|---|
| Kayleigh Anderson-Natale | Project sponsor | | |
| Brandon Y Lau | Project team | | |
| Molly Tran | Project team | | |
| Jennifer Sun | Project team | | |
| Zhenyu (Eric) Song | Project team | | |
