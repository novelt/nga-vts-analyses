SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

rem This database should be the one used to calculate the pop, so it should have the geometry + the zonal stats 
SET MASTER_FGDB=D:\work\pop\VTS_NIGERIA.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres


"%GDAL_HOME%\ogr2ogr.exe" -progress -f "PostgreSQL" -overwrite PG:"%GDAL_DATABASE_CONNECTION_INFO%"     "%MASTER_FGDB%" --config PG_USE_COPY YES