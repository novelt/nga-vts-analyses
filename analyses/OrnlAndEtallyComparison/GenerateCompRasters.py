# ------------------------------------------------------------
# Name:    GenerateRasters.py
# Purpose: This script will take as input rasters containing population; rasters containing population proportions for age groups / gender and create zonal stats for those tables 
#
# Author:    Novel-T 
# Created:   01.10.2015
# Modified:  22.10.2015
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.3.1 
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
import shutil
from arcpy import env
from subprocess import Popen, PIPE, CREATE_NEW_PROCESS_GROUP
#from common import *
from arcpy.sa import *
import os
import glob
import errno

OGR2OGR_LOC = "D:\\OSGeo4W64\\bin\\ogr2ogr.exe"

BASE_DIR = "D:/work/pop/Comparison"
#Copied from population work direcotry, a mosaic / max of all state pop rasters 
COMBINED_POPULATION_RASTER = BASE_DIR + "/Population/populationSourceCombined.tif"
#COMBINED_POPULATION_RASTER_DENSITY = BASE_DIR + "/Population/populationDensity.tif"
UNDER5_RASTER              = BASE_DIR + "/Demographics/AgeUnder5.tif"
UNDER5_RESAMPLED_RASTER    = BASE_DIR + "/Demographics/AgeUnder5_Resample.tif"

UNDER5_POP_RASTER    = BASE_DIR + "/Population/Under5_Population.tif"
UNDER5_POPULATION_DENSITY_RASTER = BASE_DIR + "/Population/Under5_Population_Density.tif"
UNDER5_POPULATION_DENSITY_RESAMPLED_RASTER = BASE_DIR + "/Population/Under5_Population_Density_{0}.tif"
UNDER5_POPULATION_RESAMPLED_WITH_ZERO = BASE_DIR + "/Population/Under5_Population_{0}_WithZero.tif"
UNDER5_POPULATION_RESAMPLED = BASE_DIR + "/Population/Under5_Population_{0}.tif"

UNDER5_POPULATION_FILTERED = BASE_DIR + "/Population/Under5_Population_{0}_filtered_using_etally.tif"

ETALLY_RASTER_WITH_ZEROS = BASE_DIR + "/Population/Etally_Raster_{0}_With_Zeros.tif"
ETALLY_RASTER = BASE_DIR + "/Population/Etally_Raster_{0}.tif"

WORK_FGDB  = """D:\work\pop\Comparison\FGDB\\tally.gdb"""
FGDB_ETALLY = WORK_FGDB.replace('\\', '/') + "/etally_{0}m"
FGDB_POP = WORK_FGDB.replace('\\', '/') + "/pop_{0}m"
FGDB_VTS_TALLY_FACT = WORK_FGDB.replace('\\', '/') + "/vts_tally_fact"

ETALLY_RAW_DATA_NAME = "etally_raw_data"
FGDB_ETALLY_RAW_DATA = WORK_FGDB.replace('\\', '/') + "/" + ETALLY_RAW_DATA_NAME

NEAR_TABLE_NAME = "TallyNearTable"
FGDB_NEAR_TABLE = WORK_FGDB.replace('\\', '/') + "/" + NEAR_TABLE_NAME

NIGERIA_FGDB = r"""D:\git\vts\src\Database\Geometry Data\VTS_NIGERIA.gdb"""


WORK_POSTGIS_GDAL_DATABASE_CONNECTION_INFO="host=localhost port=5434 dbname=pop user=postgres password=postgres"


CLEAN = True
CLEAN = False 

arcpy.env.overwriteOutput = False

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured
            
            
def log(text, loglevel = 4):
    arcpy.AddMessage(text)
    return
    
def Run(cmd):
	log("Execute command: " + cmd)
	p = Popen(cmd, stderr=PIPE, stdout=PIPE, shell=True) #, creationflags=CREATE_NEW_PROCESS_GROUP )
	output, errors = p.communicate()
	if p.returncode or errors:
		raise Exception('Errorlevel = {0} in cmd:{1} \r\nReason:{2}\r\nOutput:{3}'.format(p.returncode,cmd,errors,output))
	else:
		return output
        
def checkIfRasterNeedsToBeCreated(rasterFileName, description):
    if CLEAN:
        silentremove(rasterFileName)
        
    if os.path.isfile(rasterFileName):
        log("Not creating Raster " + description + ": " + rasterFileName, 3)
        return False
    else :
        log("Creating raster " + description + ": " + rasterFileName, 3)
        return True

def raster_to_point(cellSizeM):

    arcpy.env.overwriteOutput=True
    
    under5_filtered = UNDER5_POPULATION_FILTERED.format(cellSizeM)
    etally_raster = ETALLY_RASTER.format(cellSizeM)
    
    fgdb_etally = FGDB_ETALLY.format(cellSizeM)
    fgdb_pop = FGDB_POP.format(cellSizeM)
    
    arcpy.RasterToPoint_conversion(in_raster=etally_raster, out_point_features=fgdb_etally,
    raster_field="Value")
    
   
    
    arcpy.RasterToPoint_conversion(in_raster=under5_filtered, out_point_features=fgdb_pop, raster_field="Value")
    
    arcpy.env.overwriteOutput=False
        
def create_resampled_under5_pop_raster(cellSizeM):

    #Convert meters to degrees using 1 degree = 110.947 km (average of lat / lon values at equator)
    cellSizesInLatLong = cellSizeM / (110.947 * 1000)
    log( "Computed cell size of " + str(cellSizeM) + " meters " + str(cellSizesInLatLong))
    
    resampled_density_raster = UNDER5_POPULATION_DENSITY_RESAMPLED_RASTER.format(cellSizeM)
    
    under5_resampled_raster = UNDER5_POPULATION_RESAMPLED.format(cellSizeM)
    
    arcpy.env.outputCoordinateSystem = COMBINED_POPULATION_RASTER
    arcpy.env.extent = COMBINED_POPULATION_RASTER
    arcpy.env.snapRaster = None 
    arcpy.env.cellSize = None 
    
    #First resample the density raster 
    if checkIfRasterNeedsToBeCreated(resampled_density_raster, "Density raster at " + str(cellSizeM) + "m"):
        arcpy.Resample_management(in_raster=UNDER5_POPULATION_DENSITY_RASTER, out_raster=resampled_density_raster,
            cell_size = cellSizesInLatLong,
            resampling_type="BILINEAR")

    #Then multiply by area to get resampled population 
    if checkIfRasterNeedsToBeCreated(under5_resampled_raster, "Under 5 Population at " + str(cellSizeM) + "m with zero values"):
        refRasterArea = float(cellSizesInLatLong * RASTER_MULT_CONSTANT)*float(cellSizesInLatLong * RASTER_MULT_CONSTANT)
        
        arcpy.gp.Times_sa(resampled_density_raster,str(refRasterArea),under5_resampled_raster) 
    
        
def create_etally_rasters(cellSizeM):
        
    under5_resampled_raster = UNDER5_POPULATION_RESAMPLED.format(cellSizeM)
    
    arcpy.env.outputCoordinateSystem = under5_resampled_raster
    arcpy.env.extent = under5_resampled_raster
    arcpy.env.snapRaster = under5_resampled_raster 
    arcpy.env.cellSize = under5_resampled_raster 
    
    #Compute etally rasters 
    etally_raster_with_zeros = ETALLY_RASTER_WITH_ZEROS.format(cellSizeM)
    etally_raster = ETALLY_RASTER.format(cellSizeM)
    
    if CLEAN:
        silentremove(etally_raster)
    
    if checkIfRasterNeedsToBeCreated(etally_raster_with_zeros, "Etally at " + str(cellSizeM) + "m") :

        arcpy.PointToRaster_conversion(in_features=FGDB_VTS_TALLY_FACT, value_field="totalchildren", out_rasterdataset=etally_raster_with_zeros, cell_assignment="SUM", priority_field="NONE", cellsize=str(cellSizesInLatLong))
        
    if checkIfRasterNeedsToBeCreated(etally_raster, "Setting zero values to NoData " + etally_raster + " for " + str(cellSizeM) + "m."):
        
        arcpy.gp.SetNull_sa(etally_raster_with_zeros, etally_raster_with_zeros,etally_raster, "VALUE = 0")

