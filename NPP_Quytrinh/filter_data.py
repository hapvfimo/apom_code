""" This class is used to filter data files covering interest areas by using the filename only """
import os
import sys
import xml.etree.ElementTree as ET
from utilities import GetAcquiredTimeFromFilename
from utilities import GetDateFromFilename
from utilities import GetStartTime
from utilities import GetEndTime
from utilities import GetLogTimeFormat
from constants import MORNING_PASS

class FilterFile:
	
	# construction function
	def __init__(self, log):
		self.file_name = ""
		self.found = 0
		self.log = log

	# check name is covering interest areas by orbit pass time
	def CheckCoveringArea(self, filename, tdata):
		if filename == "":
			return 0
		elif len(filename) != 78:
			return 0
		else:
			acquired_time = GetAcquiredTimeFromFilename(filename, typef = tdata)
			stime = GetStartTime(str(acquired_time))
			etime = GetEndTime(str(acquired_time))
			
			if stime >= GetStartTime(MORNING_PASS) and etime <= GetEndTime(MORNING_PASS) and stime <= GetEndTime(MORNING_PASS) and etime >= GetStartTime(MORNING_PASS):
				return 1
			return 0

	# get file name from xml document
	def FilterFileByName(self, document, output):
		try:
			log = open(self.log, "a")
			# open file
			out = open(output, "a")
			# initializing XML tree and processing
			tree = ET.parse(document)
			root = tree.getroot()
			for fname in root.iter('FileName'):
				status = self.CheckCoveringArea(fname.text, "aot")
				if status == 1:
					out.write(fname.text)
					out.write("\n")
					self.found = 1
			out.close()
			if self.found == 1:
				log.write("[{0}] found data file in {1}\n".format(GetLogTimeFormat(), document))
				self.found = 0
				log.close()
				return 1
			log.close()
			return 0
		except IOError as e:
			out.close()
			log.write(str(e))
			log.close()
			return 0

