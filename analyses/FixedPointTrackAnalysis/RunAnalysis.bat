SET OBR_LIB_DIR=D:\git\obr
SET GDM_LIB_DIR=D:\git\nga-gis-vts-gdb\VTS.GeoDataManagementAutomation
SET PYTHONPATH=%OBR_LIB_DIR%;%GDM_LIB_DIR%
SET PYHOME=C:\Python27\ArcGISx6410.3
SET GDAL_DATA=C:\OSGeo4W64\share\gdal
SET Path=%PYHOME%;C:\WINDOWS\system32;


%~d0
cd %~dp0

python RunAnalysis.py %1 %2