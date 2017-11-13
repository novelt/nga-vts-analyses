# ------------------------------------------------------------
# Name:    0b-ImportOSMLines.py
# Purpose: Import the OSM data into our model
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

OSM_LINES_INPUT   = arcpy.GetParameterAsText(0)
CLEAN_LINES_INPUT = arcpy.GetParameterAsText(1)
WORKSPACE         = arcpy.GetParameterAsText(2)



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
Stores the valid point with the reason
PARAMS: 
	- trackPoint: the invalidPoint to store
	- campaignId: the id of the campaign
'''
def storeLine(teamID, campaignDay, campaignID, timeStamp, source, sourceID, shape):
	c = arcpy.da.InsertCursor("_0b_cleanTracksLinesWithOSM",("TeamID", "CampaignDay", "CampaignID", "TimeStamp", "Source", "SourceID", "SHAPE@")) 
	c.insertRow([teamID,campaignDay,campaignID,timeStamp,source, sourceID, shape])
	del c
	
	
	
'''
Creates the output FC that will store the polylines
'''
def createOutputFC():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_0b_cleanTracksLinesWithOSM", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_0b_cleanTracksLinesWithOSM")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "Source", "TEXT")
	arcpy.AddField_management(outFC, "SourceID", "TEXT")

	
	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	createOutputFC()
	
	log("Copy cleanLines...",1)
	with arcpy.da.SearchCursor(CLEAN_LINES_INPUT, ("OID@", "SHAPE@", "TeamID", "CampaignDay", "CampaignID", "TimeStamp")) as cleanLinesCursor:
		for cleanLine in cleanLinesCursor:
			storeLine(cleanLine[2],cleanLine[3],cleanLine[4],cleanLine[5],"VTS",cleanLine[0],cleanLine[1])
	log("  -> OK...",1)
	
	
	log("Copy OSM Lines...",1)
	with arcpy.da.SearchCursor(OSM_LINES_INPUT, ("OID@", "SHAPE@")) as osmLinesCursor:
		for osmLine in osmLinesCursor:
			storeLine("",0,0,0,"OSM",osmLine[0],osmLine[1])
	log("  -> OK...",1)
	
	
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass