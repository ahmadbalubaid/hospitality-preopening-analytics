SELECT MAX(Snapshot_Date) AS Latest_Snapshot_Date
FROM TaskSnapshots;

SELECT
    Status,
    COUNT(*) AS Task_Count
FROM TaskSnapshots
WHERE Snapshot_Date = '2027-02-22'
GROUP BY Status;

SELECT
    ROUND(AVG(Progress_Percentage), 2) AS Overall_Readiness_Percentage
FROM TaskSnapshots
WHERE Snapshot_Date = '2027-02-22';

SELECT
    Risk_Level,
    COUNT(*) AS Task_Count
FROM TaskSnapshots
WHERE Snapshot_Date = '2027-02-22'
GROUP BY Risk_Level
ORDER BY Task_Count DESC;

SELECT
    t.Task_ID,
    t.Task_Name,
    t.Department_ID,
    s.Status,
    s.Progress_Percentage,
    s.Delay_Days,
    s.Risk_Level
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND s.Risk_Level IN ('High', 'Critical')
ORDER BY s.Delay_Days DESC;

SELECT
    t.Task_ID,
    t.Task_Name,
    t.Department_ID,
    t.Critical_Path_Flag,
    s.Status,
    s.Progress_Percentage,
    s.Delay_Days,
    s.Risk_Level,
    s.Open_Issues
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND s.Risk_Level IN ('High', 'Critical')
    AND s.Status NOT IN ('Completed', 'Cancelled')
ORDER BY
    CASE
        WHEN s.Risk_Level = 'Critical' THEN 1
        WHEN s.Risk_Level = 'High' THEN 2
    END,
    s.Delay_Days DESC;

    SELECT
    d.Department_Name,
    COUNT(*) AS Open_High_Critical_Tasks,
    SUM(CASE WHEN s.Risk_Level = 'Critical' THEN 1 ELSE 0 END) AS Critical_Tasks,
    ROUND(AVG(s.Progress_Percentage), 2) AS Avg_Progress,
    ROUND(AVG(CAST(s.Delay_Days AS DECIMAL(10,2))), 2) AS Avg_Delay_Days,
    SUM(s.Open_Issues) AS Total_Open_Issues
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND s.Risk_Level IN ('High', 'Critical')
    AND s.Status NOT IN ('Completed', 'Cancelled')
GROUP BY d.Department_Name
ORDER BY Open_High_Critical_Tasks DESC;

SELECT
    t.Task_ID,
    t.Task_Name,
    d.Department_Name,
    s.Status,
    s.Progress_Percentage,
    s.Delay_Days,
    s.Risk_Level,
    s.Open_Issues
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND t.Critical_Path_Flag = 1
    AND s.Status NOT IN ('Completed', 'Cancelled')
ORDER BY
    s.Delay_Days DESC;

    SELECT
    s.Status,
    COUNT(*) AS Critical_Path_Tasks
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND t.Critical_Path_Flag = 1
GROUP BY s.Status
ORDER BY Critical_Path_Tasks DESC;

SELECT
    ROUND(AVG(s.Progress_Percentage), 2) AS Critical_Path_Readiness
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND t.Critical_Path_Flag = 1;

    SELECT
    d.Department_Name,
    COUNT(*) AS Total_Tasks,
    ROUND(AVG(s.Progress_Percentage), 2) AS Readiness_Percentage
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
WHERE s.Snapshot_Date = '2027-02-22'
GROUP BY d.Department_Name
ORDER BY Readiness_Percentage ASC;

SELECT
    d.Department_Name,
    ROUND(AVG(s.Progress_Percentage), 2) AS Readiness_Percentage
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
WHERE s.Snapshot_Date = '2027-02-22'
GROUP BY d.Department_Name
HAVING AVG(s.Progress_Percentage) < 95
ORDER BY Readiness_Percentage ASC;

SELECT
    d.Department_Name,
    COUNT(*) AS Delayed_Tasks,
    ROUND(AVG(s.Delay_Days), 2) AS Avg_Delay_Days,
    MAX(s.Delay_Days) AS Max_Delay_Days
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND s.Delay_Days > 0
    AND s.Status NOT IN ('Completed', 'Cancelled')
GROUP BY d.Department_Name
ORDER BY Delayed_Tasks DESC;

SELECT
    Delay_Reason,
    COUNT(*) AS Delayed_Tasks,
    ROUND(AVG(CAST(Delay_Days AS DECIMAL(10,2))), 2) AS Avg_Delay_Days,
    MAX(Delay_Days) AS Max_Delay_Days
FROM TaskSnapshots
WHERE Snapshot_Date = '2027-02-22'
    AND Delay_Days > 0
    AND Status NOT IN ('Completed', 'Cancelled')
GROUP BY Delay_Reason
ORDER BY Delayed_Tasks DESC;

SELECT
    COUNT(*) AS Vendor_Tasks,
    SUM(
        CASE 
            WHEN s.Delay_Days > 0 
                 AND s.Status NOT IN ('Completed', 'Cancelled')
            THEN 1 
            ELSE 0 
        END
    ) AS Open_Delayed_Vendor_Tasks
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND t.Vendor_ID IS NOT NULL;

    SELECT
    v.Vendor_Name,
    v.Vendor_Category,
    COUNT(*) AS Vendor_Tasks,
    SUM(
        CASE
            WHEN s.Delay_Days > 0
                 AND s.Status NOT IN ('Completed', 'Cancelled')
            THEN 1
            ELSE 0
        END
    ) AS Open_Delayed_Tasks,
    ROUND(
        AVG(
            CASE
                WHEN s.Delay_Days > 0
                     AND s.Status NOT IN ('Completed', 'Cancelled')
                THEN CAST(s.Delay_Days AS DECIMAL(10,2))
            END
        ),
        2
    ) AS Avg_Open_Delay_Days
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Vendors v
    ON t.Vendor_ID = v.Vendor_ID
WHERE s.Snapshot_Date = '2027-02-22'
GROUP BY
    v.Vendor_Name,
    v.Vendor_Category
HAVING SUM(
    CASE
        WHEN s.Delay_Days > 0
             AND s.Status NOT IN ('Completed', 'Cancelled')
        THEN 1
        ELSE 0
    END
) > 0
ORDER BY
    Open_Delayed_Tasks DESC,
    Avg_Open_Delay_Days DESC;

    SELECT
    Delay_Reason,
    COUNT(*) AS Vendor_Linked_Delayed_Tasks
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE s.Snapshot_Date = '2027-02-22'
    AND t.Vendor_ID IS NOT NULL
    AND s.Delay_Days > 0
    AND s.Status NOT IN ('Completed', 'Cancelled')
GROUP BY Delay_Reason
ORDER BY Vendor_Linked_Delayed_Tasks DESC;

SELECT
    ROUND(SUM(t.Planned_Cost), 2) AS Total_Planned_Cost,
    ROUND(SUM(s.Actual_Cost), 2) AS Total_Actual_Cost
FROM Tasks t
JOIN TaskSnapshots s
    ON t.Task_ID = s.Task_ID
WHERE s.Snapshot_Date = '2027-02-22';

SELECT
    ROUND(SUM(t.Planned_Cost), 2) AS Total_Planned_Cost,
    ROUND(SUM(s.Actual_Cost), 2) AS Total_Actual_Cost,

    ROUND(
        SUM(s.Actual_Cost) - SUM(t.Planned_Cost),
        2
    ) AS Budget_Variance,

    ROUND(
        (
            (SUM(s.Actual_Cost) - SUM(t.Planned_Cost))
            / NULLIF(SUM(t.Planned_Cost), 0)
        ) * 100,
        2
    ) AS Budget_Variance_Percentage

FROM Tasks t
JOIN TaskSnapshots s
    ON t.Task_ID = s.Task_ID

WHERE s.Snapshot_Date = '2027-02-22';

SELECT
    d.Department_Name,

    ROUND(SUM(t.Planned_Cost), 2) AS Planned_Cost,

    ROUND(SUM(s.Actual_Cost), 2) AS Actual_Cost,

    ROUND(
        SUM(s.Actual_Cost) - SUM(t.Planned_Cost),
        2
    ) AS Cost_Variance,

    ROUND(
        (
            (SUM(s.Actual_Cost) - SUM(t.Planned_Cost))
            / NULLIF(SUM(t.Planned_Cost), 0)
        ) * 100,
        2
    ) AS Variance_Percentage

FROM TaskSnapshots s

JOIN Tasks t
    ON s.Task_ID = t.Task_ID

JOIN Departments d
    ON t.Department_ID = d.Department_ID

WHERE s.Snapshot_Date = '2027-02-22'

GROUP BY d.Department_Name

ORDER BY Cost_Variance DESC;


SELECT
    Snapshot_Date,
    ROUND(AVG(Progress_Percentage), 2) AS Overall_Readiness
FROM TaskSnapshots
GROUP BY Snapshot_Date
ORDER BY Snapshot_Date;

SELECT
    s.Snapshot_Date,
    d.Department_Name,
    ROUND(AVG(s.Progress_Percentage), 2) AS Department_Readiness
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
JOIN Departments d
    ON t.Department_ID = d.Department_ID
GROUP BY
    s.Snapshot_Date,
    d.Department_Name
ORDER BY
    s.Snapshot_Date,
    d.Department_Name;

    SELECT
    s.Snapshot_Date,
    ROUND(AVG(s.Progress_Percentage), 2) AS Critical_Path_Readiness
FROM TaskSnapshots s
JOIN Tasks t
    ON s.Task_ID = t.Task_ID
WHERE t.Critical_Path_Flag = 1
GROUP BY s.Snapshot_Date
ORDER BY s.Snapshot_Date;