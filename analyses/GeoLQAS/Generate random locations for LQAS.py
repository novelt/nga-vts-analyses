# ------------------------------------------------------------
# Name:    GetLots.py
# Purpose: This script will pseudo-randomly pick a given number of 
# settlement that will then be used for LQA
#
# Author:    YM
# Created:   26.11.2014
# Modified:  26.11.2014
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.1
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy
import os, inspect
import sys
import csv
import shutil
from random import shuffle
from random import randint
from math import floor
from common import *



# Path to currently running script
scriptPath = os.path.dirname(__file__)
os.chdir(scriptPath)

# overwrite output if existing
arcpy.env.overwriteOutput = OVERWRITEOUTPUT
arcpy.env.workspace = scriptPath



# ------------------------------------------------------------
# Script Parameters
# ------------------------------------------------------------
LOG_LEVEL         = 1 #0:None / 1=Important / 2: INFO / 3:DEBUG

AGGREGATE_LEVEL   = "LGA"
INPUT_WORKSPACE   = arcpy.GetParameterAsText(0)
NB_SETTLEMENT     = int(arcpy.GetParameterAsText(1))

#split array, remove empty strings, and remove ' and " characters (which appear if multiwork strings are in the input
SELECTED_STATES   = filter(None, arcpy.GetParameterAsText(2).replace('"', '').replace("'", '').split(';'))
numberOfSelectedStates = len(SELECTED_STATES)

RECURSE_LIMIT     = 10
GDB_NAME          = "LQAS.gdb"
OUTPUT_WORKSPACE  = os.path.join(".",GDB_NAME)
OUTPUT_NAME       = "LQASResult"
FC_RESULT         = os.path.join(OUTPUT_WORKSPACE,OUTPUT_NAME)





# ------------------------------------------------------------
# Local Variables
# ------------------------------------------------------------
FIELD_WEIGHT = "Weight"
FC_STATE_RAW     = INPUT_WORKSPACE+"\\"+FCL_STATES
FC_LGA_RAW       = INPUT_WORKSPACE+"\\"+FCL_LGAS
FC_WARD_RAW      = INPUT_WORKSPACE+"\\"+FCL_WARDS
FC_BUA_RAW       = INPUT_WORKSPACE+"\\"+FCL_FE_BUILTUPAREA
FC_SSA_RAW       = INPUT_WORKSPACE+"\\"+FCL_FE_SMLSETTLEMENTAREAS
FC_HA_RAW        = INPUT_WORKSPACE+"\\"+FCL_FE_HAMLETAREAS
FC_BUA_GRID_RAW  = INPUT_WORKSPACE+"\\"+FCL_BUAGRIDS
FC_HAMLET_RAW    = INPUT_WORKSPACE+"\\"+FCL_HAMLETS

FC_STATE = OUTPUT_WORKSPACE+"\\"+FCL_STATES
FC_LGA = OUTPUT_WORKSPACE+"\\"+FCL_LGAS
FC_WARD = OUTPUT_WORKSPACE+"\\"+FCL_WARDS
FC_BUA = OUTPUT_WORKSPACE+"\\"+FCL_FE_BUILTUPAREA
FC_SSA = OUTPUT_WORKSPACE+"\\"+FCL_FE_SMLSETTLEMENTAREAS
FC_HA = OUTPUT_WORKSPACE+"\\"+FCL_FE_HAMLETAREAS
FC_BUA_GRID = OUTPUT_WORKSPACE+"\\"+FCL_BUAGRIDS
FC_HAMLET = OUTPUT_WORKSPACE+"\\"+FCL_HAMLETS


#Define the name of temporary FeatureClass that will be used
LAYER_WARD           = FC_WARD_RAW+"_layer"
LAYER_LGA            = FC_LGA_RAW+"_layer"
LAYER_STATE          = FC_STATE_RAW+"_layer"
LAYER_BUA            = FC_BUA_RAW+"_layer"
SORT_BUA             = FC_BUA_RAW+"_sort"
LAYER_SSA            = FC_SSA_RAW+"_layer"
LAYER_HA             = FC_HA_RAW+"_layer"
LAYER_BUA_GRID       = FC_BUA_GRID_RAW+"_layer"
LAYER_HAMLET         = FC_HAMLET_RAW+"_layer"


#(0:Type,1:StateCode,2:StateName,3:LGACode,4:AMAPCODE,5:LGAName,6:WardCode,7:AMAPCODE,8:WardName,9:SettlementObjectId,10:SettlementName,11:Weight,12:SHAPE,13:CumulatedWeight)
TYPE_IDX        = 0
LGACODE_IDX     = 3
WARDCODE_IDX    = 6
OID_IDX         = 9
WEIGHT_IDX      = 11
CUMULWEIGHT_IDX = 13

stateCodesWhere = None
cumulatedWeight = 0

buaLGACode       = None
buaStateCode     = None
buaStateName     = None
buaLGA_AmapCode  = None
buaLGAName       = None
buaWardCode      = None
buaWard_AmapCode = None
buaWardName      = None
buaOID           = None
buaName          = None
buaWeight        = None

buaList = None
ssaList = None
haList = None
gridList = None
hamletList = None
ssaEntryList = None


# ------------------------------------------------------------
# ------------------------------------------------------------
# Function definitions
# ------------------------------------------------------------
# ------------------------------------------------------------
	
def testPrerequisites():
	pass



'''
Create output FGDB if needed
'''
def createFGDB():
	workspaces = arcpy.ListWorkspaces(GDB_NAME, "FileGDB")
	if(len(workspaces) <= 0):
		arcpy.CreateFileGDB_management(".", GDB_NAME)



'''
Projects the input layers if needed
'''
def projInput():
	global FC_STATE
	global FC_LGA
	global FC_WARD
	global FC_BUA
	global FC_SSA
	global FC_HA
	global FC_BUA_GRID
	global FC_HAMLET

	#arcpy.Project_management(FC_STATE_RAW, FC_STATE, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_LGA_RAW, FC_LGA, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_WARD_RAW, FC_WARD, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_BUA_RAW, FC_BUA, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_SSA_RAW, FC_SSA, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_HA_RAW, FC_HA, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_BUA_GRID_RAW, FC_BUA_GRID, arcpy.SpatialReference(4326))
	#arcpy.Project_management(FC_HAMLET_RAW, FC_HAMLET, arcpy.SpatialReference(4326))
	
	FC_STATE = FC_STATE_RAW
	FC_LGA = FC_LGA_RAW
	FC_WARD = FC_WARD_RAW
	FC_BUA = FC_BUA_RAW
	FC_SSA = FC_SSA_RAW
	FC_HA = FC_HA_RAW
	FC_BUA_GRID = FC_BUA_GRID_RAW
	FC_HAMLET = FC_HAMLET_RAW



'''
Creates the output GDB used to store the results
Creates the folder to store KML for each LGA
'''
def createOutput():
	
	geometry_type = "POINT"
	arcpy.CreateFeatureclass_management(OUTPUT_WORKSPACE, OUTPUT_NAME, geometry_type, "", "", "", FC_SSA)
	arcpy.AddField_management(FC_RESULT, "StateName", "TEXT")
	arcpy.AddField_management(FC_RESULT, "StateCode", "TEXT")
	arcpy.AddField_management(FC_RESULT, "LGAName", "TEXT")
	arcpy.AddField_management(FC_RESULT, "LGACode", "TEXT")
	arcpy.AddField_management(FC_RESULT, "LGA_AmapCode", "TEXT")
	arcpy.AddField_management(FC_RESULT, "WardName", "TEXT")
	arcpy.AddField_management(FC_RESULT, "WardCode", "TEXT")
	arcpy.AddField_management(FC_RESULT, "Ward_AmapCode", "TEXT")
	arcpy.AddField_management(FC_RESULT, "SettlementName", "TEXT")
	arcpy.AddField_management(FC_RESULT, "SettlementType", "TEXT")
	arcpy.AddField_management(FC_RESULT, "SettlementObjectId", "TEXT")
	arcpy.AddField_management(FC_RESULT, "Weight", "TEXT")
	arcpy.AddField_management(FC_RESULT, "Lat", "FLOAT")
	arcpy.AddField_management(FC_RESULT, "Lon", "FLOAT")
	arcpy.AddField_management(FC_RESULT, "Direction", "SHORT")
	arcpy.AddField_management(FC_RESULT, "ClosestSettlement", "TEXT")
	arcpy.AddField_management(FC_RESULT, "ClosestNamedSettlement", "TEXT")

	lgaKmlDir = os.path.join('.','LGA_KML')
	if os.path.exists(lgaKmlDir):
		shutil.rmtree(lgaKmlDir, ignore_errors=True)

	arcpy.CreateFolder_management(".", "LGA_KML")

	
	
'''
Get the list of states from the selected state names
If no state is selected, returns all the states
RETURN
	the list of stateCode selected
'''
def getListOfStates():
	global stateCodesWhere
	if len(SELECTED_STATES) > 0:
		selectedStateNames = ','.join(map(lambda s: "'{0}'".format(s), SELECTED_STATES))
		selectedStateNames = "({0})".format(selectedStateNames)

	arcpy.MakeFeatureLayer_management(FC_STATE, LAYER_STATE)
	
	if len(SELECTED_STATES) > 0:
		state_cursor = arcpy.da.SearchCursor(LAYER_STATE,["StateCode", "StateName"], where_clause="StateName IN "+selectedStateNames)
	else:
		state_cursor = arcpy.da.SearchCursor(LAYER_STATE,["StateCode", "StateName"])
		
	#somehow the values are not unique. So we filter in memory
	listOfStates = list(state_cursor)
	del state_cursor
	
	listOfStateCodes = []
	for stateObj in listOfStates:
		stateCode = stateObj[0]
		stateName = stateObj[1]
		listOfStateCodes.append(stateCode)
		
	stateCodesWhere = ','.join(map(lambda s: "'{0}'".format(s), listOfStateCodes))
	stateCodesWhere = "({0})".format(stateCodesWhere)
	
	return listOfStateCodes
	
	

