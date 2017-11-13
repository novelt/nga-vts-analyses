
import lib.file as fileLib
import lib.config_helper as configLib
import lib.postgis as dbLib
import lib.logger as logLib
import LibGDM as gdmLib 
import LibSteps as stepsLib 
import lib.threading_functions as threadLib

import glob
import psycopg2
import os
import subprocess
import logging
import sys
import re
from datetime import datetime
import pytz
from functools import partial

import zipfile
import logging
import Queue
import os, sys, shutil
import inspect 

#try:
#	import arcpy
#except ImportError as Ex:
#	print "Unable to import Arcpy, ESRI related functions will not work"
import multiprocessing 
from datetime import date

def step_create_work_db(currentStepNum):
	dbLib.createDatabase(cfg, dbParamsPrefix= cfg.WORK_PREFIX, 
		dropIfExists = True,
	 addPostgis= True)



	with dbLib.createDbConnectionPrefix(cfg, dbParamsPrefix= cfg.WORK_PREFIX) as conn:
		dbLib.runSqlLogErrors(baseCfg= cfg, conn= conn, sql_with_vars= '''
		
		CREATE SCHEMA IF NOT EXISTS {{WORK_SCHEMA_GEOMETRY}};
		
		''')

def step_import_boundaries():
	task_queue = Queue.Queue()

	
	for fc in [cfg.FC_Boundary_VaccLGAs, cfg.FC_Boundary_VaccWards, cfg.FC_Boundary_VaccStates]:
		task_queue.put(partial(
			dbLib.import_geometry_from_fgdb_to_postgis,
				cfg                   =cfg, 
				dbParamsPrefix        = cfg.WORK_PREFIX, 
				fgdbPath              = cfg.VTS_NIGERIA_FGDB_SOURCE_PATH, 
				tableName             =fc, 
				schemaName            =cfg.WORK_SCHEMA_GEOMETRY, 
				geomType              =cfg.GEOMETRY_TYPES[fc], 
				rowLimit              = -1, 
				reprojectToSrid       = None,
				dropTableBeforeImport =True,
				customWhereSql        =None))
	
	threadLib.finish_threads(task_queue, numItemsInQueue=3)

def step_import_settlements():

	wardCodeList = []

	

	with dbLib.createDbConnectionPrefix(cfg, dbParamsPrefix= cfg.WORK_PREFIX) as conn:
		cur = conn.cursor()

		sql = dbLib.replaceSqlTokens(cfg, '''
SELECT wardCode FROM {{WORK_SCHEMA_GEOMETRY}}.{{FC_Boundary_VaccWards}} w 
INNER JOIN {{WORK_SCHEMA_GEOMETRY}}.{{FC_Boundary_VaccLGAs}} lga ON lga.lgacode = w.lgacode
WHERE lga.statecode IN (%(stateCodeList)s)

		''')

		cur.execute(sql, {'stateCodeList': tuple(cfg.SOURCE_STATE_CODES) })

		results = cur.fetchall()

		wardCodes = [ "'%s'" % rec[0] for rec in results]

	task_queue = Queue.Queue()

	for fc in [cfg.FC_FE_HamletAreas, cfg.FC_FE_SmlSettlementAreas, cfg.FC_FE_BuiltUpArea]:
		task_queue.put(partial(
		dbLib.import_geometry_from_fgdb_to_postgis,
				cfg                   = cfg, 
				dbParamsPrefix        = cfg.WORK_PREFIX, 
				fgdbPath              = cfg.VTS_NIGERIA_FGDB_SOURCE_PATH, 
				tableName             = fc, 
				schemaName            = cfg.WORK_SCHEMA_GEOMETRY, 
				geomType              = cfg.GEOMETRY_TYPES[fc], 
				rowLimit              = -1, 
				reprojectToSrid       = None,
				dropTableBeforeImport = True,
				customWhereSql        = 'wardCode IN (%s)' % ', '.join(wardCodes)
		))

	threadLib.finish_threads(task_queue, numItemsInQueue=3)

def step_import_tracks():

	dbLib.transfer_table_between_postgis_db_with_query(
		cfg = cfg, 
		fromDbPrefix = cfg.TRACKS_SOURCE_PREFIX, 
		toDbPrefix = cfg.WORK_PREFIX, 
		sourceQuery = "select row_number() over() as id, 
		destSchemaName, destTableName, 
		rowLimit = -1, dropTableBeforeTransfer=True,