def filter_under5_pop_using_etally(cellSizeM):
    
    etally_raster = ETALLY_RASTER.format(cellSizeM)
    under5_resampled_raster = UNDER5_POPULATION_RESAMPLED.format(cellSizeM)
    
    under5_filtered = UNDER5_POPULATION_FILTERED.format(cellSizeM)
    
    if checkIfRasterNeedsToBeCreated(under5_filtered, "Filtering population raster using E-Tally for " + str(cellSizeM)):
        #Effectively takes only the under5 raster values which have etally data, otherwise, is NoData 
        arcpy.gp.SetNull_sa(etally_raster, under5_resampled_raster, under5_filtered, "VALUE IS NULL")


def createRasters():

    POP_RASTER_CELL_SIZE = float(arcpy.GetRasterProperties_management(in_raster=COMBINED_POPULATION_RASTER, property_type="CELLSIZEX", band_index="")[0])
    
    #To avoid using decimal numbers too small, this is multiplied by the cell size.  
    RASTER_MULT_CONSTANT = 10000

    if checkIfRasterNeedsToBeCreated(UNDER5_RESAMPLED_RASTER, "Resampling under 5 raster to match population rasters"):
        
        
        
        
        log("Cell size " + str(POP_RASTER_CELL_SIZE))
        
        arcpy.env.outputCoordinateSystem = COMBINED_POPULATION_RASTER
        arcpy.env.extent = COMBINED_POPULATION_RASTER
        arcpy.env.snapRaster = COMBINED_POPULATION_RASTER
        arcpy.env.cellSize = COMBINED_POPULATION_RASTER
            
        # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
        # The following inputs are layers or table views: "AgeUnder5.tif", "populationSourceCombined.tif"
        arcpy.Resample_management(in_raster=UNDER5_RASTER, out_raster=UNDER5_RESAMPLED_RASTER,
            cell_size = POP_RASTER_CELL_SIZE,
            resampling_type="NEAREST")

        '''
    
        '''
        
    if checkIfRasterNeedsToBeCreated(UNDER5_POP_RASTER, "Under 5 Population"):

        arcpy.env.outputCoordinateSystem = COMBINED_POPULATION_RASTER
        arcpy.env.extent = COMBINED_POPULATION_RASTER
        arcpy.env.snapRaster = COMBINED_POPULATION_RASTER
        arcpy.env.cellSize = COMBINED_POPULATION_RASTER

        #refRasterArea = float(POP_RASTER_CELL_SIZE * RASTER_MULT_CONSTANT)*float(POP_RASTER_CELL_SIZE * RASTER_MULT_CONSTANT)

        arcpy.gp.Times_sa(COMBINED_POPULATION_RASTER,UNDER5_RESAMPLED_RASTER,UNDER5_POP_RASTER) 
        log("\t---> OK", 3)
        
    if checkIfRasterNeedsToBeCreated(UNDER5_POPULATION_DENSITY_RASTER, "Under5 Population divided (density)") :
    
        rasterResSq = float(POP_RASTER_CELL_SIZE * RASTER_MULT_CONSTANT)*float(POP_RASTER_CELL_SIZE * RASTER_MULT_CONSTANT)

        arcpy.env.outputCoordinateSystem = COMBINED_POPULATION_RASTER
        arcpy.env.extent = COMBINED_POPULATION_RASTER
        arcpy.env.snapRaster = COMBINED_POPULATION_RASTER
        arcpy.env.cellSize = COMBINED_POPULATION_RASTER
        
        #Divide each cell of population raster, dividing by constant
        arcpy.gp.Divide_sa(UNDER5_POP_RASTER,"{0}".format(rasterResSq*1.0),UNDER5_POPULATION_DENSITY_RASTER)
        
    cellSizesToGenerate = [30, 50, 150]
        
    if os.path.exists(WORK_FGDB) and CLEAN :
        shutil.rmtree(WORK_FGDB)
    
    if not os.path.exists(WORK_FGDB):
        Run(   '  "D:\\OSGeo4W64\\bin\\ogr2ogr.exe" --config FGDB_BULK_LOAD YES -progress -append -f "FileGDB" -gt 66536                     -sql "Select COALESCE(fact.vaccinated::integer, 0) + COALESCE(fact.household_already_vaccinated::integer, 0) + COALESCE(fact.household_away::integer, 0) + COALESCE(fact.household_non_compliant::integer, 0) AS totalchildren, ST_Transform(shape, 4326) as shape, id FROM postgis.vts_tally_fact fact WHERE fact.revisit_type IS NULL AND campaign_id = 65"  "' + WORK_FGDB + '"  PG:"host=openvts-stage-nga-gis-eoc port=5433 dbname=nigeria_eoc user=postgres password=postgres" -nln vts_tally_fact -nlt POINT -a_srs "EPSG:4326"  ' )


    
    
    for cellSizeM in cellSizesToGenerate:
    
        create_resampled_under5_pop_raster(cellSizeM)
        
        create_etally_rasters(cellSizeM)
        
        filter_under5_pop_using_etally(cellSizeM)
        
        raster_to_point(cellSizeM)
     
#Loads Etally data from prod VTS db to work fgdb using projection 4326
def get_etally_data():
     Run(   '  "' + OGR2OGR_LOC + '" --config FGDB_BULK_LOAD YES -progress -append -f "FileGDB" -gt 66536                     -sql "SELECT id, start_date, campaign_id, campaign_day, state_code, state_name, lga_code, lga_name, ward_code, ward_name, ward_day, team_code,        imei, lat, lon, vaccinated, outside_vaccinated, compound_number,        household_number, household_eligible, household_vaccinated, household_already_vaccinated,        household_away, household_non_compliant, household_non_compliant_reason,        household_afp, household_revisit_notes, revisit_type, revisit_count,        gps_utc_date_time, gps_timezone_date_time, phone_date_time, is_compound_first_row,        compound_households_count, is_team_day_first_row, team_day_households_count,        team_day_compounds_count, household_total_population, settlement_name,        ST_Transform(shape, 4326) as shape, ward_day_teams_deployed, vts_tally_form_id, COALESCE(fact.vaccinated::integer, 0) + COALESCE(fact.household_already_vaccinated::integer, 0) + COALESCE(fact.household_away::integer, 0) + COALESCE(fact.household_non_compliant::integer, 0) AS totalchildren FROM postgis.vts_tally_fact fact WHERE fact.revisit_type IS NULL "  "' + WORK_FGDB + '"  PG:"host=openvts-stage-nga-gis-eoc port=5433 dbname=nigeria_eoc user=postgres password=postgres" -nln etally_raw_data -nlt POINT -a_srs "EPSG:4326"  ' )
     
#Generates near table of etally in work fgdb using nigeria fgdb's geometry
def generate_near_table():
    print("Generating near table")
    
    arcpy.GenerateNearTable_analysis(in_features=FGDB_ETALLY_RAW_DATA, near_features=r"'{0}\VTS_GPRefLyrSSABuffers';'{0}\VTS_GPRefLyrBUAGrids';'{0}\VTS_GPRefLyrHABuffers'".format(NIGERIA_FGDB), out_table=FGDB_NEAR_TABLE, search_radius="", location="NO_LOCATION", angle="NO_ANGLE", closest="CLOSEST", closest_count="0", method="PLANAR")

def export_neartable_to_pop_postgis():

    Run(   '  "' + OGR2OGR_LOC + '" -progress -f "PostgreSQL"  -overwrite  PG:"' + WORK_POSTGIS_GDAL_DATABASE_CONNECTION_INFO + '"  --config PG_USE_COPY YES "' + WORK_FGDB + '" ' + NEAR_TABLE_NAME )
    
def export_raw_etally_table():

    #need the objectids 
    Run(   '  "' + OGR2OGR_LOC + '" -progress -f "PostgreSQL" -nln "postgis.etally_raw_data" -overwrite  PG:"' + WORK_POSTGIS_GDAL_DATABASE_CONNECTION_INFO + '"  --config PG_USE_COPY YES "' + WORK_FGDB + '" ' + ETALLY_RAW_DATA_NAME )
    
def main():

    #Have a work postgis database, retaining 4326 projections on the FE / denominator classes 

    # Check out any necessary licenses
    #arcpy.CheckOutExtension("spatial")
     
    #get_etally_data()
    
    #generate_near_table()    
    #export_neartable_to_pop_postgis()
    
    export_raw_etally_table()
    
    
    return

if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass