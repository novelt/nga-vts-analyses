# Versions

2.1

eligible children  = (away + non compliant - already vacc + vacc) + outside

no revisits

2.2 

Changed as we want pop in a denominator so not looking at outside vaccinations

eligible children = (away + non compliant + already vacc + vacc) - outside

no revisits

2.3 

eligible children = (away + non compliant + already vacc + vacc) - outside

no revisits

Using new population generated on 2016-05-17


# Approach


Basically, a seperate db is created (named pop) with the zonal stats tables copied from nigeria_master_checkout after the population step has been launched (on a FGDB, not an sql server)

## Files

### ToPostGis.bat 

Used to import the FGDB.

Then, the geometry tables (4326) were imported to the pop database using the <Geom>.bat files from the geometry import scripts.  See https://github.com/novelt/nga-gis-vts/blob/ward_teams_analysis_map/src/Database/ScriptGenerator/build_geometry_scripts.bat

### xfer_db_table.bat

Used to import a couple tables like vts_dim_settlements and vts_campaigns from the stage db (which is assumed to be a copy of prod)

### ETallyPop.sql

All the scripts here.  This script creates a table,

public.pop_comparison

which contains the values per settlement

There is also a helper table used for HA's called pop_ha_helper

The reason behind this table is to there is too much population in the HA that are not in any hamlets.  This is seen by the adjusted hamlet populations being up to 300%.

So, to calcuate the Hamlet pop, we do a mini ajdustment, taking the proportion of hamlet population / total unadjusted hamlet population and multiplying that by the total unajdusted HA population.

### PopulationAnalysis_v2.0

On dropbox D:\dropbox-novel-t\Dropbox (Novel-T Sarl)\Novel-T Projects\BMGF - NGA - VTS\06 - Deliverables\Analyses\eTally Population

This xls imports the pop_comp CSV created from ETallyPop using a connection.  Refreshing the connection should prompt for the CSV.

### GenerateCompRasters.py

Has some functions used.

* get_etally_data -- Have an FGDB Tally.fgdb containing the projected postgis.vts_tally_fact table to 4326
* generate_near_table -- Generates near table with nigeria fgdbs geometry and the etally_raw_table imported with get_etally_data
* export_neartable_to_pop_postgis -- Exports near table to pop postgis db
* export_raw_etally_table -- Exports raw etally table because neartable links to esri generated objectids


## Databases Used

* Nigeria FGDB - Copy of latest geometry
* Tally FGDB - Work FGDB to calculate near table
* FGDB nigeria master checkout used to generate pop -- Source of the zonal stat tables to get unadjusted population values
* Postgis db "Pop" -- work postgis DB to rassemble geometry tables, zonal stats tables to export final analysis


# Step By Step procedure

1. Create a database pop with the latest geometry in the postgis schema 

Use the backup here as a template -- \\nas\Projects\NGA-GIS-VTS\Data\Population\Zonal Stats and Rasters for 1.25 Geometry\Database for eTally pop analysis - 2.2

Update the geometry in the postgis schema 

Update the population table 

In 
D:\git\vts\src\Database\Geometry Import Scripts

Set environment variables

SET POSTGRESQL_HOME=C:\Program Files\PostgreSQL\9.5
SET GDAL_HOME=D:\OSGeo4W64\bin

rem SET MASTER_FGDB=D:\work\pop\VTS_ZonalStats_1_24_NIGERIA\VTS_NIGERIA.gdb
SET MASTER_FGDB=D:\git\vts\src\Database\Geometry Data\VTS_NIGERIA.gdb

SET DATABASE_NAME=pop
SET POSTGRESQL_CONNECTION_INFO=--host=localhost --port=5434 --username=postgres
SET GDAL_DATABASE_CONNECTION_INFO=host=localhost port=5434 dbname=%DATABASE_NAME% user=postgres password=postgres


cd %~d0
cd %~dp0

SET SCRIPT_DIR=.



vts_gpreflyrssabuffers.bat 
FE_SmlSettlementAreas.bat 

vts_gpreflyrbuagrids.bat 
fe_builtUpArea.bat 

VTS_GPRefLyrHABuffers.bat 
FE_HamletAreas.bat 

boundary_vaccstates.bat
boundary_vacclgas.bat 
boundary_vaccwards.bat

vts_populationEstimates.bat 

Run xfer_db_table to pick up some needed VTS tables 


Copy the zonal stats from the FGDB used to caluclate the pop.

2. Create an FGDB for the eTally near table 

Use the toolbox function get_etally_data to import/create this.  

Check paths in variables of GenerateCompRasters.py 

Lots of dead code for checking rasters directly

Comment out functions as needed in main function 

Run GenerateCompRasters.bat to generate / export near table 

Result will be TallyNearTable in pop postgis database

* 

Also need to import the etally_raw_table table because the near table uses the ESRI generated objectid 

it's the export_raw_etally_table function 
