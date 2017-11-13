import sys
import arcpy
import shutil
from arcpy import env
from subprocess import Popen, PIPE, CREATE_NEW_PROCESS_GROUP
from common import *
from arcpy.sa import *
import os
import glob
import errno

###########################################################
# Creates a raster from the eTally table (which contains eTally of latest campaign for each ward)
###########################################################
def build_etally_raster():
	print("Processing eTally raster")
	
	arcpy.env.overwriteOutput = False
		
	arcpy.env.outputCoordinateSystem = NIGERIA_TOTAL_POP_RASTER		
	arcpy.env.snapRaster = NIGERIA_TOTAL_POP_RASTER
	arcpy.env.cellSize = NIGERIA_TOTAL_POP_RASTER
	
	if needs_to_be_created(ETALLY_RASTER):
		arcpy.PointToRaster_conversion(in_features=ETALLY_TABLE, value_field="household_eligible", out_rasterdataset=ETALLY_RASTER, cell_assignment="SUM", priority_field="NONE", cellsize="0.000833333328")
	
	#Set 0 fields to NoData
	if needs_to_be_created(ETALLY_RASTER_NODATA):
		arcpy.gp.SetNull_sa(ETALLY_RASTER, ETALLY_RASTER, ETALLY_RASTER_NODATA, "VALUE = 0")
	
	
	arcpy.env.overwriteOutput = True
	
	#Creates a point for display in MXD
	arcpy.RasterToPoint_conversion(in_raster=ETALLY_RASTER_NODATA, out_point_features=ETALLY_POP_TABLE, raster_field="Value")
	
	arcpy.env.overwriteOutput = False

def clip_nigeria_raster():
	print("Clipping Nigeria Population Raster to ETally (both VTS / provided)\n")
	
	if needs_to_be_created(NIGERIA_TOTAL_POP_CLIPPED_RASTER) :
		arcpy.Clip_management(in_raster=NIGERIA_TOTAL_POP_RASTER, out_raster=NIGERIA_TOTAL_POP_CLIPPED_RASTER, in_template_dataset=ETALLY_WARD_MULTI_TABLE, nodata_value="-32768", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")
	
def raster_to_point(raster_start, raster_clip, raster_filtered, table_name):
	
	if needs_to_be_created(raster_clip) :
		arcpy.Clip_management(in_raster=raster_start, out_raster=raster_clip, in_template_dataset=ETALLY_WARD_MULTI_TABLE, nodata_value="-32768", clipping_geometry="ClippingGeometry", maintain_clipping_extent="NO_MAINTAIN_EXTENT")
	
	if needs_to_be_created(raster_filtered) :
		arcpy.gp.SetNull_sa(raster_clip, raster_clip, raster_filtered, "VALUE <= 0")
	
	arcpy.env.overwriteOutput = True
	
	arcpy.RasterToPoint_conversion(in_raster=raster_filtered, out_point_features=table_name, raster_field="Value")
	
	arcpy.env.overwriteOutput = False

def call_raster_to_point():
	
	print("Create raster table for under5 population")
	raster_to_point(NIGERIA_UNDER5_POP_RASTER, NIGERIA_UNDER5_POP_CLIPPED_RASTER, NIGERIA_UNDER5_POP_FILTERED_RASTER, UNDER5_POP_TABLE)
	
	
	
def etally_with_no_pop ():

	print("\nCreate raster for etally pop without GIS pop\n")
	#arcpy.gp.RasterCalculator_sa("Con( \"" + ETALLY_RASTER_NODATA + "\" > 0, Con( IsNull(\""     + NIGERIA_TOTAL_POP_CLIPPED_RASTER + "\"), 1, \"" + NIGERIA_TOTAL_POP_CLIPPED_RASTER + "\" <= 0 ), -32768 )", ETALLY_WITH_NO_POP)
	arcpy.env.nodata = "MINIMUM"
	
	rasterEtally = Raster(ETALLY_RASTER_NODATA)
	rasterPop = Raster(NIGERIA_TOTAL_POP_CLIPPED_RASTER)
	
	no_data_val = -1
	
	if needs_to_be_created(ETALLY_WITH_NO_POP):
		#Do we have Etally population?
		rasterEtallyWithNoPop = Con(
			(rasterEtally > 0) & ( IsNull(rasterPop) | (rasterPop <= 0 ) ), 
			rasterEtally,
			no_data_val )
			
	
	
		rasterEtallyWithNoPop.save(ETALLY_WITH_NO_POP)
	
	arcpy.env.nodata = "PROMOTION"
	
	if needs_to_be_created(ETALLY_WITH_NO_POP_NODATA):
			
		arcpy.gp.SetNull_sa(ETALLY_WITH_NO_POP, ETALLY_WITH_NO_POP, ETALLY_WITH_NO_POP_NODATA, "VALUE <= 0")

def pop_with_no_etally():    
	
	print("Create raster for GIS pop without eTally\n")
	
	
	rasterEtally = Raster(ETALLY_RASTER_NODATA)
	rasterPop = Raster(NIGERIA_TOTAL_POP_CLIPPED_RASTER)
	
	arcpy.env.nodata = "MINIMUM"
	
	if needs_to_be_created(POP_WITH_NO_ETALLY) :
		rasterPopWithNoEtally = Con( rasterPop > 0, Con( IsNull(rasterEtally), rasterPop, rasterEtally <= 0), -1 )
	
		rasterPopWithNoEtally.save(POP_WITH_NO_ETALLY)
	
	if needs_to_be_created(POP_WITH_NO_ETALLY_NODATA):
		arcpy.gp.SetNull_sa(POP_WITH_NO_ETALLY, POP_WITH_NO_ETALLY, POP_WITH_NO_ETALLY_NODATA, "VALUE <= 0")

	
try:
	
	arcpy.CheckOutExtension("spatial")
	
	build_etally_raster()    
	
	
	clip_nigeria_raster()
	
	call_raster_to_point()
	
	etally_with_no_pop()
	
	pop_with_no_etally()
except Exception, e :
	print(e)
	#raw_input("Press Enter to continue...")
#finally:
	
	