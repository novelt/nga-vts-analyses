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
MAX_SHAPE_DIST = arcpy.GetParameterAsText(4)



OUT_NEARTBL = os.path.join(OUT_GDB,"nearTbl")
IN_NAME     = "in_name"
NEAR_NAME   = "near_name"

processed   = [] #Contains the OBJECTID of the features processed
listOfGroups = []
arcpy.env.overwriteOutput = OVERWRITEOUTPUT


# ------------------------------------------------------------
# ------------------------------------------------------------
# Function definitions
# ------------------------------------------------------------
# ------------------------------------------------------------
'''
Creates Near table: distance between each settlement
'''
def generateNearTable():
	arcpy.GenerateNearTable_analysis(in_features=INPUT_FC, near_features=INPUT_FC, out_table=OUT_NEARTBL, search_radius="{0} Meters".format(MAX_SHAPE_DIST), location="LOCATION", angle="NO_ANGLE", closest="ALL", closest_count="0", method="PLANAR")
	


'''
Adds the names to the near table (IN_NAME and NEAR_NAME)
'''
def addNames():
	arcpy.AddField_management(OUT_NEARTBL, IN_NAME, "TEXT")
	arcpy.AddField_management(OUT_NEARTBL, NEAR_NAME, "TEXT")

	near_tblView   = arcpy.MakeTableView_management(OUT_NEARTBL,"near_tblView")
	inFeaturesView = arcpy.MakeFeatureLayer_management(INPUT_FC, "inFeaturesView")

	#Join to add name for the IN_FID
	arcpy.AddJoin_management(in_layer_or_view=near_tblView, in_field="IN_FID", join_table=inFeaturesView, join_field="OBJECTID", join_type="KEEP_ALL")

	fullFieldName = NAME_FIELD
	for field in arcpy.ListFields(near_tblView):
		if NAME_FIELD in ".{0}".format(field.name):
			fullFieldName = field.name
			continue

	arcpy.CalculateField_management(near_tblView, IN_NAME,'!{0}!'.format(fullFieldName), "PYTHON")
	joinName = fullFieldName.split(".")[0]
	arcpy.RemoveJoin_management(in_layer_or_view=near_tblView, join_name=joinName)


	#Join to add name for the NEAR_FID
	arcpy.AddJoin_management(in_layer_or_view=near_tblView, in_field="NEAR_FID", join_table=inFeaturesView, join_field="OBJECTID", join_type="KEEP_ALL")
	
	fullFieldName = NAME_FIELD
	for field in arcpy.ListFields(near_tblView):
		if NAME_FIELD in ".{0}".format(field.name):
			fullFieldName = field.name
			continue

	arcpy.CalculateField_management(near_tblView, NEAR_NAME,'!{0}!'.format(fullFieldName), "PYTHON")
	joinName = fullFieldName.split(".")[0]
	arcpy.RemoveJoin_management(in_layer_or_view=near_tblView, join_name=joinName)



'''
Creates the groups of features in an internal structure (List)
'''
def createGroups():
	count = 0
	with arcpy.da.SearchCursor(OUT_NEARTBL, ["IN_FID",IN_NAME,"NEAR_FID",NEAR_NAME,"FROM_X","FROM_Y","NEAR_X","NEAR_Y"]) as searchCursor:
		for nearRow in searchCursor:
			in_fid      = nearRow[0]
			in_name     = nearRow[1]
			near_fid    = nearRow[2]
			near_name   = nearRow[3]
			in_coords   = [nearRow[4],nearRow[5]]
			near_coords = [nearRow[6],nearRow[7]]

			if in_fid not in processed: #If not in processed, means it is not close to an existing group
				processed.append(in_fid)
				addNewGroup(in_name,in_fid,in_coords)


			if near_fid not in processed:
				processed.append(near_fid)
				matchingGroups = getMatchingGroups(near_name)

				if(len(matchingGroups)<=0):
					addNewGroup(near_name,near_fid,near_coords)
				else:
					sorted_matches = sorted(matchingGroups, key=lambda x: x[1],reverse=True)
					#log("MATCHING groups: {0}".format(sorted_matches),3)
					bestMatch = sorted_matches[0]
					bestMatchIndex = bestMatch[0]
					addToExistingGroup(bestMatchIndex,near_name,near_fid,near_coords)
			
			count=count+1




'''
Adds a new group
'''
def addNewGroup(name,id,coords):
	global listOfGroups
	groupUID = uuid.uuid1()
	listOfGroups.append([name,[id],groupUID,[coords]])
	#log("CREATE group: {0}".format(name),3)



'''
Adds a new name to an existing group
'''
def addToExistingGroup(groupIndex,name,id,coords):
	global listOfGroups
	listOfGroups[groupIndex][1].append(id) #1 is the list of IDs
	listOfGroups[groupIndex][3].append(coords) #3 is the list of points



'''
Returns the group with close names 
'''
def getMatchingGroups(nameToMatch):
	result = []

	currentIndex = 0
	for group in listOfGroups:
		groupName = group[0]
		groupFeatures = group[1]

		dist = getStringDistance(nameToMatch,groupName)
		#log("\tDISTANCE from {0} to {1} = {2}".format(groupName,nameToMatch,dist),3)
		if dist > MAX_TEXT_DIST:
			item = (currentIndex, dist)
			result.append(item)
		currentIndex=currentIndex+1

	return result



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
			groupUID  = group[2]
			groupGeom = group[3]
			point = arcpy.Point()
			point.X = groupGeom[0][0]
			point.Y = groupGeom[0][1]
			geomToStore =  arcpy.PointGeometry(point)
			insertCur.insertRow([groupName,groupUID,geomToStore])



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
		OIDs = group[1]
		if id in OIDs:
			return group[2]

	return None



def createGroupForIsolatedFeatures():
	with arcpy.da.UpdateCursor(INPUT_FC, ["OID@",NAME_FIELD,"SHAPE@","RefGlobalID"],"RefGlobalID is null") as updateCursor:
		out_fc = os.path.join(OUT_GDB,"UniqueGroups")
		rowsToInsert = []
		for feature in updateCursor:
			groupUID = uuid.uuid1()
			groupName = feature[1]
			groupShape = feature[2]
			rowsToInsert.append([groupName,groupUID,groupShape])
			feature[3] = groupUID
			updateCursor.updateRow(feature) 
			#log("{0}".format(feature[0]),3)

	with arcpy.da.InsertCursor(out_fc,["Name","UUID","SHAPE@"]) as insertCur:
		for row in rowsToInsert:
			insertCur.insertRow(row)



	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	log("Generating Near table...",1)
	generateNearTable()
	log("  -> OK...",1)

	log("Adding names to the Near table...",1)
	addNames()
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

	log("Creating group for isolated features...",1)
	createGroupForIsolatedFeatures()
	log("  -> OK...",1)


	#log(listOfGroups,3)
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass