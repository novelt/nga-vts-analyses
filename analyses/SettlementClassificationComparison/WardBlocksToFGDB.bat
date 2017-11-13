rem change to drive then directory of this batch file
@echo off 

cd %~d0
cd  %~dp0 


rem "c:\Program Files\PostgreSQL\9.5\bin\pgsql2shp.exe" -f "D:\git\vts\src\esri\scripts\SettlementClassificationComparison\scWards.shp" -h localhost -u postgres -p 5434 -P postgres pop "SELECT * FROM postgis.ward_settlement_classification_blocks"


SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

SET MASTER_FGDB=D:\git\vts\src\esri\scripts\SettlementClassificationComparison\scWards.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres

SET SKIP_ETALLY_IMPORT=1


@echo on 

if EXIST "%MASTER_FGDB%" rd /S /Q "%MASTER_FGDB%" || Echo This failed!

if %ERRORLEVEL% GEQ 1 EXIT /B 1
if EXIST "%MASTER_FGDB%" EXIT /B 1



rem md "%MASTER_FGDB%"
rem "%GDAL_HOME%\ogr2ogr.exe" -progress -f "PostgreSQL" -overwrite PG:"%GDAL_DATABASE_CONNECTION_INFO%"     "%MASTER_FGDB%" --config PG_USE_COPY YES
rem "Select * from public.test1"

rem use query to make id a normal integer column to not mess up the zonal stats


"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "ward_settlement_classification_blocks" -nlt POLYGON  -a_srs "EPSG:4326" -sql " SELECT  id AS wscb_id,  ST_Transform(shape, 4326) as shape, block_objectid, ward_objectid, polygon_number, ward_name,       lga_name, state_name, type, handmade_etally_ward, under5_pop,        total_pop, group_num,  ward_source FROM postgis.ward_settlement_classification_blocks"

rem "%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "fgdb_ward_sc_3857" -nlt POLYGON  -a_srs "EPSG:3857" -sql " SELECT  id AS wscb_id,  shape, block_objectid, ward_objectid, polygon_number, ward_name,       lga_name, state_name, type, handmade_etally_ward, under5_pop,        total_pop, group_num, inside_eligible, total_eligible FROM postgis.ward_settlement_classification_blocks"

rem Import eTally 
IF %SKIP_ETALLY_IMPORT%==1 GOTO after_etally

"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "vts_tally_fact" -nlt POINT  -a_srs "EPSG:3857" -sql "select * from postgis.vts_tally_fact"

:after_etally


