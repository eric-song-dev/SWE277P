Can we get some test data (spreadsheets) soon? 
Main use cases? Examples? 
What provides the source of truth when reconciling participant identities? 
For the reports/exports, how might that look like, what kind of info are they looking for to be displayed on that? 
Could you clarify what cohort status, award status means (from required reports and exports primary content section on proposal doc)? 
Its a website, so can they host it on AWS? Do you have credits we can use? Or local? 
Stakeholders, where should it live?

Can you walk us through the current end-to-end workflow for reconciling registration and attendance data? 
Which identifiers should we prioritize when matching participants across different data sources? 
Can you provide sample files for each required data source, 12twenty, CampusGroups/ZotSpot, Zoom, and in person sign-in sheets? (Same as #1 above)
What kind of identifiers-matching problems do you see most often? Name formatting issues, missing emails, duplicate records, missing IDs?
Who are the actual end users of each report, is there an existing report template you currently send to sponsors we should match?
Which reports and exports are the highest priority for your team?
For the reports/exports, how might that look like, what kind of info are they looking for to be displayed on that? 
For certificate or multi-session programs, what rules are currently used to determine participant progress and completion?
Which reports and exports are the highest priority for your team?
Are there any specific workflows or scenarios you definitely want us to support?
For uncertain matches, what information would be most helpful for staff to decide whether two records belong to the same person?
How should users authenticate to the web app? Google Login? 
Where should the app be deployed / run? Locally, AWS? Any restrictions on tech stack or are we free to choose? (Same as #6)


For MVP
Can we just do 1 registration format, and 1 attendance format. 12twenty, and zoom?

Certificate and multi session programs, can we cut this out, maybe week 6 or 7 later if we have time?
—-
NOTES

At end, she wants an output of a report, 4 things. 

Basic workflow
After log in. Drag and drop, one box is registration, one box is attendance. Program will take those records, normalize it, figure out columns and participants and try to match them. After matching, front end will display all the matches, have a confidence score for each one, and allows the user to say like this should be with this instead. And at the end, user can say finalize, then output the report. 

Techstack - python, fast API, frontend - react. DB - figure after weds, if its cloud hosted AWS then use dynamoDB. If its local SQLite. 
Django - full stack framework 
—
If you choose Django instead of FastAPI, your new tech stack is a decoupled React + Django architecture, which breaks down as follows:
Frontend: React (handles the user interface, routing, and client-side state).
Backend & API: Django + Django REST Framework (DRF) (handles business logic, native user authentication, and provides the JSON API endpoints for React).
Database (Local): SQLite (seamlessly managed by Django's native Object-Relational Mapper).
Database (Cloud/AWS): Amazon RDS (PostgreSQL or MySQL) (instead of DynamoDB, because Django requires a relational SQL database to fully utilize its built-in authentication and features).
This structure gives you a robust, relational SQL-backed system where Django acts strictly as a powerful API backend and React runs as a separate client application.



Notes with prof emily
JIRA, tello, gitlab. One of these for coordinating the project. Burndown charts, gantts, can sync with discord. Maybe make it now before the requirements. 
—
Notes from zoom W 10/7
Dr. 
Karen operations? 11 years
Rosie - analyst  3 years
Intros 
Past few years, simple data. Rosie - spreadsheets. Campus groups, zot spot (registration). 12twenty for other programs (Registration). Outputs dont look the exact same. Want to see how many events eric song has attended over the academic year. NET ID (since its uniquely identifiable). 
rosie/kayliegh will share the folder. 
Differences in the outputs. 
NET ID, student id number these are the identiifers. Usually want the PII to be NET ID. 
Walk in - can look them up afterwards on campus group, (only what campus group gives is first name last name email, net ID). dont know if theyre international, masters students, doctoral, unless look that up. Want to get this under control, with central dept data dream. GPSRC 2026-2027, if we gave to data team ,they can pull things. 
12 TWENTY
Similar questions, it doesn’t have a net id, but their email is their netID? 99%. Usu use student numbers. Some are @ hs.uci which is diff. Unless like jennifer.sun@uci.edu change it. 
But dont have international/domestic question, dont think they can do it. 
No graduation term on campus groups. 
Program (here) vs depts is a bit different 
Check in (student assistants) is google form. They grab the names, then go to the registrations ones and mark them as attended. 
They have like a master data spreadsheet (except maybe not certificate) A through like H is what th student worker fills out when they copy and apste the stuff on the right. 
1 challenge she mentioned is not consistent, so allowing blank columns after uploaded that can be addressed later
1 other thing is she mentioned itd be nice for them to do human in the loop to confirm this is the correct match
Would like an output similar to excel, what students from this group, csv. 
Templates, understanding these things. Next week can go forward from this.
Netid is better, because name and student id together is technicaly a FERPA issue but its more about reporting 
Pulling by school biological sciences, how many of her students attended, how many unique students. 
Dashboard, to see these more user friendly, but also to download the export excel. 
Bagel breakfast, invite to donut breakfast. Pull on events, can email those people. 
Current output GSRCP Data project template, pretty in line with this. Campus group vs 12twenty. 
12twenty the NET Id isn’t there, their identifying info is the email address that record. 
Associated with their student account NETID for campus groups. 
Sometimes google form, what platform is that marketed on. 
Certificate programs (don’t focus on this, only if that has time for later.
12twenty? Its the uci email, if its . can change to email address. Still unique,it can still flag. See if it doesn’t match exactly, then human review. Post docs. 
AWS , log in, all can access, database create so they dont have to pull it down. 
Usually dont have the data stored for rsvp, but usually only work with who attended the events. Ipad then put it on those other sides, then pull who attended from those websites. <45 people, vs bagel breakfast longer, maybe 20 minutes-30 minutes. 
Zoom, same process as ipad checkin, a little less data than ipad, just get zoom name and sometimes their email. Name is self inputted, but same process. 


Challenges:
Different programs to track registration 
NetID  (identifiable- match attendance data) automatically inputted by login , connected to their student ID
Templates (Google folder) 
RSVP (CampusGroup, 12Twenty) First name, last name, email 

12Twenty
-pulls the email for the NETID , connect 

Staff can fill out incomplete data 

AWS cost and credit 
Spend about 20 - 30 mins manually cross checking 

