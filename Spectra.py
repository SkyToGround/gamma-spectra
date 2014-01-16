#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python
# encoding: utf-8

import struct
import numpy
import re
import datetime

class Spectra:
	def __init__(self, filename):
		fl = open(filename, "rb")
		data = fl.read()
		fl.close()
		if (struct.unpack("<h", data[0:2])[0] == -1):
			self.read_as_chn(filename)
		elif (struct.unpack("<hh", data[0:4]) == (1,1)):
			self.read_as_binary(filename)
		elif (filename[-3:] == "IEC" or filename[-3:] == "iec"):
			self.read_as_iec(filename)
		else:
			self.read_as_text_new(filename)
	
	def read_as_iec(self, filename):
		fl = open(filename, "r")
		self.data = fl.read()
		fl.close()
		
		line_data = self.data.split("\n")
		
		times_and_ch = re.match("A004[ ]{0,13}([0-9.]{1,14})[ ]{0,13}([0-9.]{1,14})[ ]{0,13}([0-9]{1,14})", line_data[1])
		self.realtime = float(times_and_ch.group(2))
		self.livetime = float(times_and_ch.group(1))
		self.channels = int(times_and_ch.group(3))
		calibration = re.match("A004[ ]{0,13}([-0-9.e]+)[ ]{0,13}([-0-9.e]+)[ ]{0,13}([-0-9.e]+)", line_data[3])
		self.A = float(calibration.group(1))
		self.B = float(calibration.group(2))
		self.C = float(calibration.group(3))
		channels = numpy.arange(self.channels)
		self.energy_calibration = self.A + channels * self.B
		
		spec_pos = self.data.find("A004USERDEFINED")
		
		spec_raw_data = self.data[spec_pos:]
		spec_lines = spec_raw_data.split("\n")
		
		self.spectra = numpy.zeros(self.channels, dtype = numpy.uint32)
		
		reg_exp = re.compile("A004[ ]{1,5}[0-9]{1,5}[ ]{1,9}([0-9]{1,9})[ ]{1,9}([0-9]{1,9})[ ]{1,9}([0-9]{1,9})[ ]{1,9}([0-9]{1,9})[ ]{1,9}([0-9]{1,9})")
		for i in range(1, len(spec_lines)):
			res = re.match(reg_exp, spec_lines[i])
			self.spectra[(i - 1) * 5] = int(res.group(1))
			try:
				self.spectra[(i - 1) * 5 + 1] = int(res.group(2))
				self.spectra[(i - 1) * 5 + 2] = int(res.group(3))
				self.spectra[(i - 1) * 5 + 3] = int(res.group(4))
				self.spectra[(i - 1) * 5 + 4] = int(res.group(5))
			except IndexError, e:
				break
	
	def read_as_chn(self, filename):
		fl = open(filename, "rb")
		self.data = fl.read()
		fl.close()
		unpack_str = "<hhhhii8s4shh"
		header_res = struct.unpack(unpack_str, self.data[0:struct.calcsize(unpack_str)])
		#print header_res
		self.meta_data = {}
		self.realtime = header_res[4] * 0.02
		self.livetime = header_res[5] * 0.02
		self.channels = header_res[9]
		
		dt = numpy.dtype(numpy.uint32)
		dt = dt.newbyteorder("<")
		self.spectra = numpy.fromstring(self.data[struct.calcsize(unpack_str):struct.calcsize(unpack_str) + 4 * self.channels], dtype = dt)
		
		footer_str = "<hhffffff"
		footer_res = struct.unpack(footer_str, self.data[struct.calcsize(unpack_str) + 4 * self.channels : struct.calcsize(unpack_str) + 4 * self.channels + struct.calcsize(footer_str)])
		self.A = footer_res[2]
		self.B = footer_res[3]
		self.C = footer_res[4]
		channels = numpy.arange(self.channels)
		#print self.channels
		#print self.spectra.shape
		self.energy_calibration = self.A + channels * self.B# + channels**self.C
	
	def read_as_binary(self, filename):
		fl = open(filename, "rb")
		self.data = fl.read()
		fl.close()
		self.len = len(self.data)
		self.res = struct.unpack("<hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhfdhhhhhff", self.data[0:98])
		# for i in range(len(self.res)):
		# 	print str(i + 1) + " :  " + str(self.res[i])
		self.realtime = self.res[41]
		self.livetime = self.res[42]
		self.meta_data = {}
		self.meta_data["ACQIRP"] = self.res[4]
		self.meta_data["SAMDRP"] = self.res[5]
		self.meta_data["DETDRP"] = self.res[6]
		self.meta_data["EBRDESC"] = self.res[7]
		self.meta_data["ANARP1"] = self.res[8]
		self.meta_data["ANARP2"] = self.res[9]
		self.meta_data["ANARP3"] = self.res[10]
		self.meta_data["ANARP4"] = self.res[11]
		self.meta_data["SRPDES"] = self.res[12]
		self.meta_data["IEQDESC"] = self.res[13]
		self.meta_data["GEODES"] = self.res[14]
		self.meta_data["MPCDESC"] = self.res[15]
		self.meta_data["CALDES"] = self.res[16]
		self.meta_data["CALRP1"] = self.res[17]
		self.meta_data["CALRP2"] = self.res[18]
		self.meta_data["SPCTRP"] = self.res[30]
		self.meta_data["SPCRCN"] = self.res[31]
		self.meta_data["SPCCHN"] = self.res[32]
		self.meta_data["ABSTCH"] = self.res[33]
		self.meta_data["ACQTIM"] = self.res[34]
		self.meta_data["ACQTI8"] = self.res[35]
		self.meta_data["SEQNUM"] = self.res[36]
		self.meta_data["MCANU"] = self.res[37]
		self.meta_data["SEGNUM"] = self.res[38]
		self.meta_data["MCADVT"] = self.res[39]
		self.meta_data["CHNSRT"] = self.res[40]
		self.meta_data["RLTMDT"] = self.res[41]
		self.meta_data["LVTMDT"] = self.res[42]
		self.channels = self.meta_data["SPCCHN"]
		# for i in range(0, len(res)):
		# 	print str(i + 1) + " : " + str(res[i])
		self.ACQINFO = struct.unpack("<128s", self.data[128 * self.res[4]:128 * self.res[4] + 128])[0].strip()
		self.SAMDINFO = struct.unpack("<128s", self.data[128 * self.res[5]:128 * self.res[5] + 128])[0].strip()
		self.spectra = self.extract_integer_spect()
		self.extract_acq_inf_rec()
		self.extract_sample_desc()
		self.extract_det_desc()
		self.extract_analysis_param()
		self.extract_en_cal()
		#self.extract_ebr_desc()
		#self.detector_name = "Hej"
	
	def read_as_text_new(self, filename):
		fl = open(filename, "rb")
		self.lines = fl.read()
		fl.close()
		i = 0
		self.meta_data = {}
		key_word_re = re.compile("\$([A-Z_]+):")
		for res in re.finditer(key_word_re, self.lines):
			sub_str = self.lines[res.end(0) + 2:]
			tmp_res = key_word_re.search(sub_str)
			if (tmp_res != None):
				sub_str = sub_str[0:tmp_res.start(0) - 2]
			self.meta_data[res.group(1)] = sub_str
		
		#Take care of spectral data
		spec_data = self.meta_data["DATA"]
		spec_lines = spec_data.split("\r\n")
		channels_re = re.compile("([0-9]+) ([0-9]+)")
		self.channels = int(channels_re.match(spec_lines[0]).group(2)) + 1
		self.spectra = numpy.zeros(self.channels)
		for i in range(1, len(spec_lines)):
			self.spectra[i - 1] = int(spec_lines[i])
		
		#Take care of real and live time
		time_data = self.meta_data["MEAS_TIM"]
		times_re = re.compile("([0-9]+) ([0-9]+)")
		times_res = times_re.match(time_data)
		self.livetime = float(times_res.group(1))
		self.realtime = float(times_res.group(2))
		
		#Take care of energy calibration
		energy_cal_data = self.meta_data["MCA_CAL"]
		cal_re = re.compile("3\r\n([+-]{0,1}[0-9]+.[0-9]+E[+-]{1}[0-9]{3}) ([+-]{0,1}[0-9]+.[0-9]+E[+-]{1}[0-9]{3}) ([+-]{0,1}[0-9]+.[0-9]+E[+-]{1}[0-9]{3})")
		cal_re_res = cal_re.match(energy_cal_data)
		self.A = float(cal_re_res.group(1))
		self.B = float(cal_re_res.group(2))
		self.C = float(cal_re_res.group(3))
		channels = numpy.arange(self.channels)
		self.energy_calibration = self.A + channels * self.B# + channels**self.C
		
		self.interpret_datefrom_txt_file()
	
	def interpret_datefrom_txt_file(self):
		datetime_str = self.meta_data["DATE_MEA"]
		self.datetime = self.start_time = self.starttime = datetime.datetime.strptime(self.meta_data["DATE_MEA"], "%m/%d/%Y %H:%M:%S")
		self.time = self.datetime
		self.date = self.datetime.date()
		self.time = self.datetime.time()
	
	def read_as_text(self, filename):
		fl = open(filename, "r")
		lines = fl.readlines()
		fl.close()
		times_line = lines[9]
		times_re = re.compile("([0-9]+) ([0-9]+)")
		re_res = times_re.match(times_line)
		self.livetime = float(re_res.group(1))
		self.realtime = float(re_res.group(2))
		for i in range(0, len(lines)):
			if (lines[i] == "$DATA:\r\n"):
				channels = int(lines[i + 1][2:]) + 1
				self.spectra = numpy.empty([channels])
				for t in range(0, channels):
					self.spectra[t] = float(lines[i + 2 + t])
				break
	
	def extract_integer_spect(self):
		dt = numpy.dtype(numpy.uint32)
		dt = dt.newbyteorder("<")
		SPCTRP = self.meta_data["SPCTRP"]
		SPCRCN = self.meta_data["SPCRCN"]
		return numpy.fromstring(self.data[(SPCTRP - 1) * 128: (SPCTRP - 1 + SPCRCN) * 128], dtype = dt)
	
	def extract_acq_inf_rec(self):
		ACQIRP = self.meta_data["ACQIRP"]
		relevant_str = self.data[(ACQIRP - 1) * 128: (ACQIRP - 1) * 128 + 90]
		self.short_file_name = relevant_str[0:16]
		self.date_str = relevant_str[16:27]
		self.time_str = relevant_str[28:38]
		self.live_time_str = relevant_str[38:48]
		self.real_time_str = relevant_str[48:58]
		datetime_str = self.date_str[:-2] + " " + self.time_str[:-2]
		self.datetime = self.start_time = self.starttime = datetime.datetime.strptime(datetime_str, "%d-%b-%y %H:%M:%S")
		self.time = self.datetime
		self.date = self.datetime.date()
		self.time = self.datetime.time()
	
	def extract_sample_desc(self):
		SAMDRP = self.meta_data["SAMDRP"]
		relevant_str = self.data[(SAMDRP - 1) * 128: (SAMDRP) * 128]
		self.sample_desc_str = relevant_str
	
	def extract_det_desc(self):
		DETDRP = self.meta_data["DETDRP"]
		relevant_str = self.data[(DETDRP - 1) * 128: (DETDRP) * 128]
		self.det_desc_str = relevant_str
		
	def extract_ebr_desc(self):
		EBRDESC = self.meta_data["EBRDESC"]
		relevant_str = self.data[(EBRDESC - 1) * 128: (EBRDESC) * 128]
		self.det_ebr_str = relevant_str
	
	def extract_analysis_param(self):
		ANARP1 = self.meta_data["ANARP1"]
		ANARP2 = self.meta_data["ANARP2"]
		ANARP3 = self.meta_data["ANARP3"]
		relevant_str1 = self.data[(ANARP1 - 1) * 128: ANARP1 *128]
		relevant_str2 = self.data[(ANARP2 - 1) * 128: ANARP2 *128]
		relevant_str3 = self.data[(ANARP3 - 1) * 128: ANARP3 *128]
	
	def extract_en_cal(self):
		CALDES = self.meta_data["CALDES"]
		CALRP1 = self.meta_data["CALRP1"]
		CALRP2 = self.meta_data["CALRP2"]
		relevant_str1 = self.data[(CALDES - 1) * 128: CALDES *128]
		relevant_str2 = self.data[(CALRP1 - 1) * 128: CALRP1 *128]
		relevant_str3 = self.data[(CALRP2 - 1) * 128: CALRP2 *128]
		unpack_str_1 = "<hhhhffffff"
		res1 = struct.unpack(unpack_str_1, relevant_str2[0:struct.calcsize(unpack_str_1)])
		self.A = res1[7]
		self.B = res1[8]
		self.C = res1[9]
		#print A, B, C
		channels = numpy.arange(self.channels)
		self.energy_calibration = self.A + channels * self.B# + channels**self.C
	
	def calculate_channel(self, energy):
		return (energy - self.A) / self.B
	
	def calculate_energy(self, channel):
		return self.A + self.B * channel
	
	def redo_energy_cal(self, A = None, B = None, C = None):
		if (A != None):
			self.A = A
		if (B != None):
			self.B = B
		if (C != None):
			self.C = C
		channels = numpy.arange(self.channels)
		self.energy_calibration = self.A + channels * self.B
	
	def show_spectra(self):
		import pylab as pl
		fig = pl.figure()
		ax1 = fig.add_subplot(111)
		channel_arr = numpy.arange(self.channels)
		ax1.plot(channel_arr, self.spectra, lw = 2, color = "blue")
		# for tl in ax1.get_yticklabels():
		#     tl.set_color('b')
		ax1.set_xlabel("Tid")
		ax1.set_ylabel(u"Höjd")
		ax2 = ax1.twinx()
		ax2.plot(time_data[start:stop], abs(vert_vel[start-1:stop]), lw = 2, color = "red")
		#pl.plot(time_data[start:stop], abs(vert_vel[start-1:stop]))
		ax2.set_ylabel("Hastighet (m/s)")
		for tl in ax2.get_yticklabels():
		    tl.set_color('r')
		pl.show()
		

if __name__ == '__main__':
	#spc = Spectra("bkg_mat_hemma/bkg_matning_hpge_000.spc")
	spc = Spectra("Obpri_Parkinglot_2A.Spc")
	from pylab import plot, show
	plot(spc.energy_calibration, spc.spectra)
	show()
	#spc = Spectra("../length/pos_000.spc")
	#variables = ["SPCRCN", "SPCCHN", "ABSTCH", "ACQTIM", "ACQTI8", "SEQNUM", "MCANU", "SEGNUM", "MCADVT", "CHNSRT", "RLTMDT", "LVTMDT"]
	#for a in variables:
	#	try:
	#		print a + ": " + str(spc.meta_data[a])
	#	except:
	#		print "Failed to locate the variable \"" + a + "\""
	# plot(spc.spectra)
	# show()
