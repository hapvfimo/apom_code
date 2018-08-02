""" This file contains utility functions """
import os
import sys
import numpy as np
import gdal
import tarfile
import gzip
from gdalconst import *
import math
import datetime
from hdf_factory import HdfFactory
from constants import JULIAN_MOCK
from datetime import datetime as dt
from constants import VN_NORTH
from constants import VN_SOUTH
from constants import VN_EAST
from constants import VN_WEST 

################## begin for date/time process ########################################
# get datetime in log format
def GetLogTimeFormat():
        t = datetime.datetime.now().replace(tzinfo=None)
        in_time = t.strftime('%Y-%m-%d %H:%M:%S')
        return str(in_time)

################## end for date/time process ########################################

################## begin for download process ########################################
#------------------- extract and aggregate h5 files ---------------------------------#
# extract all data files
def ExtractTarFile(log, directory, datatype):
	factory = HdfFactory()
	dpattern, gpattern = factory.TarPattern(datatype)
	flog = open(log, "a")
        tarfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.tar') and (f.startswith(dpattern) or f.startswith(gpattern))]
        for f in tarfiles:
                try:
                        ar = tarfile.open(f)
                        ar.extractall(directory)
                        ar.close()
                        flog.write("[{0}] successfully extracted {1}\n".format(GetLogTimeFormat(), f))
                except tarfile.TarError as e:
                        flog.write("[{0}] Error while extracting {1}: {2}\n".format(GetLogTimeFormat(), f, str(e)))
			flog.close()
	flog.close()
        return 1

# extract all gzip files
def ExtractGzFile(log, directory):
	flog = open(log, "a")
        gzfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.gz')]
        for f in gzfiles:
		try:
                	gzif = gzip.open(f, 'rb')
              		s = gzif.read()
                	gzif.close()
                	fname = f[:-3]
                # store uncompressed file data from 's' variable
                	open(fname, 'w').write(s)
                	os.remove(f)
		except Exception as e:
			print str(e)
			return 0
	flog.write("[{0}] successfully extracted all gzip files\n".format(GetLogTimeFormat()))
	flog.close()
        return 1

# compare file with file array (for use in __remove_unused_files__())
def CompareFileInArray(filename, array):
        for f in array:
                if filename == f:
                        return 1
        return 0

# remove all files that are out of favorite orbir pass time
def RemoveLevel1(directory, ref_file):
        ref = open(ref_file, "r" )
        files = []
        for line in ref:
                files.append(line[:-1])
        ref.close()
        h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5')]
        for f in h5files:
                check = CompareFileInArray(f, files)
                if check == 0:
                        os.remove(f)
        return 1

# check hdf image in bounding area of Viet nam 
def CheckMatchImg(coor_check_La, coor_check_Lo, north, south, east, west):
	if coor_check_Lo >= west and coor_check_Lo <= east:
		if coor_check_La >= south and coor_check_La <= north:
			return 1
	return 0

# remove all file out of favorite area
def RemoveLevel2(directory, datatype, geotype):
	check = [0,0,0,0,0,0,0,0]
	count = 0
	factory = HdfFactory()
	dtype = factory.DataType(datatype)
	h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5') and f.lower().startswith(geotype)]
	for f in h5files:
		lad, lod = factory.LatLonDataset(f, dtype)
		coors = GetBoundingCoor(lad, lod)
		check[0] = CheckMatchImg(coors[0], coors[3], VN_NORTH, VN_SOUTH, VN_EAST, VN_WEST)
		check[1] = CheckMatchImg(coors[0], coors[2], VN_NORTH, VN_SOUTH, VN_EAST, VN_WEST)
		check[2] = CheckMatchImg(coors[1], coors[3], VN_NORTH, VN_SOUTH, VN_EAST, VN_WEST)
		check[3] = CheckMatchImg(coors[1], coors[2], VN_NORTH, VN_SOUTH, VN_EAST, VN_WEST)
		check[4] = CheckMatchImg(VN_NORTH, VN_EAST, coors[0], coors[1], coors[2], coors[3])
		check[5] = CheckMatchImg(VN_NORTH, VN_WEST, coors[0], coors[1], coors[2], coors[3])
		check[6] = CheckMatchImg(VN_SOUTH, VN_EAST, coors[0], coors[1], coors[2], coors[3])
		check[7] = CheckMatchImg(VN_SOUTH, VN_WEST, coors[0], coors[1], coors[2], coors[3])
		
		for i in check:
			if i == 1:
				count = 1
		if count == 0:
			os.remove(f)
			os.remove(GetDataName(directory, datatype, f[21:25], f[30:34]))
		count = 0
	return 1

# get land surface temperature file corresonding to geolocation file
def GetDataName(directory, dataprefix, start_time, end_time):
        h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(dataprefix)]
        for f in h5files:
                stime = f[21:25]
                etime = f[30:34]
                if stime == start_time and etime == end_time:
                        return f
        return ""

# aggregate gmtco and vlsto files into one
def AggregateGmtcoVlsto(fgmtco, fvlsto):
        # aggregate all data first
        faggre = "GMTCO-" + fvlsto
        os.system("h5copy -p -i " + fvlsto + " -o " + faggre + " -s " + "//All_Data/VIIRS-LST-EDR_All" + " -d " + "//All_Data/VIIRS-LST-EDR_All")
        os.system("h5copy -p -i " + fgmtco + " -o " + faggre + " -s " + "//All_Data/VIIRS-MOD-GEO-TC_All" + " -d " + "//All_Data/VIIRS-MOD-GEO-TC_All")
        # aggregate data products
        os.system("h5copy -p -i " + fvlsto + " -o " + faggre + " -s " + "//Data_Products/VIIRS-LST-EDR" + " -d " + "//Data_Products/VIIRS-LST-EDR")
        os.system("h5copy -p -i " + fgmtco + " -o " + faggre + " -s " + "//Data_Products/VIIRS-MOD-GEO-TC" + " -d " + "//Data_Products/VIIRS-MOD-GEO-TC")
        return faggre

# aggregate gaero and vaooo files into one
def AggregateGaeroVaooo(fgaero, fvaooo):
        # aggregate all data first
        faggre = "GAERO-" + fvaooo
        os.system("h5copy -p -i " + fvaooo + " -o " + faggre + " -s " + "//All_Data/VIIRS-Aeros-EDR_All" + " -d " + "//All_Data/VIIRS-Aeros-EDR_All")
        os.system("h5copy -p -i " + fgaero + " -o " + faggre + " -s " + "//All_Data/VIIRS-Aeros-EDR-GEO_All" + " -d " + "//All_Data/VIIRS-Aeros-EDR-GEO_All")
        # aggregate data products
        os.system("h5copy -p -i " + fvaooo + " -o " + faggre + " -s " + "//Data_Products/VIIRS-Aeros-EDR" + " -d " + "//Data_Products/VIIRS-Aeros-EDR")
        os.system("h5copy -p -i " + fgaero + " -o " + faggre + " -s " + "//Data_Products/VIIRS-Aeros-EDR-GEO" + " -d " + "//Data_Products/VIIRS-Aeros-EDR-GEO")
        return faggre

# aggregate all files in directory
def AggregateImgsInDir(log, directory, savedir, datatype, geotype):
	flog = open(log, "a")
        h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(geotype)]
        for geo in h5files:
                data = GetDataName(directory, datatype, geo[21:25], geo[30:34])
		if geotype == "GAERO":
                	aggre = AggregateGaeroVaooo(geo, data)
			os.system("mv {0}/{1} {2}/".format(directory, aggre, savedir))
		if geotype == "GMTCO":	
			aggre = AggregateGmtcoVlsto(geo, data)
			os.system("mv {0}/{1} {2}/".format(directory, aggre, savedir))
		#if os.path.isfile(geo) and os.path.isfile(data):
                        #os.remove(geo)
                        #os.remove(data)
        flog.write("[{0}] successfully aggregated geolocation files and it's matching data file\n".format(GetLogTimeFormat()))
	flog.close()
	return 1

# remove files
def ExtractRemoveAggregate(log, directory, savedir, date, datatype, geotype):
	print date
	ExtractTarFile(log, directory, datatype)
	ExtractGzFile(log, directory)
	if date != "":
		RemoveLevel1(directory, date)
	RemoveLevel2(directory, datatype, geotype)
	AggregateImgsInDir(log, directory, savedir, datatype, geotype)

#------------------------------------------------------------------------------------#
# convert julian to date
def JulianToDate(julian):
        F, I = math.modf(float(julian))
        I = int(I)
        A = math.trunc((I - 1867216.25)/36524.25)
        if I > 2299160:
                B = I + 1 + A - math.trunc(A / 4.)
        else:
                B = I
        C = B + 1524
        D = math.trunc((C - 122.1) / 365.25)
        E = math.trunc(365.25 * D)
        G = math.trunc((C - E) / 30.6001)
        day = C - E + F - math.trunc(30.6001 * G)
        if G < 13.5:
                month = G - 1
        else:
                month = G - 13

        if month > 2.5:
                year = D - 4716
        else:
                year = D - 4715
	if len(str(int(month))) == 1:
		month = '0' + str(int(month))
	else:
		month = str(int(month))
	if len(str(int(day))) == 1:
		day = '0' + str(int(day))
	else:
		day = str(int(day))

        return str(int(year)) + str(month) + str(day), str(int(year))

	
# add count to specify file in ftp server
def AddCount(step):
	count = "000"
	if step >= 10:
		count = count + str(step)
	else:
		count = count + "0" + str(step)
	return count

# get aqquired time from file name 
def GetAcquiredTimeFromFilename(filename = "", typef = "aot"):
	start_time = ""
        end_time = ""
	interval = ""
	if filename == "":
		return ""
	if typef == "aot":
		start_time = filename[21:25]
		end_time = filename[30:34]	
	elif typef == "aot_geo":
		start_time = filename[21:25]
		end_time = filename[30:34]
	elif typef == "lst":
		start_time = filename[21:25]
		end_time = filename[30:34]
	elif typef == "lst_geo":
		start_time = filename[21:25]
		end_time = filename[30:34]
	else:
		return ""	
	interval = start_time + end_time
	return interval

# get date from filename
def GetDateFromFilename(filename = ""):
	date = ""
	if filename == "":
		return 0
	date = filename[11:19]
	return date

# get start time and end time from total time
def GetStartTime(time):
	return int(time[0:4])
def GetEndTime(time):
	return int(time[4:8])

################## end for download process #######################################
################## begin for resampling and insertion data ############################## 
# get bounding coordinates
def GetBoundingCoor(lad, lod):

	gran1 = gdal.Open(lad, GA_ReadOnly)
	gran4 = gdal.Open(lod, GA_ReadOnly)

	latitude = np.array(gran1.ReadAsArray())
	longitude = np.array(gran4.ReadAsArray())

	la = np.ma.masked_equal(latitude, -999.3, copy=False)
	lo = np.ma.masked_equal(longitude, -999.3, copy=False)

	coors = []
	coors.append(np.amax(la))
	coors.append(np.amin(la))
	coors.append(np.amax(lo))
	coors.append(np.amin(lo))

	return coors

# get other filename corresponding to original hdf5 file based on extension, this function is used in __get_other_filenames__ function
def GetFilenameInDir(forg, directory, extension):
        out = ""
        files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith(extension)]
        for f in files:
                if forg[0:44] == f[0:44]:
                        out = f
                        break
        return out

# get all other filenames corresponding to original hdf5 file
def GetAncilaryFilesInDir(forg, directory):
        png = GetFilenameInDir(forg, directory, "convert.png")
        pngori = GetFilenameInDir(forg, directory, "thumbnail.png")
        meta = GetFilenameInDir(forg, directory, "metadata.txt")
        corner = GetFilenameInDir(forg, directory, "corner.txt")
	tiffulaot = GetFilenameInDir(forg, directory, "550.tif")
	tiffullst = GetFilenameInDir(forg, directory, "LST.tif")
	if tiffulaot != "":
		tifful = tiffulaot
	else:
		tifful = tiffullst
        return png, pngori, meta, corner, tifful

# move npp aot to saving directory
def MoveToSaveDir(log, h5file, resfile, srcdir, dstdirorg, dstdirres):
	try:
		idir = dstdirorg + "/" + h5file[:-3]
		png, pngori, meta, corner, tiff = GetAncilaryFilesInDir(h5file, srcdir)
		if png != "" and pngori != "" and meta != "" and corner != "" and tiff != "":
			if not os.path.exists(idir): os.makedirs(idir)
			os.system("mv {0}/{1} {2}/".format(srcdir, h5file, idir))
			os.system("mv {0}/{1} {2}/".format(srcdir, png, idir))
			os.system("mv {0}/{1} {2}/".format(srcdir, pngori, idir))
			os.system("mv {0}/{1} {2}/".format(srcdir, meta, idir))
			os.system("mv {0}/{1} {2}/".format(srcdir, corner, idir))
			os.system("mv {0}/{1} {2}/".format(srcdir, tiff, idir))
		
		resdir = dstdirres + "/" + resfile[:-4]
		if not os.path.exists(resdir): os.makedirs(resdir)
		os.system("mv {0}/{1} {2}/".format(srcdir, resfile, resdir))
	except Exception as e:
		print str(e)
		return ""
	flog = open(log, "a")
	flog.write("[{0}] successfully move hdf and resample files to corressponding directories\n".format(GetLogTimeFormat()))
	flog.close()
	return resdir + "/" + resfile

# make dir for saving images in same year
def MakeYearDir(year, org_dir, res_dir):
	ydir_org = org_dir + year 
	ydir_res = res_dir + year
	if not os.path.exists(ydir_org):
    		os.makedirs(ydir_org)
		os.chmod(ydir_org , 0777)
	if not os.path.exists(ydir_res):
    		os.makedirs(ydir_res)
		os.chmod(ydir_res , 0777)

# check hdf5 file valid
#check file valid
def IsValid(h5file):

	dataset = "HDF5:" + h5file + "://All_Data/VIIRS-LST-EDR_All/LandSurfaceTemperature"
	lad = "HDF5:" + h5file + "://All_Data/VIIRS-MOD-GEO-TC_All/Latitude"
	lod = "HDF5:" + h5file + "://All_Data/VIIRS-MOD-GEO-TC_All/Longitude"
	x = os.system("gdalinfo {0} >> temp".format(dataset))
	y = os.system("gdalinfo {0} >> temp".format(lad))
	z = os.system("gdalinfo {0} >> temp".format(lad))
	
	if x==256 or y ==256 or z ==256:
		return 1 # not valid
	else:
		return 0

################## end for resampling and insertion data ############################## 
#AggregateGaeroVaooo("GAERO_npp_d20150424_t0534484_e0543205_b00001_c20150424063007.h5", "VAOOO_npp_d20150424_t0534484_e0543205_b00001_c20150424063007.h5")

#AggregateGmtcoVlsto("GMTCO_npp_d20150424_t0534484_e0543205_b00001_c20150424054321.h5", "VLSTO_npp_d20150424_t0534484_e0543205_b00001_c20150424064604.h5")
