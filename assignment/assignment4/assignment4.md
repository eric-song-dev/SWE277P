# Project Charter

## Program Registration & Attendance Data Hub

| | |
|---|---|
| **Course** | SWE 277P Capstone Project in Software Engineering, Assignment 4 |
| **Authors** | Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song |
| **Date** | October 18, 2026 |
| **Version** | 1.0 (based on our Business Case and our Project Scope and High-Level Design document) |
| **Sponsor** | Kayleigh Anderson-Natale, PhD, UCI Graduate Division |

### Project Stakeholders

| Name | Title | Role in this project |
|---|---|---|
| Kayleigh Anderson-Natale, PhD | Director of Postdoc and Professional Development, UCI Graduate Division (GPSRC) | Project sponsor and main user. Sets priorities and accepts the deliverables |
| Rosie Victor | GPSRC staff | User. Explained the current data process and provides sample data |
| Karen Friedlander | GPSRC staff | User. Checks that the sample files match real 12twenty and CampusGroups exports |
| GPSRC student assistants | Front-desk student employees | Download event exports and upload them to the Hub |
| Graduate Division dean and leadership, partner schools | Report recipients | Receive counts and lists from GPSRC staff. They do not use the system |
| Graduate students and postdocs | Event attendees | Their attendance records are the data, and they are protected under FERPA |
| UCI Office of Information Technology (OIT) | Runs the ZotGPT Gateway AI service | Provides AI access and test credits. Would review any future use of real data or hosting on a UCI server |
| Prof. Emily Navarro | Instructor, SWE 277P | Project management guidance, weekly team meetings, grading |
| Rakib Hossain | Teaching Assistant, SWE 277P | Weekly team meetings, grading |
| Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song | MSWE students | Project team. Plan, design, build, test, document, and hand off the prototype |

---

## 1. Project Description

### 1.1 Background and current situation

The Graduate & Postdoctoral Scholar Resource Center (GPSRC) in UCI Graduate Division holds professional development, wellness, and fellowship events for graduate students and postdocs all year. The current process for each event is:

1. Students and postdocs register for the event on CampusGroups/ZotSpot or 12twenty.
2. At the event, they check in on a GPSRC iPad or laptop using a Google Form, or they join on Zoom.
3. Student assistants compare the check-ins with the registrations and mark attendance on the platform.
4. They download the attendee list for that event and paste it into the "GPSRC Data Project" Google Sheet for the academic year, then type in the event details by hand.

### 1.2 Problem

Step 3 is routine work for the front-desk student assistants, and the sponsor told us it is not a pain point. The harder part comes later, when staff need to get information out of the data:

- Attendance data is spread across one file per event and one large sheet per academic year. Filtering and combining it across terms and years in Excel is difficult.
- CampusGroups and 12twenty export different columns. CampusGroups has NetID, Student ID, and domestic/international status. 12twenty has none of these and only identifies people by email. It also uses "Major/Academic Program" where CampusGroups uses "Department".
- Common reporting requests take a lot of manual work. For example, a new dean asked for a full year of programming data, a school asked how many of its students attended, and staff wanted to invite past Bagel Breakfast attendees to a new Donut Breakfast. The sheet counts rows instead of people, so even the number of unique students has to be worked out by hand.
- There is no easy way to query the data. The sponsor has used SQL before but not recently, and other staff do not use SQL.

As the sponsor said in our October 14 meeting:

> "Every once [in a] while I am asked to do reporting and I have to get out a ton of Excel sheets … I have to work across different documents, I have to compile documents."

### 1.3 Scope changes since the proposal

The sponsor's original proposal was a "Registration & Attendance Reconciliation Hub" that would match registrations with Zoom and sign-in records and track certificate programs. After our meetings on October 7 and October 14, the sponsor narrowed the project:

- Reconciliation will stay with the student assistants.
- Certificate programs are postponed.
- The only inputs are the attendee exports from the two platforms.
- The tool will run locally on one computer, not in a public cloud.

On October 16 we met with Professor Navarro, who suggested that we first build what the sponsor asked for and add more features in later sprints once the core works. The scope in this charter replaces the scope in the original proposal.

### 1.4 Proposed solution

We will build a web application, which we call the Hub, that runs on one GPSRC computer:

- Staff upload each event's attendee export as downloaded and confirm the event details.
- Each upload is added to one permanent dataset that keeps growing across academic years. The same person is matched across events by NetID or email.
- Staff ask questions in plain English through an AI chatbot and get numbers, student lists, or email lists, which they can download as Excel files.
- The AI only gets a description of the data and writes a SQL query. The Hub runs the query locally with a read-only database account, so student records stay on the computer.

### 1.5 Desired impact

- Show leadership and partner schools how many students the GPSRC reaches, by school, by program, and by unique student.
- Find gaps in service, such as schools or programs with low attendance. The sponsor mentioned humanities students as an example.
- Respond to reporting and outreach requests faster, using one tool instead of several spreadsheets.
- Give UCI a starting point that could later be moved to an OIT server, along with handoff documentation.

According to the sponsor, better reporting matters more than saving staff time.

---

## 2. Measurable Organizational Value (MOV)

### 2.1 MOV statement

> This project will be successful if, by December 4, 2026, GPSRC staff can load the sponsor's sample 12twenty and CampusGroups exports into one dataset that matches the sponsor's compiled sheet, and can use the chatbot to correctly answer at least 90% (18 of 20) of a benchmark of sponsor-style reporting questions, with each answer exported to Excel in under one minute.

### 2.2 MOV details

| Area of impact | Value | Metric and target | How we will verify it |
|---|---|---|---|
| Strategic | Do more. Answer questions that are hard to answer from the spreadsheets today, such as unique students per school across events | At least 18 of 20 benchmark questions answered correctly by the chatbot | Run the benchmark at the final demo. Expected answers come from the sponsor's `GSPRC Compiled Dataset.xlsm` |
| Operational | Better. One consistent dataset where each person is counted once | The 10 sample files import into 293 rows and 79 unique NetIDs, the same as the compiled sheet. Uploading a file again adds 0 rows | Automated import test at the end of Sprint 1 (October 28), and again at the final demo |
| Operational | Faster. Quicker answers for reports and outreach lists | Under 1 minute from typing a question to downloading the Excel file. Today the same answer requires opening and combining several spreadsheets by hand | Timed with the sponsor at the final demo |

We count a benchmark answer as correct if the chatbot's SQL returns the same result as the expected answer, even if the SQL is written differently. The 20 questions will be based on the sponsor's examples and kept separate from the example questions in the chatbot's prompt. Here are three sample questions. We checked the answers against the sample data.

| Question | Expected answer |
|---|---|
| How many unique Biological Sciences students came to a Bagel Breakfast in Fall 2026? | 6 |
| Which school had the fewest unique attendees in Fall 2026? | School of Information and Computer Sciences (7) |
| List the emails of everyone who attended any Bagel Breakfast. | 55 unique addresses |

### 2.3 How the MOV supports the GPSRC's goals

The GPSRC wants to show leadership how graduate students and postdocs take part in its programs and to find where access is lacking. The MOV is tied to this goal because it measures whether staff can get correct answers to the kinds of questions leadership and partner schools ask, using one dataset that covers all events instead of a separate spreadsheet each year. Accuracy is important because these numbers go into reports to the dean, so the database calculates the answers and the AI only writes the query. Since results can be exported to Excel, staff can keep making charts and reports the way they do now.

### 2.4 Changes since the Business Case

- "Merging the sample files" now has a specific target: 293 rows, 79 unique NetIDs, and no duplicate rows when a file is uploaded again.
- We defined how benchmark answers are scored.
- We added the one-minute target for getting an answer.

We will ask the sponsor to confirm the MOV and these targets at our October 21 meeting.

---

## 3. Project Scope

### 3.1 In scope (MVP)

| # | Feature | Details |
|---|---|---|
| 1 | Import platform exports | Accept 12twenty (.xlsx) and CampusGroups (.csv or .xlsx) attendee exports as downloaded. The Hub detects the source from the header row and rejects unknown layouts with a list of the missing columns. Rows with blank fields are kept and flagged |
| 2 | Event details | The exports do not include event details, so staff enter or confirm the event name, date, term, in-person/virtual/hybrid, host and partners, event type, and who entered the data |
| 3 | Common layout | Every row is converted to the 19 columns of the sponsor's GPSRC Data Project template. If a platform does not provide a field, it stays blank. Each row keeps its source file name and row number |
| 4 | Permanent dataset | Data is stored in a local database and is not split by academic year. The same file cannot be uploaded twice |
| 5 | Matching people across events | Records are linked by exact NetID first, then exact email. Rows with neither are kept and flagged. No fuzzy matching |
| 6 | AI chatbot | Staff type a question and get a number, table, or list, along with a short summary, the filters used, the SQL, and any assumption the chatbot made, such as academic year vs. calendar year |
| 7 | Privacy and SQL safety | The AI only receives the question and a description of the data, never student records or results. The generated SQL must be a single read-only query on one approved view, and it runs with a read-only database account. Every query is logged |
| 8 | Switchable AI provider | ZotGPT Gateway (UCI OIT) is the default. OpenAI or DeepSeek can be chosen in a settings file without changing code |
| 9 | Excel and CSV export | Any result, or the full dataset, can be downloaded. Values that Excel would treat as formulas are saved as plain text |
| 10 | Local install and login | Installed with one Docker Compose command and only reachable from that computer. One staff account, and no data can be viewed without logging in |

### 3.2 Deliverables (due December 4, 2026)

- Working prototype and setup guide
- Database schema and data dictionary
- Import mappings for both exports and the synthetic sample files used for testing
- Chatbot benchmark (20 questions with expected answers) and results for each provider
- Automated tests, including security tests
- User guide, list of known limitations, and handoff notes in case the Hub is later moved to an OIT server

### 3.3 Acceptance criteria

The sponsor will accept the MVP when the following work on the synthetic sample data:

1. The 10 sample files import into the same data as the compiled sheet (293 rows, 79 unique NetIDs), and uploading a file again adds no rows.
2. The chatbot answers at least 18 of the 20 benchmark questions correctly, and still works after the provider is changed in the settings file.
3. Every table or list result can be downloaded as Excel, and no exported cell runs as a formula.
4. The log of AI requests contains no student rows or query results.
5. Harmful SQL, such as DROP, DELETE, multiple statements, or reading the user account table, is blocked by the SQL check. When the check is turned off for testing, the read-only database account still blocks it.
6. No data can be viewed or exported without logging in.

### 3.4 Stretch goals (not committed)

We will only work on these after the sponsor accepts the MVP (planned for week 8) and if we have time left in the sprint:

- A filter table that does not use AI, so staff can filter the dataset by column and export the result. This also gives staff a backup if the AI gives a wrong answer or is unavailable.
- A data quality view that lists rows missing a NetID, email, or school and lets staff fill in the blanks by hand. The sponsor asked for this on October 7.

### 3.5 Out of scope

| Item | Reason | Future path |
|---|---|---|
| Registration and attendance reconciliation, including Zoom, Google Form, and paper sign-in files | Student assistants already do this at the front desk, and the sponsor said it is not a pain point (October 14) | Possible change request after the MVP if the sponsor asks for it |
| Certificate and multi-session program tracking | Postponed by the sponsor (October 7) | Later phase |
| Charts and dashboards | The sponsor makes charts in Excel from exported data (October 14) | Later phase |
| AI that suggests insights on its own, follow-up questions in the chatbot, saved queries | Not requested by the sponsor, and they add more AI risk | Later phase |
| Multiple staff accounts and permission roles | One staff login is enough for a prototype on one computer (October 14) | Needed only if the Hub moves to a shared server |
| Importing last year's GPSRC Data Project sheet | The sponsor has not confirmed this yet | Change request if confirmed on October 21 |
| Public cloud hosting, OIT server deployment, UCI single sign-on, production use | The sponsor ruled out public cloud for privacy reasons (October 14). Hosting at UCI needs an OIT review | Later phase with OIT |
| Student information system integration, live 12twenty/CampusGroups/Zoom APIs, writing data back to these platforms | Outside the proposal's boundaries. The platforms stay the system of record | Not planned |
| Arbitrary spreadsheet formats, automatic fuzzy merging of people | Keeps imports predictable. The sponsor does not want the system to guess | Not planned |
| Real student data | Only synthetic data is used during the capstone | After a UCI privacy and security review |

---

## 4. Project Schedule Summary

- **Start date:** September 24, 2026
- **End date:** December 4, 2026
- **Length:** 10 weeks

After the first four weeks of initiation and planning, we will work in one-week sprints. We meet with the sponsor on Wednesdays and with the instructor during class on Tuesdays.

| Week | Dates | Phase | Main work | Milestone |
|---|---|---|---|---|
| 1 | Sep 24–30 | Initiation | Team formation, review of the sponsor's proposal | Team statement submitted Oct 6 (done) |
| 2 | Oct 1–7 | Initiation | First sponsor meeting about the current data process, templates, and identifiers | Sponsor kickoff Oct 7 (done) |
| 3 | Oct 8–14 | Initiation | MOV draft, review of sample data, scope discussion with the sponsor | Scope narrowed to compiling and querying data, run locally, Oct 14 (done) |
| 4 | Oct 15–21 | Planning | Meeting with the instructor (Oct 16), scope and design document, business case, project charter, repository setup, Docker Compose skeleton, CI | Sponsor confirms scope and MOV (Oct 21) |
| 5 | Oct 22–28 | Sprint 1 | Database schema, import for both exports, event details form, matching people across events, check that ZotGPT Gateway works with our setup | Sample files reproduce the compiled sheet (293 rows, 79 NetIDs) |
| 6 | Oct 29–Nov 4 | Sprint 2 | Chatbot pipeline (prompt, provider adapters, SQL check, read-only account), first draft of the 20-question benchmark with the sponsor | First chatbot answers on sample data |
| 7 | Nov 5–11 | Sprint 3 | Chat screen, results view, Excel/CSV export, login, security tests | Mid-project demo of the full MVP to the sponsor. Nov 11 is Veterans Day, so the meeting will be moved to another day that week |
| 8 | Nov 12–18 | Sprint 4 | Fixes based on sponsor feedback, benchmark tuning, stretch goals only if the MVP is accepted | MVP feature-complete |
| 9 | Nov 19–25 | Sprint 5 | Feature freeze, full benchmark on each provider, end-to-end testing, bug fixes | Benchmark at 90% or higher |
| 10 | Nov 26–Dec 4 | Closing | Setup guide, user guide, data dictionary, known limitations, handoff notes, final presentation (Thanksgiving is Nov 26–27) | Final demo and handoff by Dec 4 |

We kept weeks 8 and 9 lighter so we have time to catch up if earlier sprints run late. Stretch goals only start if we are on schedule.

---

## 5. Resources Required

### 5.1 People

| Role | Who | Responsibilities | Estimated time |
|---|---|---|---|
| Project sponsor (product owner) | Kayleigh Anderson-Natale | Sets priorities, answers questions about the workflow, gives example questions for the benchmark, reviews demos, accepts deliverables | 1-hour weekly meeting (about 9 hours) plus the final demo |
| Subject matter experts | Rosie Victor, Karen Friedlander | Provide synthetic sample data and confirm that it matches the real exports | About 6 hours total |
| Project team | Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song | Planning, design, development, testing, documentation, and handoff. All four of us develop, and tasks are assigned at each sprint planning based on strengths and availability | About 10 hours per person per week for 10 weeks (about 400 hours) |
| Course instructor and TA | Prof. Emily Navarro, Rakib Hossain | Project management guidance, weekly team meetings, review of deliverables | Provided by the course |
| UCI OIT | ZotGPT Gateway service | Provides AI access and test credits | No project time expected |

### 5.2 Technology

| Category | Resource | Purpose |
|---|---|---|
| Application | React with TypeScript, Python FastAPI, pandas and openpyxl, PostgreSQL, Nginx (all open source) | Web interface, API, file import and export, database, local web server |
| AI | ZotGPT Gateway (default, with $100 in OIT test credits), OpenAI and DeepSeek developer keys | Turning questions into SQL, testing provider switching |
| Packaging | Docker Compose, with Docker Desktop or a free alternative | One-command install on the GPSRC computer or a team laptop |
| Development | GitHub repository, GitHub Actions, project board (free plans) | Version control, automated tests, sprint tracking and burndown |
| Hardware | Team laptops, plus one existing GPSRC computer for the final prototype (Mac or Windows, to be confirmed Oct 21) | Development, demos, final install |
| Collaboration | Google Drive (course documents), Zoom (sponsor meetings), Discord and text messages (team) | Communication and document sharing |

### 5.3 Other resources

- Synthetic sample data from the sponsor, which we already have: 4 12twenty exports, 6 CampusGroups exports, the compiled dataset for these 10 Fall 2026 events, and the platform templates.
- A 1-hour weekly meeting with the sponsor on Wednesdays. We can use the last 20 minutes for our own team discussion.
- Example questions from the sponsor for the chatbot benchmark.
- ISEB 1310 during Tuesday class. Otherwise we work remotely.

---

## 6. Cost of Resources

Capstone students are not paid and the software we use is free, so the GPSRC has almost no cash cost. To show how much effort the project takes, we estimated people's time at $25 per hour. This rate is only an assumption for the estimate.

| Resource | Basis of estimate | Estimated value | Cash cost |
|---|---|---|---|
| Project team | 4 people × about 10 h/week × 10 weeks = 400 h × $25/h | $10,000 | $0 (capstone course) |
| Sponsor and GPSRC staff | About 9 weekly meetings, about 6 h of help with data, and the final demo, about 20 h × $25/h | $500 | $0 (existing staff) |
| Instructor and TA | Part of the course | Not counted | $0 |
| ZotGPT Gateway usage | Development and benchmark runs, about 2,000 test questions at about 3,500 tokens each | $100 (OIT test credits) | $0 |
| OpenAI and DeepSeek usage | Testing provider switching, with a spending limit on each account | Up to $20 | Up to $20 (team developer accounts) |
| Software and tools | Open-source software, free plans for GitHub, GitHub Actions, and the project board, UCI Google Drive and Zoom | $0 | $0 |
| Hardware | Team laptops and an existing GPSRC computer | $0 | $0 |
| **Total** | | **About $10,620** | **Up to $20, paid by the team, not the GPSRC** |

For contingency, we are counting on schedule time instead of extra money. Weeks 8 and 9 are buffer, and the stretch goals can be dropped if needed. The spending limits on the AI accounts also keep cash costs from growing.

Ongoing costs after December 4 (not part of the project budget):

- AI usage: each question uses about 3,500 tokens, so a few hundred questions a month would cost a few dollars at current prices for smaller models.
- Hosting: $0 on the existing GPSRC computer. Moving to an OIT server would be decided in a later phase.
- Docker: Docker Desktop is free for our student development work. Before staff use the Hub long term, the GPSRC should check with OIT whether UCI needs a paid Docker subscription. A free alternative such as Rancher Desktop or Podman Desktop would avoid this cost.

---

## 7. Assumptions, Constraints, and Risks

### 7.1 Assumptions

- The sample files are synthetic but have the same headers as the real exports. Karen is double-checking the 12twenty format.
- Each input file has already been reconciled and only lists people who attended.
- A NetID identifies one person. 12twenty emails are usually `netid@uci.edu`, and other email formats are flagged instead of guessed.
- ZotGPT Gateway works with the same API calls as OpenAI. We will confirm this by October 28. Using real student data with any AI provider would need approval from the sponsor and OIT.

### 7.2 Constraints

- 10 weeks, ending December 4, 2026, with four team members working part time. Several of us also have full-time jobs.
- No public cloud hosting, only synthetic data, and no student information system, single sign-on, or live platform APIs.

### 7.3 Key risks

| Risk | Likelihood / Impact | Response |
|---|---|---|
| Scope creep. The scope has already changed twice, and we may be tempted to add features to make the project more complex | Medium / High | Follow the change control process (Section 8). Only start stretch goals after the sponsor accepts the MVP |
| The chatbot gives a wrong answer that looks correct | Medium / High | Show the SQL, filters, and assumptions with every answer, keep the 90% benchmark target, and use the filter table stretch goal as a backup |
| The sponsor does not agree to the chatbot plan on October 21 | Low / Medium | Import, the dataset, and export are still useful by themselves. The filter table would become the main way to query |
| Limited team time, since several members work full time | Medium / Medium | One-week sprints, buffer in weeks 8 and 9, and stretch goals are dropped first |
| Docker cannot be installed on the GPSRC computer | Medium / Low | Ask on October 21, run demos on a team laptop, or use a free alternative |
| Real 12twenty exports are different from the sample files | Low / Medium | Staff are checking the format. Imports that do not match will fail with a list of the missing columns |

### 7.4 Open questions for the October 21 sponsor meeting

- Does the sponsor agree with the MOV targets and with the AI chatbot being part of the MVP?
- Which computer will the Hub run on (Mac or Windows), and can Docker be installed on it?
- Can ZotGPT be used with real data later, since a question might include a student's name?
- Should last year's GPSRC Data Project sheet be imported?
- Who will enter the event details at upload, student assistants or staff?

---

## 8. Project Governance and Change Control

- We meet with the sponsor every Wednesday for up to an hour on Zoom to show progress and agree on priorities for the next sprint.
- We meet with the instructor and TA every Tuesday during class.
- Each one-week sprint starts with planning, includes a demo at the sponsor meeting, and ends with a short retrospective.
- Following our team ground rules, we use Discord or text for updates and reply within 24 hours on weekdays. At least one other team member reviews every major deliverable before it is submitted.

New feature requests from the sponsor, the instructors, or the team go into the backlog first. A request is added to a sprint only if the sponsor agrees it is worth more than the work it would replace, and either something of similar size is moved out or there is time left after the MVP is accepted. Any change to the MOV, the out-of-scope list, or the end date needs agreement from both the sponsor and the team, and will be recorded as a new version of this charter.

---

## 9. Acceptance and Approval

| Name | Role | Signature | Date |
|---|---|---|---|
| Kayleigh Anderson-Natale | Project sponsor | | |
| Brandon Y Lau | Project team | | |
| Molly Tran | Project team | | |
| Jennifer Sun | Project team | | |
| Zhenyu (Eric) Song | Project team | | |
