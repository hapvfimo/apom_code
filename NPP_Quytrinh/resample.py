import os
import sys
import gdal
import numpy as np
from gdalconst import *
from constants import *
from hdf_factory import *
from utilities import GetBoundingCoor
from utilities import GetLogTimeFormat
from utilities import IsValid

class ResampleNPP:
	
	# init
	def __init__(self, log):
		self.iband = ""
		self.resimage = ""
		self.log = log
		self.factory = HdfFactory()

	# convert dataset to raw image file containing uncorrected GCPs for land surface temperature data
	def Hdf5ToRawImageLST(self, h5file):
		check = IsValid(h5file)
		if check == 1:
			return ""
		lad, lod = self.factory.LatLonDataset(h5file, "lst")
		coors = GetBoundingCoor(lad, lod)
		# write corners to file
		corfile = h5file[:-3] + "_LST_corner.txt"
		fi = open(corfile, "w")
		fi.write("{0} {1}, {2} {3}, {4} {5}, {6} {7}".format(str(coors[0]), str(coors[3]), str(coors[0]), str(coors[2]), str(coors[1]), str(coors[2]), str(coors[1]), str(coors[3])))
		fi.close()

		# write LST dataset to image
		out = h5file[:-3] + "_LST.raw"
		self.iband = h5file[:-3] + "_LST"
		dataset = "HDF5:" + h5file + "://All_Data/VIIRS-LST-EDR_All/LandSurfaceTemperature"
		command = "gdal_translate -of GTiff {0} {1}".format(dataset, out)
		status = os.system(command)

		if status == 0:
			return out
		return ""

	# convert dataset to raw image file containing uncorrected GCPs for aerosol data
	def Hdf5ToRawImageAOT(self, h5file, band):
		lad, lod = self.factory.LatLonDataset(h5file, "aot")
		coors = GetBoundingCoor(lad, lod)
		# write corners to file
		corfile = h5file[:-3] + "_550_corner.txt"
		fi = open(corfile, "w")
		fi.write("{0} {1}, {2} {3}, {4} {5}, {6} {7}".format(str(coors[0]), str(coors[3]), str(coors[0]), str(coors[2]), str(coors[1]), str(coors[2]), str(coors[1]), str(coors[3])))
		fi.close()

		out = h5file[:-3] + "_" + str(band) + ".raw"
		self.iband = h5file[:-3] + "_" + str(band)
		command = "gdal_translate -of GTiff HDF5:\"" + h5file + "\"://All_Data/VIIRS-Aeros-EDR_All/AerosolOpticalDepth_at_" + str(band) + "nm " + out
		status = os.system(command)

		if status == 0:
			return out
		return ""

	# correct GCPs points
	def CorrectGCPs(self, imgfname, datatype):
		# check data type
		scale, offset, nodata = self.factory.ScaleFactor(datatype)

		if scale == 0 and offset == 0 and nodata == 0:
			return ""

		flog = open(self.log, "a")
		dataset = gdal.Open(imgfname, GA_ReadOnly)	
		if dataset is None:
			flog.write('[{0}] Unable to open file: {1}\n'.format(GetLogTimeFormat(), self.GCPuncorrect_fname))
			flog.close()
			return ""
		data = dataset.ReadAsArray()
		cols = dataset.RasterXSize
		rows = dataset.RasterYSize
	
		# get GCP points	
		gcps = dataset.GetGCPs()
		refine_gcps = []
		for gcp in gcps:
			if gcp.GCPX != 0 and gcp.GCPX != -999.3 and gcp.GCPY != 0 and gcp.GCPY != -999.3:
				gcp.GCPX = gcp.GCPX - 180
				refine_gcps.append(gcp)
		
		# create output maxtri
		datal = np.zeros((rows, cols), dtype=np.float32)

		# calculate aot value with offset and scale
		for i in range(0, rows):
			for j in range(0, cols):
				if data[i,j] <= 0 or data[i,j] > 65000:
					datal[i,j] = nodata 
				else:
					datal[i,j] = scale*data[i,j] + offset
		
		# create output file
		correctedfname = imgfname + "_correctedGCPs.rec"
		gtiff = gdal.GetDriverByName('GTiff')
		output = gtiff.Create(correctedfname, cols, rows, 1, gdal.GDT_Float32)
		if output is None:
			flog.write("[{0}] can't create corrected GCP file: {1}\n".format(GetLogTimeFormat(), correctedfname))
			return ""
		output.SetGCPs(tuple(refine_gcps), output.GetProjection())
		output.GetRasterBand(1).WriteArray(datal)
		
		flog.close()
		return correctedfname

	# resample 
	def Resample(self, imgfname, datatype):
		# make vrt file
		vrt_fname = imgfname + ".vrt"
		os.system("gdal_translate -of VRT " + imgfname + " " + vrt_fname)

		# create PNG
		tiffull = self.iband + ".tif"
		metadata = tiffull[:-4] + "_metadata.txt"
		pngori = tiffull[:-4] + "_convert.png"
		pnglarge = tiffull[:-4] + "_thumbnail.png"
		os.system("gdalwarp -of GTiff -tps {0} {1}".format(vrt_fname, tiffull))
		os.system("gdalinfo {0} > {1}".format(tiffull, metadata))

		# create resample image
		resampfname = self.iband + "_resample.tif"
		if datatype == "aot":
			os.system("gdal_translate -of PNG -ot Byte -scale 0 10 0 10000 {0} {1}".format(tiffull, pngori))
			os.system("gdal_translate -of PNG -ot Byte -scale 0 10 0 10000 -outsize 500 450 {0} {1}".format(tiffull, pnglarge))
			command = "gdalwarp -t_srs '+proj=longlat +datum=WGS84' -tps -ot Float32 -wt Float32 -te 100.1 6.4 111.8 25.6 -tr 0.05 -0.05 -r bilinear -srcnodata 0.0 -dstnodata 0.0 -overwrite -multi {0} {1}".format(vrt_fname, resampfname)
		elif datatype == "lst":
			os.system("gdal_translate -of PNG -ot Byte {0} {1}".format(tiffull, pngori))
			os.system("gdal_translate -of PNG -ot Byte -outsize 500 450 {0} {1}".format(tiffull, pnglarge))
			command = "gdalwarp -t_srs '+proj=longlat +datum=WGS84' -tps -ot Float32 -wt Float32 -te 100.1 6.4 111.8 25.6 -tr 0.05 -0.05 -r bilinear -srcnodata -32768 -dstnodata -32768 -overwrite -multi {0} {1}".format(vrt_fname, resampfname)
		else:
			return ""
		os.system(command)
		return resampfname

	# process in chain
	def ChainProcess(self, h5file, datatype, band):
		if datatype == "aot":
			s = self.Hdf5ToRawImageAOT(h5file, band)
		elif datatype == "lst":
			s = self.Hdf5ToRawImageLST(h5file)
		else:
			return ""
		if s == "":
			return ""
		s = self.CorrectGCPs(s, datatype)
		if s == "":
			return ""
		s = self.Resample(s, datatype)
		return s

	# resample hdf5 files in directory
	def ResampleHdf5InDir(self, directory, datatype):
		dataprefix, geoprefix = self.factory.DataPrefix(datatype)
		h5files = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.h5') and f.startswith(geoprefix)]
		
		for f in h5files:
			s = self.ChainProcess(f, datatype, BAND)
			if s == 1:
				continue

		rawfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.raw')]
		for f in rawfiles:
			os.remove(f)
		recfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.rec')]
		for f in recfiles:
			os.remove(f)
		vrtfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.vrt')]
		for f in vrtfiles:
			os.remove(f)
		xmlfiles = [f for f in os.listdir(directory) if os.path.isfile(f) and f.endswith('.xml')]
		for f in xmlfiles:
			os.remove(f)
		return 0


