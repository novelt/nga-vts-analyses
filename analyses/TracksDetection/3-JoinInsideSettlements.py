# ------------------------------------------------------------
# Name:    3-JoinInsideSettlements.py
# Purpose: Joins entry points for each settlement to a point inside the settlement
#
# Author:    YM
# Created:   19.02.2015
# Modified:  19.02.2015
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.2.2
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
import os
from arcpy import env

MERGED_SETTLEMENTS = arcpy.GetParameterAsText(0)
OSM_LINES          = arcpy.GetParameterAsText(1)
VTS_CLEAN_LINES    = arcpy.GetParameterAsText(2)
BEST_LINES         = arcpy.GetParameterAsText(3)
MERGED_TRACKS      = arcpy.GetParameterAsText(4)
WORKSPACE          = arcpy.GetParameterAsText(5)

OVERWRITEOUTPUT    = True
LOG_LEVEL          = 2 #0:None / 1=Important / 2: INFO / 3:DEBUG

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
def storeLine(singlePartLine):
	#("OID@","Shape@", "TeamID","CampaignDay","CampaignID","TimeStamp", "Source", "SourceID", "ORIG_FID")
	outFC = os.path.join(WORKSPACE,"_3_JoinedLines")
	c = arcpy.da.InsertCursor(outFC,("TeamID","CampaignDay","CampaignID","TimeStamp","Shape@")) 
	
	c.insertRow([singlePartLine[2],singlePartLine[3],singlePartLine[4],singlePartLine[5], singlePartLine[1]])
	del c
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createJoinedPolylineFC():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_3_JoinedLines", geometry_type,BEST_LINES , "", "", arcpy.SpatialReference(102100))
	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	log("Creating Output FC...",1)
	createJoinedPolylineFC()
	log("\t---> OK",1)
	
	log("Clipping lines...",1)
	clippedFC = os.path.join(WORKSPACE,"_3_ClippedLines")	
	singlePartLineFC = os.path.join(WORKSPACE,"_3_SinglePartClippedLines")
	arcpy.Clip_analysis(in_features=VTS_CLEAN_LINES,clip_features=MERGED_SETTLEMENTS,out_feature_class=clippedFC,cluster_tolerance="#")
	log("\t---> OK",1)
	
	log("Converting to singlePart...",1)
	arcpy.MultipartToSinglepart_management(in_features=clippedFC,out_feature_class=singlePartLineFC)
	log("\t---> OK",1)
	
	arcpy.MakeFeatureLayer_management(singlePartLineFC,"singlepartline_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_TRACKS,"tracks_lyr")
	
	log("Intersecting tracks...",1)
	with arcpy.da.SearchCursor(singlePartLineFC, ("OID@","Shape@", "TeamID","CampaignDay","CampaignID","TimeStamp")) as singlePartCursor:
		for singlePartLine in singlePartCursor:
			arcpy.SelectLayerByAttribute_management(in_layer_or_view="singlepartline_lyr",selection_type="NEW_SELECTION",where_clause="OBJECTID = {0}".format(singlePartLine[0]))
			arcpy.SelectLayerByLocation_management(in_layer="tracks_lyr",overlap_type="INTERSECT",select_features="singlepartline_lyr",search_distance="#",selection_type="NEW_SELECTION")
			result = arcpy.GetCount_management("tracks_lyr")
			intersectCount = int(result.getOutput(0))
			
			tracksCount=0
			with arcpy.da.SearchCursor("tracks_lyr", ("Speed"),"TeamID = '{0}' AND CampaignDay = {1} AND CampaignID = {2}".format(singlePartLine[2],singlePartLine[3],singlePartLine[4])) as tracksCursor:
				for track in tracksCursor:
					tracksCount=tracksCount+1
					
			if(tracksCount>0):
				storeLine(singlePartLine)
	
	log("\t---> OK",1)

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass