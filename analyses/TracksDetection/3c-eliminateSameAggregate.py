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


MERGED_AGGREGATES = arcpy.GetParameterAsText(0)
SINGLEPART_LINES  = arcpy.GetParameterAsText(1)
WORKSPACE         = arcpy.GetParameterAsText(2)

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
	outFC = os.path.join(WORKSPACE,"_3c_InterAggregatesLines")
	c = arcpy.da.InsertCursor(outFC,("TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID", "ORIG_FID", "Shape@")) 
	c.insertRow([line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8]])
	del c
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createEliminatedTracksOutput():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_3c_InterAggregatesLines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_3c_InterAggregatesLines")
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
	
	arcpy.MakeFeatureLayer_management(MERGED_AGGREGATES,"workingAggregates_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_AGGREGATES,"aggregate1_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_AGGREGATES,"aggregate2_lyr")
	arcpy.MakeFeatureLayer_management(SINGLEPART_LINES,"singlepartlines_lyr")
	
	
	log("Select aggregates in working extent",1)
	arcpy.SelectLayerByLocation_management(in_layer="workingAggregates_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="singlepartlines_lyr",search_distance="5 Meters",selection_type="NEW_SELECTION")
	result = arcpy.GetCount_management("workingAggregates_lyr")
	count = int(result.getOutput(0))
	log("---> OK ({0} aggregates selected)".format(count),1)
	
	currentCount = 1
	processed = []
	with arcpy.da.SearchCursor("workingAggregates_lyr", ("OID@")) as aggregatesCursor:
		for aggregate in aggregatesCursor:
			log("Aggregate {0} ({1}/{2})".format(aggregate[0],currentCount,count),1)
			
			processed.append(str(aggregate[0]))
			
			arcpy.SelectLayerByAttribute_management("aggregate1_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",aggregate[0]))
			arcpy.SelectLayerByLocation_management(in_layer="singlepartlines_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="aggregate1_lyr",search_distance="5 Meters",selection_type="NEW_SELECTION")
					
			with arcpy.da.SearchCursor("workingAggregates_lyr", ("OID@"), "OBJECTID not in ({0})".format(','.join(processed))) as otherAggregateCursor:
				for otherAggregate in otherAggregateCursor:
					
					arcpy.MakeFeatureLayer_management("singlepartlines_lyr","singlepartlines2_lyr")
					arcpy.SelectLayerByAttribute_management("aggregate2_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",otherAggregate[0]))
					arcpy.SelectLayerByLocation_management(in_layer="singlepartlines2_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="aggregate2_lyr",search_distance="5 Meters",selection_type="NEW_SELECTION")
					
					with arcpy.da.SearchCursor("singlepartlines2_lyr", ("OID@","TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID", "ORIG_FID", "Shape@")) as selectedLinesCursor:
						for selectedLine in selectedLinesCursor:
							storeLine(selectedLine)
			currentCount = currentCount+1

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass