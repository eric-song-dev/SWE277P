# 智能纪要：Project Demo and Discussion 2026年11月5日

录音时间：2026\-11\-04 15:00 \- 2026\-11\-04 15:39

# 总结

This meeting covers a working AI\-powered student data management system demo, function updates, bug fixes, deployment arrangements, and follow\-up work plans, content as follows:

- **Attendance and Pre\-meeting Arrangement**

    - **Present members**: Core project team members and the client; Rosie joined with camera off due to physical discomfort, Brandon arrived late, Karen could not attend the meeting\.

    - **Recording approval**: The team requested to record the demo for Karen who could not attend, and the client approved the request with no further distribution of the recording\.

- **System Demo and Core Function Introduction**

    - **Basic System Structure**

        - Four core tabs: Chat interaction, new file upload, existing uploaded files management, dataset creation, and system settings\.

        - Supported AI models: Multiple options including Thought GPT, Deep Seek, and Claude, with production environment highly recommended to use Solid GPT for P3 student data privacy protection\.

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=M2JkY2Y4ZWViMWJmMGIxNjhhMjcxODA0ZGRjOWRmYjJfMzViNTdmNWUwZDE1MzAyNmEwN2M0YTMzNjFhMmMxZWVfSUQ6NzcwNDQ2NTcxMDUyNDgxMjMyMV8xNzkzODM2MDk5OjE3OTM5MjI0OTlfVjM)

    - **Core Workflow**

        - Natural language query: Users input natural language questions, the AI automatically generates corresponding SQL to query the dataset and return results\.

        - Feature toggle function: When enabled, the AI can view and summarize query results; when disabled, the AI only displays the SQL query and returns raw dataset results directly\.

    - **Data Export Function**

        - Partial result export: After the AI returns the query response, users can download the corresponding result as Excel or CSV file\.

        - Full dataset export: Users can directly download the complete compiled full dataset from the dedicated entry\.

    - **File Upload Mechanism**

        - Upload process: After uploading event files from 1220 or campus groups, users fill in event details, then commit to add the data to the full compiled dataset\.

        - Duplicate identification: The system can flag and block re\-upload of identical files, but currently has a bug that allows re\-upload of files with minor modifications to be added as new entries\.

    - **Student Record Matching Logic**: The system first matches student records via Net ID, and will use email for matching if the Net ID field is missing\.

- **Deployment and Training Arrangement**

    - **Deployment Preparation**

        - Pre\-requisite: The client needs to install Docker on their Windows computer, and the project team will provide a detailed installation guide in advance\.

        - Target timeline: The deployment and training session is scheduled within the period from November 30th to December 2nd, before the capstone showcase on December 7th\.

    - **Confirmed Meeting Schedule**: 30 p\.m\. on November 30th on campus, and the project team will notify the client via email if any schedule change occurs\.

![Image](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/authcode/?code=ZDNhYjY2ZDdiY2YwZmU3YmY2MDMzMDEwNDUwYjYwZjZfMjkzYjhkZTk4NWU2MTA4MjJmNjlmMjUyMTJjMzVlYzJfSUQ6NzcwNDQ2NTcxNDA4MTQ4Mzc3NF8xNzkzODM2MDk5OjE3OTM5MjI0OTlfVjM)

- **Identified Issues and Follow\-up Backlog**

    - **Existing Bugs to Fix**

        - Missing data flag optimization: The current system cannot clearly display the reason for flagged records, the team will optimize to show specific missing information such as blank Net ID or blank email\.

        - Duplicate upload bug fix: Resolve the issue that files with minor modifications re\-uploaded will be added as duplicate entries to the compiled dataset\.

    - **Pending Function Development**

        - Data editing function: Add the ability to edit event details of uploaded files after submission\.

        - Dataset deletion function: Support complete deletion of the entire dataset and all corresponding associated records\.

        - Staff login function: This feature is planned for Sprint 3, and the team will update the client on its progress later\.

    - **Follow\-up Work Plan**

        - Full manual testing: All team members will test the system thoroughly to discover and fix other potential hidden bugs\.

        - Upload flow optimization: Add a warning pop\-up before users commit uploaded files with missing data, and provide the option to bypass flags for special scenarios\.



# 智能章节

00:00**  Graduation Project AI Website Demo and Discussion**

> The meeting opens with graduation\-related chats, then notes attendee statuses: Karen is absent, unwell Rosie keeps camera off, Brandon arrives late\. The team presents their unfinished working model demo website, introducing its 4 tabs, available AI models, P3 student data protection via recommended Solid GPT, and a feature toggle for AI data summary\. They request and get approval to record the demo for absent Karen, and explain different model setups on each member's device\.
> 
> 

05:37**  Introduction to Data Download, Upload Features and Existing Duplicate Upload Bug**

> This section of the meeting introduces the platform's data export and upload functions: after AI responds to a specific query, users can download the corresponding targeted spreadsheet in Excel or CSV format, and they can also get the complete compiled full dataset file\. When uploading new event files from different sources, users need to fill in event details before committing to add them to the full dataset; the system can flag re\-uploaded identical files as duplicates to avoid repeated addition, but there is an existing bug that files with minor modifications will still be added, which is scheduled to be fixed in the next sprint\.
> 
> 

08:45**  Discussion on missing data detection, sample data status and related data sheet issues**

> This section discusses the data flagging function for missing data and duplicate student records that appear across multiple events\. The team notes the provided sample data was originally embedded with intentional missing entries for realism, but all raw entries have been fully imported into the compiled data sheet, with the total verified as 293 rows that filled all original gaps\. They confirm the flag feature needs further follow\-up verification to confirm it can properly mark missing or duplicate records as expected\.
> 
> 

11:13**  Discussion on On\-site Tool Setup and Staff Training Schedule**

> This discussion confirms the plan to set up the relevant tool on the recipient's Windows computers and train their staff before the December 7 capstone showcase\. The two sides tentatively schedule an on\-campus in\-person meeting at 4:30 p\.m\. on November 30, and the team will make a Docker download guideline in advance\. They note they will email if any schedule change happens, and a Zoom backup on the subsequent Wednesday is also reserved\.
> 
> 

13:22**  System Demo, Student Record Matching Discussion and Project Follow\-up Arrangement**

> This meeting covers checks on the current system: its matching logic prioritizes net ID first, then email, and does not use student ID\. The team is fixing existing bugs, plans to add potential new features including staff login in Sprint 3 if time permits\. They confirm the next meeting will be held on the 18th, two weeks later, and later discuss the 6000 API usage volume and pending submission of the project link\.
> 
> 

19:22**  Discussion on System Flagging Function Issues and Dataset Related Problems**

> This meeting section focuses on the system's flagging function issue\. Speaker 2 notes relevant problems to fix, points out that some data rows that should be marked with flags are not properly processed\. Speaker 4 admits he was unclear about the flag function before and did not test it, and the two sides agree that the missing related information in datasets needs to be supplemented, and the system should allow users to click the flag to view the specific flagged content and the reason for flagging\.
> 
> 

20:26**  Discussion on pending fixes for dataset upload editing and deletion functions**

> This section of the meeting discusses pending issues to add to the team's backlog\. The first identified problem is that users cannot edit any uploaded data sheet after submission, such as correcting wrongly filled pre\-form content like mislabeled event names\. The team also notes that the complete delete flow for data sets is still missing, and the relevant lead data set flagging function also needs proper implementation, both of which will be added to the backlog for subsequent resolution\.
> 
> 

21:44**  Discussion on Missing Data Flagging and Upload Processing Logic**

> This section discusses handling data records with missing information, noting that an uploaded LinkedIn info session dataset with 34 rows had 3 flags, traced to row 8 where both net ID and email were blank making the row unlinkable to a person\. The team agrees missing info records should be flagged for correction, and opts to avoid building a dedicated in\-system editor, letting users manually correct files in Excel before re\-uploading, with the editing function listed as a potential future Sprint 3 feature\.
> 
> 

28:11**  Discussion on Optimizing Dataset Upload Mechanism to Avoid Duplicate Entries and Handle Flag Warnings**

> The team discusses duplicate data entries in compiled sheets caused by re\-uploading modified files\. They evaluate multiple solutions including mapping datasets to specific rows with unique identifiers to enable overwriting, adding pre\-commit pop\-up warnings for flagged issues, allowing users to correct data locally in Excel before re\-upload or bypass flags when needed, and supporting post\-commit data deletion\. They agree to further research the optimal approach for this issue\.
> 
> 

36:23**  Discussion on Software Bug Testing and Follow\-up Meeting Arrangements**

> This meeting section confirms two pending bug\-related items including the file and dataset deletion function, requires all members to manually test the software fully to identify and record more bugs for subsequent fixes\. The team schedules to meet a third party on the 30th to help set up the software, and discusses the possibility of meeting her earlier to collect her usage feedback in advance, and agrees to continue supporting her to fix issues even after graduation\. No other pending topics are raised, then the meeting concludes\.
> 
> 



# 关键决策

- **Key Decision**: Tentatively schedule an in\-person system setup and usage training meeting with the client at 4:30 PM on November 30th, create a Docker download guideline in advance, and notify the client via email if the schedule changes\.

    - **Problem**: The client needs to get the AI data query system set up on their device and learn to use it before the capstone showcase on December 7th, while the student team has limited available time slots\.

    - **Discussion Plan**:

        - Speaker 2 proposed that the team can meet the client either in person on campus on November 30th to December 2nd after 4 PM, or via Zoom on the Wednesday in that window, and will prepare a Docker download guideline beforehand\.

        - Speaker 1 confirmed they can be on campus late on November 30th and suggested an in\-person meeting at 4 PM that day\.

        - Speaker 2 responded that the team can adjust to 4:30 PM on November 30th, and will update the client via email if there are any schedule changes\.

    - **Decision Basis**: The time slot fits both the client's availability and the student team's class arrangement, and the in\-person format is more convenient for on\-site setup guidance\.

---

- **Other Decisions**:

    1. Fix the duplicate upload bug and data flag display logic in the next sprint\.

    2. Add a pre\-commit warning prompt for flagged data during the file upload process\.

    3. Add a data set deletion function to the system\.

    4. Schedule the next client check\-in meeting on December 18th\.

    5. The team will continue manual testing to identify and fix other existing bugs\.



# 金句时刻

「So we think using this solid GPT, we can upload the student record here and privately, because solid GPT will like keep the p 3\.」

—— It clearly states the core security advantage of the recommended AI model for handling sensitive student data, which is a key technical selling point of the system\.



「Yeah, we so our system right now will match the net ID first and if the net ID is missing, we will match the email\.」

—— It explicitly clarifies the core data matching logic of the system, directly responding to the client's key concern about cross\-source student record matching\.



「I mean, it could be our ongoing project after we graduate\.」

—— It provides a clear long\-term support plan for the client, eliminating concerns about subsequent maintenance of the system after the team graduates\.

> （注：部分内容可能由 AI 生成）
