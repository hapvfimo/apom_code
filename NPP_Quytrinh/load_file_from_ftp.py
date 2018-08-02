""" This is a class for dowloading file from given ftp servers.
It can be used to download both xml and compressed file but 
can't do anything else"""
import os
import sys
import os.path
from constants import *
from utilities import GetLogTimeFormat
from os.path import basename

class LoadFileFTP:
	xml_extension = "manifest.xml"
	compressed_extension = "tar"

	# constructor 
	def __init__(self, log, date, base_url = BASE_URL, viirs = VIIRS_EDR, base_url_data = AOT_DIR, base_url_geo = GEO_AOT_DIR, data_name = AOT_NAME, geo_name = GEO_AOT_NAME):
		self.base_url_data = "{0}/{1}/{2}/{3}/".format(base_url, date, viirs, base_url_data)
		self.base_url_geo = "{0}/{1}/{2}/{3}/".format(base_url, date, viirs, base_url_geo)
		self.data_name = data_name
		self.data_geo = geo_name
		self.date = date
		self.log = log

		# parameter for download
		self.data = ""
		# this variable has value 0 indicate errors
		self.status = 1
		
	# preprocessing before download action
	def Preprocessing(self, number = "00001", tdata = "aot", mode = "xml"):
		# check if data is geo or aot data
		if tdata == "aot":
			self.dataurl = self.base_url_data + self.data_name
		elif tdata == "aot_geo":
			self.dataurl = self.base_url_geo + self.data_geo
		elif tdata == "lst":
			self.dataurl = self.base_url_data + self.data_name
		elif tdata == "lst_geo":
			self.dataurl = self.base_url_geo + self.data_geo
		else:
			self.status = 0
		# check if data is xml or real data
		if mode == "xml":
			self.data = self.dataurl + "_" + self.date + "_" + number + "." + self.xml_extension
		elif mode == "data":
			self.data = self.dataurl + "_" + self.date + "_" + number + "." + self.compressed_extension
		else:
			self.status = 0

	# load file from server
	def LoadFile(self, number = "00001", tdata = "aot", mode = "xml"):
		
		log = open(self.log, "a")
		self.Preprocessing(number = number, tdata = tdata, mode = mode)
		if self.status == 0:
			log.write("[{0}] nothing to download\n".format(GetLogTimeFormat()))
			log.close()
			return 0
		# check connection is on and download file
		log.write("[{0}] downloading {1}...\n".format(GetLogTimeFormat(), self.data))
		check = os.system("wget {0}".format(self.data))
		if check == 1024:
			log.close()
			if os.path.isfile(self.data):
				os.remove(self.data)
			return 0
		log.write("[{0}] downloaded {1}\n".format(GetLogTimeFormat(), self.data))
		# change to previous directory
		log.close()
		return basename(self.data)

