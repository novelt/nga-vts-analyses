# ------------------------------------------------------------
# Name:    2c-selectBestLine.py
# Purpose: Selects the best line inter-settlement
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
WEIGHTED_TRACKS = arcpy.GetParameterAsText(1)
WORKSPACE       = arcpy.GetParameterAsText(2)


WEIGHT_LIMIT    = 4000
MAX_DIST_POINTS = 50 #entry points in a buffer of 50m are considered the same


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
Selects the best line to keep from a collection of lines
PARAMS:
	- sortedLines: the lines sorted on the Shape_Length field
'''
def selectBestLines(interSettlementLines,fromSettlementOID,toSettlementOID):
	sortedLinesByWeight =  sorted(interSettlementLines, key=lambda l: l[13], reverse=True)
	
	addedLines = []
	for line in sortedLinesByWeight:
		if(len(addedLines) == 0):
			log("Add lineWeight {0} first".format(line[13]),3)
			storeLine(line, fromSettlementOID, toSettlementOID)
			addedLines.append(line)
		elif (line[13] >= WEIGHT_LIMIT):
			log("Add lineWeight {0} above weight limit".format(line[13]),3)
			storeLine(line, fromSettlementOID, toSettlementOID)
			addedLines.append(line)
		else:
			isDisjoint = True
			hasDifferentEntryPoints = True
			for previousLine in addedLines:
				previousLineGeom = previousLine[0]
				currentLineGeom = line[0]
				
				#Test if geometries are disjoint
				outGeom = arcpy.Geometry()
				outGeomList = arcpy.Buffer_analysis(previousLineGeom,outGeom,"25 Meters")
				bufferedGeom = outGeomList[0]
				geomDisjoint = bufferedGeom.disjoint(currentLineGeom)
				log("lineWeight {0} disjoint with lineWeight {1}: {2}".format(line[13], previousLine[13], geomDisjoint),3)
				isDisjoint = (isDisjoint and geomDisjoint)
				
				
				#test if first and end points are close to each other. If so consider same road
				#	compare first point of currentLine
				firstPointGeometry = arcpy.PointGeometry(currentLineGeom.firstPoint)
				prevFirstPointGeometry = arcpy.PointGeometry(previousLineGeom.firstPoint)
				prevLastPointGeometry = arcpy.PointGeometry(previousLineGeom.lastPoint)
				firstDist = firstPointGeometry.distanceTo(prevFirstPointGeometry)
				lastDist = firstPointGeometry.distanceTo(prevLastPointGeometry)
				
				if(firstDist <= MAX_DIST_POINTS or lastDist <= MAX_DIST_POINTS):
					#	 compare last point of current line
					lastPointGeometry = arcpy.PointGeometry(currentLineGeom.lastPoint)
					firstDist2 = lastPointGeometry.distanceTo(prevFirstPointGeometry)
					lastDist2  = lastPointGeometry.distanceTo(prevLastPointGeometry)
					
					if(firstDist2 <= MAX_DIST_POINTS or lastDist2 <= MAX_DIST_POINTS):
						hasDifferentEntryPoints = False
			
			log("LineWeight {0} disjoint: {1} - entryPointsDifferent: {2}".format(line[13], isDisjoint, hasDifferentEntryPoints),3)
			
			if(isDisjoint and hasDifferentEntryPoints):
				log("Add lineWeight {0}".format(line[13]),3)
				storeLine(line, fromSettlementOID, toSettlementOID)
				addedLines.append(line)
				
				
	

'''
Stores an entrypoint for a given settlement in 'entryPoints' FC
PARAMS:
	- touchingPoint: the entry point
	- bua: the settlement
	- settlementType: the type of settlement
'''
def storeLine(line, fromSettlement, toSettlement):
	outFC = os.path.join(WORKSPACE,"_2c_BestLines")
	c = arcpy.da.InsertCursor(outFC,("SHAPE@","TeamID", "CampaignDay", "CampaignID", "TimeStamp","Source", "SourceID", "ORIG_FID", "Intersect_Count", "Tracks_Count", "MinSpeed", "MaxSpeed", "AvgSpeed", "Weight", "FromSettlement", "ToSettlement")) 
	c.insertRow([line[0], line[1], line[2], line[3], line[4], line[5], line[6], line[7], line[8], line[9], line[10], line[11], line[12], line[13], fromSettlement, toSettlement])
	del c
	
	
	
'''
Creates the output FC that will store the centroid polylines
'''
def createBestLineOutput():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_2c_BestLines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_2c_BestLines")
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
	arcpy.AddField_management(outFC, "FromSettlement", "TEXT")
	arcpy.AddField_management(outFC, "ToSettlement", "TEXT")
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	
	createBestLineOutput()
	
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"workingSettlements_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"settlement1_lyr")
	arcpy.MakeFeatureLayer_management(MERGED_POLY,"settlement2_lyr")
	arcpy.MakeFeatureLayer_management(WEIGHTED_TRACKS,"weightedlines_lyr")
	
	
	log("Select settlements in working extent",1)
	arcpy.SelectLayerByLocation_management(in_layer="workingSettlements_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="weightedlines_lyr",search_distance="#",selection_type="NEW_SELECTION")
	result = arcpy.GetCount_management("workingSettlements_lyr")
	count = int(result.getOutput(0))
	log("\---> OK ({0} settlements selected)".format(count),1)
	
	currentCount = 1
	processed = []
	with arcpy.da.SearchCursor("workingSettlements_lyr", ("OID@","SettlementObjectId")) as settlementCursor:
		for settlement in settlementCursor:
			log("Settlement {0} ({1}/{2})".format(settlement[0],currentCount,count),1)
			poly1Id = settlement[1]
			
			processed.append(str(settlement[0]))
			
			arcpy.SelectLayerByAttribute_management("settlement1_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",settlement[0]))
			arcpy.SelectLayerByLocation_management(in_layer="weightedlines_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="settlement1_lyr",search_distance="#",selection_type="NEW_SELECTION")
					
			with arcpy.da.SearchCursor("workingSettlements_lyr", ("OID@","SettlementObjectId"), "OBJECTID not in ({0})".format(','.join(processed))) as otherSettlementCursor:
				for otherSettlement in otherSettlementCursor:
					poly2Id = otherSettlement[1]
					
					arcpy.MakeFeatureLayer_management("weightedlines_lyr","weightedlines2_lyr")
					arcpy.SelectLayerByAttribute_management("settlement2_lyr", "NEW_SELECTION", "{0} = {1}".format("OBJECTID",otherSettlement[0]))
					arcpy.SelectLayerByLocation_management(in_layer="weightedlines2_lyr",overlap_type="BOUNDARY_TOUCHES",select_features="settlement2_lyr",search_distance="#",selection_type="NEW_SELECTION")
					
					with arcpy.da.SearchCursor("weightedlines2_lyr", ("SHAPE@","TeamID", "CampaignDay", "CampaignID", "TimeStamp", "Source", "SourceID", "ORIG_FID", "Intersect_Count", "Tracks_Count", "MinSpeed", "MaxSpeed", "AvgSpeed", "Weight")) as selectedLinesCursor:
						interSettlementLines = list(selectedLinesCursor)
					
					#log("\tCompared to {0} (selected lines {1})".format(otherSettlement[0],len(interSettlementLines)),3)
					
					if(len(interSettlementLines) >0):
						selectBestLines(interSettlementLines,poly1Id,poly2Id)
			currentCount = currentCount+1

	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass