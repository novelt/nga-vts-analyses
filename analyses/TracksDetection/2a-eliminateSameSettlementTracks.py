# ------------------------------------------------------------
# Name:    2-JoinLines.py
# Purpose: Starts from a multipart polyline FC (where intersection with settlements have been erased). It joins the entry points for the settlements to the centroid.
#
# Author:    YM
# Created:   10.02.2015
# Modified:  11.02.2015
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.2.2
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
import os
import math
from arcpy import env


MERGED_POLY     = arcpy.GetParameterAsText(0)
MULTIPART_LINES = arcpy.GetParameterAsText(1)
WORKSPACE       = arcpy.GetParameterAsText(2)

TEAM_ID_FIELD      = "TeamID"
CAMPAIGN_DAY_FIELD = "CampaignDay"
CAMPAIGN_ID_FIELD  = "CampaignID"
TIMESTAMP_FIELD    = "TimeStamp"
BUA_ID_FIELD       = "SettlementObjectId"


OVERWRITEOUTPUT    = True
LOG_LEVEL          = 3 #0:None / 1=Important / 2: INFO / 3:DEBUG

arcpy.env.overwriteOutput = OVERWRITEOUTPUT
env.workspace = WORKSPACE

	

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
Stores an entrypoint for a given settlement in 'entryPoints' FC
PARAMS:
	- touchingPoint: the entry point
	- bua: the settlement
	- settlementType: the type of settlement
'''
def storeLine(line):
	#("OID@","TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID", "ORIG_FID", "Shape@")
	outFC = os.path.join(WORKSPACE,"_2a_InterSettlementLines")
	c = arcpy.da.InsertCursor(outFC,("TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID", "ORIG_FID", "Shape@")) 
	c.insertRow([line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8]])
	del c
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createEliminatedTracksOutput():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_2a_InterSettlementLines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_2a_InterSettlementLines")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "Source", "TEXT")
	arcpy.AddField_management(outFC, "SourceID", "TEXT")
	arcpy.AddField_management(outFC, "ORIG_FID", "SHORT")
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	createEliminatedTracksOutput()
	
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"workingSettlements_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"settlement1_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"settlement2_lyr")
	arcpy.MakeFeatureLayer_management(MULTIPART_LINES,"multipartlines_lyr")
	
	
	log("Select settlements in working extent",1)
	arcpy.SelectLayerByLocation_management(in_layer="workingSettlements_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="multipartlines_lyr",search_distance="#",selection_type="NEW_SELECTION")
	result = arcpy.GetCount_management("workingSettlements_lyr")
	count = int(result.getOutput(0))
	log("---> OK ({0} settlements selected)".format(count),1)
	
	currentCount = 1
	processed = []
	with arcpy.da.SearchCursor("workingSettlements_lyr", ("OID@","SettlementObjectId")) as settlementCursor:
		for settlement in settlementCursor:
			log("Settlement {0} ({1}/{2})".format(settlement[0],currentCount,count),1)
			poly1Id = settlement[1]
			
			processed.append(str(settlement[0]))
			
			arcpy.SelectLayerByAttribute_management("settlement1_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",settlement[0]))
			arcpy.SelectLayerByLocation_management(in_layer="multipartlines_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="settlement1_lyr",search_distance="#",selection_type="NEW_SELECTION")
					
			with arcpy.da.SearchCursor("workingSettlements_lyr", ("OID@","SettlementObjectId"), "OBJECTID not in ({0})".format(','.join(processed))) as otherSettlementCursor:
				for otherSettlement in otherSettlementCursor:
					poly2Id = otherSettlement[1]
					
					arcpy.MakeFeatureLayer_management("multipartlines_lyr","multipartlines2_lyr")
					arcpy.SelectLayerByAttribute_management("settlement2_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",otherSettlement[0]))
					arcpy.SelectLayerByLocation_management(in_layer="multipartlines2_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="settlement2_lyr",search_distance="#",selection_type="NEW_SELECTION")
					
					with arcpy.da.SearchCursor("multipartlines2_lyr", ("OID@","TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID", "ORIG_FID", "Shape@")) as selectedLinesCursor:
						for selectedLine in selectedLinesCursor:
							storeLine(selectedLine)
			currentCount = currentCount+1

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass