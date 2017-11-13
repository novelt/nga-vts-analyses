# ------------------------------------------------------------
# Name:    0-GetPopOutsideSettlements.py
# Purpose: This script will generate a raster showing where population is detected outside the settlements
#
# Author:    Novel-T / YMI
# Created:   18.03.2015
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.2.2
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
from arcpy import env
from arcpy.sa import *
import os


NG_WORKSPACE         = arcpy.GetParameterAsText(0)
OUT_GDB              = arcpy.GetParameterAsText(1)
RASTER_POP           = arcpy.GetParameterAsText(2)

BUA_THRESHOLD = 150
SSA_THRESHOLD = 100
HA_THRESHOLD = 100

CELL_BUFFER   = "45 Meters"

FCL_STATES                = "Boundary_VaccStates"
FCL_LGAS                  = "Boundary_VaccLGAs"
FCL_WARDS                 = "Boundary_VaccWards"
FCL_FE_BUILTUPAREA        = "FE_BuiltUpArea"
FCL_FE_HAMLETAREAS        = "FE_HamletAreas"
FCL_FE_HAMLET             = "FE_Hamlet"
FCL_HABUFFERS             = "VTS_GPRefLyrHABuffers"
FCL_FE_SMLSETTLEMENTAREAS = "FE_SmlSettlementAreas"
FE_NONRESIDENTIALAREA     = "FE_NonResidentialArea"

EMPTYBUA_TABLENAME        = "EmptyBUAs"
EMPTYSSA_TABLENAME        = "EmptySSAs"
EMPTYHA_TABLENAME         = "EmptyHAs"
EMPTYHAMLET_TABLENAME     = "EmptyHamlets"
POPOUTSIDE_TABLENAME      = "PopOutside"
POPOUTSIDE_TABLE          = os.path.join(OUT_GDB,POPOUTSIDE_TABLENAME)
BUAPOPBELOW_TABLENAME     = "BUAPopBelowThreshold"
BUAPOPBELOW_TABLE         = os.path.join(OUT_GDB,BUAPOPBELOW_TABLENAME)
SSAPOPBELOW_TABLENAME     = "SSAPopBelowThreshold"
SSAPOPBELOW_TABLE         = os.path.join(OUT_GDB,SSAPOPBELOW_TABLENAME)
HAPOPBELOW_TABLENAME      = "HAPopBelowThreshold"
HAPOPBELOW_TABLE          = os.path.join(OUT_GDB,HAPOPBELOW_TABLENAME)


HAMLETS_BUFFERED          = os.path.join("in_memory","hamletsBuffer")
BUA_ZONAL_TBL             = os.path.join(OUT_GDB,"ZonalStats_BUA")
SSA_ZONAL_TBL             = os.path.join(OUT_GDB,"ZonalStats_SSA")
HA_ZONAL_TBL              = os.path.join(OUT_GDB,"ZonalStats_HA")
HAMLET_ZONAL_TBL          = os.path.join(OUT_GDB,"ZonalStats_Hamlet")
	
RASTERTOPOLY_FC           = os.path.join(OUT_GDB,"rasterToPoly")
	
OVERWRITEOUTPUT           = True
LOG_LEVEL                 = 3 #0:None / 1=Important / 2: INFO / 3:DEBUG

arcpy.env.overwriteOutput = OVERWRITEOUTPUT

# ------------------------------------------------------------
# ------------------------------------------------------------
# Function definitions
# ------------------------------------------------------------
# ------------------------------------------------------------
'''
Adds message to the result window
'''
def log(text, loglevel):
	if(LOG_LEVEL >= loglevel):
		arcpy.AddMessage(text)
	return

	

'''
Creates the needed output tables
'''  
def createOutputs():
	emptyBuaFC = os.path.join(OUT_GDB,EMPTYBUA_TABLENAME)
	arcpy.CreateFeatureclass_management(OUT_GDB, EMPTYBUA_TABLENAME, "POLYGON",os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA),"DISABLED", "DISABLED", os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA) )
	arcpy.DeleteField_management(emptyBuaFC, ["SettlementID", "Source", "TimeStamp", "GlobalID", "SettlementNameCalc","Weight"])
	
	emptySsaFC = os.path.join(OUT_GDB,EMPTYSSA_TABLENAME)
	arcpy.CreateFeatureclass_management(OUT_GDB, EMPTYSSA_TABLENAME, "POLYGON",os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS),"DISABLED", "DISABLED", os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS) )
	arcpy.DeleteField_management(emptySsaFC, ["SettlementID", "Source", "TimeStamp", "GlobalID", "SettlementNameCalc","Weight"])
		
	emptyHaFC = os.path.join(OUT_GDB,EMPTYHA_TABLENAME)
	arcpy.CreateFeatureclass_management(OUT_GDB, EMPTYHA_TABLENAME, "POLYGON",os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS),"DISABLED", "DISABLED", os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS) )
	arcpy.DeleteField_management(emptyHaFC, ["SettlementID", "Source", "TimeStamp", "GlobalID", "SettlementNameCalc","Weight"])
		
	emptyHamletFC = os.path.join(OUT_GDB,EMPTYHAMLET_TABLENAME)
	arcpy.CreateFeatureclass_management(OUT_GDB, EMPTYHAMLET_TABLENAME, "POLYGON",os.path.join(NG_WORKSPACE,FCL_HABUFFERS),"DISABLED", "DISABLED", os.path.join(NG_WORKSPACE,FCL_HABUFFERS) )
	arcpy.DeleteField_management(emptyHamletFC, ["SettlementID", "SettlementName","SettlementGUID", "GlobalID"])
		
		
		
'''
Returns the cells from the population Raster where population value >0 and is outside settlements
'''
def getPopulationOutsideSettlements():
	arcpy.Copy_management(RASTERTOPOLY_FC, POPOUTSIDE_TABLE)
	rasterToPolyLayer = POPOUTSIDE_TABLENAME+"_lyr"
	arcpy.MakeFeatureLayer_management(POPOUTSIDE_TABLE, rasterToPolyLayer)
	
	arcpy.SelectLayerByAttribute_management(in_layer_or_view=rasterToPolyLayer,selection_type="NEW_SELECTION",where_clause="grid_code=0")
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="INTERSECT",select_features=os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA),search_distance="#",selection_type="ADD_TO_SELECTION")
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="INTERSECT",select_features=os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS),search_distance="#",selection_type="ADD_TO_SELECTION")
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="INTERSECT",select_features=os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS),search_distance="#",selection_type="ADD_TO_SELECTION")

	nbRows = 0
	with arcpy.da.UpdateCursor(rasterToPolyLayer,["OID@"]) as deleteCursor:
		for row in deleteCursor:
			deleteCursor.deleteRow()
			nbRows = nbRows + 1
	log("\t{0} rows deleted".format(nbRows),3)
	
	
	
'''
Returns the population below a given threshold inside the settlements
'''
def getPopulationBelowThreshold():
	arcpy.CreateFeatureclass_management(OUT_GDB, BUAPOPBELOW_TABLENAME, "POINT",RASTERTOPOLY_FC,"DISABLED", "DISABLED", RASTERTOPOLY_FC )
	arcpy.CreateFeatureclass_management(OUT_GDB, SSAPOPBELOW_TABLENAME, "POINT",RASTERTOPOLY_FC,"DISABLED", "DISABLED", RASTERTOPOLY_FC )
	arcpy.CreateFeatureclass_management(OUT_GDB, HAPOPBELOW_TABLENAME, "POINT",RASTERTOPOLY_FC,"DISABLED", "DISABLED", RASTERTOPOLY_FC )
	
	rasterToPolyLayer = "rasterToPoly_lyr"
	arcpy.MakeFeatureLayer_management(RASTERTOPOLY_FC, rasterToPolyLayer)
	
	#BUA Threshold
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA),search_distance=CELL_BUFFER,selection_type="NEW_SELECTION")
	arcpy.SelectLayerByAttribute_management(in_layer_or_view=rasterToPolyLayer,selection_type="SUBSET_SELECTION",where_clause="grid_code<={0}".format(BUA_THRESHOLD))
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FE_NONRESIDENTIALAREA),search_distance=CELL_BUFFER,selection_type="REMOVE_FROM_SELECTION")
	arcpy.CopyFeatures_management(rasterToPolyLayer, BUAPOPBELOW_TABLE)
	
	#SSA Threshold
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS),search_distance=CELL_BUFFER,selection_type="NEW_SELECTION")
	arcpy.SelectLayerByAttribute_management(in_layer_or_view=rasterToPolyLayer,selection_type="SUBSET_SELECTION",where_clause="grid_code<={0}".format(SSA_THRESHOLD))
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FE_NONRESIDENTIALAREA),search_distance=CELL_BUFFER,selection_type="REMOVE_FROM_SELECTION")
	arcpy.CopyFeatures_management(rasterToPolyLayer, SSAPOPBELOW_TABLE)
	
	#HA Threshold
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS),search_distance=CELL_BUFFER,selection_type="NEW_SELECTION")
	arcpy.SelectLayerByAttribute_management(in_layer_or_view=rasterToPolyLayer,selection_type="SUBSET_SELECTION",where_clause="grid_code<={0}".format(HA_THRESHOLD))
	arcpy.SelectLayerByLocation_management(in_layer=rasterToPolyLayer,overlap_type="HAVE_THEIR_CENTER_IN",select_features=os.path.join(NG_WORKSPACE,FE_NONRESIDENTIALAREA),search_distance=CELL_BUFFER,selection_type="REMOVE_FROM_SELECTION")
	arcpy.CopyFeatures_management(rasterToPolyLayer, HAPOPBELOW_TABLE)

	
	
'''
Returns the settlements with no population inside
'''	
def getSettlementsEmpty():

	#BUAs
	BUA_FC = os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA)
	BUA_lyr = "BUA_lyr"
	arcpy.MakeFeatureLayer_management(BUA_FC, BUA_lyr)
	BUAToStore = []
	with arcpy.da.SearchCursor(BUA_ZONAL_TBL, ["OBJECTID_1"], "SUM <= 0") as emptyBUAs:
		for BUA in emptyBUAs:
			with arcpy.da.SearchCursor(BUA_lyr, ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"], "OBJECTID = {0}".format(BUA[0])) as matchingBUAs:
				for matchingBUA in matchingBUAs:
					BUAToStore.append(matchingBUA)
	
	cursor = arcpy.da.InsertCursor(os.path.join(OUT_GDB,EMPTYBUA_TABLENAME), ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"])
	
	for bua in BUAToStore:
		cursor.insertRow(bua)
	del cursor
	
	#SSAs
	SSA_FC = os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS)
	SSA_lyr = "SSA_lyr"
	arcpy.MakeFeatureLayer_management(SSA_FC, SSA_lyr)
	SSAToStore = []
	with arcpy.da.SearchCursor(SSA_ZONAL_TBL, ["OBJECTID_1"], "SUM <= 0") as emptySSAs:
		for SSA in emptySSAs:
			with arcpy.da.SearchCursor(SSA_lyr, ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"], "OBJECTID = {0}".format(SSA[0])) as matchingSSAs:
				for matchingSSA in matchingSSAs:
					SSAToStore.append(matchingSSA)
	
	cursor = arcpy.da.InsertCursor(os.path.join(OUT_GDB,EMPTYSSA_TABLENAME), ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"])
	
	for ssa in SSAToStore:
		cursor.insertRow(ssa)
	del cursor
	
	#HAs
	HA_FC = os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS)
	HA_lyr = "HA_lyr"
	arcpy.MakeFeatureLayer_management(HA_FC, HA_lyr)
	HAToStore = []
	with arcpy.da.SearchCursor(HA_ZONAL_TBL, ["OBJECTID_1"], "SUM <= 0") as emptyHAs:
		for HA in emptyHAs:
			with arcpy.da.SearchCursor(HA_lyr, ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"], "OBJECTID = {0}".format(HA[0])) as matchingHAs:
				for matchingHA in matchingHAs:
					HAToStore.append(matchingHA)
	
	cursor = arcpy.da.InsertCursor(os.path.join(OUT_GDB,EMPTYHA_TABLENAME), ["SHAPE@", "SettlementName","WardCode", "SettlementObjectID", "NbDenominator"])
	
	for ha in HAToStore:
		cursor.insertRow(ha)
	del cursor
	
	
	#Hamlets
	Hamlets_lyr = "Hamlets_lyr"
	arcpy.MakeFeatureLayer_management(os.path.join(NG_WORKSPACE,FCL_HABUFFERS), Hamlets_lyr)
	HamletsToStore = []
	with arcpy.da.SearchCursor(HAMLET_ZONAL_TBL, ["OBJECTID_1"], "SUM <= 0") as emptyHamlets:
		for hamlet in emptyHamlets:
			with arcpy.da.SearchCursor(Hamlets_lyr, ["SHAPE@", "SettlementNameCalc","WardCode", "SettlementObjectID"], "OBJECTID = {0}".format(hamlet[0])) as matchingHamlets:
				for matchingHamlet in matchingHamlets:
					HamletsToStore.append(matchingHamlet)
	
	cursor = arcpy.da.InsertCursor(os.path.join(OUT_GDB,EMPTYHAMLET_TABLENAME), ["SHAPE@", "SettlementNameCalc","WardCode", "SettlementObjectID"])
	
	for hamlet in HamletsToStore:
		cursor.insertRow(hamlet)
	del cursor
		
		

'''
Generate the Zonal statistics tables
'''		
def generateZonalStats():

	BUA_FC = os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA)
	BUA_lyr = "BUA_lyr"
	arcpy.MakeFeatureLayer_management(BUA_FC, BUA_lyr)
	ZonalStatisticsAsTable(BUA_lyr, "OBJECTID", RASTER_POP, BUA_ZONAL_TBL, "DATA", "SUM")

	SSA_FC = os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS)
	SSA_lyr = "SSA_lyr"
	arcpy.MakeFeatureLayer_management(SSA_FC, SSA_lyr)
	ZonalStatisticsAsTable(SSA_lyr, "OBJECTID", RASTER_POP, SSA_ZONAL_TBL, "DATA", "SUM")

	HA_FC = os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS)
	HA_lyr = "HA_lyr"
	arcpy.MakeFeatureLayer_management(HA_FC, HA_lyr)
	ZonalStatisticsAsTable(HA_lyr, "OBJECTID", RASTER_POP, HA_ZONAL_TBL, "DATA", "SUM")

	Hamlets_lyr = "Hamlets_lyr"
	arcpy.MakeFeatureLayer_management(HAMLETS_BUFFERED, Hamlets_lyr)
	arcpy.env.outputCoordinateSystem = RASTER_POP
	arcpy.env.extent = RASTER_POP
	arcpy.env.snapRaster = RASTER_POP
	arcpy.env.cellSize = RASTER_POP
	ZonalStatisticsAsTable(Hamlets_lyr, "OBJECTID", RASTER_POP, HAMLET_ZONAL_TBL, "DATA", "SUM")
	
	
	
def bufferHamlets():
	hamlets_fc = os.path.join(NG_WORKSPACE,FCL_HABUFFERS)
	arcpy.Buffer_analysis(in_features=hamlets_fc,out_feature_class=HAMLETS_BUFFERED,buffer_distance_or_field="20 Meters",line_side="FULL",line_end_type="ROUND",dissolve_option="NONE",dissolve_field="#")
	
	
	
'''
Copy the boundaries to the output GDB
'''		
def copyBoundaries():
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_STATES), OUT_GDB+"\\"+FCL_STATES)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_LGAS), OUT_GDB+"\\"+FCL_LGAS)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_WARDS), OUT_GDB+"\\"+FCL_WARDS)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_FE_BUILTUPAREA), OUT_GDB+"\\"+FCL_FE_BUILTUPAREA)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_FE_HAMLETAREAS), OUT_GDB+"\\"+FCL_FE_HAMLETAREAS)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS), OUT_GDB+"\\"+FCL_FE_SMLSETTLEMENTAREAS)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_FE_SMLSETTLEMENTAREAS), OUT_GDB+"\\"+FCL_FE_SMLSETTLEMENTAREAS)
	arcpy.CopyFeatures_management(os.path.join(NG_WORKSPACE,FCL_HABUFFERS), OUT_GDB+"\\"+FCL_HABUFFERS)
	
	

# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	createOutputs()
	
	log("Buffering Hamlets...",1)
	bufferHamlets()
	log("---> OK",1)
	
	log("Generating Zonal statistics...",1)
	generateZonalStats()
	log("---> OK",1)
	
	log("Converting Raster to Points...",1)
	#arcpy.RasterToPolygon_conversion(in_raster=RASTER_POP,out_polygon_features=RASTERTOPOLY_FC,simplify="NO_SIMPLIFY",raster_field="VALUE")
	arcpy.RasterToPoint_conversion(in_raster=RASTER_POP,out_point_features=RASTERTOPOLY_FC,raster_field="VALUE")
	log("---> OK",1)
	
	log("Getting population outside the settlements...",1)
	getPopulationOutsideSettlements()
	log("---> OK",1)
	
	#log("Getting population below threshold...",1)
	#getPopulationBelowThreshold()
	#log("---> OK",1)
	
	log("Getting settlements with 0 population...",1)
	getSettlementsEmpty()
	log("---> OK",1)
	
	log("Copying Boundaries...",1)
	copyBoundaries()
	log("---> OK",1)
	
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass