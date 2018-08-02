""" this is main file that get executed as main process """
import os
import sys
import datetime
from datetime import datetime as dt
from resample import ResampleNPP
from postgres_server import Server
from utilities import MakeYearDir
from utilities import JulianToDate
from utilities import MoveToSaveDir
from constants import *

# change cur dir to home dir and create log file
os.chdir(HOME_DIR)
if not os.path.exists(LOG_FILE):
	open(LOG_FILE, 'a').close()
	os.chmod(LOG_FILE, 0775)

# main function that get executed at a fixed time everyday
def main():
	# resample and sql server objects
	res = ResampleNPP(LOG_FILE)
	dserv = Server(log = LOG_FILE, host=HOST, dbname=DBNAME, user=USERNAME, passwd=PASSWORD, port=PORT)
	
	aotdir = "/home/rasdaman/FTP_Automatic/20150424/aot"
	lstdir = "/home/rasdaman/FTP_Automatic/20150424/lst"
	year = "2015"

	# resapmle aot
	res.ResampleHdf5InDir(aotdir, "aot")
	res.ResampleHdf5InDir(lstdir, "lst")
	# insert into database
		
	# process AOT and LST
	s = dserv.Connect()
	if s == 1:
		p = dserv.InsertImgInDir(aotdir, 0, 3000, "aot")
		t = dserv.InsertImgInDir(lstdir, 0, 3000, "lst")
		dserv.Disconnect()
		if t == 0 and p == 0:
			resaot = MoveToSaveDir(LOG_FILE, aotdir, HOME_DIR_AOT_ORG_DATA + year, HOME_DIR_AOT_RESAMPLE_DATA + year)
			reslst = MoveToSaveDir(LOG_FILE, lstdir, HOME_DIR_LST_ORG_DATA + year, HOME_DIR_LST_RESAMPLE_DATA + year)
		
			print resaot
			print reslst
	else:	
		return 1

	# run Ha Script
	#os.system(Rscript NPPAodToPM.R npp aod_file temp_file source_id)
	#exit(1)
		
	del res, dserv
	
	return 0

main()
	
	
	

