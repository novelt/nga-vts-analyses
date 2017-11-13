
import arcpy
import os, sys
import re
import glob, datetime

arcpy.AddMessage("Starting...")
mxd = arcpy.mapping.MapDocument("CURRENT")
dataFrame = arcpy.mapping.ListDataFrames(mxd, "*")[0]

stateCodes = ['AB', 'AD', 'AK', 'AN', 'BA', 'BE', 'BR', 'BY', 'CR', 'DE', 'EB', 'ED', 'EK', 'EN', 'FC', 'GO', 'IM', 'JI', 'KB', 'KD', 'KN', 'KO', 'KT', 'KW', 'LA', 'NA', 'NI', 'OG', 'ON', 'OS', 'OY', 'PL', 'RI', 'SO', 'TA', 'YO', 'ZA']

stateNames = ['Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Benue', 'Borno', 'Bayelsa', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Fct, Abuja', 'Gombe', 'Imo', 'Jigawa', 'Kebbi', 'Kaduna', 'Kano', 'Kogi', 'Katsina', 'Kwara', 'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara']

groupLayerNames = []

for index, stateCode in enumerate(stateCodes):
	stateName = stateNames[index]
	#arcpy.AddMessage("Creating name " + stateCode)

	groupLayerName = stateName + " (" + stateCode + ")"
	
	#Create a group layer 
	#groupLayer = arcpy.mapping.Layer(r"D:\temp\EmptyGroup.lyr")
	#groupLayer.name = stateName + " (" + stateCode + ")"
	#arcpy.mapping.AddLayer(dataFrame, groupLayer, "BOTTOM")
	
	groupLayerNames.append(groupLayerName)

#arcpy.RefreshTOC()

layerList = arcpy.mapping.ListLayers(mxd, "", dataFrame)

symbologyLayer = None 

for layer in layerList:
	if layer.name == "VTS Denominators styles":
		symbologyLayer = layer 
		arcpy.AddMessage("Setting symbology layer")
		


for layer in layerList:
	arcpy.AddMessage("Found layer " + layer.name)
	
	if layer.name in groupLayerNames:
		#arcpy.AddMessage("Adding denom layer")
		#denomLayer = arcpy.mapping.Layer(r"D:\git\vts\src\analyses\CMSLDenominatorAnalysis\EsriMxdScripts\Denom.lyr")
		#arcpy.mapping.AddLayerToGroup(dataFrame, layer, denomLayer, "BOTTOM")
		
		arcpy.AddMessage("Getting denom layer")
		subLayers = arcpy.mapping.ListLayers(layer)
		
		stateCode = re.match('.*\((.*)\)', layer.name).group(1)
		
		for subLayer in subLayers:
			arcpy.AddMessage("Sub layer name: " + subLayer.name)
			if subLayer.supports("DATASOURCE"):
				arcpy.AddMessage("Data source: " + subLayer.dataSource)
				correctDataSource = r"D:\dropbox-novel-t\Dropbox (Novel-T Sarl)\Novel-T -ext- BMGF-NGA-VTS\Chronically Missed Denominator Analysis\data_" + stateCode + r".gdb\vts_denominators"
				
				correctDataSourceGdb = r"D:\dropbox-novel-t\Dropbox (Novel-T Sarl)\Novel-T -ext- BMGF-NGA-VTS\Chronically Missed Denominator Analysis\data_" + stateCode + r".gdb"
				
				if subLayer.dataSource != correctDataSource:
					arcpy.AddMessage("Correcting data source from \n" + subLayer.dataSource + " to \n" + correctDataSource + "\nin DataSet\n" + subLayer.datasetName)
					
					subLayer.replaceDataSource(correctDataSourceGdb, 'FILEGDB_WORKSPACE', subLayer.datasetName, True)
					
				arcpy.ApplySymbologyFromLayer_management (subLayer, symbologyLayer)
			else:
				arcpy.AddMessage("No Data source.")
			


arcpy.AddMessage("Done.")

del mxd 