# -*- coding: utf-8 -*-
#--------------------- Copyright Block ----------------------
# Prayer Times Calculator
# Copyright (C) 2007-2010 Hamid Zarrabi-Zadeh
# Copyright (C) Saeed Rasooli
#
# Source: http://praytimes.org
# License: GNU General Public License, version 3
#
# Permission is granted to use this code, with or without
# modification, in any website or application provided that
# the following conditions are met:
#
#	1. Credit is given to the original work with a
#	   link back to PrayTimes.org.
#
#	2. Redistributions of the source code and its
#	   translations into other programming languages
#	   must retain the above copyright notice.
#
# This program is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY.
#
# PLEASE DO NOT REMOVE THIS COPYRIGHT BLOCK.

# User's Manual:
# http://praytimes.org/manual
#
# Calculation Formulas:
# http://praytimes.org/calculation

import time
import math
from math import floor

tr = str ## FIXME

timeNames = (
	'imsak',
	'fajr',
	'sunrise',
	'dhuhr',
	'asr',
	'sunset',
	'maghrib',
	'isha',
	'midnight',
	'timezone',
)

ASR_STANDARD, ASR_HANAFI = (1, 2)
## asr juristics:
##   standard => Shafi`i, Maliki, Ja`fari, Hanbali
##   hanafi => Hanafi
## used in which method? FIXME

MIDNIGHT_STANDARD, MIDNIGHT_JAFARI = list(range(2))
## midnight methods
##   standard => Mid Sunset to Sunrise
##   jafari => Mid Maghrib to Fajr

## Adjust Methods for Higher Latitudes
highLatMethods = (
	'NightMiddle', # middle of night
	'AngleBased',  # angle/60th of night
	'OneSeventh',  # 1/7th of night
	'None'         # No adjustment
)


class Method:
	def __init__(
		self,
		name,
		desc,
		fajr=15,
		isha=15,
		maghrib='0 min',
		midnight=MIDNIGHT_STANDARD,
	):
		self.name = name
		self.desc = desc
		self.fajr = fajr
		self.isha = isha
		self.maghrib = maghrib
		self.midnight = midnight


methodsList = [
	Method(
		'MWL',
		'Muslim World League',
		fajr=18,
		isha=17,
	),
	Method(
		'ISNA',
		'Islamic Society of North America',
		fajr=15,
		isha=15,
	),
	Method(
		'Egypt',
		'Egyptian General Authority of Survey',
		fajr=19.5,
		isha=17.5,
	),
	Method(
		'Makkah',
		'Umm Al-Qura University, Makkah',
		fajr=18.5,
		isha='90 min',
	),  # fajr was 19 degrees before 1430 hijri
	Method(
		'Karachi',
		'University of Islamic Sciences, Karachi',
		fajr=18,
		isha=18,
	),
	Method(
		'Jafari',
		'Shia Ithna-Ashari, Leva Research Institute, Qum',
		fajr=16,
		maghrib=4,
		isha=14,
		midnight=MIDNIGHT_JAFARI,
	),
	Method(
		'Tehran',
		'Institute of Geophysics, University of Tehran',
		fajr=17.7,
		maghrib=4.5,
		midnight=MIDNIGHT_JAFARI,
	),
]

methodsDict = {
	m.name: m for m in methodsList
}

########################### Functions ####################################


def isMin(tm):
	return isinstance(tm, str) and tm.endswith('min')


def minEval(tm):
	return float(tm.split(' ')[0]) if isinstance(tm, str) else tm


def dirSign(direction):
	return -1 if direction == 'ccw' else 1


def dtr(d):
	return (d * math.pi) / 180


def rtd(r):
	return (r * 180) / math.pi


def sin(d):
	return math.sin(dtr(d))


def cos(d):
	return math.cos(dtr(d))


def tan(d):
	return math.tan(dtr(d))


def arcsin(d):
	return rtd(math.asin(d))


def arccos(d):
	return rtd(math.acos(d))


def arctan(d):
	return rtd(math.atan(d))


def arccot(x):
	return rtd(math.atan(1 / x))


def arctan2(y, x):
	return rtd(math.atan2(y, x))


def fix(a, b):
	a = a - b * floor(a / b)
	return a + b if a < 0 else a


def fixAngle(a):
	return fix(a, 360)


def fixHour(a):
	return fix(a, 24)


def timeDiff(time1, time2):
	return fixHour(time2 - time1)


def timesMiddle(time1, time2):
	return time1 + fixHour(time2 - time1) / 2


################################ Classes ################################

class PrayTimes:
	numIterations = 1

	def __init__(
		self,
		lat,
		lng,
		elv=0,
		methodName='Tehran',
		imsak='10 min',
		asrMode=ASR_STANDARD,
		highLats='NightMiddle',
		timeFormat='24h',
	):
		"""
		timeFormat possible values:
			'24h'
			'12h'
			'12hNS': 12-hour format with no suffix
			'Float'
		"""
		self.lat = lat
		self.lng = lng
		self.elv = elv
		self.method = methodsDict[methodName]
		self.imsak = imsak
		self.asrMode = asrMode
		self.highLats = highLats
		self.timeFormat = timeFormat

	def getTimesByJd(self, jd, utcOffset):
		"""
		return prayer times for a given julian day
		"""
		#if time.daylight and time.gmtime(core.getEpochFromJd(jd)):
		#print(time.gmtime((jd-2440588)*(24*3600)).tm_isdst)
		self.utcOffset = utcOffset
		self.jDate = jd - 0.5 - self.lng / (15 * 24)
		return self.computeTimes()

	def getFormattedTime(self, tm, format=None):
		"""
		convert float time to the given format (see timeFormats)
		"""
		assert isinstance(tm, float)
		if not format:
			format = self.timeFormat
		if format == 'float':
			return tm

		tm = fixHour(tm + 0.5 / 60)  # add 0.5 minutes to round
		hours = floor(tm)
		minutes = floor((tm - hours) * 60)
		if format == '24h':
			return '%d:%.2d' % (hours, minutes)
		elif format == '12h':
			return '%d:%.2d %s' % (
				(hours - 1) % 12 + 1,
				minutes,
				tr('AM') if hours < 12 else tr('PM'),
			)
		elif format == '12hNS':
			return '%d:%.2d' % (
				(hours - 1) % 12 + 1,
				minutes,
			)
		else:
			raise ValueError('bad time format %s' % format)

	def midDay(self, tm):
		"""
		compute mid-day time
		"""
		return fixHour(12 - self.sunEquation(self.jDate + tm))

	def sunAngleTime(self, angle, tm, direction='cw'):
		"""
		compute the time at which sun reaches a specific angle below horizon
		"""
		decl = self.sunDeclination(self.jDate + tm)
		noon = self.midDay(tm)
		ratio = (
			-sin(angle) - sin(decl) * sin(self.lat)
		) / (cos(decl) * cos(self.lat))
		ratio = min(max(ratio, -1.0), 1.0)
		#try:
		t = arccos(ratio) / 15
		#except:
		#	print(
		#		'sunAngleTime: angle=%s' % angle +
		#		', tm=%s' % tm +
		#		', direction=%s' % direction +
		#		' ==> ratio=%s' % ratio
		#	)
		#	return 0
		return noon + dirSign(direction) * t

	def asrTime(self, factor, tm):
		"""
		compute asr time
		"""
		return self.sunAngleTime(
			-arccot(
				factor + tan(abs(
					self.lat - self.sunDeclination(self.jDate + tm)
				)),
			),
			tm,
		)

	'''
	# compute declination angle of sun and equation of time
	# Ref: http://aa.usno.navy.mil/faq/docs/SunApprox.php
	def sunPosition(self, jd):
		D = jd - 2451545.0
		g = fixAngle(357.529 + 0.98560028*D)
		q = fixAngle(280.459 + 0.98564736*D)
		L = fixAngle(q + 1.915*sin(g) + 0.020*sin(2*g))

		R = 1.00014 - 0.01671*cos(g) - 0.00014*cos(2*g)
		e = 23.439 - 0.00000036*D

		RA = arctan2(cos(e)*sin(L), cos(L)) / 15.0
		eqt = q/15 - fixHour(RA)
		decl = arcsin(sin(e)*sin(L))

		return {'declination': decl, 'equation': eqt}
	'''

	def sunDeclination(self, jd):
		D = jd - 2451545.0
		g = fixAngle(357.529 + 0.98560028 * D)
		q = fixAngle(280.459 + 0.98564736 * D)
		L = fixAngle(q + 1.915 * sin(g) + 0.020 * sin(2 * g))
		e = 23.439 - 0.00000036 * D
		return arcsin(sin(e) * sin(L))

	def sunEquation(self, jd):
		D = jd - 2451545.0
		g = fixAngle(357.529 + 0.98560028 * D)
		q = fixAngle(280.459 + 0.98564736 * D)
		L = fixAngle(q + 1.915 * sin(g) + 0.020 * sin(2 * g))
		e = 23.439 - 0.00000036 * D
		RA = arctan2(cos(e) * sin(L), cos(L)) / 15
		return q / 15 - fixHour(RA)

	#---------------------- Compute Prayer Times -----------------------

	# compute prayer times
	def computeTimes(self, format=None):
		# default times
		times = {
			'imsak': 5,
			'fajr': 5,
			'sunrise': 6,
			'dhuhr': 12,
			'asr': 13,
			'sunset': 18,
			'maghrib': 18,
			'isha': 18,
		}

		# main iterations
		for i in range(self.numIterations):
			## computePrayerTimes
			## dayPortion
			for key in times:
				times[key] /= 24
			times['imsak'] = self.sunAngleTime(
				minEval(self.imsak),
				times['imsak'],
				'ccw',
			)
			times['fajr'] = self.sunAngleTime(
				minEval(self.method.fajr),
				times['fajr'],
				'ccw',
			)
			times['sunrise'] = self.sunAngleTime(
				self.riseSetAngle(),
				times['sunrise'],
				'ccw',
			)
			times['dhuhr'] = self.midDay(times['dhuhr'])
			times['asr'] = self.asrTime(self.asrMode, times['asr'])
			times['sunset'] = self.sunAngleTime(
				self.riseSetAngle(),
				times['sunset'],
			)
			times['maghrib'] = self.sunAngleTime(
				minEval(self.method.maghrib),
				times['maghrib'],
			)
			times['isha'] = self.sunAngleTime(
				minEval(self.method.isha),
				times['isha'],
			)

		## adjustTimes
		for key in times:
			times[key] += self.utcOffset - self.lng / 15.0
		if self.highLats != 'None':
			## adjustHighLats
			nightTime = timeDiff(
				times['sunset'],
				times['sunrise'],
			)
			times['imsak'] = self.adjustHLTime(
				times['imsak'],
				times['sunrise'],
				minEval(self.imsak),
				nightTime,
				'ccw',
			)
			times['fajr'] = self.adjustHLTime(
				times['fajr'],
				times['sunrise'],
				minEval(self.method.fajr),
				nightTime,
				'ccw',
			)
			times['isha'] = self.adjustHLTime(
				times['isha'],
				times['sunset'],
				minEval(self.method.isha),
				nightTime,
			)
			times['maghrib'] = self.adjustHLTime(
				times['maghrib'],
				times['sunset'],
				minEval(self.method.maghrib),
				nightTime,
			)

		if isMin(self.imsak):
			times['imsak'] = times['fajr'] - minEval(self.imsak) / 60

		if isMin(self.method.maghrib):
			times['maghrib'] = times['sunset'] + minEval(
				self.method.maghrib
			) / 60

		if isMin(self.method.isha):
			times['isha'] = times['maghrib'] + minEval(self.method.isha) / 60

		# add midnight time
		times['midnight'] = timesMiddle(
			times['sunset'],
			times[
				'fajr' if self.method.midnight == MIDNIGHT_JAFARI
				else 'sunrise'
			],
		)

		for key in times:
			times[key] = times[key] % 24

		#times = self.tuneTimes(times)  # FIXME
		#for key in times:
		#	times[key] = self.getFormattedTime(times[key], format)

		times['timezone'] = 'GMT%+.1f' % self.utcOffset
		# ^^^ utcOffset is not timeZone FIXME

		return times

	# return sun angle for sunset/sunrise
	def riseSetAngle(self):
		#earthRad = 6371009 ## in meters
		#angle = arccos(earthRad/(earthRad+self.elv))
		angle = 0.0347 * math.sqrt(self.elv) ## an approximation
		return 0.833 + angle

	#def tuneTimes: ## FIXME

	def adjustHLTime(self, tm, base, angle, night, direction='cw'):
		"""
		adjust a time for higher latitudes
		"""
		# nightPortion: the night portion used for adjusting times in
		# higher latitudes
		if self.highLats == 'AngleBased':
			portion = angle / 6
		elif self.highLats == 'OneSeventh':
			portion = 1 / 7
		else:
			portion = 0.5  # MidNight
		portion *= night

		diff = (
			timeDiff(tm, base) if direction == 'ccw'
			else timeDiff(base, tm)
		)

		if diff > portion:
			tm = base + dirSign(direction) * portion
		return tm
