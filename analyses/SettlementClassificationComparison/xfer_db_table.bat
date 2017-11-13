SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=pop 
SET PGPASSWORD=4NGAdb00p5!

SET PGDUMP_ARGS= -h 10.1.1.37 --port=5432 -U postgres  --dbname=nigeria_eoc --clean --format=plain

cd %~d0
cd  %~dp0 

SET TABLE_NAME=vts_dim_settlements
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" > vts_tables.sql

SET TABLE_NAME=vts_campaigns
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql

SET TABLE_NAME=vts_campaignTargetedAreas
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql

SET TABLE_NAME=vts_dim_geo_admin
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql

SET TABLE_NAME=postgis.vts_tally_fact
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql


SET TABLE_NAME=postgis.fe_hamletareas
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql


SET TABLE_NAME=postgis.fe_builtUpArea
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql


SET TABLE_NAME=postgis.fe_smlsettlementareas
"%POSTGRESQL_HOME%\bin\pg_dump.exe" %PGDUMP_ARGS% --table="%TABLE_NAME%" >> vts_tables.sql

SET PGPASSWORD=postgres
"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --file=vts_tables.sql