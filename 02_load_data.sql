-- Load the cleaned task dataset into SQL Server.
-- Replace the file path below with the local location of raw_tasks.csv.

BULK INSERT Tasks
FROM 'C:\path\to\raw_tasks.csv'
WITH (
    FORMAT = 'CSV',
    FIRSTROW = 2,
    FIELDQUOTE = '"',
    ROWTERMINATOR = '0x0a',
    TABLOCK
);