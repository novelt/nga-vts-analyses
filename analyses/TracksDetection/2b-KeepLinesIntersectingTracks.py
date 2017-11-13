# ------------------------------------------------------------
# Name:    2b-KeepLinesIntersectingTracks.py
# Purpose: Removes the lines that do not intersect a track (with a buffer)
#
# Author:    YM
# Created:   18.02.2015
# Modified:  18.02.2015
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.2.2
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
import os
import sys
import math
from arcpy import env


INTERSETTLEMENT_LINES = arcpy.GetParameterAsText(0)
TRACKS                = arcpy.GetParameterAsText(1)
WORKSPACE             = arcpy.GetParameterAsText(2)

OVERWRITEOUTPUT    = True
LOG_LEVEL          = 3 #0:None / 1=Important / 2: INFO / 3:DEBUG

OSM_DEFAULT_COUNT  = 1000
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
Creates the output FC that will store the lines intersecting tracks
'''
def createIntersectingTracksOutput():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_2b_WeightedTracks", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_2b_WeightedTracks")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "Source", "TEXT")
	arcpy.AddField_management(outFC, "SourceID", "TEXT")
	arcpy.AddField_management(outFC, "ORIG_FID", "SHORT")
	arcpy.AddField_management(outFC, "Intersect_Count", "LONG")
	arcpy.AddField_management(outFC, "Tracks_Count", "LONG")
	arcpy.AddField_management(outFC, "MinSpeed", "FLOAT")
	arcpy.AddField_management(outFC, "MaxSpeed", "FLOAT")
	arcpy.AddField_management(outFC, "AvgSpeed", "FLOAT")
	arcpy.AddField_management(outFC, "Weight", "FLOAT")
	
	
'''
Stores an entrypoint for a given settlement in 'entryPoints' FC
PARAMS:
	- touchingPoint: the entry point
	- bua: the settlement
	- settlementType: the type of settlement
'''
def storeLine(intersectingLine, intersectCount, tracksCount, minSpeed, maxSpeed, avgSpeed):
	#("OID@","Shape@", "TeamID","CampaignDay","CampaignID","TimeStamp", "Source", "SourceID", "ORIG_FID")
	outFC = os.path.join(WORKSPACE,"_2b_WeightedTracks")
	c = arcpy.da.InsertCursor(outFC,("TeamID","CampaignDay","CampaignID","TimeStamp","Source", "SourceID","ORIG_FID", "Intersect_Count", "Tracks_Count","MinSpeed","MaxSpeed","AvgSpeed","Weight", "Shape@")) 
	
	coefIntersect = 2
	coefTrack=3
	weight = (intersectCount*coefIntersect) + (tracksCount*coefTrack) + ((1/(avgSpeed*10))*(tracksCount/coefTrack))
	
	c.insertRow([intersectingLine[2],intersectingLine[3],intersectingLine[4],intersectingLine[5],intersectingLine[6],intersectingLine[7],intersectingLine[8],intersectCount, tracksCount, minSpeed, maxSpeed, avgSpeed, weight, intersectingLine[1]])
	del c
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	createIntersectingTracksOutput()
	
	arcpy.MakeFeatureLayer_management(INTERSETTLEMENT_LINES,"intersettlementLines_lyr", "Source = 'VTS'")
	arcpy.MakeFeatureLayer_management(INTERSETTLEMENT_LINES,"singleline_lyr", "Source = 'VTS'")
	arcpy.MakeFeatureLayer_management(INTERSETTLEMENT_LINES,"osmline_lyr", "Source = 'OSM'")
	arcpy.MakeFeatureLayer_management(TRACKS,"tracks_lyr")
	
	log("Store OSM Lines",1)
	with arcpy.da.SearchCursor("osmline_lyr", ("OID@","Shape@", "TeamID","CampaignDay","CampaignID","TimeStamp", "Source", "SourceID", "ORIG_FID")) as osmCursor:
		for osmLine in osmCursor:
			storeLine(osmLine, OSM_DEFAULT_COUNT, OSM_DEFAULT_COUNT, 1, 1, 1)
	log("---> OK",1)
	
	
	log("Select lines intersecting tracks",1)
	arcpy.SelectLayerByLocation_management(in_layer="intersettlementLines_lyr",overlap_type="INTERSECT",select_features="tracks_lyr",search_distance="5 Meters",selection_type="NEW_SELECTION")
	result = arcpy.GetCount_management("intersettlementLines_lyr")
	count = int(result.getOutput(0))
	log("---> OK ({0} lines selected)".format(count),1)
	
	currentCount = 1
	with arcpy.da.SearchCursor("intersettlementLines_lyr", ("OID@","Shape@", "TeamID","CampaignDay","CampaignID","TimeStamp", "Source", "SourceID", "ORIG_FID")) as intersectCursor:
		for intersectingLine in intersectCursor:
			log("line {0} ({1}/{2})".format(intersectingLine[0],currentCount,count),1)
			
			arcpy.SelectLayerByAttribute_management(in_layer_or_view="singleline_lyr",selection_type="NEW_SELECTION",where_clause="OBJECTID = {0}".format(intersectingLine[0]))
			arcpy.SelectLayerByLocation_management(in_layer="tracks_lyr",overlap_type="INTERSECT",select_features="singleline_lyr",search_distance="5 Meters",selection_type="NEW_SELECTION")
			result2 = arcpy.GetCount_management("tracks_lyr")
			intersectCount = int(result2.getOutput(0))
			log("---> OK ({0} tracks selected)".format(intersectCount),1)
			
			tracksCount=0
			minSpeed = sys.maxint
			maxSpeed = 0
			sumSpeed = 0
			with arcpy.da.SearchCursor("tracks_lyr", ("Speed"),"TeamID = '{0}' AND CampaignDay = {1} AND CampaignID = {2}".format(intersectingLine[2],intersectingLine[3],intersectingLine[4])) as tracksCursor:
				for track in tracksCursor:
					tracksCount=tracksCount+1
					minSpeed = min(minSpeed,track[0])
					maxSpeed = max(maxSpeed,track[0])
					sumSpeed = sumSpeed+track[0]
			
			if(tracksCount>0 and sumSpeed>0 and  maxSpeed>0):
				storeLine(intersectingLine, intersectCount, tracksCount, minSpeed, maxSpeed, sumSpeed/tracksCount)
			currentCount = currentCount+1

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass