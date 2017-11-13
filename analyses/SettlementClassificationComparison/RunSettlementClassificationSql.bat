SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=pop 


cd %~d0
cd  %~dp0 

REM Note assumes xfer_db_table has been run on the pop db, need to have up to date settlement FE layers from VTS and have run the zonal stats (to have imported the blocks (raw not clipped by ward, see merge_settlement_classification_blocks which merges the raw data from blocks.gdb).

SET PGPASSWORD=postgres
SET PGCLIENTENCODING=UTF8
"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --file=Queries.sql  -v ON_ERROR_STOP=1 -X

rem "%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT create_single_settlement_table()"  -v ON_ERROR_STOP=1 -X

rem "%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT classify_settlements()"  -v ON_ERROR_STOP=1 -X

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT export_vts_settlement_classification_csv()"  -v ON_ERROR_STOP=1 -X
