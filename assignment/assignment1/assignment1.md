INTERNAL Team Statement
Group Members: Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu Song
Project Description (type this out) 
Section 1: Jennifer, Section 2: Molly, Section 3: Brandon, Section 4: Eric
1. What is this project actually trying to solve?
When the UCI Graduate Division hosts workshops or certificate programs, people sign up on one website (like 12twenty or CampusGroups) and then show up on Zoom or sign a physical sheet.
The problem? On Zoom, someone might use a nickname like "Dave's Laptop" or a personal Gmail address instead of their official UCI email. Right now, staff members spend hours manually comparing messy spreadsheets to figure out who actually attended, who skipped, and who showed up without registering.
2. What will our team build in 10 weeks?
We are building a web app prototype where staff can upload those messy spreadsheets and let the software do the heavy lifting:
Upload Spreadsheets: Staff drag and drop CSV or Excel files from Zoom, 12twenty, or sign-in sheets.
Automatic Exact Matching: The app immediately links people who used their official UCI NetID or UCI email.
Smart Suggestions (Review Queue): If someone's name on Zoom is slightly different, the app flags it and says: "Hey, is 'Dave S' the same person as 'David Smith'?" A staff member clicks Yes or No.
Attendance Tracking: The system categorizes everyone into one of four bucket statuses: Attended, Absent, Walk-in (attended without registering), or Unresolved.
Certificate & Multi-Session Tracking: It keeps track of students over multiple weeks to see who completed all required sessions for a certificate.
Reports & Exports: Staff can download clean, reconciled spreadsheets and view summaries of how many unique students they reached.
3. What are we explicitly NOT building?
We are not connecting directly to live university databases or software vendor APIs like Zoom. These registration records will be manually uploaded by the user.
We are not allowing the system to automatically merge records without human approval (to avoid accidental mistakes).
We are not setting up complex single sign-on (SSO) or deploying to live UCI servers. We are building a working web app prototype that runs locally or on a basic dev environment.
We will not support arbitrary spreadsheet parsing. The input will follow a defined format.
We will not support configurable criteria for certificate programs to determine who earns a certificate at the end. For example, there could be different requirements for different certificates, like “To earn this certificate, a student must attend 3 sessions out of a total of 5.”

4. Why is this project a great 10-week capstone fit?
File processing, database modeling, and building a clean UI fit well within a 10-week student schedule.
Clear Input/Output: We will be provided with sample/synthetic spreadsheet files, so you won't be blocked waiting for data access.
Full-Stack Deliverable: We get to design a backend database, build a matching algorithm, and create an intuitive frontend dashboard.
2. Initial Team Plan
Brandon Lau
Strengths: Writing clean, maintainable code and debugging issues.
One thing you want the team to know: Working full time during the day, so availability will be limited to evenings or weekends.
Jennifer Sun
Strengths: communication, planning, 
One thing you want the team to know: working full time but want to contribute well
Zhenyu Song
Strengths: 
One thing you want the team to know:
Molly Tran
Strengths: 
One thing you want the team to know:

Team Bonding : 7:30PM 10/6/2026 Dinner at restaurant
Ten Questions to ask Sponsor (completed, at bottom of doc)
1~3 Jennifer, 4~6 Molly, 7~8 and 11-12 Brandon, 9~10 Eric

 	List of Things we need to start learning

1~2 Jennifer, 3~4 Molly, 5~6 Brandon, 7~8 Eric
Understand the current staff workflow, including registration, attendance evidence, no-shows, walk-ins, unresolved records, and certificate-award decisions.
Learn how to parse the required 12twenty, CampusGroups/ZotSpot, Zoom, in-person sign-in, and certificate-cohort files; validate required columns; report errors; and convert different formats into a common structure.
Learn how to model participants, events, programs, sessions, registrations, attendance records, certificate requirements, awards, file imports, and identity-review decisions in a relational database.
Study data-cleaning techniques such as email and name normalization, exact matching by NetID or institutional ID, duplicate detection, candidate ranking, confidence indicators, and human-reviewed fuzzy matching.
Select and learn the team’s frontend, backend, database, and API technologies, and understand how the interface, reconciliation logic, file-processing pipeline, and database will work together.
Learn how to implement administrator/program-staff and read-only roles, least-privilege access, protected exports, basic activity logs, and safe handling of synthetic or de-identified participant information.
Learn how to generate event-reconciliation, certificate-progress, program-reach, and data-quality reports, as well as downloadable reconciled datasets.
Learn how to test file imports, matching decisions, permissions, reporting accuracy, and end-to-end workflows, while preparing setup instructions, a user guide, a data dictionary, known limitations, and handoff documentation.



3. Team Ground Rules
1~3 Jennifer, 4~6 Molly, 7~8  Brandon, 9~10 Eric


Prefer to divide and conquer the tasks, but also ask if unsure and we can do some together or help unblock others if challenges arise
Keep the team informed on your progress so there is no duplication of efforts or stepping on each other’s toes
We will meet after class ends if there’s free time, and try to do some work in person, but if people need to leave then it’s okay too. 
Communicate if you can’t attend or if something comes up; just try to be responsible and respectful of the other team members by keeping them in the loop and of their time.
If there is an issue, please try to address it as soon as possible and in a respectful way so it doesn’t blow up into a bigger issue.
Provide constructive and respectful feedback. It should focus on the work and not the person. 
We will use communication platforms like text messaging or Discord for team updates and target a response within 24 hours.
All major deliverables should be reviewed by at least one other team member prior to the submission deadline and allow for sufficient time for revisions if necessary.
Avoid interrupting each other when someone is speaking; ensure everyone has an opportunity to speak during team meetings.
Decisions will be made by consensus whenever possible, but if an agreement cannot be reached, a majority vote will determine the path forward.
We want good work quality, but also don’t feel like you need to spend an unreasonable amount of time on this (since we’re working and job searching).





3. Team Ground Rules
Divide and conquer when possible. We prefer to divide tasks based on each member’s strengths and availability. However, if someone is unsure about a task or needs help, they should ask, and we can work on it together.
Keep the team informed about progress. Everyone should provide reasonable updates on what they are working on, especially if a task is taking longer than expected or if there are blockers.
Balance quality with time. We want to produce high-quality work, but we also understand that everyone is balancing classes, work, and job searching. We should avoid spending an unreasonable amount of time trying to make something perfect when it is already good enough.
Meet in person when convenient. When possible, we can meet after classes to work together in person. However, if someone needs to leave or has another commitment, there is no expectation that everyone must stay.
Respond to team messages within a reasonable time. During weekdays, team members should try to respond to important messages within about 24 hours, even if the response is only to acknowledge the message and say when they can follow up.
Let the team know about schedule changes early. If someone cannot attend a meeting, complete a task on time, or has an unexpected conflict, they should inform the team as soon as possible rather than waiting until the deadline.
Be responsible for catching up after an absence. If a team member misses a meeting, they should review the meeting notes or group messages and ask questions if anything is unclear. Other members should help provide important context when needed.
Review important work before submission. Major deliverables, presentations, reports, or important technical decisions should be reviewed by at least one other team member before being finalized.
Give constructive and respectful feedback. Feedback should focus on the work rather than the person. Everyone should feel comfortable raising concerns, suggesting improvements, and disagreeing respectfully.
Make sure everyone has a chance to speak. During discussions and meetings, we should avoid interrupting each other and give everyone an opportunity to share their ideas or concerns.
Make decisions as a team when they affect everyone. For important decisions involving project scope, architecture, deadlines, or workload distribution, we should discuss the options together and try to reach agreement before moving forward.
Follow through on commitments. If someone agrees to own a task, they are responsible for completing it by the agreed deadline or communicating early if they need help or additional time.




Questions for Our Sponsor
Can you walk us through the current end-to-end workflow for reconciling registration and attendance data?
We would like to understand what staff currently do from receiving the files to producing the final report.
Can you provide representative sample files for each required data source, including 12twenty, CampusGroups/ZotSpot, Zoom, and in-person sign-in sheets?
We would also like to know which columns are always present and which ones may be missing.
Which identifiers should we prioritize when matching participants across different data sources?
For example, should NetID, student/employee ID, institutional email, and personal email have different levels of priority?
What kinds of identity-matching problems occur most often in practice?
For example, do you usually see different email addresses, nicknames, name formatting differences, duplicate records, or missing IDs?
For uncertain matches, what information would be most helpful for staff when deciding whether two records belong to the same person?
For example, would you like to see a confidence score, side-by-side record comparison, or the reason why the system suggested the match?
What should happen when a participant cannot be matched confidently to any registration record?
Should the record remain unresolved, be marked as a walk-in, or require manual staff review before a final status is assigned?
For certificate or multi-session programs, what rules are currently used to determine participant progress and completion?
Are attendance requirements different across programs, and which requirements should be included in the MVP versus entered manually by staff?
Which reports and exports are the highest priority for your team?
The proposal mentions event reconciliation, certificate progress, program reach, and data-quality reports. Which of these are used most frequently or provide the most value? 2026 Graduate Division MSE Capstone Project Proposal - Kayleigh Anderson Natale.pdfPDF
What would make the final prototype successful from your perspective?
Are there specific workflows, scenarios, or demo cases that you definitely want to see working by the end of the quarter?
If we have extra time after completing the required MVP, which stretch goal would provide the most value to your team?
 For example, should we prioritize the data-request workbook, re-importing enrichment files, richer audit history, or additional dashboards?
11. How should users authenticate? Google login? We don’t want to manage users and passwords.
12. Where should the app be deployed / ran? Locally? AWS? Any restrictions on tech stack or are we free to choose?
