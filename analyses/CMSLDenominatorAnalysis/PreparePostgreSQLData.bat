SET PSQL="C:\Program Files\PostgreSQL\9.5\bin\psql.exe" -v ON_ERROR_STOP=ON
SET POSTGRESQL_PORT=5434
SET POSTGRESQL_HOST=localhost 

SET POSTGRESQL_PORT=5433
SET POSTGRESQL_HOST=openvts-stage-nga-gis-eoc

SET POSTGRESQL_USERNAME=postgres
rem SET POSTGRESQL_DATABASE=pg_nigeria_master
SET POSTGRESQL_DATABASE=nigeria_eoc
SET PG_PASSWORD=postgres


cd %~d0
cd  %~dp0 

%PSQL%  --host=%POSTGRESQL_HOST% --port=%POSTGRESQL_PORT% --username=postgres --file="PreparePostgreSQLData.sql"  %POSTGRESQL_DATABASE% >out.txt 2>&1

if errorlevel 1 echo ERROR!  Psql.exe did not return success  

if %ERRORLEVEL% GEQ 1 type out.txt

if %ERRORLEVEL% GEQ 1 EXIT /B 1

rem %PSQL%  --host=%POSTGRESQL_HOST% --port=%POSTGRESQL_PORT% --username=postgres --command="select create_temp_vts_fact_settlement_feature_history()"  %POSTGRESQL_DATABASE% 
