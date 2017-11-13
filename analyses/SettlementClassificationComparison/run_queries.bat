SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=pop 


cd %~d0
cd  %~dp0 


SET PGPASSWORD=postgres
SET PGCLIENTENCODING=UTF8
"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --file=Queries.sql  -v ON_ERROR_STOP=1 -X


"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT clean_zonal_stats_tables()"  -v ON_ERROR_STOP=1 -X
