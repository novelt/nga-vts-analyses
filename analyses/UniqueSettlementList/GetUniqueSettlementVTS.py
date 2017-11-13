# ------------------------------------------------------------
# Name:    2-preprocessDEM.py
# Purpose: PreProcess a DEM so that we can query a Watershed for any point
#
# Author:    YM
# Created:   17.11.2014
# Modified:  18.11.2014
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.2.2
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
from arcpy import env
from common import *
import operator
import uuid
import difflib
import sys
import os


OUT_GDB        = arcpy.GetParameterAsText(0)
INPUT_FC       = arcpy.GetParameterAsText(1)
NAME_FIELD     = arcpy.GetParameterAsText(2)
MAX_TEXT_DIST  = float(arcpy.GetParameterAsText(3))
MAX_DIST       = int(arcpy.GetParameterAsText(4))
IN_BUA_LAYER   =  arcpy.GetParameterAsText(5)
IN_SSA_LAYER   =  arcpy.GetParameterAsText(6)
IN_HA_LAYER    =  arcpy.GetParameterAsText(7)



OUT_NEARTBL  = os.path.join(OUT_GDB,"nearTbl")
OUT_MERGE_FC = os.path.join(OUT_GDB,"mergedSettl")

processed   = [] #Contains the OBJECTID of the features processed
listOfGroups = [] #Contains Tuples (GroupName, Guid, shape, [featureOID])
arcpy.env.overwriteOutput = OVERWRITEOUTPUT


# ------------------------------------------------------------
# ------------------------------------------------------------
# Function definitions
# ------------------------------------------------------------
# ------------------------------------------------------------
'''
'''
def mergePolygons():
	arcpy.Merge_management(inputs="{0};{1};{2}".format(IN_BUA_LAYER,IN_SSA_LAYER,IN_HA_LAYER), output=OUT_MERGE_FC)



'''
Creates Near table: distance between each settlement
'''
def generateNear():
	arcpy.Near_analysis(in_features=INPUT_FC, near_features=OUT_MERGE_FC, search_radius="{0} Meters".format(MAX_DIST), location="NO_LOCATION", angle="NO_ANGLE", method="PLANAR")
	


'''
Creates the groups of features in an internal structure (List)
'''
def createGroups():

	#Process groups linked to a polygon
	with arcpy.da.SearchCursor(in_table=INPUT_FC, field_names=[NAME_FIELD,"NEAR_FID","NEAR_DIST","OID@","SHAPE@"],where_clause="NEAR_FID<>-1",sql_clause=(None,"ORDER BY NEAR_FID ASC, NEAR_DIST ASC")) as searchCursor:
		inputList = list(searchCursor)
		for inFeature in inputList:
			currentOID   = inFeature[3]
			currentName  = inFeature[0]
			currentShape = inFeature[4]
			polyId       = inFeature[1]

			if currentOID not in processed:
				groupIndex = createNewGroup(currentName,currentOID,currentShape)
				processed.append(currentOID)
				#log("Processing {0} ({1})".format(currentName,currentOID),3)
				featuresWithId = getFeaturesWithId(polyId)

				for sameIdFeature in featuresWithId:
					if sameIdFeature[3] != currentOID:
						featureOID   = sameIdFeature[3]
						featureName  = sameIdFeature[0]
						#log("Same feature {0} ({1})".format(featureName,featureOID),3)
						textDist = getStringDistance(currentName,featureName)

						if textDist > MAX_TEXT_DIST:
							appendToGroup(groupIndex,featureOID)
							processed.append(featureOID)

				del featuresWithId
	del inputList

	# #Process groups outside any polygon
	# with arcpy.da.SearchCursor(in_table=INPUT_FC, field_names=[NAME_FIELD,"NEAR_FID","NEAR_DIST","OID@","SHAPE@"],where_clause="NEAR_FID=-1",sql_clause=(None,"ORDER BY NEAR_FID ASC, NEAR_DIST ASC")) as searchCursor:
	# 	for row in searchCursor:
	# 		currentOID   = row[3]
	# 		currentName  = row[0]
	# 		currentShape = row[4]
	# 		createNewGroup(currentName,currentOID,currentShape)



'''
'''
def createNewGroup(groupName,featureOID,featureShape):
	global listOfGroups
	groupUID = uuid.uuid1()
	listOfGroups.append([groupName,groupUID,featureShape,[featureOID]])
	index = len(listOfGroups)-1
	#log("CREATE group: {0}".format(groupName),3)
	return index



'''
'''
def appendToGroup(groupIndex,featureOID):
	global listOfGroups
	listOfGroups[groupIndex][3].append(featureOID)



'''
'''
def getFeaturesWithId(nearId):
	with arcpy.da.SearchCursor(in_table=INPUT_FC, field_names=[NAME_FIELD,"NEAR_FID","NEAR_DIST","OID@"],where_clause="NEAR_FID={0}".format(nearId),sql_clause=(None,"ORDER BY NEAR_FID ASC, NEAR_DIST ASC")) as searchCursor:
		inputList = list(searchCursor)
		return inputList



'''
Returns the distance between 2 strings
'''
def getStringDistance(stringA,stringB):

	if stringA is not None and stringB is None:
		return 0

	if stringB is not None and stringA is None:
		return 0

	if stringB is None and stringA is None:
		return 1

	charsToRemove = [" ",","]

	normalizedA = stringA.lower()
	normalizedB = stringB.lower()

	for char in charsToRemove:
		normalizedA = "".join(normalizedA.split(char))
		normalizedB = "".join(normalizedB.split(char))

	seq=difflib.SequenceMatcher(None,normalizedA, normalizedB)
	ratio = seq.ratio()
	return seq.ratio()


	
'''
Stores the groups in a new FeatureClass and generates GlobalIDs
'''
def storeGroups():
	arcpy.CreateFeatureclass_management(out_path=OUT_GDB, out_name="UniqueGroups", geometry_type="POINT", spatial_reference=INPUT_FC)
	out_fc = os.path.join(OUT_GDB,"UniqueGroups")
	arcpy.AddField_management(out_fc, "Name", "TEXT")
	arcpy.AddField_management(out_fc, "UUID", "TEXT")

	with arcpy.da.InsertCursor(out_fc,["Name","UUID","SHAPE@"]) as insertCur:
		for group in listOfGroups:
			groupName = group[0]
			groupUID  = group[1]
			groupGeom = group[2]
			insertCur.insertRow([groupName,groupUID,groupGeom])



'''
'''
def appendGUID():
	arcpy.AddField_management(INPUT_FC, "RefGlobalID", "TEXT")

	with arcpy.da.UpdateCursor(INPUT_FC, ["OID@","RefGlobalID"]) as cursor:
		for row in cursor:
			groupGUID = getUIDForItemID(row[0])
			row[1] = groupGUID
			cursor.updateRow(row) 



'''
'''
def getUIDForItemID(id):
	for group in listOfGroups:
		OIDs = group[3]
		if id in OIDs:
			return group[1]

	return None



'''
'''
def cleanInput():
	 arcpy.DeleteField_management(INPUT_FC, ["NEAR_FID","NEAR_DIST"])


# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():

	log("Merging layers...",1)
	mergePolygons()
	log("  -> OK...",1)

	log("Generating Near features...",1)
	generateNear()
	log("  -> OK...",1)

	log("Creating the groups...",1)
	createGroups()
	log("  -> OK...",1)

	log("Storing the groups...",1)
	storeGroups()
	log("  -> OK...",1)

	log("Adding GUID to original FC...",1)
	appendGUID()
	log("  -> OK...",1)

	log("Cleaning input FC...",1)
	#cleanInput()
	log("  -> OK...",1)


	#log(listOfGroups,3)
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass