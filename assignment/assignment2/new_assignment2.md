# Assignment 2: Measurable Organizational Value (MOV)

**Project:** Program Registration & Attendance Data Hub

**Team:** ZotSync: Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu (Eric) Song

**Sponsor:** Kayleigh Anderson-Natale, PhD, Director of Postdoc and Professional Development, Graduate & Postdoctoral Scholar Resource Center (GPSRC), UCI Graduate Division

**Date:** October 27, 2026 (the sponsor confirmed this MOV on October 21, 2026)

---

## Part 1. The MOV

> **This project will be successful if, by December 4, 2026, staff can load the sponsor's sample files into one dataset that matches the sponsor's compiled sheet, with no duplicates, and the chatbot correctly answers at least 90% (18 of 20) of a set of sponsor-style reporting questions, with each answer downloaded as an Excel file in under one minute.**

We reached this statement with the six steps from Lecture 2.

**Step 1. Area of impact**

- **Strategic (primary).** The GPSRC needs to show Graduate Division leadership and partner schools how many students its programs reach, and to find the groups of students it is not reaching.
- **Operational (secondary).** Today student assistants paste each event's attendee export into a yearly Google Sheet by hand, and staff answer every reporting question by filtering and combining those sheets in Excel.

**Step 2. Value**

- **Do more.** Answer questions the spreadsheets cannot answer today, such as how many *unique* students from one school attended. The yearly sheet counts rows, not people.
- **Better.** One accurate dataset that links the same person across events and never counts an attendee twice.
- **Faster.** An answer in under a minute, instead of filtering, sorting, copying between sheets and removing duplicates by hand.

**Step 3. Metrics**

| Area | Value | Metric | Today | Target |
|---|---|---|---|---|
| Strategic | Do more | Sponsor-style reporting questions answered correctly by the chatbot | Questions about unique students need manual de-duplication across several files | At least 18 of 20 (90%) |
| Operational | Better | Sample files imported correctly | Each export is pasted by hand; the two platforms export different columns (12twenty has no NetID) | 293 rows and 79 unique NetIDs, the same as the sponsor's compiled sheet; 0 rows added when a file is uploaded again |
| Operational | Faster | Time from asking a question to a downloaded Excel file | "Several files and a long time" (sponsor, October 21) | Under 1 minute |

How we measure each metric:

- **Chatbot accuracy.** We wrote 20 reporting questions in the style the sponsor uses, with the correct answer worked out in advance from the sample data. One example is "How many unique Biological Sciences students came to a Bagel Breakfast in Fall 2026?" An answer counts as correct only if its result matches the known answer. Ten more questions, written before any tuning, check that the chatbot was not fitted to the 20.
- **Import accuracy.** We upload the sponsor's 10 synthetic sample exports (6 from CampusGroups, 4 from 12twenty) and compare the result with the sponsor's compiled sheet. Then we upload every file a second time and check that the dataset still has 293 rows.
- **Speed.** We time benchmark questions from the moment the question is sent to the moment the Excel file is saved.

All three checks are automated acceptance tests, so we can re-run them at any time.

**Step 4. Time frame.** By December 4, 2026: the end of the project period (September 24 to December 4) and the date of the final demo to the sponsor and instructor.

**Step 5. Verify and agree.** We presented the three metrics to the sponsor at the weekly meeting on October 21, 2026, and the sponsor confirmed them (see Part 3).

**Step 6. Statement.** The statement at the top of Part 1.

---

## Part 2. How the MOV Supports the GPSRC's Vision, Mission and Strategy

The GPSRC exists to support UCI's graduate students and postdoctoral scholars through professional development, wellness and fellowship programs. To serve all of them, and not only the ones who already come, it has to know who its programs reach and who they miss. Today that is hard to see. The attendance data sits in one file per event and one large sheet per year, CampusGroups and 12twenty export different columns, and the sheet counts entries instead of unique students. The "Do more" metric targets this directly. If the chatbot answers 18 of 20 reporting questions correctly, staff can see how many unique students from each school, department and program attend, who comes back to several events, and which schools rarely appear. The sponsor expects this to help the GPSRC find gaps in its services and make its programs more responsive, so that more of the graduate population is served.

The GPSRC's strategy also depends on showing its work to Graduate Division leadership and partner schools. A new dean recently asked for data on a full year of programming, and schools such as Biological Sciences ask how many of their students attended. Today each request means filtering, sorting, copying and removing duplicates across several files. The "Faster" metric turns that into a question answered and downloaded as Excel in under a minute, so staff can answer leadership quickly and spend their time on programs instead of spreadsheets. The "Better" metric protects trust in those numbers: if the imported data matches the compiled sheet row for row and a re-uploaded file never counts twice, the numbers sent to the dean are the ones staff would have produced by hand. Each answer also shows the SQL behind it, so staff can check a number before sending it. Finally, the MOV is met without putting student records at risk, which the Graduate Division must protect under FERPA. The Hub runs on one GPSRC computer and links students by NetID and email, never by student ID. The AI writes SQL from a description of the data, and it sees query results only when staff turn that on.

---

## Part 3. Communication with the Sponsor About the MOV

Our MOV changed once, as the sponsor's needs became clearer. At the first meeting on October 7, Kayleigh, Rosie and Karen walked us through how student assistants check event sign-ins against registrations and copy each event into a yearly sheet, and the staff estimated that reconciling one event takes 20 to 30 minutes. Our first draft MOV was therefore operational: cut that reconciliation time by a set percentage. In the same meeting, however, Kayleigh explained that the project is not about compliance. Its value is reporting, such as answering the new dean's request for a year of data or telling a school how many unique students it sent. On October 14 the sponsor removed reconciliation from the scope, because student assistants already do it at the front desk, and asked us to focus on combining event exports into one long-term dataset that staff can query and export. Our time-saving metric no longer measured anything the sponsor needed, so we rewrote the MOV around reporting. Because we chose an AI chatbot as the way staff ask questions, chatbot accuracy became the main metric, with import accuracy and speed beside it. We presented the three metrics at the October 21 meeting. Kayleigh agreed that all three are reasonable and said the tool would help the GPSRC find gaps in its services. Kayleigh also told us that finding out who comes to the programs now takes several files and a long time, and listed the kinds of questions the tool must handle: by event, by school or department, by student name, by a mix of these and by date range, with full and partial exports to Excel. We walked each of these requests through the prototype on October 22.
