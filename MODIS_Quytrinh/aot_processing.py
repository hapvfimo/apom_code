# -*- coding: utf-8 -*-
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.cm as cm 
import matplotlib.colors as clr
import psycopg2
import gdal
import numpy as np
import xml.etree.ElementTree as ET
from shutil import copyfile
import datetime
import re
import traceback
import string
#from createAQI import *
from os.path import basename
from gdalconst import *
from pylab import *

###################################################################
AOTDIR = "/apom_data/apom/prod/ProdMODISAOT_Province"
AOTVNTABLE = "prodaot.prodmodisaot_vn_collection0" # 2010 - 2014
AOTPROVTABLE = "prodaot.prodmodisaot_province_collection0"
SHAPEPROV = "org.gis_adm1"
SHAPEVN = "org.gis_adm0"
AOTMYD = "res.satresampmyd04"
AOTMOD = "res.satresampmod04"

host_win = "118.70.72.13"
db_win = "apom"
user_win = "postgres"
pass_win = "fimopostgre54321"
port_win = 8100

host_ubun = "192.168.0.61"
db_ubun = "apom"
user_ubun = "postgres"
pass_ubun = "fimopostgre54321"
port_ubun = 5432

home_folder = "/home/apom/"
read_raster_command = "{0} -a -f rasref -F {1} {2}"
raster2pgsql = "/usr/bin/raster2pgsql"

###################################################################
NODATA = -9999.0
PM25LOWVALUE = 0.0
PM25HIGHVALUE = 500.0
QCPM25 = 50

#insert_vn = "INSERT INTO {0}(filename, filepath, gridid, max, min, avg, aqstime, rasref, id_vn, type, sourceid) VALUES ('{1}', '{2}', {3}, {4}, {5}, {6},'{7}'::timestamp, '{8}'::raster, {9}, {10}, {11})"
#insert_prov = "INSERT INTO {0}(filename, filepath, aotid, gridid, max, min, avg, aqstime, rasref, id_tinh, type, sourceid) VALUES ('{1}', '{2}', {3}, {4}, {5}, {6}, {7}, '{8}'::timestamp, '{9}'::raster, {10}, {11}, {12})" 

insert_vn = "INSERT INTO {0}(filename, filepath, gridid, max, min, avg, aqstime, rasref, id_vn, type, sourceid) SELECT '{1}', '{2}', {3}, {4}, {5}, {6},'{7}'::timestamp, '{8}'::raster, {9}, {10}, {11} WHERE NOT EXISTS (SELECT * FROM {0} AS T WHERE T.filename = '{1}')"
insert_prov = "INSERT INTO {0}(filename, filepath, aotid, gridid, max, min, avg, aqstime, rasref, id_tinh, type, sourceid) SELECT '{1}', '{2}', {3}, {4}, {5}, {6}, {7}, '{8}'::timestamp, '{9}'::raster, {10}, {11}, {12} WHERE NOT EXISTS (SELECT * FROM {0} AS T WHERE T.filename = '{1}')" 



# return threshod ranges of international for PM2.5
def RangesAOTGlobal():

	# declare array to save data
	RANGE = []
	# 7 sub-arrays to save 7 ranges
	for i in range (0, 7):
		RANGE.append([])
	
	# fill data in RANGE
	RANGE[0].append(0.0)
	RANGE[0].append(120.0)
	
	RANGE[1].append(120.0)
	RANGE[1].append(350.0)

	RANGE[2].append(350.0)
	RANGE[2].append(550.0)
	
	RANGE[3].append(550.0)
	RANGE[3].append(1500.0)
	
	RANGE[4].append(1500.0)
	RANGE[4].append(2500.0)
		
	RANGE[5].append(2500.0)
	RANGE[5].append(3500.0)
	
	RANGE[6].append(3500.0)
	RANGE[6].append(5000)
	
	return RANGE

# return ranges AQI Global
def AQIRangeGlobal():

	# declare array to save data
	RANGE = []
	
	# 7 sub-arrays to save 7 ranges
	for i in range (0, 7):
		RANGE.append([])

	# fill data in RANGE
	RANGE[0].append(0)
	RANGE[0].append(50)
	
	RANGE[1].append(51)
	RANGE[1].append(100)

	RANGE[2].append(101)
	RANGE[2].append(150)
	
	RANGE[3].append(151)
	RANGE[3].append(200)
	
	RANGE[4].append(201)
	RANGE[4].append(300)

	RANGE[5].append(301)
	RANGE[5].append(400)
	
	RANGE[6].append(401)
	RANGE[6].append(500)
	
	return RANGE

###########################################################
# create color file
def CreateColorImage(inputfile, colorpalette, outputfile):
	
	# create color file from input file and color palette file	
	os.system("gdaldem color-relief {0} {1} {2}".format(inputfile, colorpalette, outputfile))

# append vrts
def AppendVRTs(srcvrt, dstvrt):

	# append vrt 
	src = ET.parse(srcvrt)
	srcroot = src.getroot()
	# change band number in src vrt file to 4
        for rasterband in srcroot.findall("VRTRasterBand"):
                rasterband.set("band", "4")
		break
	src.write(srcvrt)

	dst = ET.parse(dstvrt)
	dstroot = dst.getroot()

	inputXML =  srcroot.find('VRTRasterBand')
	dstroot.append(inputXML)
	dst.write(dstvrt)

	# change data type information in dst vrt file
	for rasterband in dstroot.findall("VRTRasterBand"):
        	rasterband.set("dataType", "Byte")
	dst.write(dstvrt)

# create and merge vrt files into one
def CreateAQIProdFromRGBAndAQI(colorfile, aqiconvert):
	
	# create vrt files from RGB files
	colorvrt = colorfile[:-3] + "vrt"
	os.system("gdal_translate -of VRT {0} {1}".format(colorfile, colorvrt))

	aqiconvertvrt = aqiconvert[:-3] + "vrt"
	#print aqiconvertvrt
	os.system("gdal_translate -of VRT {0} {1}".format(aqiconvert, aqiconvertvrt))
	AppendVRTs(aqiconvertvrt, colorvrt)
	os.remove(aqiconvertvrt)
	
	# make AQI product
	product = colorfile + ".AQI.tif"
	os.system("gdal_translate {0} {1}".format(colorvrt, product))

	# remove vrt files
	os.remove(colorfile)
	os.remove(colorvrt)

	return product
###########################################################

######################### Create PM color images ########
# generate color file
def CreateColorMap(fcolor):
	
	# normalize 500 different PM values
	data=np.arange(500)
	norm = clr.Normalize(0, 499) 
	n=norm(data) 

	# color for 7 ranges of PM 
	c1 = '#00E400'
	c2 = '#FFFF00'
	c3 = '#FF7E00'
	c4 = '#FF0000'
	c5 = '#99004C'
	c6 = '#7E0000'
	c7 = '#7E0000'


	# generater color map
	pmcolormap = mpl.colors.LinearSegmentedColormap.from_list('pmcolors', [c1, c2, c3, c4, c5, c6, c7])
	rgba = pmcolormap(n)
	rgb = rgba[:,:3]

	# write to color map files
	relief = open(fcolor, "w")
	i = 0
	for color in rgb:
		r = int(color[0]*255)
		g = int(color[1]*255)
		b = int(color[2]*255)
		relief.write("{0} {1} {2} {3}\n".format(i, r, g, b))
		i = i + 1
	# specify color values for NODATA value
	relief.write("{0} {1} {2} {3}\n".format(-1.0, 0, 0, 0))
	
	relief.close()
	return 1

# calculate AQI value based on international standard 2013: QCVN 05:2013/BTNMT
def AOTConversion(aotfile, savedir):
	# create transparent file
	transfile = "{0}/transparent.tif".format(savedir)
	copyfile(aotfile, transfile)
	
	# open pm file and get data band
	dset = gdal.Open(aotfile, gdal.GA_Update)
	dband = dset.GetRasterBand(1)
	ddata = dband.ReadAsArray()

	srcA = gdal.Open(transfile, gdal.GA_Update)
	bandA = srcA.GetRasterBand(1)
	dataA = bandA.ReadAsArray()

	RANGE = RangesAOTGlobal()
	AQIRANGE = AQIRangeGlobal()

	# calculate AQI values and convert to be in range(0, 1)
	rg = 0
	i = 0
	j = 0
	for n in ddata:
		for m in n:
			if ddata[i, j] >= RANGE[0][0] and ddata[i, j] <= RANGE[6][1]:
				for rg in range (0, 6):
					if ddata[i, j] >= RANGE[rg][0] and ddata[i, j] <= RANGE[rg][1]:
						A = (AQIRANGE[rg][1] - AQIRANGE[rg][0])/(RANGE[rg][1] - RANGE[rg][0])
						B = ddata[i, j] - RANGE[rg][0]
						ddata[i, j] = int(A*B + AQIRANGE[rg][0])
						break
				dataA[i, j] = 255
			else:
				ddata[i, j] = -1.0
				dataA[i, j] = 0
			j = j + 1
		j = 0
		i = i + 1
	
	# save/close the file
	dband.WriteArray(ddata)
	bandA.WriteArray(dataA)
	del ddata, dband, dset, dataA, bandA, srcA
	
	return aotfile, transfile

def CreateAOTPNGImg(aotfile, savedir):

	tempaot = "{0}/data_temp.tif".format(savedir)
	color = "{0}/color_relief.txt".format(savedir)
	# backup PM original file
	copyfile("{0}/{1}".format(savedir, aotfile), tempaot)
	
	# convert PM to AQI
	aot, transfile = AOTConversion(tempaot, savedir)
		
	# create color table and create color file for PM
	CreateColorMap(color)
	colorfile = savedir + "/" + aotfile[:-4] + ".col"
	CreateColorImage(tempaot, color, colorfile)
	product = CreateAQIProdFromRGBAndAQI(colorfile, transfile)
	os.system("gdal_translate -of PNG {0} {1}".format(product, product[:-11] + "png"))
	# remove temp files
	os.remove(product)
	os.remove(tempaot)
	os.remove(color)

###########################################################
# calculate max, min, avg in tif file
def CalMaxMinAvgTif(tifname):
	dset = gdal.Open(tifname, gdal.GA_ReadOnly)
	dband = dset.GetRasterBand(1)
	ddata = dband.ReadAsArray()

	maxval = 0.0
	avg = 0.0
	minval = 3000.0
	count  = 0
	i = 0
	j = 0
	for n in ddata:
		for m in n:
			if ddata[i, j] > 0:
				count = count + 1
				if ddata[i, j] > maxval:
					maxval = ddata[i, j]
				if ddata[i, j] < minval:
					minval = ddata[i, j]
				avg = avg + ddata[i, j]
			j = j + 1
		j = 0
		i = i + 1
	if count <= 0:
		avg = 0.0
		maxval = 0.0
		minval = 0.0
	else:
		avg = avg/count
	return maxval, avg, minval, count

def SignToNotSign(str):
    try:
        if str == '': return
        if type(str).__name__ == 'unicode': str = str.encode('utf-8')
        list_pat = ["á|à|ả|ạ|ã|â|ấ|ầ|ẩ|ậ|ẫ|ă|ắ|ằ|ẳ|ặ|ẵ", "Á|À|Ả|Ạ|Ã|Â|Ấ|Ầ|Ẩ|Ậ|Ẫ|Ă|Ắ|Ằ|Ẳ|Ặ|Ẵ",
                    "đ", "Đ", "í|ì|ỉ|ị|ĩ", "Í|Ì|Ỉ|Ị|Ĩ", "é|è|ẻ|ẹ|ẽ|ê|ế|ề|ể|ệ|ễ", "É|È|Ẻ|Ẹ|Ẽ|Ê|Ế|Ề|Ể|Ệ|Ễ",
                    "ó|ò|ỏ|ọ|õ|ô|ố|ồ|ổ|ộ|ỗ|ơ|ớ|ờ|ở|ợ|ỡ", "Ó|Ò|Ỏ|Ọ|Õ|Ô|Ố|Ồ|Ổ|Ộ|Ỗ|Ơ|Ớ|Ờ|Ở|Ợ|Ỡ",
                    "ú|ù|ủ|ụ|ũ|ư|ứ|ừ|ử|ự|ữ", "Ú|Ù|Ủ|Ụ|Ũ|Ư|Ứ|Ừ|Ử|Ự|Ữ", "ý|ỳ|ỷ|ỵ|ỹ", "Ý|Ỳ|Ỷ|Ỵ|Ỹ"]
        list_re = ['a', 'A', 'd', 'D', 'i', 'I', 'e', 'E', 'o', 'O', 'u', 'U', 'y', 'Y']
        for i in range(len(list_pat)):
            str = re.sub(list_pat[i], list_re[i], str)
        return str
    except:
        traceback.print_exc()

# class server to connect and manipulate data 
class Server:
	
	# init
	#def __init__(self, host="112.137.132.48", dbname="apom", user="postgres", passwd="apom23qaz", port=1188 ):
	def __init__(self, host=host_ubun, dbname=db_ubun, user=user_ubun, passwd=pass_ubun, port=port_ubun):
		self.con = None
		self.host = host
		self.dbname = dbname
		self.user = user
		self.passwd = passwd
		self.port = port
		self.cur = None 

	# connect to server
	def Connect(self):
		try:
			self.con = psycopg2.connect(database=self.dbname, user=self.user, password=self.passwd, host=self.host, port=self.port)	
			self.cur = self.con.cursor()
			print("connect to database server successfully\n")
			return 1
		except psycopg2.Error as e:
			print("can't connect to database server\n")
			return 0

	# return insert raster query
	def InsertRasterQuery(self, imgdir, imgname, table):
		tif_location = imgdir + "/" + imgname
		tif_script = os.popen(read_raster_command.format(raster2pgsql, tif_location, table)).read() #
		first_index = tif_script.find("('")
		last_index = tif_script.find("':")
		tif_ref = tif_script[first_index+2:last_index]
		return tif_ref
		
	# ++++++ clip raster ++++++
	# insert and update PM provinces
	def InsertTIF(self, table, fname, fdir, oriid, grid_id, id_shape, aqstime, sat_type, sourceid):
		CreateAOTPNGImg(fname, fdir)
		maxval, avg, minval, count = CalMaxMinAvgTif("{0}/{1}".format(fdir, fname))
		if maxval <= 0.0:
			return 0
		fdir_store = fdir.replace(home_folder, "")
		raster = self.InsertRasterQuery(fdir, fname, table)
		if oriid == "":
			insertsql = insert_vn.format(table, fname, fdir_store, grid_id, maxval, minval, avg, aqstime, raster, id_shape, sat_type, sourceid) # insert vietnam
		else:
			insertsql = insert_prov.format(table, fname, fdir_store, oriid, grid_id, maxval, minval, avg, aqstime, raster, id_shape, sat_type, sourceid) # insert province
		try:
			self.cur.execute(insertsql)
			self.con.commit()
			#print("inserted information of {0} into database\n".format(fname))
		except psycopg2.Error as e:
			print e.pgerror
			return 0
		return count
	
	# create Vietnam file
	def CreateVietnam(self, oritable, vntable, shapetable, savedir, filename, sat_type, sourceid):
		# sql
		oriinfo = "SELECT id, gridid, aqstime FROM {0} WHERE filename='{1}'".format(oritable, filename)
		sql1 = "select oid, lowrite(lo_open(oid, 131072), tif) AS num_bytes FROM (VALUES (lo_create(0),ST_AsTIFF((select ST_Clip ({0}.rasref, {1}.shape) FROM {2}, {3} where {4}.id = {5} and {6}.filename = '{7}' limit 1)))) AS v(oid,tif)".format(oritable, shapetable, shapetable, oritable, shapetable, 1, oritable, filename.strip())
		try:
			# get original information
			self.cur.execute(oriinfo)
			records = self.cur.fetchall()
			oriid =  records[0][0]
			gridid = records[0][1]
			aqstime = records[0][2]
		
			# execute clip vietnam and save to save directory
			self.cur.execute(sql1)
			records = self.cur.fetchall()
			sqlexport = "select lo_export({0}, '{1}/{2}')".format(records[0][0], savedir, filename.strip())
			sqlexport1 = "select lo_unlink({0})".format(records[0][0])
			self.cur.execute(sqlexport)	
			self.cur.execute(sqlexport1)
			# create PNG image for AOT
			numpi = self.InsertTIF(vntable, filename.strip(), savedir, "", gridid, 1, aqstime, sat_type, sourceid)
			return numpi
		except psycopg2.Error as e:
			print e.pgerror
			return 0
		
	# create province PM/AQI file
	def CreateProvince(self, oritable, provtable, shapetable, savedir, filename, datatype, typeaqi, sat_type, numpi, sourceid):
		provname = ""
		# get inforation for this pm image
		oripminfo = "SELECT id, gridid, aqstime FROM {0} WHERE filename='{1}'".format(oritable, filename)
		try:
			self.cur.execute(oripminfo)
			records = self.cur.fetchall()
		except psycopg2.Error as e:
			#print "FAILED"
			return 0
		oriid =  records[0][0]
		gridid = records[0][1]
		aqstime = records[0][2]
		
		# check
		num = 0
		# create and insert province pm images into database
		for count in range (1, 64):
			sql1 = "select oid, lowrite(lo_open(oid, 131072), tif) AS num_bytes FROM (VALUES (lo_create(0),ST_AsTIFF((select ST_Clip ({0}.rasref, {1}.shape) FROM {2}, {3} where {4}.id = {5} and {6}.filename = '{7}' limit 1)))) AS v(oid,tif)".format(oritable, shapetable, shapetable, oritable, shapetable, count, oritable, filename)
			sql2 = "select name from {0} where {1}.id = {2}".format(shapetable, shapetable, count)
			self.cur.execute(sql1)
			records = self.cur.fetchall()
			self.cur.execute(sql2)
			name = self.cur.fetchall()
			provname = SignToNotSign(name[0][0])
			provname = provname.replace(' ', '_')
			provname = "{0}-{1}".format(filename[:-4], provname)
			sqlexport = "select lo_export({0}, '{1}/{2}.tif')".format(records[0][0], savedir, provname)
			sqlexport1 = "select lo_unlink({0})".format(records[0][0])
			self.cur.execute(sqlexport)	
			self.cur.execute(sqlexport1)
			# insert and update province image into database
			if datatype == "AOT":
				num = num + self.InsertTIF(provtable, "{0}.tif".format(provname), "{0}/".format(savedir), oriid, gridid, count, aqstime, sat_type, sourceid)
				if num >= numpi - 2:
					return 0
			provname = ""
		return 0

	# check pmfile exist
	def CheckTIFDatabase(self, tiffile, tiftable):
		sql = "select count(filename) FROM {0} WHERE {1}.filename = '{2}'".format(tiftable, tiftable, tiffile)
		try:
			self.cur.execute(sql)
			records = self.cur.fetchall()
			print records[0][0]
			if records[0][0] == 1:
				return 0
		except psycopg2.Error as e:
			print "Can't find pm file {0} in database: {1}".format(tiffile, e.pgerror)
			return 1
		return 1
		
	# get pm name
	def GetTIFFilename(self, tiftable, tifname):
		sql = "SELECT filename, to_char(aqstime, 'yyyy'), sourceid FROM {0} WHERE filename ='{1}' ORDER BY aqstime asc".format(tiftable, tifname)
		self.cur.execute(sql)
		records = self.cur.fetchall()
		return records
		
	# disconnect
	def Disconnect(self):
		if self.con:
			self.con.close()

def ExecuteAll(tifname, sat_type, sourceid):
	#print tifname + " " + str(sat_type) + " " + str(sourceid);
	#exit(1);
	#print(pmname)
	#print sat_type
	# run manual from input HaPV

	dserv = Server()
	s = dserv.Connect()
	print tifname, sat_type, sourceid

	if sat_type == '0':
		AOTTABLE = AOTMOD
	else:
		AOTTABLE = AOTMYD

	records = dserv.GetTIFFilename(AOTTABLE, tifname)
	print "records: ", records

	if records == None:
		print "can't find {0} in database".format(tifname)
		return 0

	aotdir = AOTDIR + "/" + records[0][1] + "/"
	#print AOTDIR, AOTTABLE

	savedir = "{0}{1}".format(aotdir, tifname.strip()[:-4])

	if not os.path.exists(savedir): os.makedirs(savedir)
	numpi = dserv.CreateVietnam(AOTTABLE, AOTVNTABLE, SHAPEVN, savedir, tifname, sat_type, sourceid)
	if numpi > 0.0:
		dserv.CreateProvince(AOTVNTABLE, AOTPROVTABLE, SHAPEPROV, savedir, tifname.strip(), "AOT", "", sat_type, numpi, sourceid)
	del dserv
	return 0

ExecuteAll(sys.argv[1], sys.argv[2],sys.argv[3])
#ExecuteAll("MOD04L2.A2015140.0350.006.2015140035747.hdf_DT_10km.tif", 0, 1)
#ExecuteAll("MOD04_L2.A2015093.0255.051.2015093094513.hdf_DT_10km_uk.tif", 0)
#ExecuteAll("MOD04_L2.A2015092.0350.051.2015092140005.hdf_DT_10km_uk.tif", 0)
#ExecuteAll("MOD04_L2.A2015103.0335.051.2015103222033.hdf_DT_10km_uk.tif", 0)
#ExecuteAll("MYD04_L2.A2015093.0605.006.2015093213708.hdf_DT_10km_uk.tif", 1)
"""
	### Manual run 
def ExecuteAll():	
	dserv = Server()
	s = dserv.Connect()
	records = dserv.GetTIFFilename(AOTMYD)

	for tifname in records:
		#d = dserv.CheckTIFDatabase(tifname[0].strip(), AOTMYD)
		#print tifname[0], tifname[1], tifname[2]
		#if d == 1:
			#print "can't find {0} in database".format(tifname[0])
			#continue
		if tifname[2] == None:
			tifname[2] = 0
		AOTDIR = "/apom_data/apom/prod/ProdMODISAOT_Province/" + tifname[1] + "/"
		savedir = "{0}{1}".format(AOTDIR, tifname[0].strip()[:-4])
		if not os.path.exists(savedir): os.makedirs(savedir)
		numpi = dserv.CreateVietnam(AOTMYD, AOTVNTABLE, SHAPEVN, savedir, tifname[0], 0, tifname[2])
		if numpi > 0.0:
			dserv.CreateProvince(AOTVNTABLE, AOTPROVTABLE, SHAPEPROV, savedir, tifname[0].strip(), "AOT", "", 0, numpi, tifname[2])
	del dserv
	return 0
ExecuteAll()
	#"""
	#""" Automatic run """

