# Hospitality Pre-Opening Analytics

A Power BI and SQL analytics project built to track the readiness of a hotel during its pre-opening phase.

The main idea was to create a reporting solution that could help management see how close the property is to opening, which departments are falling behind, where the main operational risks are, and how vendors and costs are performing.

## About the Data

I couldn't use real hotel operational data for a public portfolio project, so I created the dataset myself.

Using Python and Pandas, I generated synthetic pre-opening data covering typical activities across departments such as IT, Engineering, Housekeeping, Front Office, F&B, HR, Finance, Security, Procurement, and Sales & Marketing.

The final dataset includes:

- 333 pre-opening tasks
- 10 departments
- 36 vendors
- 3,996 weekly task snapshots

Each weekly snapshot tracks information such as task status, risk level, delays, open issues, planned cost, actual cost, and vendor involvement.

After generating the data, I cleaned and validated it in Python before loading it into SQL Server.

## How I Built It

I used SQL Server to store and analyze the data before connecting it to Power BI.

The SQL work included JOINs, CTEs, CASE statements, aggregations, and window functions to explore task progress, delays, departmental performance, vendor performance, and cost data.

In Power BI, I created the data model and DAX measures needed for the main KPIs and built the report around three areas.

### Executive Overview

The first page gives an overall view of opening readiness.

It tracks:

- Overall readiness
- Delayed and blocked tasks
- High-risk tasks
- Critical open issues
- Readiness by department
- Readiness over time

### Action Center

This page focuses on tasks that need management attention.

Instead of only showing summary numbers, it provides task-level information including the department, current status, risk level, delay days, delay reason, open issues, and latest snapshot date.

### Vendor & Cost Performance

The final page looks at the financial and vendor side of the pre-opening process.

It compares planned and actual costs, calculates cost variance, and shows which vendors are associated with the highest number of delayed tasks.

## Tools Used

**Python / Pandas**  
Data generation, cleaning, transformation, and validation.

**SQL Server**  
Data storage and analysis using JOINs, CTEs, CASE statements, aggregations, and window functions.

**Power BI / DAX**  
Data modeling, KPI calculations, interactive analysis, and dashboard development.

## Data Model

The Power BI model is built around five main tables:

- Departments
- Tasks
- Task Snapshots
- Vendors
- Date

This allows the report to analyze task performance across departments, vendors, dates, risk levels, status, and cost.

## Dashboard

Dashboard screenshots will be added here.

## Note

This is an independent portfolio project. All data shown in the project is synthetic and was generated specifically for this analysis.

No confidential or operational data from my employer or any real hotel property is included.

## Author

**Ahmed Balubaid**  
Data Analyst | IT Specialist

[LinkedIn](https://www.linkedin.com/in/ahmedbalubaid) | [Portfolio](https://ahmadbalubaid.github.io/)
