#!/usr/bin/env python3
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

from scal3 import logger
log = logger.get()

from math import log10

from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
	getFloatJdFromEpoch,
	getJhmsFromEpoch,
	getUtcOffsetCurrent,
)
from scal3.date_utils import jwday, getEpochFromDate
from scal3.cal_types import calTypes, jd_to, to_jd

from scal3.timeline import tl
from scal3.timeline.box import (
	calcEventBoxes,
)

from scal3.locale_man import tr as _
from scal3.locale_man import (
	rtl,
	numEncode,
	textNumEncode,
	addLRM,
	getMonthName,
)

from scal3 import core
from scal3.core import jd_to_primary

from scal3.color_utils import hslToRgb
from scal3.utils import ifloor, iceil, toBytes
from scal3 import ui
from scal3.ui import getHolidaysJdList

from scal3.timeline import tl
from scal3.timeline.tick import Tick
from scal3.timeline.utils import *

####################################################



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
			y_e = f"{y:E}"
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
				fac_s = _(fac) + "×"
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
	# log.debug(f"dayPixel = {dayPixel} px")

	def getEPos(epoch):
		return (epoch - timeStart) * pixelPerSec

	def getJPos(jd):
		return (getEpochFromJd(jd) - timeStart) * pixelPerSec

	# ###################### Holidays
	holidays = []
	if (
		tl.changeHolidayBg and
		tl.changeHolidayBgMinDays < widthDays < tl.changeHolidayBgMaxDays
	):
		for jd in getHolidaysJdList(jd0, jd1 + 1):
			holidays.append(getJPos(jd))
	# ###################### Ticks
	ticks = []
	tickEpochList = []
	minStep = tl.minorStepMin / pixelPerSec ## second
	#################
	year0, month0, day0 = jd_to_primary(jd0)
	year1, month1, day1 = jd_to_primary(jd1)
	# ########## Year
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
		if unitSize >= tl.majorStepMin:
			label = formatYear(year, prettyPower=tl.yearPrettyPower)
		else:
			label = ""
		ticks.append(Tick(
			tmEpoch,
			getEPos(tmEpoch),
			unitSize,
			label,
		))
		tickEpochList.append(tmEpoch)
	# ########## Month
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
				getMonthName(calTypes.primary, m) if unitSize >= tl.majorStepMin else "",
			))
			tickEpochList.append(tmEpoch)
	################
	if tl.showWeekStart and tl.showWeekStartMinDays < widthDays < tl.showWeekStartMaxDays:
		wd0 = jwday(jd0)
		jdw0 = jd0 + (core.firstWeekDay - wd0) % 7
		unitSize = dayPixel * 7
		if unitSize < tl.majorStepMin:
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
				color=tl.weekStartTickColor,
			))
			# tickEpochList.append(tmEpoch)
	# ########## Day of Month
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
			if unitSize < tl.majorStepMin:
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
	# ########## Hour, Minute, Second
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
			if unitSize < tl.majorStepMin:
				label = ""
			else:
				jd, h, m, s = getJhmsFromEpoch(tmEpoch)
				if s == 0:
					label = f"{_(h)}:{_(m, fillZero=2)}"
				else:# elif timeWidth < 60 or stepSec < 30:
					label = addLRM(_(s, fillZero=2) + '"')
				#else:
				#	label = f"{_(h)}:{_(m, fillZero=2)}:_(s, fillZero=2)"
			ticks.append(Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
			))
			tickEpochList.append(tmEpoch)
	# ###################### Event Boxes
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
