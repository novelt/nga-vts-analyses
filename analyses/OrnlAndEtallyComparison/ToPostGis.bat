SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

SET MASTER_FGDB=D:\work\pop\Comparison\FGDB\tally.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres


"%GDAL_HOME%\ogr2ogr.exe" -progress -f "PostgreSQL" -overwrite PG:"%GDAL_DATABASE_CONNECTION_INFO%"     "%MASTER_FGDB%" --config PG_USE_COPY YES