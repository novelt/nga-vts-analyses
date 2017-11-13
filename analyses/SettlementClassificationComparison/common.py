import os

BASE_DIR = r"D:\git\vts\src\esri\scripts\SettlementClassificationComparison"
RASTER_DIR = os.path.join(BASE_DIR, "rasters")

ETALLY_FGDB = os.path.join(BASE_DIR, r"etallyRaster.gdb")

ETALLY_TABLE = os.path.join(ETALLY_FGDB, "vts_tally_fact")
ETALLY_WARD_MULTI_TABLE = os.path.join(ETALLY_FGDB, "etally_ward_multi")
UNDER5_POP_TABLE = os.path.join(ETALLY_FGDB, "under5_pop")
ETALLY_POP_TABLE = os.path.join(ETALLY_FGDB, "etally_pop")


NIGERIA_TOTAL_POP_RASTER = os.path.join(RASTER_DIR, r"total_90by90.tif")
NIGERIA_TOTAL_POP_CLIPPED_RASTER = os.path.join(RASTER_DIR, r"total_90by90_clipped.tif")

NIGERIA_UNDER5_POP_RASTER = os.path.join(RASTER_DIR, r"under5_90by90.tif")
NIGERIA_UNDER5_POP_CLIPPED_RASTER = os.path.join(RASTER_DIR, r"under5_90by90_clipped.tif")
NIGERIA_UNDER5_POP_FILTERED_RASTER = os.path.join(RASTER_DIR, r"under5_90by90_clipped_filtered.tif")


ETALLY_RASTER = os.path.join(RASTER_DIR,r"etally_raster.tif")
ETALLY_RASTER_NODATA = os.path.join(RASTER_DIR,r"etally_raster_nodata.tif")

ETALLY_WITH_NO_POP = os.path.join(RASTER_DIR,r"etally_no_pop.tif")
ETALLY_WITH_NO_POP_NODATA = os.path.join(RASTER_DIR,r"etally_no_pop_nodata.tif")

POP_WITH_NO_ETALLY = os.path.join(RASTER_DIR,r"pop_no_etally.tif")
POP_WITH_NO_ETALLY_NODATA = os.path.join(RASTER_DIR,r"pop_no_etally_nodata.tif")

def needs_to_be_created(filename) :
    
    if os.path.isfile(filename):
        print (filename + " already exists")
        return False
    else :
        print (filename + " does NOT exist, creating...")
        return True
    
def remove_file(filename):
    if os.path.isfile(filename) :
        print("Deleting " + filename)
        
        os.remove(filename)
    else :
        print(filename + " is not a file")