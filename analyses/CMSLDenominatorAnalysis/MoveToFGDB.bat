SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

SET MASTER_FGDB=D:\git\vts\src\analyses\CMSLDenominatorAnalysis\data_%1.gdb

SET DATABASE_NAME=nigeria_eoc
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres --dbname=%DATABASE_NAME%
SET POSTGRESQL_CONNECTION_INFO=--host=openvts-stage-nga-gis-eoc --port=5433 --username=postgres --dbname=%DATABASE_NAME%
SET POSTGRESQL_CONNECTION_INFO=--host=10.1.1.37 --port=5432 --username=postgres --dbname=%DATABASE_NAME%

SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=openvts-stage-nga-gis-eoc port=5433 dbname=%DATABASE_NAME% user=postgres password=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=10.1.1.37 port=5432 dbname=%DATABASE_NAME% user=postgres password=4NGAdb00p5!


REM Reset ErrorLevel
VERIFY > nul 

rem "%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "vts_fact_settlement_feature_history" -nlt NONE  -sql "SELECT fh.settlementObjectId || gpRefLyrObjectId AS join_id, date_trunc('month', campaignStartDate)::date AS campaign_month, isCovered AS ""isCovered"", isNewlyCovered AS ""isNewlyCovered"",  nbOfTimesTrackedAsAtRound AS ""To date # of Times Tracked"", nbOfTimesTrackedTotal AS ""Total # of Times Tracked"", num_times_prev_missed_consecutive AS ""# of Times Missed Consecutively"", num_times_prev_missed AS ""To date # of times missed"" FROM temp.vts_fact_settlement_feature_history fh INNER JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = fh.settlementObjectId WHERE ds.statecode = '%1' " 


"%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "vts_fact_settlement_feature_history_with_shape" -nlt POLYGON -a_srs "EPSG:3857"  -sql "SELECT fh.settlementObjectId, fh.gpRefLyrObjectId, d.shape, date_trunc('month', campaignStartDate)::date AS campaign_month, isCovered AS ""isCovered"", isNewlyCovered AS ""isNewlyCovered"",  nbOfTimesTrackedAsAtRound AS ""To date # of Times Tracked"", nbOfTimesTrackedTotal AS ""Total # of Times Tracked"", num_times_prev_missed_consecutive AS ""# of Times Missed Consecutively"", num_times_prev_missed AS ""To date # of times missed"" FROM temp.vts_fact_settlement_feature_history fh INNER JOIN cmsl_analysis.vts_denominators d ON d.settlementObjectId = fh.settlementObjectId AND fh.gpRefLyrObjectId = d.objectid WHERE d.state_code = '%1' " 


if %ERRORLEVEL% GEQ 1 EXIT /B 1

rem "%GDAL_HOME%\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -overwrite -f "FileGDB"   "%MASTER_FGDB%" PG:"%GDAL_DATABASE_CONNECTION_INFO%" -nln "vts_denominators" -nlt POLYGON -a_srs "EPSG:3857"  -sql "(SELECT d.settlementObjectId || objectId as join_id_denom, d.globalid, 'BUA' as settlement_type, shape, d.settlementguid FROM postgis.vts_gpreflyrbuagrids d INNER JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = d.settlementObjectId WHERE ds.statecode = '%1' ) UNION ALL (SELECT d.settlementObjectId || objectId as join_id_denom, d.globalid, 'HA' as settlement_type, shape, d.settlementguid FROM postgis.vts_gpreflyrhabuffers d INNER JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = d.settlementObjectId WHERE ds.statecode = '%1' ) UNION ALL (SELECT d.settlementObjectId || objectId as join_id_denom, d.globalid, 'SSA' as settlement_type, shape, d.settlementguid FROM postgis.vts_gpreflyrssabuffers d INNER JOIN public.vts_dim_settlements ds ON ds.settlementObjectId = d.settlementObjectId WHERE ds.statecode = '%1' ) "





if %ERRORLEVEL% GEQ 1 EXIT /B 1