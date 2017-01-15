# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from math import log10

from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
	getFloatJdFromEpoch,
	getJhmsFromEpoch,
	getUtcOffsetByEpoch,
	getUtcOffsetCurrent,
)
from scal3.date_utils import jwday, getEpochFromDate
from scal3.cal_types import calTypes, jd_to, to_jd
from scal3.timeline_box import *
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, numEncode, textNumEncode, addLRM

from scal3 import core
from scal3.core import myRaise, getMonthName, jd_to_primary

from scal3.color_utils import hslToRgb
from scal3.utils import ifloor, iceil, toBytes
from scal3 import ui
from scal3.ui import getHolidaysJdList

####################################################

bgColor = ui.bgColor ## FIXME
fgColor = ui.textColor ## FIXME
baseFontSize = 8

majorStepMin = 50 ## with label
minorStepMin = 5 ## with or without label
maxLabelWidth = 60 ## or the same majorStepMin
baseTickHeight = 1
baseTickWidth = 0.5
maxTickWidth = 20
maxTickHeightRatio = 0.3
labelYRatio = 1.1

currentTimeMarkerHeightRatio = 0.3
currentTimeMarkerWidth = 2
currentTimeMarkerColor = (255, 100, 100)

#sunLightH = 10  # FIXME


showWeekStart = True
showWeekStartMinDays = 1
showWeekStartMaxDays = 60
weekStartTickColor = (0, 200, 0)

changeHolidayBg = False
changeHolidayBgMinDays = 1
changeHolidayBgMaxDays = 60
holidayBgBolor = (60, 35, 35)


scrollZoomStep = 1.2  # > 1
keyboardZoomStep = 1.2  # > 1

#############################################

enableAnimation = False
movingStaticStep = 20
movingUpdateTime = 10 ## milisecons

movingV0 = 0

## Force is the same as Acceleration, assuming Mass == 1

## different for keyboard (arrows) and mouse (scroll) FIXME
movingHandForce = 1100 ## px / (sec**2)
movingHandSmallForce = 900 ## px / (sec**2)

movingFrictionForce = 600 ## px / (sec**2)
## movingHandForce > movingFrictionForce

movingMaxSpeed = 1200 ## px / sec
## movingMaxSpeed = movingAccel * 4
## reach to maximum speed in 4 seconds


movingKeyTimeoutFirst = 0.5

movingKeyTimeout = 0.1 # seconds
# ^ continuous keyPress delay is about 0.05 sec

#############################################
truncateTickLabel = False

# 0: no rotation
# 1: 90 deg CCW (if needed)
# -1: 90 deg CW (if needed)

####################################################

fontFamily = ui.getFont()[0]

dayLen = 24 * 3600
minYearLenSec = 365 * dayLen
avgMonthLen = 30 * dayLen

unitSteps = (
	(3600, 12),
	(3600, 6),
	(3600, 3),
	(3600, 1),
	(60, 30),
	(60, 15),
	(60, 5),
	(60, 1),
	(1, 30),
	(1, 15),
	(1, 5),
	(1, 1),
)


class Tick:
	def __init__(self, epoch, pos, unitSize, label, color=None):
		self.epoch = epoch
		self.pos = pos  # pixel position
		self.height = unitSize ** 0.5 * baseTickHeight
		self.width = min(unitSize ** 0.2 * baseTickWidth, maxTickWidth)
		self.fontSize = unitSize ** 0.1 * baseFontSize
		self.maxLabelWidth = min(unitSize * 0.5, maxLabelWidth)  # FIXME
		self.label = label
		if color is None:
			color = fgColor
		self.color = color


#class Range:
#	def __init__(self, start, end):
#		self.start = start
#		self.end = end
#	def dt(self):
#		return self.end - self.start
#	def __cmp__(self, other):
#		return cmp(self.dt(), other.dt())


def getNum10FactPow(n):
	if n == 0:
		return 0, 1
	n = str(int(n))
	nozero = n.rstrip("0")
	return int(nozero), len(n) - len(nozero)


def getNum10Pow(n):
	return getNum10FactPow(n)[1]


def getYearRangeTickValues(u0, y1, minStepYear):
	data = {}
	step = 10 ** max(0, ifloor(log10(y1 - u0)) - 1)
	u0 = step * (u0 // step)
	for y in range(u0, y1, step):
		n = 10 ** getNum10Pow(y)
		if n >= minStepYear:
			data[y] = n
	if u0 <= 0 <= y1:
		data[0] = max(data.values())
	return sorted(data.items())


def formatYear(y, prettyPower=False):
	if abs(y) < 10 ** 4:## FIXME
		y_st = _(y)
	else:
		#y_st = textNumEncode("%.0E"%y, changeDot=True)## FIXME
		fac, pw = getNum10FactPow(y)
		if not prettyPower or abs(fac) >= 100:## FIXME
			y_e = "%E" % y
			for i in range(10):
				y_e = y_e.replace("0E", "E")
			y_e = y_e.replace(".E", "E")
			y_st = textNumEncode(y_e, changeDot=True)
		else:
			sign = ("-" if fac < 0 else "")
			fac = abs(fac)
			if fac == 1:
				fac_s = ""
			else:
				fac_s = "%s×" % _(fac)
			pw_s = _(10) + "ˆ" + _(pw)
			#pw_s = _(10) + "<span rise="5" size="small">" + \
			#	_(pw) + "</span>"  # Pango Markup Language
			y_st = sign + fac_s + pw_s
	return addLRM(y_st)


#def setRandomColorsToEvents():
#	import random
#	events = ui.events[:]
#	random.shuffle(events)
#	dh = 360.0/len(events)
#	hue = 0
#	for event in events:
#		event.color = hslToRgb(hue, boxColorSaturation, boxColorLightness)
#		hue += dh


def calcTimeLineData(timeStart, timeWidth, pixelPerSec, borderTm):
	timeEnd = timeStart + timeWidth
	jd0 = getJdFromEpoch(timeStart)
	jd1 = getJdFromEpoch(timeEnd)
	widthDays = float(timeWidth) / dayLen
	dayPixel = dayLen * pixelPerSec ## px
	#print("dayPixel = %s px"%dayPixel)
	getEPos = lambda epoch: (epoch - timeStart) * pixelPerSec
	getJPos = lambda jd: (getEpochFromJd(jd) - timeStart) * pixelPerSec
	######################## Holidays
	holidays = []
	if (
		changeHolidayBg and
		changeHolidayBgMinDays < widthDays < changeHolidayBgMaxDays
	):
		for jd in getHolidaysJdList(jd0, jd1 + 1):
			holidays.append(getJPos(jd))
	######################## Ticks
	ticks = []
	tickEpochList = []
	minStep = minorStepMin / pixelPerSec ## second
	#################
	year0, month0, day0 = jd_to_primary(jd0)
	year1, month1, day1 = jd_to_primary(jd1)
	############ Year
	minStepYear = minStep // minYearLenSec ## years ## int or iceil?
	yearPixel = minYearLenSec * pixelPerSec ## pixels
	for (year, size) in getYearRangeTickValues(
		year0,
		year1 + 1,
		minStepYear,
	):
		tmEpoch = getEpochFromDate(year, 1, 1, calTypes.primary)
		if tmEpoch in tickEpochList:
			continue
		unitSize = size * yearPixel
		label = formatYear(year) if unitSize >= majorStepMin else ""
		ticks.append(Tick(
			tmEpoch,
			getEPos(tmEpoch),
			unitSize,
			label,
		))
		tickEpochList.append(tmEpoch)
	############ Month
	monthPixel = avgMonthLen * pixelPerSec ## px
	minMonthUnit = float(minStep) / avgMonthLen ## month
	if minMonthUnit <= 3:
		for ym in range(
			year0 * 12 + (month0 - 1),
			year1 * 12 + (month1 - 1) + 1,  # +1 FIXME
		):
			if ym % 3 == 0:
				monthUnit = 3
			else:
				monthUnit = 1
			if monthUnit < minMonthUnit:
				continue
			y, m = divmod(ym, 12); m += 1
			tmEpoch = getEpochFromDate(y, m, 1, calTypes.primary)
			if tmEpoch in tickEpochList:
				continue
			unitSize = monthPixel * monthUnit
			ticks.append(Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				getMonthName(calTypes.primary, m) if unitSize >= majorStepMin else "",
			))
			tickEpochList.append(tmEpoch)
	################
	if showWeekStart and showWeekStartMinDays < widthDays < showWeekStartMaxDays:
		wd0 = jwday(jd0)
		jdw0 = jd0 + (core.firstWeekDay - wd0) % 7
		unitSize = dayPixel * 7
		if unitSize < majorStepMin:
			label = ""
		else:
			label = core.weekDayNameAb[core.firstWeekDay]
		for jd in range(jdw0, jd1 + 1, 7):
			tmEpoch = getEpochFromJd(jd)
			ticks.append(Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
				color=weekStartTickColor,
			))
			#tickEpochList.append(tmEpoch)
	############ Day of Month
	hasMonthName = timeWidth < 5 * dayLen
	minDayUnit = float(minStep) / dayLen ## days
	if minDayUnit <= 15:
		for jd in range(jd0, jd1 + 1):
			tmEpoch = getEpochFromJd(jd)
			if tmEpoch in tickEpochList:
				continue
			year, month, day = jd_to_primary(jd)
			if day == 16:
				dayUnit = 15
			elif day in (6, 11, 21, 26):
				dayUnit = 5
			else:
				dayUnit = 1
			if dayUnit < minDayUnit:
				continue
			unitSize = dayPixel * dayUnit
			if unitSize < majorStepMin:
				label = ""
			elif hasMonthName:
				label = _(day) + " " + getMonthName(calTypes.primary, month)
			else:
				label = _(day)
			ticks.append(Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
			))
			tickEpochList.append(tmEpoch)
	############ Hour, Minute, Second
	for stepUnit, stepValue in unitSteps:
		stepSec = stepUnit * stepValue
		if stepSec < minStep:
			break
		unitSize = stepSec * pixelPerSec
		utcOffset = int(getUtcOffsetCurrent())
		firstEpoch = iceil(
			(timeStart + utcOffset) / stepSec
		) * stepSec - utcOffset
		for tmEpoch in range(firstEpoch, iceil(timeEnd), stepSec):
			if tmEpoch in tickEpochList:
				continue
			if unitSize < majorStepMin:
				label = ""
			else:
				jd, h, m, s = getJhmsFromEpoch(tmEpoch)
				if s == 0:
					label = "%s:%s" % (
						_(h),
						_(m, fillZero=2),
					)
				else:# elif timeWidth < 60 or stepSec < 30:
					label = addLRM("%s\"" % _(s, fillZero=2))
				#else:
				#	label = "%s:%s:%s"%(
				#		_(h),
				#		_(m, fillZero=2),
				#		_(s, fillZero=2),
				#	)
			ticks.append(Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
			))
			tickEpochList.append(tmEpoch)
	######################## Event Boxes
	data = {
		"holidays": holidays,
		"ticks": ticks,
		"boxes": [],
	}
	###
	data["boxes"] = calcEventBoxes(
		timeStart,
		timeEnd,
		pixelPerSec,
		borderTm,
	)
	###
	return data
