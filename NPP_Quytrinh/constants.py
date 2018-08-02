# milestone 10/7/2014 (20140710) as first day in period 
JULIAN_MOCK = 2456945

# home directory of program
HOME_DIR = "/var/www/html/NPP_Quytrinh/"

# constant log filename
LOG_FILE = HOME_DIR + "log.txt"

# home directory of data
HOME_DIR_AOT_ORG_DATA = "/apom_data/apom/org/SatOrgVIIRSAOT/"
HOME_DIR_AOT_RESAMPLE_DATA = "/apom_data/apom/res/SatResampleViirsAOT/"

HOME_DIR_LST_ORG_DATA = "/apom_data/apom/org/SatOrgVIIRSTemp/"
HOME_DIR_LST_RESAMPLE_DATA = "/apom_data/apom/res/SatResampVIIRSTemp/"

# bounding coordinate Viet Nam for resample
NORTH = 25.6
SOUTH = 6.4
EAST = 111.8
WEST = 100.1

# bounding coordinate Viet Nam for check image
VN_NORTH = 23.392
VN_SOUTH = 8.563
VN_EAST = 109.469
VN_WEST = 102.145

# server database
#HOST = "118.70.72.13"
#PORT = 8100
#DBNAME = "apom"
#USERNAME = "postgres"
#PASSWORD = "fimopostgre54321"

HOST = "192.168.0.61"
PORT = 5432
DBNAME = "apom"
USERNAME = "postgres"
PASSWORD = "fimopostgre54321"

# band to resample
BAND = 550

# table database
AOT_RES = "res.satresampviirs"
AOT_ORG = "org.satorgviirsaot"

LST_RES = "res.satresampviirstemperature"
LST_ORG = "org.satorgviirstemperature"

# satellite pass time
MORNING_PASS = "05300545"


# ftp server parameters
BASE_URL = "ftp://ftp-npp.class.ngdc.noaa.gov"  
VIIRS_EDR = "VIIRS-EDR"
AOT_DIR = "VIIRS-Aerosol-Optical-Thickness-AOT-EDR" 
GEO_AOT_DIR = "VIIRS-Aerosol-Aggregated-EDR-Ellipsoid-Geo" 
AOT_NAME = "VIIRS-EDR_VIIRS-Aerosol-Optical-Thickness-AOT-EDR" 
GEO_AOT_NAME = "VIIRS-EDR_VIIRS-Aerosol-Aggregated-EDR-Ellipsoid-Geo"

LST_DIR = "VIIRS-Land-Surface-Temperature-EDR"
GEO_LST_DIR = "VIIRS-Land-Surface-Temperature-EDR/VIIRS-Moderate-Bands-SDR-Terrain-Corrected-Geo"
LST_NAME = "VIIRS-EDR_VIIRS-Land-Surface-Temperature-EDR"
GEO_LST_NAME = "VIIRS-SDR_VIIRS-Moderate-Bands-SDR-Terrain-Corrected-Geo"

# scale/factor
AOT_SCALE = 1.6786973E-4
AOT_FACTOR = -1.0

LST_SCALE = 0.0025455155
LST_FACTOR = 183.2

# grid parameters
GRID_ID_VIIRS = 2
PROJECTION = 4326


