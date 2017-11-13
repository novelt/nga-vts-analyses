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


LINES  = arcpy.GetParameterAsText(0)
NEAR        = arcpy.GetParameterAsText(1)
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
	c = arcpy.da.InsertCursor("simplifiedLines",("SHAPE@")) 
	c.insertRow([line[1]])
	del c
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createLineTouch():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "simplifiedLines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"simplifiedLines")
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	createLineTouch()
	
	log("Joining entryPoints to the centroids...",1)
	currentCount=1
	arcpy.MakeTableView_management(NEAR,"near_vw")
	arcpy.MakeFeatureLayer_management(LINES, "lines_lyr")
	processed = []
	with arcpy.da.SearchCursor(LINES, ("OID@")) as linesCursor:
		for line in linesCursor:
		
			if(line[0] in processed):
				log("already processed",3)
			else:
				arcpy.SelectLayerByAttribute_management("near_vw", "NEW_SELECTION", "IN_FID = {0} and NEAR_DIST=0 ".format(line[0]))
				with arcpy.da.SearchCursor("near_vw", ("NEAR_FID")) as linesCursor2:
					nearFeatures = list(linesCursor2)
				
				log("near for line {0}: {1}".format(line[0],nearFeatures),3)
				
				if(len(nearFeatures) == 2):
					nearFid1 = nearFeatures[0][0]
					nearFid2 = nearFeatures[1][0]
					
					arcpy.SelectLayerByAttribute_management("near_vw", "NEW_SELECTION", "NEAR_FID ={0} or NEAR_FID={1} and NEAR_DIST=0 ".format(nearFid1,nearFid2))
					with arcpy.da.SearchCursor("near_vw", ("IN_FID")) as linesNearCursor:
						list2 = list(linesNearCursor)
						for lineNear in list2:
							if(list2.count(lineNear)==2):
								log("line {0} = line {1}".format(line[0],lineNear[0]),3)
								arcpy.SelectLayerByAttribute_management("lines_lyr", "NEW_SELECTION", "OBJECTID ={0}".format(lineNear[0]))
								with arcpy.da.SearchCursor("lines_lyr", ("OID@", "SHAPE@", "Shape_Length")) as linesNearCursor2:
									sortedTrackPoints =  sorted(linesNearCursor2, key=lambda l: l[2])
								
								for sortedLine in sortedTrackPoints:
									processed.append(sortedLine[0])
								middle = sortedTrackPoints[int(math.floor(len(sortedTrackPoints)/2))]
								storeLine(middle)
				
	log("\t---> OK",1)
	

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass