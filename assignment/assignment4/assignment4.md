# Project Charter: Program Registration & Attendance Data Hub

**Authors:** Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song

**Date:** October 18, 2026

### Project Stakeholders

| Name | Title / Role |
|---|---|
| Kayleigh Anderson-Natale, PhD | Director of Postdoc and Professional Development, UCI Graduate Division. Project sponsor and main user |
| Rosie Victor, Karen Friedlander | GPSRC staff. Users who provide sample data and confirm export formats |
| GPSRC student assistants | Upload event attendance files |
| Graduate Division leadership and partner schools | Receive reports from GPSRC staff |
| Prof. Emily Navarro, Rakib Hossain | SWE 277P instructor and TA |
| Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song | Project team |

---

## 1. Project Description

The Graduate & Postdoctoral Scholar Resource Center (GPSRC) runs events for graduate students and postdocs all year. Students register on CampusGroups or 12twenty. After each event, student assistants download the attendee list and paste it into a yearly Google Sheet, adding the event details by hand.

This makes reporting hard for the sponsor:

- The data is spread across one file per event and one large sheet per year, which is hard to filter and combine in Excel.
- The two platforms export different columns. For example, 12twenty has no NetID.
- Simple questions take manual work, such as how many students from a school attended, or the emails of everyone who came to Bagel Breakfast. The sheet counts rows, not unique students.

Our original proposal also included registration and attendance reconciliation and certificate tracking. In the October 14 meeting the sponsor removed both, because student assistants already handle reconciliation.

We will build a web app that runs locally on one GPSRC computer. Staff upload each event's export, and the app adds it to one dataset that keeps growing over the years. Staff can then ask questions in plain English through an AI chatbot and download the results as Excel files. The AI only writes SQL from a description of the data, so student records stay on the computer.

**Desired impact:** staff can quickly show leadership how many students the GPSRC reaches, by school and program, and find groups of students the GPSRC is not reaching.

---

## 2. Measurable Organizational Value (MOV)

This project will be successful if, by December 4, 2026, staff can load the sponsor's sample files into one dataset that matches the sponsor's compiled sheet, and the chatbot correctly answers at least 90% (18 of 20) of a set of sponsor-style reporting questions.

| Area | Value | Metric | Target |
|---|---|---|---|
| Strategic | Do more | Benchmark questions answered correctly | At least 18 of 20 |
| Operational | Better | Sample files imported correctly | 293 rows and 79 unique NetIDs, the same as the compiled sheet, with no duplicates when a file is uploaded twice |
| Operational | Faster | Time to answer a question and download the Excel file | Under 1 minute |

---

## 3. Project Scope

**In scope**

- Import 12twenty and CampusGroups attendee exports without editing them
- Enter event details at upload
- Combine everything into one permanent dataset in the GPSRC Data Project format
- Match the same person across events by NetID or email
- AI chatbot that answers plain-English questions and shows the SQL it used
- Export any result to Excel or CSV
- Local install with one staff login

**Out of scope**

- Registration and attendance reconciliation
- Certificate and multi-session programs
- Charts and dashboards
- Multiple user accounts and roles
- Cloud or UCI server hosting, UCI single sign-on
- Live connections to 12twenty, CampusGroups, or Zoom
- Real student data (we use synthetic data only)

---

## 4. Project Schedule Summary

**Start:** September 24, 2026 &nbsp;&nbsp; **End:** December 4, 2026

| Weeks | Dates | Work | Milestone |
|---|---|---|---|
| 1–4 | Sep 24 – Oct 21 | Sponsor meetings, scope, MOV, business case, charter, project setup | Sponsor confirms scope (Oct 21) |
| 5 | Oct 22 – Oct 28 | Database and file import | Sample files import correctly |
| 6 | Oct 29 – Nov 4 | Chatbot | First chatbot answers |
| 7 | Nov 5 – Nov 11 | Chat screen, export, login | Mid-project demo to sponsor |
| 8–9 | Nov 12 – Nov 25 | Fix feedback, testing, benchmark | MVP complete |
| 10 | Nov 26 – Dec 4 | Documentation and handoff | Final demo |

---

## 5. Resources Required

**People**

- Project team: 4 students, about 10 hours per person per week
- Sponsor: 1-hour weekly meeting and demo reviews
- GPSRC staff: sample data and format checks
- Instructor and TA: weekly guidance

**Technology**

- React, FastAPI, PostgreSQL, and Docker (all free and open source)
- ZotGPT Gateway from UCI OIT for the chatbot, with OpenAI or DeepSeek as alternatives
- GitHub for code and a free project board for sprint tracking
- Team laptops and an existing GPSRC computer

**Other**

- Synthetic sample data from the sponsor (already received)

---

## 6. Cost of Resources

Team and staff time is estimated at $25 per hour.

| Resource | Estimate | Cost |
|---|---|---|
| Project team | 4 people × 10 h/week × 10 weeks = 400 h | $10,000 |
| Sponsor and GPSRC staff | About 20 h | $500 |
| ZotGPT usage | Covered by $100 in OIT test credits | $100 |
| OpenAI / DeepSeek testing | With spending limits | $20 |
| Software and hardware | Free tools, existing computers | $0 |
| **Total** | | **$10,620** |

The GPSRC pays nothing in cash, since the team works as part of the capstone course and the software is free.
