# ------------------------------------------------------------
# Name:    0-CleanTracks.py
# Purpose: Given a list of tracks FC, it join the points into polylines with an algo that determines whether the track is valid or not
#
# Author:    YM
# Created:   10.02.2015
# Modified:  19.02.2015
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

TRACKS_LAYERS     = arcpy.GetParameterAsText(0)
WORKSPACE         = arcpy.GetParameterAsText(1)

CREATE_INVALID_OUTPUT = False
CREATE_VALID_OUTPUT   = True


CAMPAIGN_DAY_FIELD = "CampaignDay"
TEAM_ID_FIELD      = "TeamID"
SPEED_FIELD        = "Speed"
ISREAL_FIELD       = "IsReal"
TIMESTAMP_FIELD    = "TimeStamp"
ACCURACY_FIELD     = "Accuracy"
ACCURACY_THRESHOLD = 50
MAX_SPEED_ALLOWED  = 35 #35 m/s = 126 km/h

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
Draws a line for each track
PARAMS:
	- tracks: The FeatureClass containing the tracks
'''
def drawRawLines(trackFC):
	split = trackFC.split('_')
	CAMPAIGN_ID = int(split[len(split)-1])
	
	#Get the list of CampaignDays and list of Teams
	results = arcpy.da.SearchCursor(trackFC, (TIMESTAMP_FIELD,SPEED_FIELD,CAMPAIGN_DAY_FIELD,TEAM_ID_FIELD, "SHAPE@XY",ISREAL_FIELD,ACCURACY_FIELD, "OID@"), "{0}>0".format(CAMPAIGN_DAY_FIELD))
	resultTracks = list(results)
	campaignDayValues = [row[2] for row in resultTracks]
	listOfCampaignDays = sorted(set(campaignDayValues))
	teamValues = [row[3] for row in resultTracks]
	listOfTeams = set(teamValues)
	
	
	polylineList = []
	
	for campaignDay in listOfCampaignDays:
		log("\tCampaignDay {0}".format(campaignDay),2)
		resultTracksPerDay = filter(lambda x: x[2] == campaignDay, resultTracks)
		for teamId in listOfTeams:
			resultTracksPerDayAndTeam = filter(lambda x: x[3] == teamId, resultTracksPerDay)
			sortedTrackPoints =  sorted(resultTracksPerDayAndTeam, key=lambda track: track[0])
				
			if(len(sortedTrackPoints)>0):
				
				#log("sortedTrackPoints: {0}".format(sortedTrackPoints),3)
				prevTrack = None
				count = 1;
				arrayOfPoints = arcpy.Array()
				for trackPoint in sortedTrackPoints:
				
					ts     = trackPoint[0]
					#log("Point: {0}".format(trackPoint[7]),3)
					#if previous track exist
					if(prevTrack is not None):
						#log("1 -prevTrack not null",3)
						#get TimeStamp diff in seconds
						current_ts = time.mktime(ts.timetuple())
						prev_ts = time.mktime(prevTrack[0].timetuple())
						ts_diff = int(current_ts-prev_ts)
						
						if(ts_diff > 180):
							#log("2-diff ts > 180, create new Line",3)
							polyline = arcpy.Polyline(arrayOfPoints)
							storePolyline(teamId,campaignDay,CAMPAIGN_ID,ts,polyline)
							arrayOfPoints = arcpy.Array()
							
							validity = isValid(None, trackPoint)
							if(validity == "OK"):
								#log("2.1-Valid",3)
								point = arcpy.Point()
								point.X = trackPoint[4][0]
								point.Y = trackPoint[4][1]							
								pointGeometry = arcpy.PointGeometry(point,arcpy.SpatialReference(4326))
								pointGeometry2 = pointGeometry.projectAs(arcpy.SpatialReference(102100))
								arrayOfPoints.add(pointGeometry2.centroid)
								storeValidPoint(trackPoint,CAMPAIGN_ID)
								prevTrack = trackPoint
							else:
								storeInvalidPoint(trackPoint,CAMPAIGN_ID,validity)
								prevTrack = None
								#log("2.2-Invalid",3)
						else:
							#If track is valid
							validity = isValid(prevTrack, trackPoint)
							if(validity == "OK"):
								#log("3-isValid",3)
								point = arcpy.Point()
								point.X = trackPoint[4][0]
								point.Y = trackPoint[4][1]		
								pointGeometry = arcpy.PointGeometry(point,arcpy.SpatialReference(4326))
								pointGeometry2 = pointGeometry.projectAs(arcpy.SpatialReference(102100))
								arrayOfPoints.add(pointGeometry2.centroid)
								
								storeValidPoint(trackPoint,CAMPAIGN_ID)
								
								if(count == len(sortedTrackPoints)):
									#log("3.1-create polyline ({0})".format(arrayOfPoints.count),3)
									polyline = arcpy.Polyline(arrayOfPoints)
									storePolyline(teamId,campaignDay,CAMPAIGN_ID,ts,polyline)
									prevTrack = None
									arrayOfPoints = arcpy.Array()
								else:
									#log("3.2-continue",3)
									prevTrack = trackPoint
								
							else:
								storeInvalidPoint(trackPoint,CAMPAIGN_ID,validity)
								#log("4-is NOT Valid",3)
								polyline = arcpy.Polyline(arrayOfPoints)
								storePolyline(teamId,campaignDay,CAMPAIGN_ID,ts,polyline)
								prevTrack = None
								arrayOfPoints = arcpy.Array()
							
					else:
						validity = isValid(None, trackPoint)
						if(validity == "OK"):
							
							#log("5-isValid",3)
							point = arcpy.Point()
							point.X = trackPoint[4][0]
							point.Y = trackPoint[4][1]		
							pointGeometry = arcpy.PointGeometry(point,arcpy.SpatialReference(4326))
							pointGeometry2 = pointGeometry.projectAs(arcpy.SpatialReference(102100))
							arrayOfPoints.add(pointGeometry2.centroid)
							storeValidPoint(trackPoint,CAMPAIGN_ID)
							prevTrack = trackPoint
						else:
							storeInvalidPoint(trackPoint,CAMPAIGN_ID,validity)
							#log("6-is NOT Valid",3)
							prevTrack = None
					
					count = count+1
			del resultTracksPerDayAndTeam
			del sortedTrackPoints
		del resultTracksPerDay
	del results
	del resultTracks
	del campaignDayValues
	del listOfCampaignDays
	del teamValues
	del listOfTeams
	

'''
Stores a clean polyline in the result FC
PARAMS:
	- teamId: the id of the team for the track
	- campaignDay: the day in the campaign for the track
	- campaignId: the id of the campaign
	- ts: the timestamp of the last point in the track
	- polyline: the shape of the track
'''	
def storePolyline(teamId,campaignDay,CAMPAIGN_ID,ts,polyline):
	c = arcpy.da.InsertCursor("_0_cleanTracksLines",("TeamID", "CampaignDay", "CampaignID", "TimeStamp", "Source", "SHAPE@")) 
	c.insertRow([teamId,campaignDay,CAMPAIGN_ID,ts, "VTS", polyline])
	del c
	log("store line: {0} - {1} - {2} - {3}".format(teamId,campaignDay,CAMPAIGN_ID,ts),3)
	
	
	
'''
Stores the invalid point with the reason
PARAMS: 
	- trackPoint: the invalidPoint to store
	- campaignId: the id of the campaign
	- reason: The reason for invalidity
'''
def storeInvalidPoint(trackPoint, campaignId, reason):
	if(CREATE_INVALID_OUTPUT):
		#TrackPoint: (TIMESTAMP_FIELD,SPEED_FIELD,CAMPAIGN_DAY_FIELD,TEAM_ID_FIELD, "SHAPE@XY",ISREAL_FIELD,ACCURACY_FIELD, "OID@")
		teamId      = trackPoint[3]
		campaignDay = trackPoint[2]
		timeStamp   = trackPoint[0]
		pointOID    = trackPoint[7]
		shape       = trackPoint[4]
		
		c = arcpy.da.InsertCursor("_0_invalidPoints",("TeamID", "CampaignDay", "CampaignID", "TimeStamp", "PointOID","Reason", "SHAPE@")) 
		c.insertRow([teamId,campaignDay,campaignId,timeStamp,pointOID,reason, shape])
		del c
	
	
	
'''
Stores the valid point with the reason
PARAMS: 
	- trackPoint: the invalidPoint to store
	- campaignId: the id of the campaign
'''
def storeValidPoint(trackPoint, campaignId):
	if(CREATE_VALID_OUTPUT):
		#TrackPoint: (TIMESTAMP_FIELD,SPEED_FIELD,CAMPAIGN_DAY_FIELD,TEAM_ID_FIELD, "SHAPE@XY",ISREAL_FIELD,ACCURACY_FIELD, "OID@")
		speed       = trackPoint[1]
		teamId      = trackPoint[3]
		campaignDay = trackPoint[2]
		timeStamp   = trackPoint[0]
		pointOID    = trackPoint[7]
		shape       = trackPoint[4]
		
		c = arcpy.da.InsertCursor("_0_mergedValidPoints",("TeamID", "CampaignDay", "CampaignID", "TimeStamp", "PointOID", "Speed", "SHAPE@")) 
		c.insertRow([teamId,campaignDay,campaignId,timeStamp,pointOID, speed, shape])
		del c
	
	


'''
Returns	 true if the current track is valid, false otherwise
PARAMS:
	- prevTrack: The previous track
	- currentTrack: The current track
'''
def isValid(prevTrack, currentTrack):
	isReal   = currentTrack[5]
	accuracy = currentTrack[6]
	speed    = currentTrack[1]
	ts       = currentTrack[0]
	oid      = currentTrack[7]
	
	isSpeedValid = (speed < MAX_SPEED_ALLOWED)
	avgSpeedValid = True
	
	if(prevTrack != None):
		prevSpeed = prevTrack[1]
		
		prevPoint = arcpy.Point()
		prevPoint.X = prevTrack[4][0]
		prevPoint.Y = prevTrack[4][1]
		prevPointGeometry = arcpy.PointGeometry(prevPoint,arcpy.SpatialReference(4326))
		prevPointGeometry2 = prevPointGeometry.projectAs(arcpy.SpatialReference(102100))
		
		currentPoint = arcpy.Point()
		currentPoint.X = currentTrack[4][0]
		currentPoint.Y = currentTrack[4][1]
		currentPointGeometry = arcpy.PointGeometry(currentPoint,arcpy.SpatialReference(4326))
		currentPointGeometry2 = currentPointGeometry.projectAs(arcpy.SpatialReference(102100))
		
		distance = currentPointGeometry2.distanceTo(prevPointGeometry2)
		log("distance: {0}".format(distance),3)
		maxSpeed = max(speed, prevSpeed)
		theoreticalSpeed = distance/120
		avgSpeedValid = (theoreticalSpeed < MAX_SPEED_ALLOWED) #41 m/s = 147 km/h
		log("theoreticalSpeed: {0} - maxSpeed: {1}".format(theoreticalSpeed,maxSpeed),3)
		
	log("isReal: {0} - accuracy: {1} - speedValid: {2} - avgSpeed: {3}".format(isReal,accuracy,isSpeedValid,avgSpeedValid),3)
	
	if(isReal == 0):
		return "ISNOTREAL"
	elif(accuracy >= ACCURACY_THRESHOLD):
		return "INACCURATE"
	elif isSpeedValid != True:
		return "INVALIDSPEED"
	elif avgSpeedValid != True:
		return "INVALIDAVGSPEED"
	else:
		return "OK"


		
'''
Creates the output FC that will store the polylines
'''
def createOutputFC():
	geometry_type = "POLYLINE"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_0_cleanTracksLines", geometry_type, "", "", "", arcpy.SpatialReference(102100))
	outFC = os.path.join(WORKSPACE,"_0_cleanTracksLines")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "Source", "TEXT")
	arcpy.AddField_management(outFC, "SourceID", "TEXT")

	

'''
Creates the output FC that will store the invalid points
'''
def createInvalidPointFC():
	geometry_type = "POINT"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_0_invalidPoints", geometry_type, "", "", "", arcpy.SpatialReference(4326))
	outFC = os.path.join(WORKSPACE,"_0_invalidPoints")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "PointOID", "LONG")
	arcpy.AddField_management(outFC, "Reason", "TEXT")
	

	
'''
Creates the output FC that will store the valid points
'''
def createValidPointFC():
	geometry_type = "POINT"
	arcpy.CreateFeatureclass_management(WORKSPACE, "_0_mergedValidPoints", geometry_type, "", "", "", arcpy.SpatialReference(4326))
	outFC = os.path.join(WORKSPACE,"_0_mergedValidPoints")
	arcpy.AddField_management(outFC, "TeamID", "TEXT")
	arcpy.AddField_management(outFC, "CampaignDay", "SHORT")
	arcpy.AddField_management(outFC, "CampaignID", "SHORT")
	arcpy.AddField_management(outFC, "TimeStamp", "DATE")
	arcpy.AddField_management(outFC, "PointOID", "LONG")
	arcpy.AddField_management(outFC, "Speed", "FLOAT")
	
	
	
# ------------------------------------------------------------
# ------------------------------------------------------------
# Main script
# ------------------------------------------------------------
# ------------------------------------------------------------
def main():
	
	tracksFC = TRACKS_LAYERS.split(';')
	currentCount=1
	
	if(CREATE_INVALID_OUTPUT):
		createInvalidPointFC()
		
	if(CREATE_VALID_OUTPUT):
		createValidPointFC()
		
	createOutputFC()
	
	for tracks in tracksFC:
		log("Cleaning Tracks ({0}/{1})...".format(currentCount,len(tracksFC)),1)
		drawRawLines(tracks)
		log("  -> OK...",1)
		currentCount = currentCount+1
	
	
	
	
if __name__ == "__main__":
    try:
        main()
    except SystemExit as err:
        pass