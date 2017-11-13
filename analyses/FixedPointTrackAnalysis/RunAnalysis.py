
import ConfigAll
import ConfigTrackAnalysis

#Step definitions
import StepsTrackAnalysis

import importlib
import os
import sys
import logging

#Novel-T Lib includes
import lib.config_helper as configLib
import lib.logger as logLib
import lib.email_functions as emailLib
import lib.postgis as dbLib
import LibSteps 
from LibSteps import runStep


cfg = configLib.setupCfgObjectFromModules(ConfigAll, ConfigTrackAnalysis)

setattr(StepsTrackAnalysis,  'cfg', cfg)
setattr(LibSteps,  'cfg', cfg)


# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------
def GeoDataManagementProcess(startStep, endStep):
	
	'''
	After checkout has been updated, this script will run 
	the steps required to update the VTS publication database
	on the abuja server.

	AFter its completion, the abuja script needs to be run to 
	update the EOC Publication database.
	'''
	
	currentStepNum = 0

	# May not be needed

	#currentStepNum = runStep(currentStepNum, 
	#	startStep, endStep, "In Nigeria Master PostGIS Db: Change settlement globalid back to character varying", 
	#	StepsKano.step_change_globalid_columns_to_varchar)

	
	
	###Novel-T steps
	currentStepNum = runStep(currentStepNum, 
		startStep, endStep, "Creating work Postgis db", 
		StepsTrackAnalysis.step_create_work_db)


	currentStepNum = runStep(currentStepNum, 
		startStep, endStep, "Import Boundaries to work Postgis db", 
		StepsTrackAnalysis.step_import_boundaries)

	currentStepNum = runStep(currentStepNum, 
		startStep, endStep, "Import settlements to work Postgis db", 
		StepsTrackAnalysis.step_import_settlements)



# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------

if __name__ == '__main__': 
	
	
	# Init logger
	#log = logLib.InitLogger(cfg.LogPath)
	log = logLib.buildLog(None, 
	consoleLevel = logging.INFO, 
	fileLevel = logging.DEBUG, 
	logFile = cfg.LogPath,
	logFormatStr="%(asctime)s %(filename)s:%(lineno)d %(levelname)s %(name)s ==> %(message)s\n")

	logger = log 

	# Given script parameters
	startStep = int(sys.argv[1])

	try:
		endStep = int(sys.argv[2])
	except: 
		endStep = 45
	
	log.info('Start python script with parameters: ' + ' '.join(sys.argv))
		
	GeoDataManagementProcess(startStep, endStep)
