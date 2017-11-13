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
from arcpy import env

LINES_FC        = arcpy.GetParameterAsText(0)
ENTRYPOINTS_FC  = arcpy.GetParameterAsText(1)
CENTROID_FC     = arcpy.GetParameterAsText(2)
WORKSPACE       = arcpy.GetParameterAsText(3)

TEAM_ID_FIELD      = "TeamID"
CAMPAIGN_DAY_FIELD = "CampaignDay"
CAMPAIGN_ID_FIELD  = "CampaignID"
TIMESTAMP_FIELD    = "TimeStamp"
BUA_ID_FIELD       = "SettlementObjectId"


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
For a given entry point, it draws a line to the centroid
PARAMS:
	- entryPoint: the entryPoint to join to the centroid
'''
def processEntryPoint(entryPoint):
	lineId = entryPoint[2]
	settlementObjectId = entryPoint[3]
	entryPointShape = entryPoint[1]
	shapePoint = arcpy.Point()
	shapePoint.X = entryPointShape[0]
	shapePoint.Y = entryPointShape[1]
	
	with arcpy.da.SearchCursor(CENTROID_FC, ("OID@", "SHAPE@XY","SettlementObjectId", "SettlementType"), "SettlementObjectId = '{0}'".format(settlementObjectId)) as centroidsCursor:
		listCentroids = list(centroidsCursor)
		log("\tSelecting centroid for SettlementOID {0}".format(settlementObjectId),3)
		if(len(listCentroids) > 0):
			
			log("\t\t{0} results".format(len(listCentroids)),3)
			centroidPoint = arcpy.Point()
			centroidPoint.X = listCentroids[0][1][0]
			centroidPoint.Y = listCentroids[0][1][1]
	
			arrayOfPoints = arcpy.Array()
			arrayOfPoints.add(shapePoint)
			arrayOfPoints.add(centroidPoint)
			polyline = arcpy.Polyline(arrayOfPoints)
			storePolyline(settlementObjectId,lineId,polyline)
	
	
	
'''
Stores a clean polyline in the result FC
PARAMS:
	- polyline: the shape of the track
'''	
def storePolyline(settlementObjectId,lineId,polyline):
	c = arcpy.da.InsertCursor("centroidPolylines",("SettlementObjectId", "LineId", "SHAPE@")) 
	c.insertRow([settlementObjectId,lineId,polyline])
	del c
	
	
	
'''
PostProcess the results: merge everything into a final FC
'''
def postProcess():
	arcpy.AddField_management(in_table=LINES_FC,field_name="LineId",field_type="LONG",field_precision="#",field_scale="#",field_length="#",field_alias="#",field_is_nullable="NULLABLE",field_is_required="NON_REQUIRED",field_domain="#")
	arcpy.CalculateField_management(in_table=LINES_FC,field="LineId",expression="[OBJECTID]",expression_type="VB",code_block="#")
	mergedFC = os.path.join(WORKSPACE,"mergedLines")
	arcpy.Merge_management(inputs=LINES_FC+";centroidPolylines",output=mergedFC,field_mappings="""TeamID "TeamID" true true false 255 Text 0 0 ,First,#,erasedTrackLines,TeamID,-1,-1;CampaignDay "CampaignDay" true true false 2 Short 0 0 ,First,#,erasedTrackLines,CampaignDay,-1,-1;CampaignID "CampaignID" true true false 2 Short 0 0 ,First,#,erasedTrackLines,CampaignID,-1,-1;TimeStamp "TimeStamp" true true false 8 Date 0 0 ,First,#,erasedTrackLines,TimeStamp,-1,-1;Shape_Length "Shape_Length" false true true 8 Double 0 0 ,First,#,erasedTrackLines,Shape_Length,-1,-1,centroidPolylines,Shape_Length,-1,-1;LineId "LineId" true true false 4 Long 0 0 ,First,#,erasedTrackLines,LineId,-1,-1,centroidPolylines,LineId,-1,-1;SettlementObjectId "SettlementObjectId" true true false 255 Text 0 0 ,First,#,centroidPolylines,SettlementObjectId,-1,-1""")
	finalFC = os.path.join(WORKSPACE,"finalCleanLines")
	arcpy.Dissolve_management(in_features=mergedFC,out_feature_class=finalFC,dissolve_field="LineId",statistics_fields="TeamID FIRST;CampaignDay FIRST;CampaignID FIRST;TimeStamp FIRST",multi_part="MULTI_PART",unsplit_lines="DISSOLVE_LINES")
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createCentroidPolylineFC():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "centroidPolylines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"centroidPolylines")
	arcpy.AddField_management(outFC, "SettlementObjectId", "TEXT")
	arcpy.AddField_management(outFC, "LineId", "Long")
	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	log("Creating Output FCs",1)
	createCentroidPolylineFC()
	log("\t---> OK",1)
	
	
	log("Joining entryPoints to the centroids...",1)
	currentCount=1
	with arcpy.da.SearchCursor(ENTRYPOINTS_FC, ("OID@", "SHAPE@XY", "LineID","SettlementObjectId")) as entryPointsCursor:
		for entryPoint in entryPointsCursor:
			processEntryPoint(entryPoint)
	log("\t---> OK",1)
	
	
	log("Merging everything back together...",1)
	postProcess()
	log("\t---> OK",1)

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass