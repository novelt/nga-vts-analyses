SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=pop 
SET PGPASSWORD=postgres

SET TABLE_NAME=vts_dim_settlements
"%POSTGRESQL_HOME%\bin\pg_dump.exe" -C -h openvts-stage-nga-gis-eoc --port=5433 -U postgres  --dbname=nigeria_eoc --table="%TABLE_NAME%" | "%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO%

SET TABLE_NAME=vts_campaigns
"%POSTGRESQL_HOME%\bin\pg_dump.exe" -C -h openvts-stage-nga-gis-eoc --port=5433 -U postgres  --dbname=nigeria_eoc --table="%TABLE_NAME%" | "%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO%

SET TABLE_NAME=vts_campaignTargetedAreas
"%POSTGRESQL_HOME%\bin\pg_dump.exe" -C -h openvts-stage-nga-gis-eoc --port=5433 -U postgres  --dbname=nigeria_eoc --table="%TABLE_NAME%" | "%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO%