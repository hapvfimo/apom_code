""" This is class for connecting and inserting data into data server"""
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
from os.path import dirname
from gdalconst import *
from pylab import *
import glob

###################################################################
NODATA = -9999.0
PM25LOWVALUE = 0.0
PM25HIGHVALUE = 500.0
QCPM25 = 50

# return threshod ranges of international for PM2.5
def RangesPM25Global():

	# declare array to save data
	RANGE = []
	# 7 sub-arrays to save 7 ranges
	for i in range (0, 7):
		RANGE.append([])
	
	# fill data in RANGE
	RANGE[0].append(0.0)
	RANGE[0].append(12.0)
	
	RANGE[1].append(12.0)
	RANGE[1].append(35.4)

	RANGE[2].append(35.4)
	RANGE[2].append(55.4)
	
	RANGE[3].append(55.4)
	RANGE[3].append(150.4)
	
	RANGE[4].append(150.4)
	RANGE[4].append(250.4)
		
	RANGE[5].append(250.4)
	RANGE[5].append(350.4)
	
	RANGE[6].append(350.4)
	RANGE[6].append(500.0)
	
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

###################################################################

###########################################################
# This part for creating AQI PNG images 
# return colors standard of international for PM2.5/PM10
def ColorsGlobal():
	
	# declare array to save data
	COLOR = []
	
	# 7 sub-arrays to save 7 ranges
	for i in range (0, 7):
		COLOR.append([])
	
	# fill data in RANGE
	COLOR[0].append(0)
	COLOR[0].append(228)
	COLOR[0].append(0)
	
	COLOR[1].append(255)
	COLOR[1].append(255)
	COLOR[1].append(0)

	COLOR[2].append(255)
	COLOR[2].append(126)
	COLOR[2].append(0)
	
	COLOR[3].append(255)
	COLOR[3].append(0)
	COLOR[3].append(0)
	
	COLOR[4].append(153)
	COLOR[4].append(0)
	COLOR[4].append(76)
	
	COLOR[5].append(126)
	COLOR[5].append(0)
	COLOR[5].append(35)
	
	COLOR[6].append(126)
	COLOR[6].append(0)
	COLOR[6].append(35)

	return COLOR

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

# create transparent files
def CreateTransparentBand(pmfile, savedir, transfile):
	ori = "{0}/{1}".format(savedir, pmfile)
	copyfile(ori, transfile)

	src = gdal.Open(ori, gdal.GA_ReadOnly)
	band = src.GetRasterBand(1)
	data = band.ReadAsArray()

	srcA = gdal.Open(transfile, gdal.GA_Update)
	bandA = srcA.GetRasterBand(1)
	dataA = bandA.ReadAsArray()

	i = 0
	j = 0
	for n in data:
		for m in n:
			if data[i, j] > 0.0:
				dataA[i, j] = 255
			else:
				dataA[i, j] = 0
			j = j + 1
		j = 0
		i = i + 1
	bandA.WriteArray(dataA)
	del data, band, src, dataA, bandA, srcA

# calculate AQI value based on international standard 2013: QCVN 05:2013/BTNMT
def PMConversion(pmfile):

	# open pm file and get data band
	dset = gdal.Open(pmfile, gdal.GA_Update)
	dband = dset.GetRasterBand(1)
	ddata = dband.ReadAsArray()

	RANGE = RangesPM25Global()
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
			else:
				ddata[i, j] = -1.0
			j = j + 1
		j = 0
		i = i + 1
	
	# save/close the file
	dband.WriteArray(ddata)
	del ddata, dband, dset
	
	return pmfile

def CreatePM25PNGImg(pmfile, savedir):

	# backup PM original file
	copyfile("{0}/{1}".format(savedir, pmfile), "{0}/data_temp.tif".format(savedir))
	
	# convert PM to AQI
	PMConversion("{0}/data_temp.tif".format(savedir))
		
	# create color table and create color file for PM
	CreateColorMap("{0}/color_relief.txt".format(savedir))
	colorfile = savedir + "/" + pmfile[:-4] + ".col"
	CreateColorImage("{0}/data_temp.tif".format(savedir), "{0}/color_relief.txt".format(savedir), colorfile)
	transfile = "{0}/transparent.tif".format(savedir)
	CreateTransparentBand(pmfile, savedir, transfile)
	product = CreateAQIProdFromRGBAndAQI(colorfile, transfile)
	os.system("gdal_translate -of PNG {0} {1}".format(product, product[:-11] + "png"))
	# remove temp files
	os.remove(product)
	os.remove("{0}/data_temp.tif".format(savedir))
	os.remove("{0}/color_relief.txt".format(savedir))
	os.remove("{0}/transparent.tif".format(savedir))

CreatePM25PNGImg(sys.argv[1], sys.argv[2])

