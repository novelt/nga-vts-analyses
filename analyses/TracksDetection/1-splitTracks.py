# ------------------------------------------------------------
# Name:    1-splitTracks.py
# Purpose: ...
# Author:    Novel-T
# Created:   18.07.2014
# Modified:  15.08.2014
# Copyright: (c) Novel-T
#
# ArcGIS Version: 10.1
# Python Version: 2.7
# ------------------------------------------------------------

import arcpy
from sets import Set
import os
import operator
import sys

# overwrite output if existing
arcpy.env.overwriteOutput = True

	
# ------------------------------------------------------------
# Script Parameters
# ------------------------------------------------------------
AGGREGATE_LEVEL   = "LGA"
INPUT_TRACKS      = arcpy.GetParameterAsText(0)


INPUT_TRACKS_LAYER = INPUT_TRACKS+"_layer"

fieldTeamCode = "TeamCode"
fieldCampaignDay = "CampaignDay"
fieldDiff = "Diff_Timestamp"
sortField = "TimeStamp"
speedLimit = 0
buff_distance = "5 Meters"


teamCodes = [row[0] for row in arcpy.da.SearchCursor(INPUT_TRACKS, (fieldTeamCode), "{0} is not null".format(fieldTeamCode))]
uniqueTeamCodes = set(teamCodes)

arcpy.AddMessage("Nb teamCodes: {0}".format(len(uniqueTeamCodes)))
count=1
bufferedFCs = []
id=0
for teamCode in uniqueTeamCodes:
	arcpy.AddMessage("TeamCodes: #{0}/{1}".format(count,len(uniqueTeamCodes)))
	count = count+1
	id = id+1
	
	arcpy.AddField_management(INPUT_TRACKS, fieldDiff, "LONG")
	arcpy.MakeFeatureLayer_management(INPUT_TRACKS, INPUT_TRACKS_LAYER+"_"+teamCode, "{0}='{1}' and Speed>{2} and isReal=1".format(fieldTeamCode,teamCode, speedLimit))
	
	prev_track = None
	with arcpy.da.UpdateCursor(INPUT_TRACKS_LAYER+"_"+teamCode,[fieldDiff,fieldTeamCode,fieldCampaignDay,sortField]) as track_cursor:
		#sorted_Tracks = sorted(track_cursor, key=operator.itemgetter(3))
		for track in track_cursor:
			if(prev_track is None):
				#do nothing
				prev_track = track
				track[0] = id
				track_cursor.updateRow(track)
			else:
				prev_timestamp = prev_track[3]
				currentTimestamp = track[3]
				diff = currentTimestamp-prev_timestamp
				if(diff.total_seconds()>240):
					id = id+1
				track[0] = id
				track_cursor.updateRow(track)
				prev_track = track
				
	
	arcpy.PointsToLine_management(INPUT_TRACKS_LAYER+"_"+teamCode,INPUT_TRACKS+"_"+teamCode.replace(" ", "")+"_PtL",fieldDiff,sortField)
	POINTS_TO_LINE_LAYER = "PtL_Layer_"+teamCode.replace(" ", "")
	arcpy.MakeFeatureLayer_management(INPUT_TRACKS+"_"+teamCode.replace(" ", "")+"_PtL", POINTS_TO_LINE_LAYER)
	arcpy.Buffer_analysis(POINTS_TO_LINE_LAYER, INPUT_TRACKS+"_"+teamCode.replace(" ", "")+"_Buff", buff_distance, "FULL", "FLAT")
	bufferedFCs.append(INPUT_TRACKS+"_"+teamCode.replace(" ", "")+"_Buff")
	
arcpy.AddMessage("Merging...")
arcpy.Merge_management(bufferedFCs, INPUT_TRACKS+"_Merged")
	