'''
Creates 3 tables where all the needed layers are joined 
- (State, LGA, Ward, BUA)
- (State, LGA, Ward, SSA)
- (State, LGA, Ward, HA)
PARAMS
	- stateCode: the stateCode for the current state
'''
def createFullJoinTables(stateCode):
	global buaLGACode,buaStateCode, buaStateName, buaLGA_AmapCode, buaLGAName, buaWardCode, buaWard_AmapCode, buaWardName, buaOID, buaName, buaWeight
	global buaList, ssaList, haList, gridList, hamletList, ssaEntryList
	
	arcpy.MakeFeatureLayer_management(FC_WARD, LAYER_WARD)
	arcpy.MakeFeatureLayer_management(FC_LGA, LAYER_LGA, where_clause="StateCode = '{0}'".format(stateCode))
	arcpy.MakeFeatureLayer_management(FC_STATE, LAYER_STATE, where_clause="StateCode ='{0}'".format(stateCode))
	
	arcpy.env.qualifiedFieldNames = False
	
	log("\t\tCreate BUA Join table...",2)
	arcpy.MakeFeatureLayer_management(FC_BUA, LAYER_BUA)	
	arcpy.AddJoin_management( LAYER_BUA, "WardCode", LAYER_WARD, "WardCode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_BUA, findFullFieldName(LAYER_BUA,"LGACode"), LAYER_LGA, "LGACode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_BUA, findFullFieldName(LAYER_BUA,"StateCode"), LAYER_STATE, "StateCode", "KEEP_COMMON")
	buaLGACode       = findFullFieldName(LAYER_BUA,"LGACode")
	buaStateCode     = findFullFieldName(LAYER_BUA,"StateCode")
	buaStateName     = findFullFieldName(LAYER_BUA,"StateName")
	buaLGA_AmapCode  = findFullFieldName(LAYER_BUA,"LGAs.AMAPCODE")
	buaLGAName       = findFullFieldName(LAYER_BUA,"LGAName")
	buaWardCode      = findFullFieldName(LAYER_BUA,"WardCode")
	buaWard_AmapCode = findFullFieldName(LAYER_BUA,"AMAPCODE")
	buaWardName      = findFullFieldName(LAYER_BUA,"WardName")
	buaOID           = findFullFieldName(LAYER_BUA,"Area.SettlementObjectID")
	buaName          = findFullFieldName(LAYER_BUA,"Area.SettlementName")
	buaWeight        = findFullFieldName(LAYER_BUA,"Weight")

	with arcpy.da.SearchCursor(LAYER_BUA,[buaStateCode,buaStateName,buaLGACode,buaLGA_AmapCode,buaLGAName,buaWardCode,buaWard_AmapCode,buaWardName,buaOID,buaName,buaWeight,"SHAPE@"]) as BUACursor:
		buaList = map(lambda t:('BUA',) + t[0:len(t)], list(BUACursor))
	log("\t\t  -> OK",2)
	
	log("\t\tCreate SSA Join table...",2)
	arcpy.MakeFeatureLayer_management(FC_SSA, LAYER_SSA)	
	arcpy.AddJoin_management( LAYER_SSA, findFullFieldName(LAYER_SSA,"WardCode"), LAYER_WARD, "WardCode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_SSA, findFullFieldName(LAYER_SSA,"LGACode"), LAYER_LGA, "LGACode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_SSA, findFullFieldName(LAYER_SSA,"StateCode"), LAYER_STATE, "StateCode", "KEEP_COMMON")	
	ssaStateCode = findFullFieldName(LAYER_SSA,"StateCode")
	ssaStateName = findFullFieldName(LAYER_SSA,"StateName")
	ssaLGACode   = findFullFieldName(LAYER_SSA,"LGACode")
	ssaWardCode  = findFullFieldName(LAYER_SSA,"WardCode")
	
	with arcpy.da.SearchCursor(LAYER_SSA,[ssaStateCode,ssaStateName,findFullFieldName(LAYER_SSA,"LGACode"),findFullFieldName(LAYER_SSA,"LGAs.AMAPCODE"),findFullFieldName(LAYER_SSA,"LGAName"),findFullFieldName(LAYER_SSA,"WardCode"),findFullFieldName(LAYER_SSA,"Wards.AMAPCODE"),findFullFieldName(LAYER_SSA,"WardName"),findFullFieldName(LAYER_SSA,"SettlementObjectID"),findFullFieldName(LAYER_SSA,"SettlementName"),findFullFieldName(LAYER_SSA,"Weight"),"SHAPE@"]) as SSACursor:
		ssaList = map(lambda t:('SSA',) + t[0:len(t)], list(SSACursor))
	log("\t\t  -> OK",2)
	
	log("\t\tCreate HA Join table...",2)
	arcpy.MakeFeatureLayer_management(FC_HA, LAYER_HA)	
	arcpy.AddJoin_management( LAYER_HA, findFullFieldName(LAYER_HA,"WardCode"), LAYER_WARD, "WardCode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_HA, findFullFieldName(LAYER_HA,"LGACode"), LAYER_LGA, "LGACode", "KEEP_COMMON")
	arcpy.AddJoin_management( LAYER_HA, findFullFieldName(LAYER_HA,"StateCode"), LAYER_STATE, "StateCode", "KEEP_COMMON")
	haWardCode  = findFullFieldName(LAYER_HA,"WardCode")
	haLGACode   = findFullFieldName(LAYER_HA,"LGACode")
	haStateCode = findFullFieldName(LAYER_HA,"StateCode")	
	with arcpy.da.SearchCursor(LAYER_HA,[findFullFieldName(LAYER_HA,"StateCode"),findFullFieldName(LAYER_HA,"StateName"),findFullFieldName(LAYER_HA,"LGACode"),findFullFieldName(LAYER_HA,"LGAs.AMAPCODE"),findFullFieldName(LAYER_HA,"LGAName"),findFullFieldName(LAYER_HA,"WardCode"),findFullFieldName(LAYER_HA,"Wards.AMAPCODE"),findFullFieldName(LAYER_HA,"WardName"),findFullFieldName(LAYER_HA,"Areas.SettlementObjectID"),findFullFieldName(LAYER_HA,"Areas.SettlementName"),findFullFieldName(LAYER_HA,"Weight"),"SHAPE@"]) as HACursor:
		haList = map(lambda t:('HA',) + t[0:len(t)], list(HACursor))
	log("\t\t  -> OK",2)
	
	if(len(buaList)>0):
		log("\t\tCreate Grid cell table...",2)
		arcpy.MakeFeatureLayer_management(FC_BUA_GRID, LAYER_BUA_GRID)
		buaIdListStr = ','.join(map(lambda s: "'{0}'".format(s[OID_IDX]), buaList))
		whereClause = "SettlementObjectId IN ({0})".format(buaIdListStr)
		with arcpy.da.SearchCursor(LAYER_BUA_GRID,("SHAPE@","OID@", "SettlementObjectId"),where_clause=whereClause) as cursorGrid:
			gridList = list(cursorGrid)
		log("\t\t  -> OK",2)
	
	if(len(ssaList)>0):
		log("\t\tCreate SSA table...",2)
		arcpy.MakeFeatureLayer_management(FC_SSA, LAYER_SSA)
		ssaIdListStr = ','.join(map(lambda s: "'{0}'".format(s[OID_IDX]), ssaList))
		whereClause = "SettlementObjectId IN ({0})".format(ssaIdListStr)
		with arcpy.da.SearchCursor(LAYER_SSA,("SHAPE@TRUECENTROID","OID@", "SettlementObjectId"),where_clause=whereClause) as cursorSSA:
			ssaEntryList = list(cursorSSA)
		log("\t\t  -> OK",2)
	
	if(len(haList) > 0):
		log("\t\tCreate Hamlet table...",2)
		arcpy.MakeFeatureLayer_management(FC_HAMLET, LAYER_HAMLET)
		haIdListStr = ','.join(map(lambda s: "'{0}'".format(s[OID_IDX]), haList))
		whereClause = "SettlementObjectId IN ({0})".format(haIdListStr)
		with arcpy.da.SearchCursor(LAYER_HAMLET,("SHAPE@TRUECENTROID","OID@", "SettlementObjectId"),where_clause=whereClause) as cursorHamlet:
			hamletList = list(cursorHamlet)
		log("\t\t  -> OK",2)
	
	

'''
Returns the full qualified name of a field for a given layer
'''
def findFullFieldName(layer, name):
	desc = arcpy.Describe(layer)
	fieldInfo = desc.fieldInfo
	
	index = 0
	while index < fieldInfo.count:
		fieldName = fieldInfo.getFieldName(index)
		if(name.lower() in fieldName.lower()):
			return fieldName
		
		index = index+1
	return name

	
	
'''
Returns a list of settlements for the given wardCode irrespective of their types
PARAMS:
	- wardCode: the wardCode for the ward to get the setllements
RETURNS
	a list of tuple () containing BUA, SSA and HA shuffled
'''
def getListOfSettlements(wardCode):
	listOfBUAs = filter(lambda x: x[WARDCODE_IDX] == wardCode, buaList)
	listOfSSAs = filter(lambda x: x[WARDCODE_IDX] == wardCode, ssaList)
	listOfHAs = filter(lambda x: x[WARDCODE_IDX] == wardCode, haList)
	
	allSettlements = listOfBUAs+listOfSSAs+listOfHAs
	
	shuffle(allSettlements)
	
	return allSettlements
	

	
'''
From the list of settlements, adds a new column where the weight is cumulated
PARAMS
	a list of shuffled settlements
RETURNS
	a list of shuffled settlements with a cumulatedWeight column
'''
def calculateCumulativeWeight(listOfSettlements):
	cumulativeSettlements = map(addWeight , listOfSettlements)
	return cumulativeSettlements



'''
Adds a weight to a tuple using the cumulatedWeight
PARAMS:
	- t: a tuple representing a settlement with a weight field
RETURNS
	a tuple with a new field 'cumulatedWeight'
'''
def addWeight(t):
	global cumulatedWeight
	tupleWeight = t[WEIGHT_IDX]
	
	if(tupleWeight is None):
		tupleWeight = 0
	cumulatedWeight += tupleWeight
	
	return t[0:len(t)] + (cumulatedWeight,)
	
	
	
'''
Use PPS a given number of settlements randomly
PARAMS: 
	- settlements: a list of shuffled settlements with a column cumulatedWeight
RETURNS
	a list of selected settlements as tuples (settlementObjectId, settlementType)
'''
def getSettlementsPPS(settlements):
	pickedSettlements = []
	samplingInterval = cumulatedWeight/NB_SETTLEMENT
	samplingIntervalFloor = floor(samplingInterval)
	samplingNumber = randint(0,samplingIntervalFloor-1)
	settlementToPick = getSettlementForWeight(settlements,samplingNumber)
	
	if(settlementToPick is not None):	
		pickedSettlements.append(settlementToPick)
		
		for i in range(1,NB_SETTLEMENT):
			samplingNumber = samplingNumber+samplingInterval
			settlementToPick = getSettlementForWeight(settlements,samplingNumber)
			if(settlementToPick is not None):	
				pickedSettlements.append(settlementToPick)
			
	
	
	return pickedSettlements
	
	

'''
Returns a tuple representing a settlement where the cumulatedWeight is just above the given weight
PARAMS:
	- settlements: The list of settlements where each tuple has a cumulatedWeight field
	- weight: The reference weight
RETURNS
	the first tuple in the list of settlement where cumulatedWeight > weight
'''
def getSettlementForWeight(settlements,weight):
	for settlement in settlements:
		cumulatedWeight = settlement[CUMULWEIGHT_IDX]
		
		if(cumulatedWeight>weight):
			return settlement
	
	#Settlement not found
	arcpy.AddError("Impossible to get settlement with cumulatedWeight > {0}. Settlements: {1}".format(weight,settlements))		
	sys.exit(0)

	
	

'''
Finds a random entry point for each selected settlement
PARAMS:
	- selectedSettlements: the list of settements selected by PPS
RETURNS
	a list of entry points as tuples (lat, long, direction)
'''
def getEntryPoints(selectedSettlements):
	results = []
	
	for settlement in selectedSettlements:
		settlementType = settlement[TYPE_IDX]
		settlementObjectId = settlement[OID_IDX]
		result = None
		
		if(settlementType == "BUA"):
			result = getGridCellForBUA(settlementObjectId)
		elif(settlementType == "SSA"):
			result = getEntryPointForSSA(settlementObjectId)
		elif(settlementType == "HA"):
			result = getEntryPointForHA(settlementObjectId)
		else:
			arcpy.AddError("Error 001: Selected settlement type {0} unknown (l.{1})\n {2}".format(settlementType,inspect.currentframe().f_back.f_lineno,settlement))		
			sys.exit(0)
		
		results.append(result)
		
	return results
	
	
	
'''
Returns an entry point for a BUA (pick a grid cell randomly and get the center)
PARAMS:
	- settlementOID: the settlementObjectId for the BUA
RETURNS
	a tuple (lat,long,None). the third field is for the direction but we don't generate a random direction for BUAs.
'''
def getGridCellForBUA(settlementOID):
	global gridList
	grids_in_bua = filter(lambda x: x[2] == settlementOID, gridList)
	nbGrids = len(grids_in_bua)
	
	if(nbGrids>0):
		#pick a random grid
		randomIdx = randint(0,nbGrids-1)
		pickedGrid = grids_in_bua[randomIdx]
		arcpy.CreateRandomPoints_management("in_memory", "buaPt", "", pickedGrid[0].extent, 1)
		with arcpy.da.SearchCursor(os.path.join("in_memory","buaPt"),("SHAPE@TRUECENTROID")) as cursorPt:
			ptRestul = list(cursorPt)
			resultTuple = ptRestul[0][0]+(None,)
			return resultTuple
	return None
		

		
'''
Returns an entry point for a SSA (Get the centroid + pick a random direction)
PARAMS:
	- settlementOID: the settlementObjectId for the SSA
RETURNS
	a tuple (lat,long,direction).
'''
def getEntryPointForSSA(settlementOID):
	global ssaEntryList
	currentSSA = filter(lambda x: x[2] == settlementOID, ssaEntryList)[0]
	randomDirection = randint(0,359)
	
	return currentSSA[0]+(randomDirection,)
		

		
'''
Returns an entry point for a HA (Get a random Hamlet + pick a random direction)
PARAMS:
	- settlementOID: the settlementObjectId for the HA
RETURNS
	a tuple (lat,long,direction).
'''
def getEntryPointForHA(settlementOID):
	global hamletList
	hamlets_in_ha = filter(lambda x: x[2] == settlementOID, hamletList)
	nbHamlets = len(hamlets_in_ha)
	
	#pick a random hamlet
	randomIdx = randint(0,nbHamlets-1)
	pickedHamlet = hamlets_in_ha[randomIdx]
	
	randomDirection = randint(0,359)
	
	return pickedHamlet[0]+(randomDirection,)
		
		
		
'''
Copies the needed boundaries in the result GDB to display in MXD
'''
def copyBoundaries():
	#Copies State, LGA and Ward FeatureClass
	arcpy.CopyFeatures_management(FC_STATE, OUTPUT_WORKSPACE+"\\"+FCL_STATES)
	arcpy.CopyFeatures_management(FC_LGA, OUTPUT_WORKSPACE+"\\"+FCL_LGAS)
	arcpy.CopyFeatures_management(FC_WARD, OUTPUT_WORKSPACE+"\\"+FCL_WARDS)
	
	
	
'''
Stores the selected settlements with entry point in the result GDB
PARAMS:
	- selectedSettlements: the list of selected settlements to store
	- entryPoints: the entry points corresponding to the settlements
'''
def storeResult(selectedSettlements,entryPoints):	
	outputRows = arcpy.da.InsertCursor(FC_RESULT,("SettlementType","StateCode","StateName","LGACode","LGA_AmapCode","LGAName","WardCode","Ward_AmapCode","WardName","SettlementObjectId","SettlementName","Weight","Lat","Lon","Direction","SHAPE@"))

	#(0:Type,1:StateCode,2:StateName,3:LGACode,4:AMAPCODE,5:LGAName,6:WardCode,7:AMAPCODE,8:WardName,9:SettlementObjectId,10:SettlementName,11:Weight,12:SHAPE)
	currentIndex = 0
	pickedBUAsSettlementObjectIds = []
	pickedSSAsSettlementObjectIds = []
	pickedHAsSettlementObjectIds  = []
	
	for settlement in selectedSettlements:
		settlementType = settlement[0]
		settlementOID  = settlement[9]
		entryPoint = entryPoints[currentIndex]
		#log("Current entry point: {0} (idx: {1})".format(entryPoint,currentIndex),3)
		
		if(entryPoint != None):
			point = arcpy.Point(float(entryPoint[0]), float(entryPoint[1]))
			ptGeometry = arcpy.PointGeometry(point,arcpy.SpatialReference(4326))
			outputRows.insertRow((settlement[0], settlement[1],settlement[2],settlement[3],settlement[4],settlement[5],settlement[6],settlement[7],settlement[8],settlement[9],settlement[10],settlement[11],entryPoint[0],entryPoint[1],entryPoint[2],ptGeometry)) 
		
		if(settlementType == "BUA"):
			pickedBUAsSettlementObjectIds.append(settlementOID)
		elif(settlementType == "SSA"):
			pickedSSAsSettlementObjectIds.append(settlementOID)
		elif(settlementType == "HA"):
			pickedHAsSettlementObjectIds.append(settlementOID)
		else:
			arcpy.AddError("Error 002 (storeResult): Selected settlement type {0} unknown (l.{1})\n {2}".format(settlementType,inspect.currentframe().f_back.f_lineno,settlement))		
			sys.exit(0)
		currentIndex += 1
	del outputRows
	
	BUA_where_clause = "SettlementObjectId in ('"+("','".join(pickedBUAsSettlementObjectIds))+"')"
	arcpy.MakeFeatureLayer_management(FC_BUA, "BUA_Layer", where_clause=BUA_where_clause)
	arcpy.CopyFeatures_management("BUA_Layer", OUTPUT_WORKSPACE+"\\"+FCL_FE_BUILTUPAREA)
	
	SSA_where_clause = "SettlementObjectId in ('"+("','".join(pickedSSAsSettlementObjectIds))+"')"
	arcpy.MakeFeatureLayer_management(FC_SSA, "SSA_Layer", where_clause=SSA_where_clause)
	arcpy.CopyFeatures_management("SSA_Layer", OUTPUT_WORKSPACE+"\\"+FCL_FE_SMLSETTLEMENTAREAS)
	
	HA_where_clause = "SettlementObjectId in ('"+("','".join(pickedHAsSettlementObjectIds))+"')"
	arcpy.MakeFeatureLayer_management(FC_HA, "HA_Layer", where_clause=HA_where_clause)
	arcpy.CopyFeatures_management("HA_Layer", OUTPUT_WORKSPACE+"\\"+FCL_FE_HAMLETAREAS)
	
	
	
'''
	Stores in the result FC the nearest settlement for each resulting settlement
'''
def getNearestSettlement():
	fc_namedSettlement = os.path.join(INPUT_WORKSPACE,"FC_SettlementPrimaryNames")
	
	
	arcpy.MakeFeatureLayer_management(fc_namedSettlement, "fc_namedSettlement_lyr")
	arcpy.MakeFeatureLayer_management(fc_namedSettlement, "fc_namedSettlement2_lyr", where_clause="SettlementPrimaryName NOT LIKE 'BUA_%' and SettlementPrimaryName NOT LIKE 'HA_%' and SettlementPrimaryName NOT LIKE 'SSA_%'")
	
	near_namedFeatures = ["fc_namedSettlement2_lyr"]
	near_features = [fc_namedSettlement]
	
	in_features = FC_RESULT
	
	recurselyFindNearestSettlementByLevel(2,in_features, near_features, near_namedFeatures)
	

	
	
def recurselyFindNearestSettlementByLevel(level,in_features, near_features, near_namedFeatures):
	near_table = os.path.join(OUTPUT_WORKSPACE,"near_settlements")
	near_namedTable = os.path.join(OUTPUT_WORKSPACE,"near_namedSettlements")
	
	arcpy.GenerateNearTable_analysis(in_features=in_features,near_features=near_features,out_table=near_table,search_radius="#",location="NO_LOCATION",angle="NO_ANGLE",closest="ALL",closest_count=str(level),method="PLANAR")
	arcpy.GenerateNearTable_analysis(in_features=in_features,near_features=near_namedFeatures,out_table=near_namedTable,search_radius="#",location="NO_LOCATION",angle="NO_ANGLE",closest="ALL",closest_count=str(level),method="PLANAR")
	
	arcpy.MakeTableView_management(near_table, "nearTable_vw")
	arcpy.MakeTableView_management(near_namedTable, "nearNamedTable_vw")
	arcpy.AddJoin_management( "nearTable_vw", "NEAR_FID", "fc_namedSettlement_lyr", "OBJECTID", "KEEP_COMMON")
	arcpy.AddJoin_management( "nearNamedTable_vw", "NEAR_FID", "fc_namedSettlement_lyr", "OBJECTID", "KEEP_COMMON")
	
	with arcpy.da.UpdateCursor(in_features, ("OID@","SettlementName","ClosestSettlement", "ClosestNamedSettlement")) as cursor:
		for row in cursor:
			row[2] = getClosestSettlementName(row)
			row[3] = getClosestNamedSettlementName(row)
			cursor.updateRow(row)
			
			
	arcpy.MakeFeatureLayer_management(FC_RESULT, "result_lyr_"+str(level),"ClosestSettlement = '' or ClosestNamedSettlement = ''")
	result = arcpy.GetCount_management("result_lyr_"+str(level))
	emptyCount = int(result.getOutput(0))
	
	#Recurse if empty results
	if(emptyCount > 0 and level < RECURSE_LIMIT):
		#log("Recurse for level {0} on {1} results".format(level+1, emptyCount),2)
		recurselyFindNearestSettlementByLevel(level+1,"result_lyr_"+str(level), near_features, near_namedFeatures)
			
			
			
'''
Gets the closes named settlement (INCLUDING machine-named settlement)
'''		
def getClosestSettlementName(settlement):
	with arcpy.da.SearchCursor("nearTable_vw", ("FC_SettlementPrimaryNames.SettlementPrimaryName"), "IN_FID = {0}".format(settlement[0]) ) as nearCursor:
		for nearRow in nearCursor:
			if(nearRow[0].strip() != settlement[1].strip()):
				#log("Closest settlement: {0} - {1}".format(nearRow[0], settlement[1]),3)
				return nearRow[0].strip()
	#log("Closest settlement not found {0}".format(settlement[0]),3)
	return ""
	
	
	
'''
Gets the closes named settlement (EXCLUDING machine-named settlement)
'''
def getClosestNamedSettlementName(settlement):
	with arcpy.da.SearchCursor("nearNamedTable_vw", ("FC_SettlementPrimaryNames.SettlementPrimaryName"), "IN_FID = {0}".format(settlement[0]) ) as nearCursor:
		for nearRow in nearCursor:
			if(nearRow[0].strip() != settlement[1].strip()):
				return nearRow[0].strip()
	return ""



'''
Create the CSV file representing the selected settlements with entry point
'''
def createCSV():
	csvFile = csv.writer(open(os.path.join(scriptPath,"LQAS.csv"), 'wb'), dialect='excel', quoting=csv.QUOTE_ALL) #output csv
	fieldnames = ["SettlementType","StateCode","StateName","LGACode","LGA_AmapCode","LGAName","WardCode","Ward_AmapCode","WardName","SettlementObjectId","SettlementName","Weight","Lat","Lon","Direction","ClosestSettlement", "ClosestNamedSettlement"]
	csvFile.writerow(fieldnames)

	crlf = '\n'
	cursor = arcpy.da.SearchCursor(FC_RESULT,("SettlementType","StateCode","StateName","LGACode","LGA_AmapCode","LGAName","WardCode","Ward_AmapCode","WardName","SettlementObjectId","SettlementName","Weight","Lat","Lon","Direction","ClosestSettlement", "ClosestNamedSettlement"))
	toCopy = list(cursor)
	del cursor
	for row in toCopy:
		newRow = tuple(str(col).replace(crlf, '') if col != None else col for col in row)
		csvFile.writerow(newRow)



'''
Create the KML file representing the selected settlements with entry point
'''
def createKML():
	lgaKmlDir = os.path.join('.','LGA_KML')

	globalTemplate = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2" xmlns:atom="http://www.w3.org/2005/Atom">
<Document>
	<name>{StateName}-{LGAName}</name>
	{placemarks}
</Document>
</kml>"""

	placemarkTemplate = """<Placemark>
			<name>{name}</name>
			<Point>
				<gx:drawOrder>1</gx:drawOrder>
				<coordinates>{lat},{long},0</coordinates>
			</Point>
		</Placemark>"""

	StateList = set(row[0] for row in arcpy.da.SearchCursor(FC_RESULT, ("StateName")))

	for stateName in StateList:
		stateDir = os.path.join(lgaKmlDir,stateName)
		os.makedirs(stateDir)

		LGAInStateList = set(row[0] for row in arcpy.da.SearchCursor(FC_RESULT, ("LGAName"), "StateName='{0}'".format(stateName)))

		for lgaName in LGAInStateList:
			lgaKML = os.path.join(stateDir,"{0}.kml".format(lgaName))

			placemarks = []
			with arcpy.da.SearchCursor(FC_RESULT, ["SettlementName", "Lat","Lon"], "LGAName='{0}'".format(lgaName.replace("'", "''"))) as cursor:
				for row in cursor:
					placemarks.append(placemarkTemplate.format(name=row[0], lat=row[1], long=row[2]))
			

			file = open(lgaKML, 'w')
			file.write(globalTemplate.format(placemarks="".join(placemarks), StateName=stateName, LGAName=lgaName))
			file.close();
		


'''
Removes projected layers
'''
def removeTempLayers():
	arcpy.Delete_management(FC_STATE)
	arcpy.Delete_management(FC_LGA)
	arcpy.Delete_management(FC_WARD)
	arcpy.Delete_management(FC_BUA)
	arcpy.Delete_management(FC_SSA)
	arcpy.Delete_management(FC_HA)
	arcpy.Delete_management(FC_BUA_GRID)
	arcpy.Delete_management(FC_HAMLET)
		


# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	global cumulatedWeight, buaList, ssaList, haList
	selectedSettlements = []
	entryPoints = []
	
	log("Create output GDB...",1)
	createFGDB()
	log("  ---> OK",1)
	
	log("Test prerequisites...",1)
	testPrerequisites()
	log("  ---> OK",1)

	log("Reprojecting inputs if needed...",1)
	projInput()
	log("  ---> OK",1)

	log("Creates output gdb...",1)
	createOutput()
	log("  ---> OK",1)
	
	log("Get the list of states to process...",1)
	listOfStates = getListOfStates()
	log("  ---> OK",1)

	currentState = 1
	
	for stateCode in listOfStates:
		log("Process state {0} ({1}/{2})...".format(stateCode,currentState,len(listOfStates)),1)
		log("\tCreates the join tables needed...",1)
		createFullJoinTables(stateCode)
		log("\t  ---> OK",1)
		
		#Get the list of LGAs
		lgaCodes = []
		with arcpy.da.SearchCursor(LAYER_LGA, [LGA_ID_FIELD]) as lgasCursor:
			for lgaCode in lgasCursor:
				lgaCodes.append(lgaCode[0])
				
			totalLGAs = len(lgaCodes)
			currentLGA = 1
			#Loop through LGAs for processing
			for lgaCode in lgaCodes:
				listOfSettlements = []
				cumulatedWeight = 0
				log("\tGet the list of settlements for LGA {0} ({1}/{2})...".format(lgaCode,currentLGA,totalLGAs),1)
				wardCodes = []
				with arcpy.da.SearchCursor(LAYER_WARD, [WARD_ID_FIELD],"{0}='{1}'".format(LGA_ID_FIELD,lgaCode)) as wardsCursor:
					for wardCode in wardsCursor:
						wardCodes.append(wardCode[0])
					
					#Shuffle Wards
					shuffle(wardCodes)
					totalWards = len(wardCodes)
					currentWard = 1
					for wardCode in wardCodes:
						#log("\t\tGet settlements for Ward {0} ({1}/{2})...".format(wardCode,currentWard,totalWards),3)
						listOfSettlements = listOfSettlements+getListOfSettlements(wardCode)
						currentWard += 1
				
				if(len(listOfSettlements) > 0):
					log("\tCalculates the cumlative weight column...",1)
					listOfSettlementsWithWeight = calculateCumulativeWeight(listOfSettlements)
					#log("CUMULATED: {0}".format(listOfSettlementsWithWeight),3)
					log("\t  ---> OK",1)
					
					log("\tUse PPS to select settlements...",1)
					currentSelected = getSettlementsPPS(listOfSettlementsWithWeight)
					selectedSettlements	+= currentSelected
					log("\t  ---> OK",1)
					
					log("\tGet the entry points...",1)
					entryPoints	+= getEntryPoints(currentSelected)
					#log("Entry points: {0}".format(entryPoints),3)
					log("\t  ---> OK",1)
				else:
					log("\tNo settlement in current LGA",1)
				
				currentLGA = currentLGA+1
		del buaList
		del ssaList
		del haList
		currentState += 1
	
	log("Copy boundaries...",1)
	copyBoundaries()
	log("  ---> OK",1)
	
	log("Store the result...",1)
	storeResult(selectedSettlements,entryPoints)
	log("  ---> OK",1)
	
	log("Get nearest named settlement...",1)
	getNearestSettlement()
	log("  ---> OK",1)
	
	log("Create the CSV...",1)
	createCSV()
	log("  ---> OK",1)
	
	log("Create the KML for each LGA...",1)
	createKML()
	log("  ---> OK",1)
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
		pass