# Work Breakdown Structure: Program Registration & Attendance Data Hub

**Authors:** Brandon Lau, Molly Tran, Jennifer Sun, Zhenyu Song

**Date:** October 25, 2026

---

## Project Basics

- **Project name:** Program Registration & Attendance Data Hub
- **Project team name:** ZotSync
- **Team members:** Brandon Lau (Database / DevOps), Jennifer Sun (Frontend), Molly Tran (Backend / Data Import), Zhenyu Song (AI / Chatbot)

---

## 1. Project Description

*Adapted from the project charter.*

**Problem.** The Graduate & Postdoctoral Scholar Resource Center (GPSRC) runs events all year, and students register on CampusGroups or 12twenty. After each event, a student assistant copies the attendee list into a yearly Google Sheet. The two platforms export different columns, and the data is spread over many files. Answering a simple question, such as how many students from one school came to events this term, takes manual filtering, sorting and de-duplicating in Excel.

**Solution.** A web app that runs on one GPSRC computer. Staff upload each event's export as-is, and the app merges it into one dataset and links the same person across events. Staff ask questions in plain English, see the SQL the AI wrote and the result table, and download any result as Excel or CSV.

**Desired impact.** Staff can quickly show Graduate Division leadership how many students the GPSRC reaches, by school and term, and spot groups it is not reaching, without compiling sheets by hand.

**Update since the charter.** The team built the MVP early, from October 20 to 22, with AI-assisted development. Every acceptance test passes except staff login, which moved to Sprint 3.

---

## 2. Measurable Organizational Value (MOV)

> This project will be successful if, by December 4, 2026, staff can load the sponsor's sample files into one dataset that matches the sponsor's compiled sheet, with no duplicates, and the chatbot correctly answers at least 18 of 20 sponsor-style reporting questions, each in under one minute.

| Metric | Target | Status on Oct 22 |
|---|---|---|
| Benchmark questions answered correctly | At least 18 of 20 | 20 of 20 |
| Sample files imported | 293 rows and 79 unique NetIDs; no duplicates on re-upload | Met, except that a second export of the same event is still counted twice; fixed in Sprint 2 (WBS 1.20) |
| Question to downloaded Excel file | Under 1 minute | 4 to 7 seconds |

The sponsor confirmed these three metrics on October 21.

---

## 3. Work Breakdown Structure

The WBS is in the attached **shorter_WBS.xlsx**, in the format of the week 4 in-class activity, and is copied below.

- **Estimated Time** is in person-hours. A row owned by "All team" counts all four members, so a 1-hour meeting is 4 hours.
- **Current sprint (Sprint 1)** is broken down into five user stories (WBS 1.9 to 1.13), each written from a GPSRC staff member's point of view, and each user story into tasks.
- **Sprints 2 and 3** cover only the work already agreed for after the MVP: four follow-up features from the team and sponsor review of the MVP, staff login, and the work to hand the Hub over to the GPSRC. We break them down further at each sprint planning.

| Sprint | Dates | Goal | Planned hours | Capacity | Status |
|---|---|---|---|---|---|
| Sprint 0 | Sep 24 – Oct 19 | Team, scope and planning documents | 60 | 140 | Complete |
| Sprint 1 | Oct 20 – Nov 2 | Build and verify the MVP; midterm; this WBS | 93 | 80 | **Current** |
| Sprint 2 | Nov 3 – Nov 16 | Sponsor demo; four follow-up features | 47 | 80 | Planned |
| Sprint 3 | Nov 17 – Dec 7 | Login, CI, handoff; final report, demo and showcase | 72 | 100 | Planned |
| **Total** | | | **272** | **400** | |

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1** | **Program Registration & Attendance Data Hub** | Yes | **272 hours** | |

#### Sprint 0: Initiation and Planning · Sep 24 – Oct 19 · Complete

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.1** | **SWE 277P Assignment 1: Team Statement (Oct 6)** | Yes | **8 hours** | All team |
| **1.2** | **SWE 277P Assignment 2: MOV (Oct 13)** | Yes | **8 hours** | All team |
| **1.3** | **SWE 276P: Project Scope and High-Level Design report (Oct 16)** | Yes | **16 hours** | All team |
| **1.4** | **SWE 277P Assignment 3: Business Case (Oct 20)** | Yes | **8 hours** | All team |
| **1.5** | **SWE 277P Assignment 4: Project Charter (Oct 20)** | Yes | **8 hours** | All team |
| **1.6** | **Sponsor meetings and requirements (Oct 7, Oct 14)** | No | **12 hours** | All team |
| **1.7** | ***Milestone: scope, MOV, business case and charter submitted*** | No | **0 hours** |  |

#### Sprint 1: MVP Build · Oct 20 – Nov 2 · Current sprint

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.8** | **Sprint planning and MVP design spec** | Yes | **5 hours** |  |
| 1.8.1 | MVP design spec and build plans | No | 4 hours | Zhenyu Song |
| 1.8.2 | Team GitHub repo and shared time log | No | 1 hour | Brandon Lau |
| **1.9** | **User story: As staff, I can upload an event's export file as-is** | Yes | **14 hours** |  |
| 1.9.1 | Database schema and migrations | No | 2 hours | Brandon Lau |
| 1.9.2 | Read CampusGroups and 12twenty files; detect which platform a file came from | No | 4 hours | Molly Tran |
| 1.9.3 | Block the same file from being imported twice; save the import | No | 2 hours | Molly Tran |
| 1.9.4 | Upload page and event details form | No | 4 hours | Jennifer Sun |
| 1.9.5 | Tests: the sample files give 293 rows and 79 unique students; a re-upload adds nothing | No | 2 hours | Molly Tran |
| **1.10** | **User story: As staff, I see the same person linked across events** | Yes | **4 hours** |  |
| 1.10.1 | Match people by NetID, then by email; flag uncertain matches | No | 3 hours | Molly Tran |
| 1.10.2 | Tests for the matching cases | No | 1 hour | Molly Tran |
| **1.11** | **User story: As staff, I can ask a question in plain English and see the SQL and the result table** | Yes | **13 hours** |  |
| 1.11.1 | AI pipeline from question to SQL, with follow-up questions, clarifying questions and error repair | No | 4 hours | Zhenyu Song |
| 1.11.2 | SQL guard: allow only one read-only SELECT on one view | No | 2 hours | Zhenyu Song |
| 1.11.3 | Read-only database view and role | No | 1 hour | Brandon Lau |
| 1.11.4 | Chat page: question box, progress steps, answer card | No | 4 hours | Jennifer Sun |
| 1.11.5 | Tests: no student data reaches the AI when sharing is off; harmful SQL is blocked | No | 2 hours | Zhenyu Song |
| **1.12** | **User story: As staff, I can choose the AI model and decide whether it may see query results** | Yes | **5 hours** |  |
| 1.12.1 | AI model settings with encrypted keys, a Test connection button and sharing rules | No | 3 hours | Zhenyu Song |
| 1.12.2 | Settings page and the per-question sharing switch | No | 2 hours | Jennifer Sun |
| **1.13** | **User story: As staff, I can download results as Excel or CSV and see what was imported** | Yes | **4 hours** |  |
| 1.13.1 | Excel and CSV export, safe against formula injection; whole-dataset export | No | 2 hours | Molly Tran |
| 1.13.2 | Dataset page and download buttons | No | 2 hours | Jennifer Sun |
| **1.14** | **MVP verification against the MOV and the acceptance tests** | Yes | **8 hours** |  |
| 1.14.1 | Chatbot benchmark: 20 sponsor-style questions, plus 10 held-out questions | No | 2 hours | Zhenyu Song |
| 1.14.2 | Run all acceptance tests; time a question to a downloaded Excel file | No | 2 hours | Brandon Lau |
| 1.14.3 | Try every user story by hand, plus the sponsor's Oct 21 requests | No | 4 hours | Brandon Lau |
| **1.15** | **Coordination and sponsor communication** | No | **19 hours** |  |
| 1.15.1 | Sponsor meetings (Oct 21, Oct 28) | No | 8 hours | All team |
| 1.15.2 | Check that UCI's ZotGPT AI service works with the Hub (by Oct 28) | No | 2 hours | Zhenyu Song |
| 1.15.3 | Send the sponsor the request for AI usage credits | No | 1 hour | Brandon Lau |
| 1.15.4 | Code walkthrough: each owner reviews their module | No | 8 hours | All team |
| **1.16** | **Capstone midterm report and presentation (Oct 26)** | Yes | **16 hours** |  |
| 1.16.1 | Report sections | No | 8 hours | All team |
| 1.16.2 | Slides and rehearsal | No | 8 hours | All team |
| **1.17** | **SWE 277P Assignment 5: Work Breakdown Structure (Oct 27)** | Yes | **5 hours** |  |
| 1.17.1 | WBS and estimates | No | 3 hours | Brandon Lau |
| 1.17.2 | Project description and MOV update | No | 1 hour | Molly Tran |
| 1.17.3 | Review and submit | No | 1 hour | Jennifer Sun |
| **1.18** | ***Milestone: MVP passes every acceptance test except staff login (Oct 22); midterm delivered*** | No | **0 hours** |  |

#### Sprint 2: Sponsor Demo and Follow-up Features · Nov 3 – Nov 16 · Planned

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.19** | **Mid-project demo to the sponsor (week 7)** | Yes | **6 hours** |  |
| 1.19.1 | Demo preparation and dry run | No | 2 hours | Brandon Lau |
| 1.19.2 | Demo and feedback | No | 4 hours | All team |
| **1.20** | **Warn when an event is uploaded twice; delete a saved import** | Yes | **7 hours** |  |
| 1.20.1 | Detect an event already in the dataset; replace or delete its rows | No | 4 hours | Molly Tran |
| 1.20.2 | Warning in the upload preview; delete button | No | 3 hours | Jennifer Sun |
| **1.21** | **Delete a chat conversation; set how long chats are kept** | Yes | **6 hours** |  |
| 1.21.1 | Delete API and automatic cleanup of old chats | No | 3 hours | Zhenyu Song |
| 1.21.2 | Database table for the retention setting | No | 1 hour | Brandon Lau |
| 1.21.3 | Delete button and retention choice in Settings | No | 2 hours | Jennifer Sun |
| **1.22** | **Downloads page that lists past AI results** | Yes | **3 hours** |  |
| 1.22.1 | API that lists past results | No | 1 hour | Zhenyu Song |
| 1.22.2 | Downloads page | No | 2 hours | Jennifer Sun |
| **1.23** | **Insights button on the Dataset page (preset questions)** | Yes | **4 hours** |  |
| 1.23.1 | Preset questions; re-run the chatbot benchmark | No | 3 hours | Zhenyu Song |
| 1.23.2 | Insights button | No | 1 hour | Jennifer Sun |
| **1.24** | **Fixes from the sponsor's demo feedback (placeholder)** | Yes | **8 hours** | All team |
| **1.25** | **Sprint 2 planning and tracking** | No | **13 hours** |  |
| 1.25.1 | Record Sprint 1 actual hours; plan Sprint 2 | No | 2 hours | Brandon Lau |
| 1.25.2 | Regression check and user guide update | No | 3 hours | Molly Tran |
| 1.25.3 | Weekly team syncs | No | 8 hours | All team |
| **1.26** | ***Milestone: sponsor demo given; the four follow-up features done*** | No | **0 hours** |  |

#### Sprint 3: Handoff and Final Delivery · Nov 17 – Dec 7 · Planned

| WBS | Task Description | Deliverable | Estimated Time | Resources |
|---|---|---|---|---|
| **1.27** | **Staff login (the one acceptance test not yet passing)** | Yes | **6 hours** |  |
| 1.27.1 | Login backend and its acceptance test | No | 4 hours | Molly Tran |
| 1.27.2 | Login page | No | 2 hours | Jennifer Sun |
| **1.28** | **Automated testing (CI) and installation at the GPSRC** | Yes | **5 hours** |  |
| 1.28.1 | GitHub Actions CI: run the tests on every change | No | 3 hours | Brandon Lau |
| 1.28.2 | Install the Hub on the GPSRC computer | No | 2 hours | Brandon Lau |
| **1.29** | **Handoff documents and staff training** | Yes | **5 hours** |  |
| 1.29.1 | Update the handoff, setup and user guides | No | 3 hours | Molly Tran |
| 1.29.2 | Training session for GPSRC staff | No | 2 hours | Zhenyu Song |
| **1.30** | **Final testing** | No | **6 hours** |  |
| 1.30.1 | Final acceptance test run and chatbot benchmark | No | 2 hours | Zhenyu Song |
| 1.30.2 | Regression check and bug fixes | No | 4 hours | All team |
| **1.31** | **Final report, final demo (Dec 4) and Capstone Showcase (Dec 7)** | Yes | **32 hours** |  |
| 1.31.1 | Final report | No | 8 hours | All team |
| 1.31.2 | Final presentation and demo | No | 12 hours | All team |
| 1.31.3 | Capstone Showcase | No | 8 hours | All team |
| 1.31.4 | Peer evaluations | No | 4 hours | All team |
| **1.32** | **Sprint 3 planning and meetings** | No | **18 hours** |  |
| 1.32.1 | Record Sprint 2 actual hours; plan Sprint 3 | No | 2 hours | Brandon Lau |
| 1.32.2 | Weekly team syncs and sponsor meetings | No | 16 hours | All team |
| **1.33** | ***Milestone: MOV met and the Hub handed over (Dec 4); showcase (Dec 7)*** | No | **0 hours** |  |

**Hours by person:** Brandon Lau 67, Jennifer Sun 64, Molly Tran 70, Zhenyu Song 71.

**Not in this plan:** the lower-priority features (filter table, data-quality view, saved queries, historical import), hosting on a UCI server, and the minor findings from the sponsor walkthrough. We add them only if the sponsor asks for them and there is time left.

---

## 4. Estimation Techniques

- **Decomposition.** We split each deliverable into tasks with one owner and no more than 4 hours of work for one person. A deliverable's estimate is the sum of its tasks.
- **Analogy.** Sprint 1 is our reference. The build sessions on October 20–22 took about 28 hours of elapsed time, and we added the owners' time to specify, review and test the code. Work in Sprints 2 and 3 is sized against similar Sprint 1 work. For example, the Downloads page (WBS 1.22) is sized like the Dataset page.
- **Three-point estimates** for items without a design yet: E = (O + 4M + P) / 6. The duplicate-event warning (WBS 1.20) is (4 + 4×6 + 14) / 6 = 7 hours, and staff login (WBS 1.27) is (3 + 4×6 + 9) / 6 = 6 hours.
- **Fixed durations.** Meetings are counted as the number of meetings × the people attending × the length.
- **Capacity check.** The charter budgets 10 hours per person per week, or 400 hours. We plan 272 hours (68% of the budget). Sprint 1 is over its share because the whole MVP was built in it. The unplanned time is kept for sponsor feedback, re-work and course assignments that are not posted yet, so we do not overcommit.
- **Tracking.** Each member logs actual hours against WBS numbers. At each sprint planning we add an Actual Time column and re-estimate the next sprint.
