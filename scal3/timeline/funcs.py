#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from scal3 import logger

log = logger.get()

from bisect import bisect_left, bisect_right
from math import log10

from scal3 import core, ui
from scal3.cal_types import calTypes
from scal3.core import jd_to_primary, primary_to_jd
from scal3.date_utils import getEpochFromDate, jwday
from scal3.locale_man import (
	addLRM,
	getMonthName,
	textNumEncode,
)
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
	getJhmsFromEpoch,
	getUtcOffsetByJd,
)
from scal3.timeline import conf
from scal3.timeline.box import (
	calcEventBoxes,
)
from scal3.timeline.tick import Tick
from scal3.timeline.utils import (
	avgMonthLen,
	dayLen,
	minYearLenSec,
	unitSteps,
)
from scal3.ui.funcs import getHolidaysJdList
from scal3.utils import iceil, ifloor

__all__ = ["calcTimeLineData"]


# ----------------------------------------------------


# class Range:
# 	def __init__(self, start, end):
# 		self.start = start
# 		self.end = end
# 	def dt(self):
# 		return self.end - self.start
# 	def __cmp__(self, other):
# 		return cmp(self.dt(), other.dt())


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
	if abs(y) < 10**4:  # FIXME
		y_st = _(y)
	else:
		# y_st = textNumEncode("%.0E"%y, changeDot=True)-- FIXME
		fac, pw = getNum10FactPow(y)
		if not prettyPower or abs(fac) >= 100:  # FIXME
			y_e = f"{y:E}"
			for _i in range(10):
				y_e = y_e.replace("0E", "E")
			y_e = y_e.replace(".E", "E")
			y_st = textNumEncode(y_e, changeDot=True)
		else:
			sign = "-" if fac < 0 else ""
			fac = abs(fac)
			if fac == 1:
				fac_s = ""
			else:
				fac_s = _(fac) + "×"
			pw_s = _(10) + "ˆ" + _(pw)
			# pw_s = _(10) + "<span rise="5" size="small">" + \
			# 	_(pw) + "</span>"  # Pango Markup Language
			y_st = sign + fac_s + pw_s
	return addLRM(y_st)


# def setRandomColorsToEvents():
# 	import random
# 	events = ui.events[:]
# 	random.shuffle(events)
# 	dh = 360.0/len(events)
# 	hue = 0
# 	for event in events:
# 		event.color = hslToRgb(hue, boxColorSaturation, boxColorLightness)
# 		hue += dh


def calcTimeLineData(timeStart, timeWidth, pixelPerSec, borderTm):
	# from time import time as now
	# funcTimeStart = now()
	timeEnd = timeStart + timeWidth
	jd0 = getJdFromEpoch(timeStart)
	jd1 = getJdFromEpoch(timeEnd)
	widthDays = timeWidth / dayLen
	dayPixel = dayLen * pixelPerSec  # px
	# log.debug(f"{dayPixel = } px")

	def getEPos(epoch):
		return (epoch - timeStart) * pixelPerSec

	def getJPos(jd):
		return (getEpochFromJd(jd) - timeStart) * pixelPerSec

	# ---------------------- Holidays
	holidays = []
	if (
		conf.changeHolidayBg.v
		and conf.changeHolidayBgMinDays.v < widthDays < conf.changeHolidayBgMaxDays.v
	):
		holidays = [getJPos(jd) for jd in getHolidaysJdList(ui.cells, jd0, jd1 + 1)]
	# ---------------------- Ticks
	ticks = []
	tickEpochSet = set()
	minStep = conf.minorStepMin.v / pixelPerSec  # second
	# -----------------
	year0, month0, day0 = jd_to_primary(jd0)
	year1, month1, day1 = jd_to_primary(jd1)
	# ---------- Year
	minStepYear = minStep // minYearLenSec  # years # int or iceil?
	yearPixel = minYearLenSec * pixelPerSec  # pixels
	for year, size in getYearRangeTickValues(
		year0,
		year1 + 1,
		minStepYear,
	):
		tmEpoch = getEpochFromDate(year, 1, 1, calTypes.primary)
		if tmEpoch in tickEpochSet:
			continue
		unitSize = size * yearPixel
		if unitSize >= conf.majorStepMin.v:
			label = formatYear(year, prettyPower=conf.yearPrettyPower.v)
		else:
			label = ""
		ticks.append(
			Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
			),
		)
		tickEpochSet.add(tmEpoch)
	# ---------- Month
	monthPixel = avgMonthLen * pixelPerSec  # px
	minMonthUnit = minStep / avgMonthLen  # month
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
			year, mm1 = divmod(ym, 12)
			month = mm1 + 1
			tmEpoch = getEpochFromDate(year, month, 1, calTypes.primary)
			if tmEpoch in tickEpochSet:
				continue
			unitSize = monthPixel * monthUnit
			monthName = (
				getMonthName(calTypes.primary, month)
				if unitSize >= conf.majorStepMin.v
				else ""
			)
			ticks.append(
				Tick(
					tmEpoch,
					getEPos(tmEpoch),
					unitSize,
					monthName,
				),
			)
			tickEpochSet.add(tmEpoch)
	# -------------- Week days
	if (
		conf.showWeekStart.v
		and conf.showWeekStartMinDays.v < widthDays < conf.showWeekStartMaxDays.v
	):
		wd0 = jwday(jd0)
		jdw0 = jd0 + (core.firstWeekDay.v - wd0) % 7
		unitSize = dayPixel * 7
		if unitSize < conf.majorStepMin.v:
			label = ""
		else:
			label = core.weekDayNameAb[core.firstWeekDay.v]
		for jd in range(jdw0, jd1 + 1, 7):
			tmEpoch = getEpochFromJd(jd)
			ticks.append(
				Tick(
					tmEpoch,
					getEPos(tmEpoch),
					unitSize,
					label,
					color=conf.weekStartTickColor.v,
				),
			)
			# tickEpochSet.add(tmEpoch)
	# ---------- Day of Month
	hasMonthName = timeWidth < 5 * dayLen
	minDayUnit = minStep / dayLen  # days

	def addDayOfMonthTick(jd, month, day, dayUnit) -> None:
		tmEpoch = getEpochFromJd(jd)
		unitSize = dayPixel * dayUnit
		if unitSize < conf.majorStepMin.v:
			label = ""
		elif hasMonthName:
			label = _(day) + " " + getMonthName(calTypes.primary, month)
		else:
			label = _(day)
		ticks.append(
			Tick(
				tmEpoch,
				getEPos(tmEpoch),
				unitSize,
				label,
			),
		)
		tickEpochSet.add(tmEpoch)

	if minDayUnit <= 1 and jd1 - jd0 < 70:
		for jd in range(jd0, jd1 + 1):
			year, month, day = jd_to_primary(jd)
			if day in {1, 16}:
				continue
			addDayOfMonthTick(jd, month, day, 1)

	if minDayUnit <= 5:
		tmpDays = [6, 11, 21, 26]

		year0, month0, day0 = jd_to_primary(jd0)
		year1, month1, day1 = jd_to_primary(jd1)

		for day in tmpDays[bisect_right(tmpDays, day0 - 1) :]:
			addDayOfMonthTick(jd0 - day0 + day, month0, day, 5)

		for ym in range(year0 * 12 + month0, year1 * 12 + month1 - 1):
			year, mm = divmod(ym, 12)
			month = mm + 1
			startJd = primary_to_jd(year, month, 1) - 1
			for day in tmpDays:
				addDayOfMonthTick(startJd + day, month, day, 5)

		for day in tmpDays[: bisect_left(tmpDays, day1 + 1)]:
			addDayOfMonthTick(jd1 - day1 + day, month1, day, 5)

	if minDayUnit <= 15:
		year0, month0, day0 = jd_to_primary(jd0)
		ym0 = year0 * 12 + month0 - 1
		if day0 > 16:
			ym0 += 1
		year1, month1, day1 = jd_to_primary(jd1)
		ym1 = year1 * 12 + month1 - 1
		if day1 < 16:
			ym1 -= 1
		for ym in range(ym0, ym1 + 1):
			year, mm = divmod(ym, 12)
			month = mm + 1
			jd = primary_to_jd(year, month, 16)
			addDayOfMonthTick(jd, month, 16, 15)

	# ---------- Hour, Minute, Second
	for stepUnit, stepValue in unitSteps:
		stepSec = stepUnit * stepValue
		if stepSec < minStep:
			break
		unitSize = stepSec * pixelPerSec
		for jd in range(jd0, jd1 + 1):
			utcOffset = getUtcOffsetByJd(jd)
			firstEpoch = (
				iceil(
					(timeStart + utcOffset) / stepSec,
				)
				* stepSec
				- utcOffset
			)
			for tmEpoch in range(
				firstEpoch,
				min(getEpochFromJd(jd + 1), iceil(timeEnd)),
				stepSec,
			):
				if tmEpoch in tickEpochSet:
					continue
				if unitSize < conf.majorStepMin.v:
					label = ""
				else:
					_jd, hms = getJhmsFromEpoch(tmEpoch)
					m2 = _(hms.m, fillZero=2)
					if hms.s == 0:
						label = f"{_(hms.h)}:{m2}"
					else:  # elif timeWidth < 60 or stepSec < 30:
						label = addLRM(_(hms.s, fillZero=2) + '"')
					# else:
					# 	label = f"{_(hms.h)}:{m2}:_(hms.s, fillZero=2)"
				ticks.append(
					Tick(
						tmEpoch,
						getEPos(tmEpoch),
						unitSize,
						label,
					),
				)
				tickEpochSet.add(tmEpoch)
	# ---------------------- Event Boxes
	data = {
		"holidays": holidays,
		"ticks": ticks,
		"boxes": [],
	}
	# ---
	data["boxes"] = calcEventBoxes(
		timeStart,
		timeEnd,
		pixelPerSec,
		borderTm,
	)
	# ---
	return data
