USE HotelPreOpeningAnalytics;

CREATE TABLE Vendors (
    Vendor_ID VARCHAR(20) PRIMARY KEY,
    Vendor_Name VARCHAR(100) NOT NULL,
    Vendor_Category VARCHAR(100) NOT NULL
);

CREATE TABLE Tasks (
    Task_ID VARCHAR(20) PRIMARY KEY,
    Task_Name VARCHAR(200) NOT NULL,
    Department_ID VARCHAR(10) NOT NULL,
    Workstream VARCHAR(150) NOT NULL,
    Owner VARCHAR(150) NOT NULL,
    Vendor_ID VARCHAR(20) NULL,
    Priority VARCHAR(20) NOT NULL,
    Critical_Path_Flag BIT NOT NULL,
    Planned_Start_Date DATE NOT NULL,
    Planned_End_Date DATE NOT NULL,
    Planned_Cost DECIMAL(18,2) NOT NULL,

    FOREIGN KEY (Department_ID) REFERENCES Departments(Department_ID),
    FOREIGN KEY (Vendor_ID) REFERENCES Vendors(Vendor_ID)
);

CREATE TABLE TaskSnapshots (
    Task_ID VARCHAR(20) NOT NULL,
    Snapshot_Date DATE NOT NULL,
    Status VARCHAR(30) NOT NULL,
    Progress_Percentage DECIMAL(5,2) NOT NULL,
    Blocked_Flag BIT NOT NULL,
    Delay_Days INT NOT NULL,
    Forecast_End_Date DATE NOT NULL,
    Delay_Reason VARCHAR(150) NULL,
    Risk_Level VARCHAR(20) NOT NULL,
    Open_Issues INT NOT NULL,
    Actual_End_Date DATE NULL,
    Actual_Cost DECIMAL(18,2) NOT NULL,

    PRIMARY KEY (Task_ID, Snapshot_Date),
    FOREIGN KEY (Task_ID) REFERENCES Tasks(Task_ID)
);