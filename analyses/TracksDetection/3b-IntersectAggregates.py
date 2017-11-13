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

WORKSPACE     = arcpy.GetParameterAsText(0)
AGGREGATES_FC = arcpy.GetParameterAsText(1)
LINES_FC      = arcpy.GetParameterAsText(2)

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
Erase the intersection between lines and Settlements
'''
def eraseSettlementIntersect():
	erasedSettlementsFC = os.path.join(WORKSPACE,"_3b_erasedAggregatesMultipartLines")
	arcpy.Erase_analysis(in_features=LINES_FC,erase_features=AGGREGATES_FC,out_feature_class=erasedSettlementsFC,cluster_tolerance="#")

	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	currentCount=1
	
	log("Erase Settlement intersection",1)
	eraseSettlementIntersect()
	log("\t---> OK",1)
	
	
	log("Convert to multipart",1)
	outFC = os.path.join(WORKSPACE,"_3b_erasedAggregatessSinglepartLines")
	arcpy.MultipartToSinglepart_management("_3b_erasedAggregatesMultipartLines",outFC)
	log("\t---> OK",1)
	

	
	
	
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass