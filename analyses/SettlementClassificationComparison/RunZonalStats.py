import sys
import arcpy
import shutil
from arcpy import env
from subprocess import Popen, PIPE, CREATE_NEW_PROCESS_GROUP
#from common import *
from arcpy.sa import *
import os
import glob
import errno

try:

    RASTER_DIR = r"D:\git\vts\src\esri\scripts\SettlementClassificationComparison\rasters"
    ZONAL_STATS_FGDB = r"D:\git\vts\src\esri\scripts\SettlementClassificationComparison\zonalStats.gdb"

    WARD_SC_TABLE = ZONAL_STATS_FGDB + r"\fgdb_ward_sc"

    UNDER5_ZONALSTATS = ZONAL_STATS_FGDB +"/ZonalStats_under5_9by9"
    UNDER5_RASTER = RASTER_DIR + r"\under5_int_9by9_mult1e6.tif"

    TOTAL_ZONALSTATS = ZONAL_STATS_FGDB +"/ZonalStats_total_9by9"
    TOTAL_RASTER = RASTER_DIR + r"\total_9by9.tif"

    MAX_GROUP_NUMBER = 9


    #mult under 5 by 1e6 & convert to integer 


    arcpy.CheckOutExtension("spatial")
    
    arcpy.env.overwriteOutput = False

    #arcpy.gp.RasterCalculator_sa("""Int("popu5tot" * 1000000)""", "D:/git/vts/src/esri/scripts/SettlementClassificationComparison/rasters/under5_int.tif")

    #Resample by 10, (so 9m x 9m 

    # cell size / 10 from 0.00083333333, 0.00083333333 to 0000
    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "under5_int.tif"
    #arcpy.Resample_management(in_raster="under5_int.tif", out_raster="D:/git/vts/src/esri/scripts/SettlementClassificationComparison/rasters/under5_int_100.tif", cell_size="0.0000833333328 0.0000833333328", resampling_type="NEAREST")

    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "north_nigeria"
    #arcpy.Resample_management(in_raster="north_nigeria", out_raster="D:/git/vts/src/esri/scripts/SettlementClassificationComparison/rasters/north_nigeria_100.tif", cell_size="0.0000833333328 0.0000833333328", resampling_type="NEAREST")

    # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
    # The following inputs are layers or table views: "fgdb_ward_sc", "under5_int_1by1.tif"

    groups_to_process =  range(0, MAX_GROUP_NUMBER + 1) # 0 to 11 inc
    if len(sys.argv) > 1 and sys.argv[1]:
        groups_to_process = [ int(sys.argv[1]) ]

    for group_num in groups_to_process:

        print("Repairing geometry")
        arcpy.RepairGeometry_management(in_features=WARD_SC_TABLE + "_" + str(group_num), delete_null="DELETE_NULL")

        print("Calculating zonal stats for group " + str(group_num))
        
        arcpy.gp.ZonalStatisticsAsTable_sa(WARD_SC_TABLE + "_" + str(group_num), "wscb_id", UNDER5_RASTER, UNDER5_ZONALSTATS +"_" + str(group_num), "DATA", "SUM")

        arcpy.gp.ZonalStatisticsAsTable_sa(WARD_SC_TABLE + "_" + str(group_num), "wscb_id", TOTAL_RASTER, TOTAL_ZONALSTATS + "_" + str(group_num),  "DATA", "SUM")
except Exception, e :
    print(e)
finally:
    raw_input("Press Enter to continue...")
    
    
# Rasterize the ward settlement zones 

#arcpy.PolygonToRaster_conversion(in_features="fgdb_ward_sc", value_field="OBJECTID", out_rasterdataset="D:/git/vts/src/esri/scripts/SettlementClassificationComparison/rasters/ward_sc_zones.tif", cell_assignment="CELL_CENTER", priority_field="NONE", cellsize="0.000833333328")


# Clip the nigeria pop raster by the zones 

#arcpy.gp.SetNull_sa("ward_sc_zones.tif", "north_nigeria", "D:/git/vts/src/esri/scripts/SettlementClassificationComparison/rasters/total_90by90_clipped.tif", "VALUE IS NULL")


#arcpy.RasterToPoint_conversion(in_raster="total_90by90_clipped.tif", out_point_features="D:/git/vts/src/esri/scripts/SettlementClassificationComparison/scWards.gdb/raster_points", raster_field="Value")
