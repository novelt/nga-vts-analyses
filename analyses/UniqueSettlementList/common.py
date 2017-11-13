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

LOG_LEVEL          = 3 #0:None / 1=Important / 2: INFO / 3:DEBUG



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
	
	
def FieldExist(featureclass, fieldname):                  # check if a field is in a feature class - based on Bjorn Kuiper
	fieldList = arcpy.ListFields(featureclass, fieldname)
	fieldCount = len(fieldList)
	
	if (fieldCount == 1):
		return True
	else:
		return False
	
	