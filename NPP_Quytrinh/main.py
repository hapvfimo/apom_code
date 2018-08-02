import os
import sys
import datetime
from datetime import datetime as dt
from resample import ResampleNPP
from load_file_from_ftp import LoadFileFTP
from filter_data import FilterFile
from hdf_factory import HdfFactory
from postgres_server import Server
from utilities import *
from constants import *

pmnpp = "/var/www/html/NPP_Quytrinh/NPPAodToPm.R"

# change cur dir to home dir and create log file
#os.chdir(HOME_DIR)
if not os.path.exists(LOG_FILE):
	open(LOG_FILE, 'a').close()
	os.chmod(LOG_FILE, 0775)

# load aot/geo data file (aot or geolocation)
def LoadDataGeoFiles(ftp, fter, tdata, date, counter = 0):
	while True:
		count = AddCount(counter)
		status_load_xml = ftp.LoadFile(count, tdata, "xml")
		if status_load_xml == 0:
			return counter
		# check covering area and download file if it's covering region is match
		print status_load_xml
		status_check_data = fter.FilterFileByName(status_load_xml, date)
		if status_check_data == 1:
			status_load_data = ftp.LoadFile(count, tdata, "data")
			if status_load_data == 0:
				return counter
		if status_check_data == 0:
			if os.path.isfile(status_load_xml):
				os.remove(status_load_xml)
		counter = counter + 1
		if counter > 15:
			return 0
	return 0

# download AOT data
def DownloadAOTByDay(date):
	# preprocessing phase
	count_aot = 0
	count_geo = 0
	ftp = LoadFileFTP(date = date, log = LOG_FILE)
	fter = FilterFile(LOG_FILE)	

	# load aot files
	count_aot = LoadDataGeoFiles(ftp, fter, "aot", date, counter = 0)
	# load geolocation file
	count_geo = LoadDataGeoFiles(ftp, fter, "aot_geo", date, counter = 0)
	if count_aot != count_geo:
		return 1
	return 0

# download land surface temperature data
def DownloadLSTByDay(date):
	count_lst = 0
	count_geo = 0
	ftp = LoadFileFTP(date = date, log = LOG_FILE, base_url = BASE_URL, viirs = VIIRS_EDR, base_url_data = LST_DIR, base_url_geo = GEO_LST_DIR, data_name = LST_NAME, geo_name = GEO_LST_NAME)
	fter = FilterFile(LOG_FILE)

	# load lst files
	count_lst = LoadDataGeoFiles(ftp, fter, "lst", date, counter = 0)
	# load geolocation files
	count_geo = LoadDataGeoFiles(ftp, fter, "lst_geo", date, counter = 0)
	if count_aot != count_geo:
		return 1
	return 0

# download data
def DownloadData(date):
	if not os.path.exists(date):
    		os.makedirs(date)
		os.chmod(date, 0777)
	os.chdir(date)
	#download_status1 = DownloadAOTByDay(date)
	download_status1 = 0
	download_status2 = DownloadLSTByDay(date)
	if download_status1 == 1 or download_status2 == 1:
		return 1
	return 0

# download, resample and processing AOT
def ProcessingSatelliteImgNOAA(date, workdir, saveorgaot, saveresaot, saveorglst, savereslst, resobj, dbobj, source, collection):
	# create directory for download day
	if not os.path.exists(date):
    		os.makedirs(date)
		os.chmod(date, 0777)
	os.chdir(date)

	year = date[:-4]
	factory = HdfFactory()
	
	directory = workdir + date
	fname = directory + "/" + date
	# directory to store aggregated h5files
	aggredir = directory + "/" + "aggre"
	if not os.path.exists(aggredir):
    		os.makedirs(aggredir)
		os.chmod(aggredir, 0777)

	aotpref, geoaotpref = factory.DataPrefix("aot")
	lstpref, geolstpref = factory.DataPrefix("lst")

 	# extract compressed files and aggregate data and geo files
	ExtractRemoveAggregate(LOG_FILE, directory, aggredir, fname, aotpref, geoaotpref)
	ExtractRemoveAggregate(LOG_FILE, directory, aggredir, fname, lstpref, geolstpref)
	
	os.chdir(aggredir)
	aoth5files = [f for f in os.listdir(aggredir) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(geoaotpref)]
	for aoth5file in aoth5files:
		lst = GetDataName(aggredir, geolstpref, aoth5file[21:25], aoth5file[30:34])
		# resapmle aot
		resaot = resobj.ChainProcess(aoth5file, "aot", BAND)
		reslst = resobj.ChainProcess(lst, "lst", "")
		# insert into database
		s = dbobj.Connect()
		if s == 1:	
			t = dbobj.ChainProcess(aggredir, aoth5file, resaot, source, collection, "aot")
			p = dbobj.ChainProcess(aggredir, lst, reslst, source, collection, "lst")
			dbobj.Disconnect()		
			if t == 0 and p == 0:
				resaotfull = MoveToSaveDir(LOG_FILE, aoth5file, resaot, aggredir, saveorgaot + year, saveresaot + year)
				reslstfull = MoveToSaveDir(LOG_FILE, lst, reslst, aggredir, saveorglst + year, savereslst + year)
				# create pm
				command = "Rscript {0} npp {1} {2} {3}".format(pmnpp, resaotfull, reslstfull, source)
				print "command: " + command
				os.system(command)
	
	return 0

# processing IMG UET
def ProcessingSatelliteImgUET(year, workdiraot, workdirlst, saveorgaot, saveresaot, saveorglst, savereslst, resobj, dbobj, source, collection):
	print "in Processing ST"
	factory = HdfFactory()	
	# processing AOT
	os.chdir(workdiraot)
	print "Processing AOT"
	aggredir = workdiraot + "/" + "aggre"
	if not os.path.exists(aggredir):
    		os.makedirs(aggredir)
		os.chmod(aggredir, 0777)
	
	aotpref, geoaotpref = factory.DataPrefix("aot")
	# extract compressed files and aggregate data and geo files
	ExtractRemoveAggregate(LOG_FILE, workdiraot, aggredir, "", aotpref, geoaotpref)
	os.chdir(aggredir)

	aoth5files = [f for f in os.listdir(aggredir) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(geoaotpref)]
	resaotfull = ""
	for aoth5file in aoth5files:
		resaot = resobj.ChainProcess(aoth5file, "aot", BAND)
		s = dbobj.Connect()
		if s == 1:	
			t = dbobj.ChainProcess(aggredir, aoth5file, resaot, source, collection, "aot")
			resaotfull = MoveToSaveDir(LOG_FILE, aoth5file, resaot, aggredir, saveorgaot + year, saveresaot + year)
	
	# processing LST
	os.chdir(workdirlst)
	aggredir = workdirlst + "/" + "aggre"
	if not os.path.exists(aggredir):
    		os.makedirs(aggredir)
		os.chmod(aggredir, 0777)
	
	lstpref, geolstpref = factory.DataPrefix("lst")
	# extract compressed files and aggregate data and geo files
	ExtractRemoveAggregate(LOG_FILE, workdirlst, aggredir, "", lstpref, geolstpref)
	os.chdir(aggredir)

	lsth5files = [f for f in os.listdir(aggredir) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(geolstpref)]
	reslstfull = ""
	for lsth5file in lsth5files:
		reslst = resobj.ChainProcess(lsth5file, "lst", BAND)
		s = dbobj.Connect()
		if s == 1:	
			t = dbobj.ChainProcess(aggredir, lsth5file, reslst, source, collection, "lst")
			reslstfull = MoveToSaveDir(LOG_FILE, lsth5file, reslst, aggredir, saveorglst + year, savereslst + year)
	print resaotfull
	print reslstfull
	#create_pm_image(type,aot,lst,sourceid)
	command = "Rscript {0} {1} {2} {3} {4}".format(pmnpp, 2, resaotfull, reslstfull, source)
	print "command: " + command
	os.system(command)	

# download, resample and processing LST
# main function that get executed at a fixed time everyday
"""
def main():
	
	# resample and sql server objects
	res = ResampleNPP(LOG_FILE)
	dserv = Server(log = LOG_FILE, host=HOST, dbname=DBNAME, user=USERNAME, passwd=PASSWORD, port=PORT)

	############### calculate days to download data ##########################
	# get the nesrest downloaded day and download day from database
	s = dserv.Connect()
	if s == 1:
		nearest_day, download_day = dserv.GetNearestDownloadDay()
		dserv.Disconnect()
	else:
		return 1
	for julian in range(1,2):#range(nearest_day, download_day):
		date, year = JulianToDate(julian)
		date = "20150302"
		os.chdir(HOME_DIR)
		#t = DownloadData(date)
		os.chdir(HOME_DIR)
		#if t == 0:
		ProcessingSatelliteImg(date, HOME_DIR, HOME_DIR_AOT_ORG_DATA, HOME_DIR_AOT_RESAMPLE_DATA, HOME_DIR_LST_ORG_DATA, HOME_DIR_LST_RESAMPLE_DATA, res, dserv, 0, 0)
		#else:
		#	print "download error"
		os.chdir(HOME_DIR)
	del res, dserv
	
	return 0
"""
def main():
	workdiraot = "/apom_data/apom/NPP/AOT/"
	workdirlst = "/apom_data/apom/NPP/LST/"
	year = "2018"
	sourceid = 1
	#workdiraot = str(sys.argv[1])
	#workdirlst = str(sys.argv[2])
	#year = sys.argv[3]
	#year = str(sys.argv[3])
	#sourceid = sys.argv[4]
	#print "Python" + workdiraot + " " + workdirlst + " " + year
	#exit(1)

	#print HOST, USERNAME, PASSWORD, PORT
	# resample and sql server objects
	res = ResampleNPP(LOG_FILE)
	dserv = Server(log = LOG_FILE, host=HOST, dbname=DBNAME, user=USERNAME, passwd=PASSWORD, port=PORT)
	ProcessingSatelliteImgUET(year, workdiraot, workdirlst, HOME_DIR_AOT_ORG_DATA, HOME_DIR_AOT_RESAMPLE_DATA, HOME_DIR_LST_ORG_DATA, HOME_DIR_LST_RESAMPLE_DATA, res, dserv, sourceid, 0)	
	
main()	

