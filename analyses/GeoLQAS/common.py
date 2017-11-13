# ------------------------------------------------------------
# Name:    common.py
# Purpose: Constants and common functions
#
# Author:    Novel-T
# Created:   18.07.2014
# Modified:  18.07.2014
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.1
# Python Version: 2.7
# ------------------------------------------------------------
import arcpy

OVERWRITEOUTPUT       = True
LOG_LEVEL             = 1 #0:None / 1=Important / 2: INFO / 3:DEBUG

FCL_FE_BUILTUPAREA        = "FE_BuiltUpArea"
FCL_FE_HAMLETAREAS        = "FE_HamletAreas"
FCL_FE_SMLSETTLEMENTAREAS = "FE_SmlSettlementAreas"
FCL_GPREF_SSA             = "VTS_GPRefLyrSSABuffers"
FCL_BUAGRIDS              = "VTS_GPRefLyrBUAGrids"
FCL_HAMLETS               = "VTS_GPRefLyrHABuffers"
FCL_STATES                = "Boundary_VaccStates"
FCL_LGAS                  = "Boundary_VaccLGAs"
FCL_WARDS                 = "Boundary_VaccWards"

BUA_JOIN_FIELD            = "SettlementObjectId"
BUA_GRID_JOIN_FIELD       = "SettlementObjectId"

HAMLETS_JOIN_FIELD        = "SettlementObjectId"
HA_JOIN_FIELD             = "SettlementObjectId"

STATE_NAME_FIELD          = "StateName"
STATE_ID_FIELD            = "StateCode"
LGA_NAME_FIELD            = "LGAName"
LGA_ID_FIELD              = "LGACode"
WARD_NAME_FIELD           = "WardName"
WARD_ID_FIELD             = "WardCode"

BUA_ID_FIELD              = "SettlementObjectId"
BUA_NAME_FIELD            = "SettlementName"
SSA_ID_FIELD              = "SettlementObjectId"
SSA_NAME_FIELD            = "SettlementName"
HA_ID_FIELD               = "SettlementObjectId"
HA_NAME_FIELD             = "SettlementName"



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