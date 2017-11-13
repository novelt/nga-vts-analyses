# ------------------------------------------------------------
# Name:    1-IntersectSettlements
# Purpose: Given a polylinesFC, it removes the intersection between the lines and every single settlement.
# It also store in a separate FC the entrypoints for each settlement and the centroids
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
from datetime import datetime
import time
from arcpy import env

WORKSPACE    = arcpy.GetParameterAsText(0)
BUA_FC       = arcpy.GetParameterAsText(1)
SSA_FC       = arcpy.GetParameterAsText(2)
HA_FC        = arcpy.GetParameterAsText(3)
LINES_FC     = arcpy.GetParameterAsText(4)


TEAM_ID_FIELD      = "TeamID"
CAMPAIGN_DAY_FIELD = "CampaignDay"
CAMPAIGN_ID_FIELD  = "CampaignID"
TIMESTAMP_FIELD    = "TimeStamp"
BUA_ID_FIELD       = "SettlementObjectId"
SSA_ID_FIELD       = "SettlementObjectId"
HA_ID_FIELD        = "SettlementObjectId"


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
Merge BUAs, SSAs and HAs in a single FC
'''
def mergeSettlements():
	arcpy.MakeFeatureLayer_management(BUA_FC,"bua_lyr")
	arcpy.MakeFeatureLayer_management(SSA_FC,"ssa_lyr")
	arcpy.MakeFeatureLayer_management(HA_FC,"ha_lyr")
	arcpy.MakeFeatureLayer_management(LINES_FC,"lines_lyr")
	
	arcpy.SelectLayerByLocation_management(in_layer="bua_lyr",overlap_type="INTERSECT",select_features="lines_lyr",search_distance="#",selection_type="NEW_SELECTION")
	arcpy.SelectLayerByLocation_management(in_layer="ssa_lyr",overlap_type="INTERSECT",select_features="lines_lyr",search_distance="#",selection_type="NEW_SELECTION")
	arcpy.SelectLayerByLocation_management(in_layer="ha_lyr",overlap_type="INTERSECT",select_features="lines_lyr",search_distance="#",selection_type="NEW_SELECTION")
	
	mergedFC = os.path.join(WORKSPACE,"_1_mergedSettlements")
	arcpy.Merge_management(["bua_lyr", "ssa_lyr", "ha_lyr"], mergedFC)

	
	
'''
Erase the intersection between lines and Settlements
'''
def eraseSettlementIntersect():
	mergedFC = os.path.join(WORKSPACE,"_1_mergedSettlements")
	erasedSettlementsFC = os.path.join(WORKSPACE,"_1_erasedSettlementsMultipartLines")
	arcpy.Erase_analysis(in_features=LINES_FC,erase_features=mergedFC,out_feature_class=erasedSettlementsFC,cluster_tolerance="#")

	
	
'''
Get the entry points for the settlements
'''
def getSettlementsEntryPoints():
	arcpy.MakeFeatureLayer_management(SSA_FC, "ssa_lyr")
	arcpy.MakeFeatureLayer_management(HA_FC, "ha_lyr")
	
	log("\tConvert lines to vertices",2)
	outFC = os.path.join(WORKSPACE,"_1_lineExtremityPoints")
	arcpy.FeatureVerticesToPoints_management(in_features="_1_erasedSettlementsMultipartLines",out_feature_class=outFC,point_location="DANGLE")	
	arcpy.MakeFeatureLayer_management("_1_lineExtremityPoints", "lineExtremityPoints_lyr")
	log("\t\t---> OK",2)
	
	
	log("\tGet entry Points for BUAs",2)
	getBUAsEntryPoints()
	log("\t\t---> OK",2)
	
	log("\tGet entry Points for SSAs",2)
	getSSAsEntryPoints()
	log("\t\t---> OK",2)
	
	log("\tGet entry Points for HAs",2)
	getHAsEntryPoints()
	log("\t\t---> OK",2)
	
	
'''
Get the entry points for the BUAs
'''
def getBUAsEntryPoints():
	arcpy.MakeFeatureLayer_management(BUA_FC, "bua_lyr")
	
	log("\t\tSelect touching BUAs",2)
	arcpy.SelectLayerByLocation_management("bua_lyr", "BOUNDARY_TOUCHES", "_1_erasedSettlementsMultipartLines")
	with arcpy.da.SearchCursor("bua_lyr", ("OID@", "SHAPE@",BUA_ID_FIELD)) as buaCursor:
		listTouchingBUAs = list(buaCursor)
	log("\t\t\t---> OK",2)
	
	
	buaCount=1
	for bua in listTouchingBUAs:
		log("\t\tGet entry points for BUA {0}/{1}".format(buaCount,len(listTouchingBUAs)),3)
		arcpy.SelectLayerByAttribute_management("bua_lyr", "NEW_SELECTION", "{0} = '{1}'".format(BUA_ID_FIELD,bua[2]))
		arcpy.SelectLayerByLocation_management("lineExtremityPoints_lyr", "BOUNDARY_TOUCHES", "bua_lyr")

		with arcpy.da.SearchCursor("lineExtremityPoints_lyr", ("OID@", "SHAPE@", "TeamID", "CampaignDay", "CampaignID", "TimeStamp", "ORIG_FID")) as touchesCursor:
			for touchingPoint in touchesCursor:
				storeEntryPoint(touchingPoint, bua[2],"bua")
		buaCentroid = arcpy.PointGeometry(bua[1].centroid,arcpy.SpatialReference(4326))
		buaCentroidP = buaCentroid.projectAs(arcpy.SpatialReference(102100))
		storeCentroid("bua",bua[2],buaCentroidP)
		buaCount = buaCount+1
		
		
		
'''
Get the entry points for the SSAs
'''
def getSSAsEntryPoints():
	arcpy.MakeFeatureLayer_management(SSA_FC, "ssa_lyr")
	
	log("\t\tSelect touching SSAs",2)
	arcpy.SelectLayerByLocation_management("ssa_lyr", "BOUNDARY_TOUCHES", "_1_erasedSettlementsMultipartLines")
	with arcpy.da.SearchCursor("ssa_lyr", ("OID@", "SHAPE@",SSA_ID_FIELD)) as ssaCursor:
		listTouchingSSAs = list(ssaCursor)
	log("\t\t\t---> OK",2)
	
	
	ssaCount=1
	for ssa in listTouchingSSAs:
		log("\t\tGet entry points for SSA {0}/{1}".format(ssaCount,len(listTouchingSSAs)),3)
		arcpy.SelectLayerByAttribute_management("ssa_lyr", "NEW_SELECTION", "{0} = '{1}'".format(SSA_ID_FIELD,ssa[2]))
		arcpy.SelectLayerByLocation_management("lineExtremityPoints_lyr", "BOUNDARY_TOUCHES", "ssa_lyr")

		with arcpy.da.SearchCursor("lineExtremityPoints_lyr", ("OID@", "SHAPE@", "TeamID", "CampaignDay", "CampaignID", "TimeStamp", "ORIG_FID")) as touchesCursor:
			for touchingPoint in touchesCursor:
				storeEntryPoint(touchingPoint, ssa[2],"ssa")
		ssaCentroid = arcpy.PointGeometry(ssa[1].centroid,arcpy.SpatialReference(4326))
		ssaCentroidP = ssaCentroid.projectAs(arcpy.SpatialReference(102100))
		storeCentroid("ssa",ssa[2],ssaCentroidP)
		ssaCount = ssaCount+1
		
		
		
'''
Get the entry points for the HAs
'''
def getHAsEntryPoints():
	arcpy.MakeFeatureLayer_management(HA_FC, "ha_lyr")
	
	log("\t\tSelect touching HAs",2)
	arcpy.SelectLayerByLocation_management("ha_lyr", "BOUNDARY_TOUCHES", "_1_erasedSettlementsMultipartLines")
	with arcpy.da.SearchCursor("ha_lyr", ("OID@", "SHAPE@",HA_ID_FIELD)) as haCursor:
		listTouchingHAs = list(haCursor)
	log("\t\t\t---> OK",2)
	
	
	haCount=1
	for ha in listTouchingHAs:
		log("\t\tGet entry points for HA {0}/{1}".format(haCount,len(listTouchingHAs)),3)
		arcpy.SelectLayerByAttribute_management("ha_lyr", "NEW_SELECTION", "{0} = '{1}'".format(HA_ID_FIELD,ha[2]))
		arcpy.SelectLayerByLocation_management("lineExtremityPoints_lyr", "BOUNDARY_TOUCHES", "ha_lyr")

		with arcpy.da.SearchCursor("lineExtremityPoints_lyr", ("OID@", "SHAPE@", "TeamID", "CampaignDay", "CampaignID", "TimeStamp", "ORIG_FID")) as touchesCursor:
			for touchingPoint in touchesCursor:
				storeEntryPoint(touchingPoint, ha[2],"ha")
		haCentroid = arcpy.PointGeometry(ha[1].centroid,arcpy.SpatialReference(4326))
		haCentroidP = haCentroid.projectAs(arcpy.SpatialReference(102100))
		storeCentroid("ha",ha[2],haCentroidP)
		haCount = haCount+1

		
		
'''
Stores the centroid of a settlement in 'settlementCentroids' FC
PARAMS:
	- settlementType: Type of settlement (BUA, SSA, HA)
	- settlementObjectid
	- shape: the point of the centroid
'''
def storeCentroid(settlementType,settlementObjectid,shape):
	c = arcpy.da.InsertCursor("_1_settlementCentroids",("SettlementType", "SettlementObjectId", "SHAPE@")) 
	c.insertRow([settlementType,settlementObjectid,shape])
	del c
	log("\t\t\tStore centroid for {0}".format(settlementType),3)
	
	

'''
Stores an entrypoint for a given settlement in 'entryPoints' FC
PARAMS:
	- touchingPoint: the entry point
	- bua: the settlement
	- settlementType: the type of settlement
'''
def storeEntryPoint(touchingPoint, settlementObjectId,settlementType):
	c = arcpy.da.InsertCursor("_1_entryPoints",("TeamID", "CampaignDay", "CampaignID", "TimeStamp", "LineID", "SettlementObjectId", "SHAPE@")) 
	c.insertRow([touchingPoint[2],touchingPoint[3],touchingPoint[4],touchingPoint[5],touchingPoint[6],settlementObjectId,touchingPoint[1]])
	del c
	log("\t\t\tPoint {0} touches {1}: {2}".format(touchingPoint[0],settlementType, settlementObjectId),3)


	
'''
Creates the output FC that will store the entryPoints
'''
def createEntryPointFC():
	geometry_type = "POINT"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_1_entryPoints", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_1_entryPoints")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "LineID", "LONG")
	arcpy.AddField_management(outFC, "SettlementObjectId", "TEXT")
	
	
	
'''
Creates the output FC that will store the centroid for each settlement
'''
def createCentroidsFC():
	geometry_type = "POINT"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_1_settlementCentroids", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_1_settlementCentroids")
	arcpy.AddField_management(outFC, "SettlementObjectId", "TEXT")
	arcpy.AddField_management(outFC, "SettlementType", "TEXT")
	
	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	currentCount=1
	
	log("Creating Output FCs",1)
	createEntryPointFC()
	createCentroidsFC()
	log("\t---> OK",1)
	
	log("Merge intersecting settlements",1)
	mergeSettlements()
	log("\t---> OK",1)
	
	log("Erase Settlement intersection",1)
	eraseSettlementIntersect()
	log("\t---> OK",1)
	
	log("Get entry points for settlements",1)
	getSettlementsEntryPoints()
	log("\t---> OK",1)
	
	log("Convert to multipart",1)
	outFC = os.path.join(WORKSPACE,"_1_erasedSettlementsSinglepartLines")
	arcpy.MultipartToSinglepart_management("_1_erasedSettlementsMultipartLines",outFC)
	log("\t---> OK",1)
	

	
	
	
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass