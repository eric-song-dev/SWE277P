# Work Breakdown Structure: Program Registration & Attendance Data Hub

**Authors:** Brandon Lau, Molly Tran, Jennifer Sun, Zhenyu Song

**Date:** October 25, 2026

**Version:** 1.0. This is a living document: we update it at every sprint planning and record actual hours against it.

---

## Project Basics

- **Project name:** Program Registration & Attendance Data Hub
- **Project team name:** ZotSync
- **Team members' names and roles:**

| Name | Role in the project |
|---|---|
| Brandon Lau | Database / DevOps |
| Jennifer Sun | Frontend |
| Molly Tran | Backend / Data Import |
| Zhenyu Song | AI / Chatbot |

**Sponsor:** Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development, UCI Graduate Division.

---

## 1. Project Description

*Adapted from the project charter (October 18) and updated with what happened since.*

### Background, current situation and problem

The Graduate & Postdoctoral Scholar Resource Center (GPSRC) runs events for graduate students and postdocs all year. Students register on CampusGroups or 12twenty. After each event, a student assistant downloads the attendee list and pastes it into a yearly Google Sheet, then adds the event details by hand.

This is what frustrates the sponsor:

- The data is spread over one file per event and one large sheet per year, which is hard to filter and combine in Excel.
- The two platforms export different columns. 12twenty, for example, has no NetID.
- Simple questions take a lot of manual work: how many students from a school came, or the emails of everyone at the Bagel Breakfast. Staff filter, sort, copy between sheets and remove duplicates by hand, and the sheet counts rows, not unique students. In the October 21 meeting the sponsor said that finding who comes to the programs, and which groups are missing, takes several files and a long time.

We are building a web app that runs on one GPSRC computer. Staff upload each event's export exactly as the platform produced it, and the app adds it to one dataset that keeps growing over the years and links the same person across events. Staff then ask questions in plain English through an AI chatbot, see the SQL it ran and the result table, and download any result as an Excel or CSV file. The AI writes SQL from a description of the data, and it reads query results only when staff allow it, so student records stay on the computer.

### Desired impact

Staff can quickly show Graduate Division leadership and partner schools how many students the GPSRC reaches, by school, program and term, and find groups of students it is not reaching. Student assistants stop compiling sheets by hand.

### What changed since the charter

- **The MVP was built early.** Using AI-assisted development (Claude Code), the team built and tested the whole MVP from October 20 to 22, in six build sessions. Every acceptance test passes except A7 (login), which the team moved to the backlog on October 19.
- **The sponsor confirmed the three success metrics** in the October 21 meeting, and listed what the Hub must answer: questions by event, by field (school, department), by student name, by a mix of these, and by time range, plus a full export, a partial export and answers in plain sentences. We walked each request in the app on October 22 (stories SP-01 to SP-14): 8 passed, 5 passed with a caveat, and 1 found a gap. A second download of an event that is already imported is recorded as a new event, which double-counts its attendees.
- **A backlog was recorded on October 22** (`project/docs/backlog.md`): B1 delete a conversation and set a retention period, B2 a Downloads page for AI results, B3 an Insights button, and B4 the double-count bug above. The handoff guide (`project/docs/handoff.md`) lists the rest: login, hosting on a UCI server, CI, ZotGPT support and the P1 features.

Because the build moved forward, this WBS plans the remaining weeks around the sponsor demo, the backlog and the handoff, instead of the week-by-week build in the charter.

---

## 2. Measurable Organizational Value (MOV)

*Adapted from the project charter. The sponsor confirmed these metrics on October 21, 2026.*

> **This project will be successful if, by December 4, 2026, staff can load the sponsor's sample files into one dataset that matches the sponsor's compiled sheet, with no duplicates, and the chatbot correctly answers at least 90% (18 of 20) of a set of sponsor-style reporting questions, each in under one minute.**

| Area | Value | Metric | Target | Status on Oct 22 |
|---|---|---|---|---|
| Strategic | Do more | Benchmark questions answered correctly | At least 18 of 20 | 20 of 20 (DeepSeek), and 10 of 10 on held-out questions |
| Operational | Better | Sample files imported correctly | 293 rows and 79 unique NetIDs, the same as the compiled sheet; no duplicates when a file is uploaded twice | Met. A re-download of the same event is still counted twice (B4, planned for Sprint 2) |
| Operational | Faster | Time from question to downloaded Excel file | Under 1 minute | 4 to 7 seconds |

The MOV supports the GPSRC's goal of showing leadership how students use its programs. A dataset that answers questions in seconds lets staff report reach by school and term and spot gaps in program access, without student assistants compiling sheets by hand.

---

## 3. Work Breakdown Structure

The full WBS is in the attached **WBS.xlsx** (sheet "WBS"), in the format of the week 4 in-class activity. A second sheet, "Effort Summary", adds up the hours by person and sprint and compares them with the team's capacity. The same WBS is reproduced below.

### How to read it

- **WBS number:** `1` is the project. `1.n` is a deliverable, a user story or a work package, and `1.n.k` is a task. As in the template, the numbers run on across sprints, and the grey sprint rows group them. Each sprint ends with a milestone row.
- **Deliverable:** "Yes" when the item itself goes to the sponsor or the instructor (a feature, a document, a demo or a course submission). Tasks are "No".
- **Estimated Time:** person-hours. A row owned by "All team" counts all four members, so a 1-hour meeting is 4 hours. A deliverable row shows the sum of its tasks.
- **Resources:** one owner per task, by role. There is no dedicated project manager: the coordination tasks (sprint planning, the time log, sponsor questions, walkthroughs and documents) are shared, and Brandon takes the most of them because the database and DevOps work is the smallest area. Development is AI-assisted: Claude Code writes most of the code from the spec and plans, and the owner specifies the task, reviews the generated code, tests it and maintains it. The estimates are for that human work.

### Sprint plan

Sprints 1 and 2 are two weeks long and start on Tuesdays, when the team meets in class. Sprint 0 covers the first four weeks of the quarter. Sprint 3 runs to the Capstone Showcase on December 7 and has Thanksgiving in the middle, so its capacity counts 2.5 weeks, up to the charter's end date of December 4.

| Sprint | Dates | Goal | Milestone | Planned hours | Capacity | Load | Status |
|---|---|---|---|---|---|---|---|
| Sprint 0 | Sep 24 – Oct 19 (Weeks 1–4) | Form the team, learn the sponsor's process, agree on scope and plan | Scope, MOV, business case and charter submitted (Oct 20) | 109 | 140 | 78% | Complete |
| Sprint 1 | Oct 20 – Nov 2 (Weeks 4–6) | Build and verify the MVP; midterm; this WBS | MVP passes A1–A10 except A7 (Oct 22); midterm delivered (Oct 26) | 120 | 80 | 150% | **Current sprint** |
| Sprint 2 | Nov 3 – Nov 16 (Weeks 6–8) | Sponsor demo; backlog B1–B4; sponsor walkthrough fixes | Sponsor demo given; B1–B4 built and tested | 75 | 80 | 94% | Planned |
| Sprint 3 | Nov 17 – Dec 7 (Weeks 8–10) | Login, hosting preparation, CI, P1 features; handoff and final delivery | MOV met and the Hub handed over (Dec 4); showcase (Dec 7) | 106 | 100 | 106% | Planned |
| **Total** | | | | **410** | **400** | **103%** | |

Capacity is 4 members × 10 hours per week × the sprint's weeks, from the charter's resource plan. Sprint 1 is over capacity on purpose; see "Capacity check" in Section 4.

### Course deliverables this quarter

| Class | Deliverable | Due | WBS | Status |
|---|---|---|---|---|
| SWE 277P | Assignment 1: Team Statement | Oct 6 | 1.1 | Done |
| SWE 277P | Assignment 2: MOV | Oct 13 | 1.3 | Done |
| SWE 276P | Project Scope and High-Level Design report | Oct 16 | 1.4 | Done |
| SWE 277P | Assignment 3: Business Case | Oct 20 | 1.6 | Done |
| SWE 277P | Assignment 4: Project Charter | Oct 20 | 1.7 | Done |
| Capstone | Midterm report and presentation | Oct 26, 11:59 PM | 1.24 | In progress |
| SWE 277P | Assignment 5: Work Breakdown Structure (this document) | Oct 27 | 1.25 | In progress |
| SWE 277P | WBS update with actual hours | At each sprint planning (Nov 3, Nov 17) | 1.27.1, 1.40.1 | Planned |
| SWE 277P | Project schedule and cost assignments | TBA (placeholder) | 1.38 | Planned |
| Capstone | Final report and final demo | Dec 4 | 1.48.1 – 1.48.7 | Planned |
| Capstone | Capstone Showcase | Dec 7 | 1.48.8, 1.48.9 | Planned |
| Capstone | Peer evaluations | End of quarter | 1.48.10 | Planned |

We will add any further SWE 276P or SWE 277P assignments to the sprint they fall in when they are posted.

### Sprint 1 (current sprint): user stories

Sprint 1 is broken down into eleven user stories. Each one groups the detailed stories in `project/docs/user-stories/` (63 stories with acceptance criteria and walk steps), listed in the "Detailed stories" column.

| Story | User story | Detailed stories | Owner | Status on Oct 25 |
|---|---|---|---|---|
| US-01 | As a student worker, I want to drop an event's CampusGroups or 12twenty export exactly as I downloaded it, so that I never have to clean a file by hand. | UP-01 – UP-10, UP-19 | Molly Tran (UI: Jennifer Sun) | Built and walked |
| US-02 | As a student worker, I want the event details prefilled where possible and checked before I commit, so that every event is recorded the same way. | UP-11 – UP-14 | Molly Tran, Jennifer Sun | Built and walked |
| US-03 | As GPSRC staff, I want the same person linked across events by NetID and then by email, so that unique counts are right and doubtful matches are flagged instead of merged. | UP-15, UP-16 | Molly Tran | Built and walked |
| US-04 | As the sponsor, I want to ask a question in plain English and see the SQL and the result table, so that I can trust and check the answer. | CH-01, CH-04, CH-11, CH-19 | Zhenyu Song (UI: Jennifer Sun) | Built and walked |
| US-05 | As the sponsor, I want to ask follow-up questions and be asked when my question is unclear, so that I get the answer I meant. | CH-02, CH-03, CH-12, CH-13, CH-22 | Zhenyu Song | Built and walked |
| US-06 | As the sponsor, I want the chatbot's SQL to be read-only and limited to one view, so that it can never change data or read the rest of the database. | A6, A8 (acceptance tests) | Zhenyu Song | Built and tested |
| US-07 | As GPSRC staff, I want to choose for each question whether the AI may read the results, so that student data reaches the AI only when we allow it. | CH-08, CH-09 | Zhenyu Song | Built and walked |
| US-08 | As GPSRC staff, I want to add and test AI models in Settings without exposing the API key, so that we can switch providers without code changes. | ST-01 – ST-10, CH-10, CH-17, CH-21 | Zhenyu Song (UI: Jennifer Sun) | Built and walked |
| US-09 | As the sponsor, I want to download any result and the full dataset as Excel or CSV, so that I can share reports with leadership. | CH-05, CH-06, DS-02 | Molly Tran | Built and walked |
| US-10 | As a student worker, I want to see which files are already imported, so that I don't upload an event twice. | DS-01 – DS-05 | Jennifer Sun | Built and walked |
| US-11 | As GPSRC staff, I want the same navigation on every page, usable on a small laptop and with the keyboard, so that the Hub is easy to use. | SH-01 – SH-07 | Jennifer Sun | Built and walked |

**Status on October 25.** The eleven stories were built from October 20 to 22 and walked by hand: 67 walk rows, 65 passed, and the 2 failures were left on purpose, with the reasons recorded. The acceptance run (`acceptance.sh`) is green except A7. What is left in Sprint 1:

- 1.23.2 send the sponsor the LLM credit request;
- 1.23.3 verify the ZotGPT gateway by October 28;
- 1.23.4 the October 28 sponsor meeting;
- 1.23.5 the code walkthrough, where each owner reviews their module in the team repo;
- 1.23.6 start the time log;
- 1.24 the midterm report and presentation (October 26) and 1.25 this WBS (October 27).

### Sprints 2 and 3: backlog and handoff

Sprints 2 and 3 hold the work that is not built yet. Each item comes from the project's own records:

- **Sprint 2** takes the backlog in `project/docs/backlog.md` (B1–B4), the sponsor walkthrough findings SF-2, SF-3, SF-4, SF-5 and SF-9, the checklist "Before the sponsor demo" in `project/PROGRESS.md`, and two import items from the handoff backlog (deleting and editing a committed import, and attaching a second file to an event). B4 comes first because it is a high-priority bug that breaks the "no duplicates" part of the MOV.
- **Sprint 3** takes the handoff guide in `project/docs/handoff.md`: login (acceptance test A7), the checklist for moving to a UCI OIT server, CI, ZotGPT support and the P1 features built on the extension points (F11 filter table, F12 data-quality view, F14 saved queries, F15 historical import), followed by the handoff to the GPSRC and the final deliverables.
- **Rules carried over from the backlog:** every backlog item gets a design draft that is reviewed before any code is written, so B1, B2 and B4 start with one and B3 starts with a spike. Any change to the chatbot prompt is followed by a benchmark re-run (B3, SF-5).
- **Waiting on the sponsor:** result sharing (D1), the retention policy (B1), how often an export is downloaded again (B4), whether date ranges matter (SF-2), whether a filter table is wanted (F11, SF-8) and one account or several (login). We ask these at the Sprint 2 demo (task 1.28.6). Their answers can change Sprint 3, which is why the P1 features are marked "pending sponsor priority."
- **Not scheduled:** F16 multiple accounts, a native Anthropic or Gemini connector, and a roster by school for measuring service gaps (SF-7) do not fit the quarter. They are listed at the end of the WBS so the next team can see them, and they are not counted in the capacity check.

### Full WBS

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1** | **Program Registration & Attendance Data Hub (scheduled sprints)** | Yes | **410 hours** | |

#### Sprint 0: Initiation and Planning · Sep 24 – Oct 19 (Weeks 1–4) · Complete

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.1** | **SWE 277P Assignment 1: Team Statement (due Oct 6)** | Yes | **15 hours** | |
| 1.1.1 | Write the project description | No | 2 hours | Jennifer Sun |
| 1.1.2 | Initial team plan: strengths, sponsor questions, learning list | No | 2 hours | Molly Tran |
| 1.1.3 | Team ground rules | No | 2 hours | Brandon Lau |
| 1.1.4 | Create the shared Google Drive folder and share it with the instructor and TA | No | 1 hour | Zhenyu Song |
| 1.1.5 | Team bonding dinner (Oct 6) | No | 8 hours | All team |
| **1.2** | **Sponsor kickoff and requirements** | No | **18 hours** | |
| 1.2.1 | Read the sponsor proposal and the sample exports | No | 3 hours | Jennifer Sun |
| 1.2.2 | Prepare questions for the first sponsor meeting | No | 2 hours | Molly Tran |
| 1.2.3 | Sponsor meeting Oct 7: current process and sample data | No | 4 hours | All team |
| 1.2.4 | Sponsor meeting Oct 14: scope narrowed to import, one dataset and queries | No | 4 hours | All team |
| 1.2.5 | Write up meeting notes and action items | No | 2 hours | Molly Tran |
| 1.2.6 | Map the GPSRC data process and the Data Project template columns | No | 3 hours | Molly Tran |
| **1.3** | **SWE 277P Assignment 2: MOV (due Oct 13)** | Yes | **6 hours** | |
| 1.3.1 | Six-step MOV draft: impact, value, metric, time frame | No | 2 hours | Molly Tran |
| 1.3.2 | Explain how the MOV supports GPSRC's vision and mission | No | 2 hours | Jennifer Sun |
| 1.3.3 | Discuss the MOV with the sponsor and record the outcome | No | 1 hour | Molly Tran |
| 1.3.4 | Review and submit | No | 1 hour | Brandon Lau |
| **1.4** | **SWE 276P: Project Scope and High-Level Design report (due Oct 16)** | Yes | **18 hours** | |
| 1.4.1 | Project overview, target users and stakeholders | No | 2 hours | Jennifer Sun |
| 1.4.2 | Scope definition: boundaries, P0/P1/P2 features, assumptions | No | 4 hours | Zhenyu Song |
| 1.4.3 | C4 context, container and component diagrams | No | 4 hours | Zhenyu Song |
| 1.4.4 | Data model and import sequence diagrams | No | 3 hours | Brandon Lau |
| 1.4.5 | Technology stack and design rationale | No | 3 hours | Zhenyu Song |
| 1.4.6 | Edit, format as PDF and submit | No | 2 hours | Molly Tran |
| **1.5** | **Technology ramp-up** | No | **12 hours** | |
| 1.5.1 | PostgreSQL, Alembic, Docker Compose and nginx | No | 3 hours | Brandon Lau |
| 1.5.2 | React, MUI and TanStack Query | No | 3 hours | Jennifer Sun |
| 1.5.3 | LangGraph, text-to-SQL and the LLM provider APIs | No | 3 hours | Zhenyu Song |
| 1.5.4 | FastAPI and reading CSV and Excel exports | No | 3 hours | Molly Tran |
| **1.6** | **SWE 277P Assignment 3: Business Case (due Oct 20)** | Yes | **8 hours** | |
| 1.6.1 | Executive summary and introduction | No | 2 hours | Brandon Lau |
| 1.6.2 | Alternatives and their analysis (TCO, TBO, feasibility, risk) | No | 3 hours | Jennifer Sun |
| 1.6.3 | Scoring model and recommendation | No | 2 hours | Molly Tran |
| 1.6.4 | Final consistency check and submit | No | 1 hour | Zhenyu Song |
| **1.7** | **SWE 277P Assignment 4: Project Charter (due Oct 20)** | Yes | **7 hours** | |
| 1.7.1 | Stakeholder table, project description and MOV | No | 2 hours | Brandon Lau |
| 1.7.2 | Scope and schedule summary | No | 2 hours | Molly Tran |
| 1.7.3 | Resources and cost estimate | No | 2 hours | Jennifer Sun |
| 1.7.4 | Title page, table of contents and formatting | No | 1 hour | Brandon Lau |
| **1.8** | **Team meetings and coordination** | No | **25 hours** | |
| 1.8.1 | Weekly check-ins with the instructor and TA (Oct 6, Oct 13) | No | 8 hours | All team |
| 1.8.2 | Team scope discussions (Oct 15, Oct 17) | No | 8 hours | All team |
| 1.8.3 | Team meeting Oct 19: split document edits, assign roles, plan the midterm | No | 8 hours | All team |
| 1.8.4 | Set up the team chat, meeting cadence and shared documents | No | 1 hour | Molly Tran |
| **1.9** | ***Milestone: scope, MOV, business case and charter submitted (Oct 20)*** | No | **0 hours** | |

#### Sprint 1: MVP Build · Oct 20 – Nov 2 (Weeks 4–6) · Current sprint

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.10** | **Sprint 1 planning and MVP design spec** | Yes | **7 hours** | |
| 1.10.1 | Write the MVP design spec (decisions D1–D10, data model, chatbot, acceptance tests A1–A10) | No | 3 hours | Zhenyu Song |
| 1.10.2 | Break the spec into session plans S2–S6; write CLAUDE.md and PROGRESS.md | No | 2 hours | Zhenyu Song |
| 1.10.3 | Set up the team's private GitHub repo and invite every member | No | 1 hour | Brandon Lau |
| 1.10.4 | Sprint planning: assign an owner to each user story | No | 1 hour | Brandon Lau |
| **1.11** | **US-01 Upload an event export as-is (UP-01 – UP-10, UP-19)** | Yes | **14 hours** | |
| 1.11.1 | Map CampusGroups and 12twenty columns to the GPSRC layout | No | 2 hours | Molly Tran |
| 1.11.2 | Database schema and migrations (import_file, event, person, attendance, flags) | No | 2 hours | Brandon Lau |
| 1.11.3 | CampusGroups and 12twenty adapters | No | 3 hours | Molly Tran |
| 1.11.4 | Detect the source from the headers; reject unknown formats and list missing columns | No | 1 hour | Molly Tran |
| 1.11.5 | Duplicate-file protection (file hash and content hash) | No | 1 hour | Molly Tran |
| 1.11.6 | Upload page: drop zone, preview, Duplicate and Rejected cards | No | 3 hours | Jennifer Sun |
| 1.11.7 | Tests: A1 (293 rows, 79 NetIDs) and A2 (a re-upload adds nothing) | No | 2 hours | Molly Tran |
| **1.12** | **US-02 Enter event details before commit (UP-11 – UP-14)** | Yes | **5 hours** | |
| 1.12.1 | Prefill the event name from the file name and the date from the Registration UID | No | 1 hour | Molly Tran |
| 1.12.2 | Event form with term check and required fields | No | 2 hours | Jennifer Sun |
| 1.12.3 | Commit in one transaction; discard a pending import | No | 1 hour | Molly Tran |
| 1.12.4 | Keep pending imports across pages and reloads | No | 1 hour | Jennifer Sun |
| **1.13** | **US-03 Link the same person across events (UP-15, UP-16)** | Yes | **4 hours** | |
| 1.13.1 | Identity linker: NetID first, then email; flag conflicts | No | 2 hours | Molly Tran |
| 1.13.2 | Data-quality flags and their counts in the preview | No | 1 hour | Molly Tran |
| 1.13.3 | Tests: linker cases; the November Bagel Breakfast row links by email | No | 1 hour | Molly Tran |
| **1.14** | **US-04 Ask a question and see the SQL and the table (CH-01, CH-04, CH-11, CH-19)** | Yes | **11 hours** | |
| 1.14.1 | Read-only attendance_view and chatbot_ro role with a 5 s timeout | No | 1 hour | Brandon Lau |
| 1.14.2 | LangGraph chat graph and SQL-generation prompt | No | 3 hours | Zhenyu Song |
| 1.14.3 | Streaming API (SSE) and saved conversations | No | 2 hours | Zhenyu Song |
| 1.14.4 | Chat page: question box, progress steps, answer card, SQL and table | No | 3 hours | Jennifer Sun |
| 1.14.5 | Recent questions in the side nav; reopen and re-run old answers | No | 1 hour | Jennifer Sun |
| 1.14.6 | Tests: graph integration tests with a scripted model | No | 1 hour | Zhenyu Song |
| **1.15** | **US-05 Follow-ups, clarifying questions and repairs (CH-02, CH-03, CH-12, CH-13, CH-22)** | Yes | **4 hours** | |
| 1.15.1 | Conversation history (questions and SQL only) for follow-ups | No | 1 hour | Zhenyu Song |
| 1.15.2 | Clarifying questions and the repair loop (up to 3 tries) | No | 2 hours | Zhenyu Song |
| 1.15.3 | Clarification bubble and Retry in the chat page | No | 1 hour | Jennifer Sun |
| **1.16** | **US-06 Keep the data safe from generated SQL (A6, A8)** | Yes | **4 hours** | |
| 1.16.1 | SQL guard: one SELECT on attendance_view, function allow-list, row limit | No | 2 hours | Zhenyu Song |
| 1.16.2 | Read-only executor that always rolls back, and the error sanitizer | No | 1 hour | Zhenyu Song |
| 1.16.3 | Tests: A8 harmful SQL and A6 privacy with a recording model | No | 1 hour | Zhenyu Song |
| **1.17** | **US-07 Choose whether the AI sees the results (CH-08, CH-09)** | Yes | **3 hours** | |
| 1.17.1 | Per-model ceiling plus per-question switch, decided on the server | No | 1 hour | Zhenyu Song |
| 1.17.2 | AI summary from capped rows, or a local summary | No | 1 hour | Zhenyu Song |
| 1.17.3 | Switch in the question box, its help text and the caution line | No | 1 hour | Jennifer Sun |
| **1.18** | **US-08 Manage AI models in Settings (ST-01 – ST-10, CH-10, CH-17, CH-21)** | Yes | **5 hours** | |
| 1.18.1 | Encrypted API keys, provider presets and Test connection | No | 2 hours | Zhenyu Song |
| 1.18.2 | Settings page: add, test, edit, set default, delete | No | 2 hours | Jennifer Sun |
| 1.18.3 | Walk the Settings stories ST-01 – ST-10 | No | 1 hour | Molly Tran |
| **1.19** | **US-09 Download results as Excel or CSV (CH-05, CH-06, DS-02)** | Yes | **5 hours** | |
| 1.19.1 | Excel and CSV writers with a formula guard; full dataset in the 19-column layout | No | 2 hours | Molly Tran |
| 1.19.2 | Export of a chat result with a row cap | No | 1 hour | Zhenyu Song |
| 1.19.3 | Download buttons and the "This file stops at N rows" notice | No | 1 hour | Jennifer Sun |
| 1.19.4 | Time question to downloaded Excel (A10, under 60 s) | No | 1 hour | Brandon Lau |
| **1.20** | **US-10 See what has been imported (DS-01 – DS-05)** | Yes | **2 hours** | |
| 1.20.1 | Imports list API with the rows each file added | No | 1 hour | Molly Tran |
| 1.20.2 | Dataset page: file list, Pending link, full download | No | 1 hour | Jennifer Sun |
| **1.21** | **US-11 Move around the app on a laptop screen (SH-01 – SH-07)** | Yes | **4 hours** | |
| 1.21.1 | UCI blue-and-gold redesign: side nav and header bar (artboards A2, D2, E1) | No | 3 hours | Jennifer Sun |
| 1.21.2 | Page not found, Not connected and reload pages; keyboard focus rings | No | 1 hour | Jennifer Sun |
| **1.22** | **MVP verification against the MOV (A1 – A10, SP-01 – SP-14)** | Yes | **10 hours** | |
| 1.22.1 | Chatbot benchmark: 20 questions and 10 held-out; tune the prompt | No | 2 hours | Zhenyu Song |
| 1.22.2 | Full acceptance run (acceptance.sh) | No | 1 hour | Brandon Lau |
| 1.22.3 | Walk the 63 user stories and log the findings | No | 3 hours | Brandon Lau |
| 1.22.4 | Walk the sponsor's Oct 21 requests (SP-01 – SP-14) | No | 2 hours | Brandon Lau |
| 1.22.5 | First drafts: setup guide, user guide, data dictionary, known limitations | No | 2 hours | Molly Tran |
| **1.23** | **Project management and sponsor communication** | No | **20 hours** | |
| 1.23.1 | Sponsor meeting Oct 21: confirm the three success metrics and the query needs | No | 4 hours | All team |
| 1.23.2 | Email the sponsor the LLM credit request ($100–200) | No | 1 hour | Brandon Lau |
| 1.23.3 | Verify the ZotGPT gateway: base URL, JSON mode, model names (by Oct 28) | No | 2 hours | Zhenyu Song |
| 1.23.4 | Sponsor meeting Oct 28 | No | 4 hours | All team |
| 1.23.5 | Code walkthrough: each owner reviews their module in the team repo | No | 8 hours | All team |
| 1.23.6 | Start the shared time log (actual hours per WBS ID) | No | 1 hour | Brandon Lau |
| **1.24** | **Capstone midterm report and presentation (due Oct 26)** | Yes | **16 hours** | |
| 1.24.1 | Report: project overview, import pipeline and MOV status | No | 2 hours | Molly Tran |
| 1.24.2 | Report: database and deployment | No | 2 hours | Brandon Lau |
| 1.24.3 | Report: UI walkthrough with screenshots | No | 2 hours | Jennifer Sun |
| 1.24.4 | Report: chatbot design and benchmark results | No | 2 hours | Zhenyu Song |
| 1.24.5 | Slides and Sunday rehearsal (1–2 minutes each) | No | 8 hours | All team |
| **1.25** | **SWE 277P Assignment 5: Work Breakdown Structure (due Oct 27)** | Yes | **6 hours** | |
| 1.25.1 | Project description and MOV update | No | 1 hour | Brandon Lau |
| 1.25.2 | WBS: sprints, tasks, owners and estimates | No | 3 hours | Brandon Lau |
| 1.25.3 | Estimation techniques | No | 1 hour | Jennifer Sun |
| 1.25.4 | Review and submit | No | 1 hour | Zhenyu Song |
| **1.26** | ***Milestone: MVP passes A1–A10 except A7 (Oct 22); midterm delivered (Oct 26)*** | No | **0 hours** | |

#### Sprint 2: Sponsor Demo and Backlog Features · Nov 3 – Nov 16 (Weeks 6–8) · Planned

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.27** | **Sprint 2 planning and tracking** | No | **10 hours** | |
| 1.27.1 | Record Sprint 1 actual hours; plan Sprint 2 (WBS update) | No | 2 hours | Brandon Lau |
| 1.27.2 | Weekly team syncs (Nov 3, Nov 10) | No | 8 hours | All team |
| **1.28** | **Mid-project demo to the sponsor (week 7)** | Yes | **10 hours** | |
| 1.28.1 | Set the attendance-source note on main's 12twenty events (SF-3) | No | 1 hour | Brandon Lau |
| 1.28.2 | Rebuild the main stack; click through every page with a real AI model | No | 1 hour | Brandon Lau |
| 1.28.3 | Try an Excel and a CSV export in Safari | No | 1 hour | Jennifer Sun |
| 1.28.4 | Demo script and dry run (README story order) | No | 2 hours | Brandon Lau |
| 1.28.5 | Demo to the sponsor and collect feedback | No | 4 hours | All team |
| 1.28.6 | Ask the sponsor: result sharing (D1), waitlisted registrants, postdocs as students, Notes wording | No | 1 hour | Brandon Lau |
| **1.29** | **B4 Warn when an event is uploaded a second time (bug, high; SF-1)** | Yes | **8 hours** | |
| 1.29.1 | Design draft: preview warning with Replace, Add anyway and Cancel | No | 1 hour | Jennifer Sun |
| 1.29.2 | Detect an existing event with the same name and term, or mostly the same people | No | 2 hours | Molly Tran |
| 1.29.3 | Preview warning and the three choices | No | 2 hours | Jennifer Sun |
| 1.29.4 | Replace an event's rows in one transaction | No | 2 hours | Molly Tran |
| 1.29.5 | Test the 35-row then 38-row download; Chat must answer 38 | No | 1 hour | Jennifer Sun |
| **1.30** | **Delete a committed import (handoff backlog; second half of the B4 fix)** | Yes | **4 hours** | |
| 1.30.1 | Delete API: remove the event, its rows and its flags | No | 2 hours | Molly Tran |
| 1.30.2 | Delete button with a confirm step on the Dataset page | No | 1 hour | Jennifer Sun |
| 1.30.3 | Tests | No | 1 hour | Molly Tran |
| **1.31** | **B1 Delete a conversation and set a retention period** | Yes | **9 hours** | |
| 1.31.1 | Design draft; ask the sponsor about UCI retention and the query log | No | 1 hour | Zhenyu Song |
| 1.31.2 | Delete API for a conversation (its turns go with it) | No | 1 hour | Zhenyu Song |
| 1.31.3 | App settings table and retention setting (never, 6, 3 or 1 month) | No | 2 hours | Brandon Lau |
| 1.31.4 | Cleanup job that deletes conversations past the retention period | No | 2 hours | Zhenyu Song |
| 1.31.5 | Delete in Recent questions; retention choice in Settings | No | 2 hours | Jennifer Sun |
| 1.31.6 | Tests | No | 1 hour | Zhenyu Song |
| **1.32** | **B2 Downloads page for AI results** | Yes | **5 hours** | |
| 1.32.1 | Design draft: which answers to list; name and icon in the side nav | No | 1 hour | Jennifer Sun |
| 1.32.2 | API that lists answers (question, date, row count) | No | 1 hour | Zhenyu Song |
| 1.32.3 | Downloads page with Excel and CSV buttons | No | 2 hours | Jennifer Sun |
| 1.32.4 | Tests | No | 1 hour | Jennifer Sun |
| **1.33** | **B3 Insights button on the Dataset page** | Yes | **4 hours** | |
| 1.33.1 | Spike: how the chatbot answers an open "insights" question | No | 1 hour | Zhenyu Song |
| 1.33.2 | Preset question set: by event, by school, repeat attendees, by term | No | 1 hour | Zhenyu Song |
| 1.33.3 | Insights button opens a new chat and sends the set | No | 1 hour | Jennifer Sun |
| 1.33.4 | Re-run the benchmark (main and held-out) | No | 1 hour | Zhenyu Song |
| **1.34** | **Fixes from the sponsor walkthrough (SF-2, SF-4, SF-5, SF-9)** | Yes | **5 hours** | |
| 1.34.1 | SF-2: warn at upload when the event date is blank | No | 1 hour | Molly Tran |
| 1.34.2 | SF-4: write the local summary as a sentence when sharing is off | No | 2 hours | Zhenyu Song |
| 1.34.3 | SF-5: refer to people by name in readings; re-run the benchmark | No | 1 hour | Zhenyu Song |
| 1.34.4 | SF-9: title-case the export headers and name the sheet | No | 1 hour | Molly Tran |
| **1.35** | **AI provider funding and second benchmark (A4)** | No | **3 hours** | |
| 1.35.1 | Set up the funded provider account with spending limits | No | 1 hour | Zhenyu Song |
| 1.35.2 | Benchmark a second provider (ZotGPT or OpenAI) | No | 2 hours | Zhenyu Song |
| **1.36** | **Import improvements (handoff backlog)** | Yes | **6 hours** | |
| 1.36.1 | Edit the event details of a committed import | No | 2 hours | Molly Tran |
| 1.36.2 | Attach a second file to an existing event | No | 2 hours | Molly Tran |
| 1.36.3 | Edit and attach controls on the Dataset page | No | 2 hours | Jennifer Sun |
| **1.37** | **Regression check and docs** | No | **5 hours** | |
| 1.37.1 | Re-walk the user stories that B1–B4 touch | No | 2 hours | Jennifer Sun |
| 1.37.2 | Full acceptance run and benchmark | No | 1 hour | Brandon Lau |
| 1.37.3 | Update the user guide and known limitations for B1–B4 | No | 2 hours | Brandon Lau |
| **1.38** | **SWE 277P schedule and cost assignments (placeholder; dates TBA)** | Yes | **6 hours** | |
| 1.38.1 | Project schedule from this WBS | No | 3 hours | Brandon Lau |
| 1.38.2 | Cost estimate from the WBS hours | No | 2 hours | Brandon Lau |
| 1.38.3 | Review | No | 1 hour | Brandon Lau |
| **1.39** | ***Milestone: sponsor demo given; B1–B4 built and tested*** | No | **0 hours** | |

#### Sprint 3: Hardening, Handoff and Final Delivery · Nov 17 – Dec 7 (Weeks 8–10, showcase) · Planned

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.40** | **Sprint 3 planning and meetings** | No | **18 hours** | |
| 1.40.1 | Record Sprint 2 actual hours; plan Sprint 3 | No | 2 hours | Brandon Lau |
| 1.40.2 | Weekly team syncs (Nov 17, Nov 24, Dec 1) | No | 8 hours | All team |
| 1.40.3 | Sponsor meetings (Nov 18, Dec 2; Nov 25 skipped for Thanksgiving) | No | 8 hours | All team |
| **1.41** | **Staff login (handoff backlog; acceptance test A7)** | Yes | **7 hours** | |
| 1.41.1 | Confirm with the sponsor: one staff account or several | No | 1 hour | Brandon Lau |
| 1.41.2 | AUTH_MODE=password: password hash, login and logout routes, httpOnly cookie | No | 3 hours | Molly Tran |
| 1.41.3 | Login page behind AuthGate; handle 401 in the API client | No | 2 hours | Jennifer Sun |
| 1.41.4 | A7 acceptance test: no data without signing in | No | 1 hour | Molly Tran |
| **1.42** | **Prepare for hosting on a UCI OIT server (handoff checklist)** | Yes | **7 hours** | |
| 1.42.1 | Ask OIT about data classification, hosting and allowed AI providers | No | 1 hour | Brandon Lau |
| 1.42.2 | HTTPS at nginx; publish only the HTTPS port | No | 2 hours | Brandon Lau |
| 1.42.3 | Secret storage and API key rotation (changing HUB_SECRET_KEY) | No | 2 hours | Brandon Lau |
| 1.42.4 | Scheduled pg_dump backups and a restore test | No | 2 hours | Brandon Lau |
| **1.43** | **CI on the team's GitHub repo** | No | **3 hours** | |
| 1.43.1 | GitHub Actions: ruff, pytest, Vitest, oxlint and build | No | 2 hours | Brandon Lau |
| 1.43.2 | Run the Playwright e2e test in CI | No | 1 hour | Brandon Lau |
| **1.44** | **ZotGPT support** | No | **3 hours** | |
| 1.44.1 | Adjust the JSON-mode detection or merge user messages if ZotGPT needs it | No | 2 hours | Zhenyu Song |
| 1.44.2 | Benchmark ZotGPT (main and held-out) | No | 1 hour | Zhenyu Song |
| **1.45** | **P1 features from the extension points (pending sponsor priority)** | Yes | **14 hours** | |
| 1.45.1 | F11 filter table on the Dataset page (SF-8): route | No | 1 hour | Molly Tran |
| 1.45.2 | F11 filter table on the Dataset page (SF-8): DataGrid page | No | 3 hours | Jennifer Sun |
| 1.45.3 | F12 data-quality view: list and resolve flags, fill blank fields (API) | No | 2 hours | Molly Tran |
| 1.45.4 | F12 data-quality view: list and resolve flags, fill blank fields (page) | No | 2 hours | Jennifer Sun |
| 1.45.5 | F14 saved queries: saved_query table and one-click run | No | 2 hours | Zhenyu Song |
| 1.45.6 | F14 saved queries: Saved list in the side nav | No | 1 hour | Jennifer Sun |
| 1.45.7 | F15 historical import: gpsrc_sheet adapter and migration | No | 3 hours | Molly Tran |
| **1.46** | **Final testing and acceptance** | No | **9 hours** | |
| 1.46.1 | Final acceptance run A1–A10, including A7 | No | 2 hours | Brandon Lau |
| 1.46.2 | Regression walk of all user stories | No | 3 hours | Zhenyu Song |
| 1.46.3 | Bug-fix buffer for the regression walk | No | 4 hours | All team |
| **1.47** | **Handoff to the GPSRC** | Yes | **9 hours** | |
| 1.47.1 | Update the handoff, setup and user guides, data dictionary and known limitations | No | 3 hours | Molly Tran |
| 1.47.2 | Regenerate the screenshots | No | 1 hour | Jennifer Sun |
| 1.47.3 | Install the Hub on the GPSRC computer (Docker Desktop) | No | 2 hours | Brandon Lau |
| 1.47.4 | Training session for GPSRC staff and student workers | No | 2 hours | Zhenyu Song |
| 1.47.5 | Hand over the repository and the key-handling steps | No | 1 hour | Brandon Lau |
| **1.48** | **Final report, final demo (Dec 4) and Capstone Showcase (Dec 7)** | Yes | **36 hours** | |
| 1.48.1 | Final report: import pipeline and MOV results | No | 2 hours | Molly Tran |
| 1.48.2 | Final report: database, deployment and project management | No | 2 hours | Brandon Lau |
| 1.48.3 | Final report: user interface | No | 2 hours | Jennifer Sun |
| 1.48.4 | Final report: chatbot, privacy and benchmark | No | 2 hours | Zhenyu Song |
| 1.48.5 | Final report: assemble, edit and submit | No | 2 hours | Jennifer Sun |
| 1.48.6 | Final presentation slides and rehearsal | No | 8 hours | All team |
| 1.48.7 | Final demo to the sponsor and instructor (Dec 4) | No | 4 hours | All team |
| 1.48.8 | Showcase poster | No | 2 hours | Jennifer Sun |
| 1.48.9 | Capstone Showcase booth and live demo (Dec 7) | No | 8 hours | All team |
| 1.48.10 | Peer evaluations | No | 4 hours | All team |
| **1.49** | ***Milestone: MOV met and the Hub handed over (Dec 4); showcase (Dec 7)*** | No | **0 hours** | |

#### Post-capstone backlog (not scheduled; not counted in the capacity check)

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.50** | **Items left for the next team or a later phase** | No | **10 hours** | |
| 1.50.1 | F16 multiple staff accounts and an admin page (needs login first) | No | 3 hours | Molly Tran |
| 1.50.2 | Native Anthropic or Gemini connector | No | 3 hours | Zhenyu Song |
| 1.50.3 | Attendance roster by school to measure service gaps (SF-7; new data source) | No | 4 hours | Molly Tran |

### Effort by person and sprint

Rows owned by "All team" are split evenly across the four members.

| Person | Role | Sprint 0 | Sprint 1 | Sprint 2 | Sprint 3 | Total |
|---|---|---|---|---|---|---|
| Brandon Lau | Database / DevOps | 24 | 26 | 21 | 31 | **102** |
| Jennifer Sun | Frontend | 27 | 29 | 20 | 26 | **102** |
| Molly Tran | Backend / Data Import | 32 | 29 | 16 | 26 | **103** |
| Zhenyu Song | AI / Chatbot | 26 | 36 | 18 | 23 | **103** |
| **Total** | | **109** | **120** | **75** | **106** | **410** |
| Capacity | 4 × 10 h × weeks | 140 | 80 | 80 | 100 | 400 |
| Load | | 78% | 150% | 94% | 106% | 103% |

---

## 4. Estimation Techniques

We combined several techniques. Each one is described below with where we used it.

### Decomposition (top-down, then bottom-up)

We broke the project down from the top: project, then sprints, then deliverables and user stories, then tasks. Then we estimated each task and added the tasks up, so every deliverable's hours are the sum of its tasks (the subtotal formulas in WBS.xlsx). We kept two rules:

- **No task over 4 hours for one person.** A bigger task was split until a single owner could finish it in one sitting. Only "All team" rows such as meetings are larger, and they are 2 hours or less per person.
- **One owner per task.** The owner is the person accountable for it, by role.

### Analogous estimation from Sprint 1

Sprint 1 is the best reference we have, because we built the whole MVP in it. The build sessions took about 28 hours of elapsed time, from the first to the last commit of each session:

| Session | Scope | Elapsed time |
|---|---|---|
| S1 | Design spec and implementation plans | 2.3 h |
| S2 | Database, import pipeline, identity linking, dataset export | 1.3 h |
| S3 | Chatbot: graph, SQL guard, AI models, streaming, benchmark | 6.9 h |
| S4 | Frontend: Upload, Chat, Settings and Dataset pages | 1.9 h |
| S5 | Benchmark tuning, timing test, handoff documents | 2.4 h |
| S6 | UI redesign, 63 user stories and their walkthrough, fixes | 8.1 h |
| After S6 | A2 revision, sponsor walkthrough, header bar, backlog | 5.3 h |

The build items in Sprint 1 (1.10 to 1.22) add up to 78 hours. That is the session time plus each owner's time to specify, review, test and walk through their part. At the end of Sprint 1 we will compare this with the hours in the time log.

For the new work in Sprints 2 and 3, we sized each item against a similar Sprint 1 item:

| New item | Similar Sprint 1 item | Sprint 1 hours | Estimate | Why it differs |
|---|---|---|---|---|
| B4 duplicate-event warning (1.29) | Duplicate-file protection and upload cards (1.11.5, 1.11.6) | 4 | 8 | Adds a design draft and a Replace flow that must run in one transaction |
| B1 delete a conversation and set retention (1.31) | US-08 Settings (1.18) | 5 | 9 | Adds a migration, a settings table and a cleanup job |
| B2 Downloads page (1.32) | US-10 Dataset page and the download buttons (1.20, 1.19.3) | 3 | 5 | Needs a new list API and a new item in the side nav |
| Staff login (1.41) | US-08 encrypted settings (1.18) | 5 | 7 | The code already has the seams (`get_current_user`, `AuthGate`), so login changes one dependency and adds one page |
| F11 filter table (1.45.1, 1.45.2) | US-10 Dataset page (1.20) | 2 | 4 | The query service exists; the work is a filterable grid |

### Three-point (PERT) estimates for uncertain items

Several Sprint 2 and 3 items have no design yet or depend on answers from the sponsor or OIT. For these we estimated an optimistic (O), most likely (M) and pessimistic (P) value and used the PERT expected value E = (O + 4M + P) / 6, rounded to whole hours:

| Item | O | M | P | E (in the WBS) | Main uncertainty |
|---|---|---|---|---|---|
| B4 duplicate-event warning (1.29) | 5 | 7 | 15 | 8 | How to detect "mostly the same people"; the Replace flow |
| Delete a committed import (1.30) | 2 | 4 | 6 | 4 | Removing people who appear in no other event |
| B1 conversations and retention (1.31) | 6 | 8 | 16 | 9 | The sponsor's retention policy; whether to keep the query log |
| B2 Downloads page (1.32) | 3 | 5 | 7 | 5 | Whether to list every answer or only downloaded ones |
| B3 Insights button (1.33) | 2 | 3 | 10 | 4 | What the chatbot does with an open question; a prompt change means a benchmark re-run |
| Import improvements (1.36) | 4 | 6 | 8 | 6 | Edge cases when files are attached to an existing event |
| Staff login (1.41) | 4 | 6 | 14 | 7 | One account or several |
| OIT hosting preparation (1.42) | 4 | 6 | 14 | 7 | OIT's answers on hosting, data classification and AI providers |
| CI (1.43) | 2 | 3 | 4 | 3 | Running the Docker-based e2e test in CI |
| ZotGPT support (1.44) | 1 | 2 | 9 | 3 | Whether the gateway supports JSON mode |
| P1 features F11, F12, F14, F15 (1.45) | 8 | 14 | 20 | 14 | Which ones the sponsor wants first |

### Fixed-duration items and expert judgment

- **Meetings** are counted as the number of meetings × the people attending × the length. A one-hour sponsor meeting with four of us is 4 hours, and a weekly team sync is 1 hour each.
- **Course deliverables** were estimated by the owner of each section, based on how long the earlier assignments (A1 to A4) and the SWE 276P report took us.

### Capacity check and leveling

The charter budgets about 10 hours per person per week, which gives 400 hours for the ten weeks. The WBS plans 410 hours (103%).

- **Sprint 1 is at 150% on purpose.** The charter spread the build over weeks 5 to 9. With AI-assisted development we built it in Sprint 1 instead, which freed Sprints 2 and 3 for the backlog and the handoff.
- **Sprint 3 is at 106%.** It includes Thanksgiving week, so we will drop the P1 feature the sponsor ranks lowest if the sprint runs late.
- **Leveling.** After we gave each technical task to the owner of its area, Brandon had the fewest hours, because the database and DevOps work is the smallest area. We then gave out the coordination tasks a project manager would usually own (sprint planning, the time log, sponsor questions, the regression walks, the schedule and cost assignments) to even the load, mostly to Brandon. Each member plans about 100 hours over the quarter: Brandon 102, Jennifer 102, Molly 103 and Zhenyu 103. Zhenyu carries more in Sprint 1, and Brandon more in Sprint 3.

### Contingency

- Sprint 2 has 5 hours of spare capacity, and Sprint 3 has a 4-hour bug-fix buffer (1.46.3).
- Items that do not fit are kept in the post-capstone backlog instead of squeezing the schedule.
- Items that depend on the sponsor or OIT carry a wide PERT range, so their estimates already absorb part of a delay, and a "no" from the sponsor frees hours instead of costing them.

### Tracking actual time from now on

- Starting this sprint, each member logs their hours in the shared time log against a WBS number (task 1.23.6).
- At each sprint planning (1.27.1 and 1.40.1), we add an **Actual Time** column to the WBS, compare it with the estimate, and re-estimate the next sprint. Any task more than 25% over its estimate is discussed at the planning meeting, and the cause feeds into the next estimates.
