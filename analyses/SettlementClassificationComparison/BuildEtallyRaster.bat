@echo off 

rem change to drive then directory of this batch file
cd %~d0
cd  %~dp0 

SET SKIP_FGDB_CREATION=1
SET SKIP_POSTGIS_MASK=1
SET SKIP_RASTER_CREATION=0


SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

SET MASTER_FGDB=D:\git\vts\src\esri\scripts\SettlementClassificationComparison\etallyRaster.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=%DATABASE_NAME%
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres

IF %SKIP_FGDB_CREATION%==1 goto after_fgdb_creation

REM Take only etally points with latest campaign for a given ward 
"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "vts_tally_fact" -nlt POINT  -a_srs "EPSG:4326" -sql "WITH tally_wards AS ( select DISTINCT ON (f.ward_code) c.campaignId AS campaign_id, f.ward_code from postgis.vts_tally_fact f INNER JOIN public.vts_campaigns c ON c.campaignid = f.campaign_id ORDER BY f.ward_code, c.startDate DESC ) select id, ST_Transform(shape, 4326), household_eligible from postgis.vts_tally_fact f INNER JOIN tally_wards tw ON f.campaign_id = tw.campaign_id AND f.ward_code = tw.ward_code "

"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "settlement_classification_blocks" -nlt POLYGON  -a_srs "EPSG:4326" -sql "select id, ST_Transform(shape, 4326), objectid, component_number, state_code, landuse, type FROM postgis.settlement_classification_blocks"

"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "z_blocks_with_etally" -nlt POLYGON  -a_srs "EPSG:4326" -sql "select DISTINCT wsc.id, wsc.state_name, wsc.lga_name, wsc.ward_name, wsc.type, ST_Transform(shape, 4326) from postgis.ward_settlement_classification_blocks wsc LEFT JOIN postgis.ward_settlement_classification_blocks_etally_pop ep ON ep.ward_settlement_classification_blocks_id = wsc.id WHERE type = 'Z' and inside_eligible > 0"


:after_fgdb_creation

IF %SKIP_POSTGIS_MASK%==1 goto SKIP_POSTGIS_MASK

echo Creating mask of all etally wards

"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "etally_ward_multi" -nlt MULTIPOLYGON  -a_srs "EPSG:4326" -sql "select ST_Transform(ST_Multi(ST_Union(shape)), 4326) from postgis.ward_settlement_classification_blocks"

:SKIP_POSTGIS_MASK

IF %SKIP_RASTER_CREATION%==1 goto SKIP_RASTER_CREATION

c:\Python27\ArcGISx6410.3\python.exe "BuildEtallyRaster.py" %1

:SKIP_RASTER_CREATION
