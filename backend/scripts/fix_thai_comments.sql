-- Run on the database used by the COMPANY backend, in Azure SQL Query Editor
-- or SQL Server Management Studio. This script does not insert test comments.
-- Check the current type first:
SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLLATION_NAME
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'comment_logs' AND COLUMN_NAME = 'comment';

-- The application's default SQL Server schema is dbo. Adjust it if the query
-- above reports another schema. The new backend also applies this on startup.
SET XACT_ABORT ON;
BEGIN TRANSACTION;
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID(N'dbo.comment_logs')
      AND name = N'comment'
      AND TYPE_NAME(system_type_id) IN (N'text', N'varchar')
)
    ALTER TABLE dbo.comment_logs ALTER COLUMN comment NVARCHAR(MAX) NOT NULL;
COMMIT TRANSACTION;

-- Text already saved as ??? has lost its original characters; re-enter it.
