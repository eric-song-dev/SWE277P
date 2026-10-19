(Internal) Assignment 3: Business Case
Authors: Brandon Y Lau, Molly Tran, Jennifer Sun, Zhenyu Song
Date: Oct 17, 2026
Executive Summary
Problem/Opportunity

The Graduate & Postdoctoral Scholar Resource Center (GPSRC) staff currently spend significant amounts of time manually copying event attendance data from two distinct platforms (CampusGroups and 12twenty) into a single compiled template. Because the platforms use different columns and identifiers, accurately answering cross-event queries, such as counting the number of students who attended 5 events or more in the past year, is difficult and time consuming.

Organization’s Goal and Strategy

The GPSRC aims to show leadership (such as the Dean and partner schools) how students engage with year round workshops and events, and to identify gaps in program access.

Project’s MOV and how it ties to the organizational goal and strategy

The project’s primary measurable value is that the system’s chatbot must successfully answer a benchmark of 20 sponsor-style queries with at least a 90% correctness rate, alongside successfully merging sample files into a single, unified dataset. Achieving this MOV directly supports the GPSRC's goal of demonstrating student engagement to Graduate Division leadership, partner schools, and the Dean. By replacing disjointed datasets with a reliable, query-able system, staff can quickly uncover gaps in program access and accurately track how unique students navigate different offerings over time. This empowers the organization to make data-driven decisions regarding student outreach and resource allocation, rather than spending valuable staff time manually reconciling spreadsheets.

Each option/alternative analyzed

Alternative 1: Maintain the existing manual data-entry process using student workers
Cons: This process is time-consuming and prone to human error.
Alternative 2: Develop a custom web application with an AI chatbot that operates locally on the users’ computer
Cons: This approach requires development time from the capstone team. Because it runs locally to satisfy privacy constraints, other staff members cannot access it from a central hosting site for data syncing, and the lack of a login system means difficulties in real time collaboration.
Alternative 3: Purchase an existing business analytics and data visualization platform like Power BI to analyze the data
Cons: This introduces high software licensing costs, and the department may be paying for additional features they may not need. In addition, there are also compliance and security concerns due to working with student data. 

Which alternative is being recommended and why

Alternative 2 (Custom web app) is recommended because it fulfills the technical requirements and metrics (90% query accuracy), operates within the strict privacy constraints preventing cloud hosting, and requires zero software licensing costs, aside from low expenses for LLM API usage (like the $100 in ZotGPT test credits) or potentially using a locally hosted model in the future.

Beyond the cost savings, this option is the most practical choice because it eliminates the manual data entry process while protecting student privacy. Since the app runs locally via Docker and only shares the database layout, not the actual student records, with the AI, we can ensure the data stays secure and FERPA compliant. Sticking to the existing process (Alternative 1) is time consuming for student workers, and buying an existing software platform (Alternative 3) introduces expensive licenses and cloud privacy issues. Building the web app ourselves fulfills the department’s requirements without compromising security or budget.
Introduction
Background / Current Situation / Problem / Opportunity

The GPSRC runs workshops and events year round, utilizing both CampusGroups and 12twenty for student registration. After events conclude, GPSRC staff rely on student assistants to manually copy data exports into a compiled template. The primary stakeholder and sponsor, director Kayleigh Anderson-Natale, faces the frustration that cross-event metrics are hard to extract because the two platforms use completely different columns and user identifiers. Consequently, reporting and querying such as identifying how many unique students from a specific school attended last year's Bagel Breakfast becomes a time consuming manual task.

Project’s MOV

The project’s MOV is to create a working web prototype that passes a benchmark test by correctly answering at least 90% of 20 sponsor style questions. Additionally, the system must successfully import and merge the provided sample files into a unified dataset.

How achieving the project’s MOV will support the organization’s goal and strategy

Achieving this MOV directly supports the organization's goal by providing a reliable, query-able database that staff can use to generate CSV reports for the Dean and partner schools. This allows the Graduate Division leadership to accurately track engagement and discover gaps in program access.

Objectives of writing this business case

This document evaluates the feasibility, costs, and benefits of potential solutions to the GPSRC’s data fragmentation problem. It is structured to outline the alternatives, analyze them systematically using a scoring model, and provide a definitive recommendation.
Alternatives
Alternative 1: Existing Manual Process

This changes nothing and continues the existing process without investing in new software solutions. Student workers will continue to manually copy exports into the compiled data template. Registration data reconciliation and cross-platform matching remain a manual task.

Alternative 2: Custom Web App

We will build a new web application that automates the manual work student workers currently do. The system will automatically map the two varying export formats into a standardized data template. It will feature a pluggable LLM provider (like ZotGPT) that allows staff to query the data in plain English.

Alternative 3: Purchase Third-Party Software Licence like Power BI

This option involves purchasing third party software like Power BI. The graduate department will be able to utilize enterprise data pipelines and dashboarding tools to ingest the CSV files, join the datasets, and build visualizations for users to review.
Analysis of Alternatives
Methodology

The alternatives are analyzed based on Total Cost of Ownership (TCO), Total Benefits of Ownership (TBO), Feasibility, and Risk. Following, the alternatives are compared using a quantitative scoring model where higher scores denote better alignment and lower risk.


Alternative 1: Existing Manual Process
TCO: Direct up-front costs are zero. Ongoing indirect costs are very high due to the continuous loss of productivity and staff time spent manually compiling spreadsheets and also the cost to hire student workers.
TBO: There are no new benefits. Customer service and decision-making capabilities remain stagnant.
Feasibility: Organizationally highly feasible since it requires no change. However, it is not scalable if the dataset grows.
Risk: High risk of manual data entry errors. Low risk of privacy breaches since the current workflow is already established.

Alternative 2: Custom Web App
TCO: Development requires a 10 week investment from 4 team members. Ongoing financial costs are minimal, limited to API test credits (estimated at $100 for ZotGPT) and local hosting on the sponsor’s existing computer.
TBO: Improves efficiency by automating the merging of files into a unified dataset. Improves decision making by allowing staff to ask natural language questions and download CSV results.
Feasibility: Highly feasible creating a web app in the 10 week time frame with the requirements. It will meet FERPA privacy requirements because the LLM only generates SQL and never sees actual student data. In addition, since public cloud hosting is out of scope due to privacy concerns, the local Docker deployment makes it even more feasible in the time frame.
Risk: The system may incorrectly merge student records or the AI may return incorrect results. We can mitigate this by prioritizing exact NetID matches and flagging uncertain matches for manual staff review rather than silently merging them.

Alternative 3: Purchase Third-Party Software Licence like Power BI
TCO: High direct ongoing costs due to enterprise software licensing, maintenance, and setup time.
TBO: Offers robust reporting, which improves decision-making. However, it may overcomplicate the simple goal of exporting CSV lists for the Dean.
Feasibility: Economically less feasible because of high software licensing costs that need to be approved by the UCI department. In addition, there will be privacy concerns and vetting needed for the software vendor to handle student data, which will require input from the UCI legal/compliance team.
Risk: Vendor lock-in and potential for violating data privacy requirements if student records are processed on external commercial servers without legal approval.

Comparing Project Alternatives

Scored on a 1-10 scale where higher is better. Risk has a reverse scale where higher scores imply lower risk.

Criterion
Weight
Alt 1: Existing Process
Alt 2: Custom Web App
Alt 3: 3rd Party Software
Financial (TCO / ROI)
20%
4
9
3
Strategic Alignment
20%
2
10
7
Organizational Feasibility
20%
9
8
4
Project / Technical Feasibility
20%
3
9
6
Risk Mitigation
20%
4
8
5
Total Score
100%
4.4
8.8
5.0


Proposed Recommendation and Why

Alternative 2 (Custom Web App) is recommended. It directly aligns with the primary MOV of achieving 90% accuracy on sponsor query benchmarks. This option provides the highest organizational value by automating a tedious manual task while strictly adhering to the mandated privacy and system boundary constraints. Because the application runs locally in a Docker container and filters data before it reaches the external LLM, it guarantees that student information is kept secure and complies with FERPA. Alternative 1 fails to address the underlying data silos, and Alternative 3 introduces unnecessary extra costs and potential privacy risks with third-party cloud hosting. Therefore, custom building the web app is the most valuable and viable path forward.
