""" This is class for connecting and inserting data into data server"""
import os
import sys
import psycopg2
import gdal
import numpy as np
import datetime
from utilities import GetBoundingCoor
from utilities import GetLogTimeFormat
from utilities import GetFilenameInDir
from gdalconst import *
from constants import *
from hdf_factory import *

raster2pgsql = "/usr/bin/raster2pgsql"
read_raster_command = "{0} -a -f rasref -F {1} {2}" # raster2pgsql, filename, tablename

insert_org = "INSERT INTO {0}(sourceid, aqstime, filename, path, corner) VALUES({1}, '{2}', '{3}', '{4}', ST_GeomFromText('POLYGON(( {5} {6}, {7} {8}, {9} {10}, {11} {12}, {13} {14}))', 4326))"
insert_raster = "INSERT INTO {0}(filename, filepath, gridid, aqstime, rasref, projection, sourceid, orgid) VALUES ('{1}', '{2}', {3}, '{4}'::timestamp, '{5}'::raster, {6}, {7}, {8})"

# convert from file name to timestamp
def ConvertToTimestamp(filename):
	year = filename[17:21]
	month = filename[21:23]
	day = filename[23:25]
	hour = filename[36:38]
	minute = filename[38:40]
	second = filename[40:42]
	times = year + "-" + month + "-" + day + " " + hour + ":" + minute + ":" + second
	return times

# class server to connect and manipulate data 
class Server:
	
	# init
	def __init__(self, log, host=HOST, dbname=DBNAME, user=USERNAME, passwd=PASSWORD, port=PORT):
		self.con = None
		self.host = host
		self.dbname = dbname
		self.user = user
		self.passwd = passwd
		self.port = port
		self.cur = None 

		self.log = log
		self.factory = HdfFactory()

	# connect to server
	def Connect(self):
		try:
			flog = open(self.log, "a")
			self.con = psycopg2.connect(database=self.dbname, user=self.user, password=self.passwd, host=self.host, port=self.port)	
			self.cur = self.con.cursor()
			flog.write("[{0}] connect to database server successfully\n".format(GetLogTimeFormat()))
		except psycopg2.Error as e:
			flog.write("[{0}] can't connect to database server: {1}\n".format(GetLogTimeFormat(), str(e)))
			flog.close()
			return 0
		flog.close()
		return 1
	
	# get the nesrest downloaded day and current day from database
	def GetNearestDownloadDay(self):
		nearest_day = 0
		download_day = 0
		sql_n = "SELECT TO_CHAR(aqstime, 'J')::integer FROM {0} ORDER BY AGE(NOW(), aqstime) ASC LIMIT 1".format(AOT_ORG)
		sql_d = "select TO_CHAR(timestamp 'now()', 'J')::integer"
		try:
			self.cur.execute(sql_n)
			nearest_day = self.cur.fetchone()
			self.cur.execute(sql_d)
			download_day = self.cur.fetchone()
			return int(nearest_day[0]), int(download_day[0])
		except psycopg2.Error as e:
			return 0, 0

	# insert original data into database
	# h5dir: containing h5 images
	# h5file: a h5 image
	# source: NASA/UET
	# collection: collection of h5 images	
	# datatype: aot/lst
	# table: table for inserting original h5 data
	# command_pattern: pattern for command inserting h5 information into DB
	def InsertOrgData(self, h5dir, h5file, source, collection, datatype, table, command_pattern):
		# check datatype
		lad, lod = self.factory.LatLonDataset(h5file, datatype)
		flog = open(self.log, "a")
		coors = GetBoundingCoor(lad, lod)
		times = ConvertToTimestamp(h5file)
		orgdir, resdir = self.factory.DirOrgRes(datatype)
		path = orgdir + h5file[17:21] + "/" + h5file[:-3] + "/"

		path = path.replace("/apom_data/", "")
		sql = command_pattern.format(table, source, times, h5file, path, str(coors[0]), str(coors[3]), str(coors[0]), str(coors[2]), str(coors[1]), str(coors[3]), str(coors[1]), str(coors[2]), str(coors[0]), str(coors[3]))  # insert_org
		sql2 = "SELECT id FROM {0} WHERE filename='{1}' limit 1".format(table, h5file)
		try:
			self.cur.execute(sql)
			self.con.commit()
			self.cur.execute(sql2)
			records = self.cur.fetchall()
			flog.write("[{0}] successfully inserted information of {1} into database\n".format(GetLogTimeFormat(), h5file))
		except psycopg2.Error as e:
			flog.write("[{0}] can't insert {1} to database server: {2}\n".format(GetLogTimeFormat(), h5file, str(e)))
			return -1	
		flog.close()
		return int(records[0][0])

	# return insert raster query
	def InsertRasterQuery(self, imgdir, imgname, table, command_pattern):
		tif_location = imgdir + "/" + imgname
		tif_script = os.popen(command_pattern.format(raster2pgsql, tif_location, table)).read() #
		first_index = tif_script.find("('")
		last_index = tif_script.find("':")
		tif_ref = tif_script[first_index+2:last_index]
		return tif_ref

	# insert resample image
	# tifdir: containing h5 images
	# tiffname: a vresample image corresponding to h5 file
	# source: NASA/UET
	# orgid: id in DB of h5 file
	# table: resample table
	# command_pattern: pattern for command inserting raster into DB
	def InsertResData(self, tifdir, tiffname, source, orgid, datatype, table, command_pattern):
		flog = open(self.log, "a")
		raster = self.InsertRasterQuery(tifdir, tiffname, table, read_raster_command)
		aqstime = ConvertToTimestamp(tiffname)
		orgdir, resdir = self.factory.DirOrgRes(datatype)
		path = resdir + tiffname[17:21] + "/" + tiffname[:-4] + "/"
		path = path.replace("/apom_data/", "")
		insertsql = command_pattern.format(table, tiffname, path, GRID_ID_VIIRS, aqstime, raster, PROJECTION, source, orgid) # insert raster
		try:
			self.cur.execute(insertsql)
			self.con.commit()
		except psycopg2.Error as e:
			flog.write("[{0}] unable to insert resample data into database: {1}\n".format(GetLogTimeFormat(), e.pgerror))
			flog.close()
			return 1
		flog.write("[{0}] successfully inserted resample data into database\n".format(GetLogTimeFormat()))
		flog.close()
		return 0
		
	# execute in chain
	# imgdir: containing h5 images
	# h5file: a h5 image
	# tiffile: a vresample image corresponding to h5 file
	# source: NASA/UET
	# collection: collection of h5 images	
	# datatype: aot/lst
	def ChainProcess(self, imgdir, h5file, tiffile, source, collection, datatype):
		r = 1
		s = 1

		orgtable, restable = self.factory.DBTable(datatype)
		if orgtable == "" and restable == "":
			return 1

		r = self.InsertOrgData(imgdir, h5file, source, collection, datatype, orgtable, insert_org)
		if r == -1:
			return 1
		s = self.InsertResData(imgdir, tiffile, source, r, datatype, restable, insert_raster)
		if s == 1:
			return 1
		return 0

	# insert files in dir
	# directory: containing h5 images
	# source: source of h5 images (NASA/UET)
	# collection: collection of h5 images
	# datatype: aot/lst
	def InsertImgInDir(self, directory, source, collection, datatype):
		ddata, gdata = self.factory.DataPrefix(datatype)
		h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(gdata)]
		for f in h5files:
			resfname = GetFilenameInDir(f, directory, ".tif")
			if resfname != "":
				s = self.ChainProcess(directory, f, resfname, source, collection, datatype)
				if s == 1:
					continue
		return 0
		
	# disconnect
	def Disconnect(self):
		if self.con:
			self.con.close()

