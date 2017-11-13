@echo off 
REM !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
rem Notes the number of groups can change, alter  MAX_GROUP_NUMBER in this file and in RunZonalStats.py

rem change to drive then directory of this batch file
cd %~d0
cd  %~dp0 

rem -------------------------------------------------------------------------------------------------------
rem Ability to skip steps, in sequential order 
rem -------------------------------------------------------------------------------------------------------

rem CLASSIFICATION_BLOCK_PROCESSING (importing the hand drawn etally borders & settlement classification blocks)
SET SKIP_STEP_1=1   
rem FGDB creation 
SET SKIP_STEP_2=0

rem Export & zonal stats 
SET SKIP_STEP_3=0

rem Import to postgis 
SET SKIP_STEP_4=0

rem Postgis zonal stats processing & csv exprot 
SET SKIP_STEP_5=0


rem -------------------------------------------------------------------------------------------------------
rem Config variables 
rem -------------------------------------------------------------------------------------------------------
SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin
SET ESRI_PYTHON_EXE=c:\Python27\ArcGISx6410.3\python.exe

SET MASTER_FGDB=D:\git\vts\src\esri\scripts\SettlementClassificationComparison\zonalStats.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=%DATABASE_NAME%
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres

SET MAX_GROUP_NUMBER=9


echo -------------------------------------------------------------------------
echo Step 0 Update Stored procedures
echo -------------------------------------------------------------------------
@echo on 


"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --file=Queries.sql  -v ON_ERROR_STOP=1 -X
if %ERRORLEVEL% GEQ 1 EXIT /B 1

@echo off 


IF %SKIP_STEP_1%==1 goto SKIP_STEP_1

echo -------------------------------------------------------------------------
echo Step 1 Process settlement classification blocks & custom etally wards
echo -------------------------------------------------------------------------


rem Import to database
SET BLOCKS_FGDB=D:\git\vts\src\esri\scripts\SettlementClassificationComparison\blocks.gdb

"%GDAL_HOME%\ogr2ogr.exe" -progress -f "PostgreSQL" -overwrite PG:"%GDAL_DATABASE_CONNECTION_INFO%"     "%BLOCKS_FGDB%" --config PG_USE_COPY YES

rem Import etally shape to postgis 

"c:\Program Files\PostgreSQL\9.5\bin\shp2pgsql.exe"  -s 4326 -d "D:\git\vts\src\esri\scripts\SettlementClassificationComparison\eTally Wards\eTallyBoundaries_Jan_2016\eTallyBoundaries_Jan_2016.shp" eTallyBoundaries_Jan_2016 > shape.sql 

rem this shape uses an interesting projection 3395
"c:\Program Files\PostgreSQL\9.5\bin\shp2pgsql.exe"  -s 3395 -d "D:\git\vts\src\esri\scripts\SettlementClassificationComparison\eTally Wards\New_eTally_Ward_Boundaries_July-Dec\eTally_Boundaries_Jul_Sep_Oct.shp" eTally_Boundaries_Jul_Sep_Oct >> shape.sql 

"c:\Program Files\PostgreSQL\9.5\bin\shp2pgsql.exe"  -s 4326 -d "D:\git\vts\src\esri\scripts\SettlementClassificationComparison\eTally Wards\New_eTally_Ward_Boundaries_July-Dec\eTally_Ward_Boundaries_Dec_2015.shp" eTally_Ward_Boundaries_Dec_2015 >> shape.sql

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --file="shape.sql"  %DATABASE_NAME%

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT merge_etally_wards()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT merge_settlement_classification_blocks()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT create_ward_settlement_type_table()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

:SKIP_STEP_1


IF %SKIP_STEP_2%==1 goto SKIP_STEP_2


echo -------------------------------------------------------------------------
echo Step 2 Creating Zonal Stats FGDB
echo -------------------------------------------------------------------------


if EXIST "%MASTER_FGDB%" rd /S /Q "%MASTER_FGDB%" || Echo This failed!

if %ERRORLEVEL% GEQ 1 EXIT /B 1
if EXIST "%MASTER_FGDB%" EXIT /B 1


echo Creating non overlapping groups 

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT split_ws_by_ward_into_non_overlapping()" -v ON_ERROR_STOP=1 -X


echo Importing groups to FGDB

FOR /L %%s IN (0,1,%MAX_GROUP_NUMBER%) DO (
"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "fgdb_ward_sc_%%s" -nlt POLYGON  -a_srs "EPSG:4326" -sql " SELECT  id AS wscb_id, block_objectid, ward_objectid, ward_name, lga_name, state_name, type, handmade_etally_ward, group_num, ST_Transform(shape, 4326) as shape FROM postgis.ward_settlement_classification_blocks_%%s"
)


:SKIP_STEP_2

rem -------------------------------------------------------------------------------------------------------

IF %SKIP_STEP_3%==1 goto SKIP_STEP_3

echo -------------------------------------------------------------------------
echo Step 3 ESRI Zonal Stats
echo -------------------------------------------------------------------------


"%ESRI_PYTHON_EXE%"  "RunZonalStats.py"

if %ERRORLEVEL% GEQ 1 EXIT /B 1

:SKIP_STEP_3


IF %SKIP_STEP_4%==1 goto SKIP_STEP_4
echo -------------------------------------------------------------------------
echo Step 4 Import ZonalStats to Postgis
echo -------------------------------------------------------------------------


echo "Importing result back into pop database"


"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT clean_zonal_stats_tables()" -v ON_ERROR_STOP=1 -X
if %ERRORLEVEL% GEQ 1 EXIT /B 1

FOR /L %%s IN (0,1,%MAX_GROUP_NUMBER%) DO (
echo %%s

"%GDAL_HOME%\ogr2ogr.exe" -progress -f "PostgreSQL" -overwrite PG:"%GDAL_DATABASE_CONNECTION_INFO%"     "%MASTER_FGDB%" -lco SCHEMA=postgis --config PG_USE_COPY YES ZonalStats_total_9by9_%%s ZonalStats_under5_9by9_%%s

if %ERRORLEVEL% GEQ 1 EXIT /B 1
)

:SKIP_STEP_4


IF %SKIP_STEP_5%==1 goto SKIP_STEP_5

echo -------------------------------------------------------------------------
echo Step 5 Postgis final processing & CSV Export
echo -------------------------------------------------------------------------

echo Merge the imported zonal stat tables  

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT merge_zonal_stats_tables('under5')" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT merge_zonal_stats_tables('total')" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

echo Update GIS pop per ward settlement block

echo on

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT create_etally_pop_per_sc()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT update_pop_in_ward_settlement_classification_blocks()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

echo Export to CSV 

"%POSTGRESQL_HOME%\bin\psql.exe" %POSTGRESQL_CONNECTION_INFO% --command="SELECT export_csv()" -v ON_ERROR_STOP=1 -X

if %ERRORLEVEL% GEQ 1 EXIT /B 1

:SKIP_STEP_5
