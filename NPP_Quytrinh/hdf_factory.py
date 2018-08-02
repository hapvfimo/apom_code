import os
import sys
import gdal
import numpy as np
from gdalconst import *
from constants import *

class HdfFactory:

	def __init__(self):
		self.my = "i produce constants"
		# do nothing
	
	# produce lat long dataset
	def LatLonDataset(self, h5file, datatype):
		if datatype == "aot":
			lad = "HDF5:" + h5file + "://All_Data/VIIRS-Aeros-EDR-GEO_All/Latitude"
			lod = "HDF5:" + h5file + "://All_Data/VIIRS-Aeros-EDR-GEO_All/Longitude"
		elif datatype == "lst":
			lad = "HDF5:" + h5file + "://All_Data/VIIRS-MOD-GEO-TC_All/Latitude"
			lod = "HDF5:" + h5file + "://All_Data/VIIRS-MOD-GEO-TC_All/Longitude"
		else:
			lad = ""
			lod = ""
		return lad, lod

	# product scale/factor 
	def ScaleFactor(self, datatype):
		if datatype == "aot":
			scale = float(AOT_SCALE)
			offset = float(AOT_FACTOR)
			nodata = 0
		elif datatype == "lst":
			scale = float(LST_SCALE)
			offset = float(LST_FACTOR)	
			nodata = -32768
		else:
			scale = 0.0
			offset = 0.0	
			nodata = 0.0 
			
		return scale, offset, nodata

	# produce original/resample table
	def DBTable(self, datatype):
		if datatype == "aot":
			orgtable = AOT_ORG
			restable = AOT_RES
		elif datatype == "lst":
			orgtable = LST_ORG
			restable = LST_RES
		else:
			orgtable = ""
			restable = ""
		return orgtable, restable

	# produce directory
	def DirOrgRes(self, datatype):
		if datatype == "aot":
			orgdir = HOME_DIR_AOT_ORG_DATA
			resdir = HOME_DIR_AOT_RESAMPLE_DATA
		elif datatype == "lst":
			orgdir = HOME_DIR_LST_ORG_DATA
			resdir = HOME_DIR_LST_RESAMPLE_DATA
		else:
			orgdir = ""
			resdir = ""
		return orgdir, resdir
	
	# produce datatype
	def DataType(self, dataname):
		if dataname == "gaero":
			datatype = "aot"
		elif dataname == "gmtco":
			datatype = "lst"
		else:
			datatype = ""
		return datatype

	# produce dataprefix	
	def DataPrefix(self, datatype):
		if datatype == "aot":
			dprefix = "VAOOO"
			gprefix = "GAERO"
		elif datatype == "lst":
			dprefix = "VLSTO"
			gprefix = "GMTCO"
		else:
			dprefix = ""
			gprefix = ""
		return dprefix, gprefix

	# produce date
	def DateData(self, date, datatype):
		if datatype == "aot":
			date = date + "/" + "aot"
		elif datatype == "lst":
			date = date + "/" + "lst"
		else:
			date = ""
		return date

	# tar pattern
	def TarPattern(self, datatype):
		if datatype == "VAOOO":
			dpattern = "VIIRS-EDR_VIIRS-Aerosol-Optical-Thickness-AOT"
			gpattern = "VIIRS-EDR_VIIRS-Aerosol-Aggregated-EDR-Ellipsoid"
		elif datatype == "VLSTO":
			dpattern = "VIIRS-EDR_VIIRS-Land-Surface-Temperature"
			gpattern = "VIIRS-SDR_VIIRS-Moderate-Bands-SDR-Terrain-Corrected"
		else:
			dpattern = ""
			gpattern = ""
		return dpattern, gpattern
	
