#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

import time
from time import time as now

from scal3.time_utils import getUtcOffsetByGDate
from scal3.cal_types import calTypes, gregorian, to_jd
from scal3 import core
from scal3.locale_man import tr as _
from scal3.types_starcal import CompiledTimeFormat


def iso_to_jd(year, week, day):
	"""
	Return Julian day of given ISO year, week, and day
	"""
	# assert week > 0 and day > 0 and day <= 7
	jd0 = gregorian.to_jd(year - 1, 12, 28)
	return day + 7 * week + jd0 - jd0 % 7 - 1


def isow_year(jd):
	""" iso week year """
	year = gregorian.jd_to(jd - 3)[0]
	if jd >= iso_to_jd(year + 1, 1, 1):
		year += 1
	return year


def isow(jd):
	""" iso week number """
	year = gregorian.jd_to(jd - 3)[0]
	if jd >= iso_to_jd(year + 1, 1, 1):
		year += 1
	return (jd - iso_to_jd(year, 1, 1)) // 7 + 1


def compileTmFormat(format, hasTime=True) -> CompiledTimeFormat:
	# format:     "Today: %Y/%m/%d"
	# pyFmt:      "Today: %s/%s/%s"
	# funcs:      (get_y, get_m, get_d)
	pyFmt = ""
	funcs = []
	n = len(format)
	i = 0
	while i < n:
		c0 = format[i]
		if c0 != "%":
			pyFmt += c0
			i += 1
			continue
		if i == n - 1:
			pyFmt += c0
			break
		c1 = format[i + 1]
		if c1 == "%":
			pyFmt += "%"
			i += 2
			continue
		if c1 == "Y":
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][0],
				fillZero=4,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "y":
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][0] % 100,
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "m":
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][1],
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "d":
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][2],
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "Q":  # calendar name (gregorian, jalali, ...)
			funcs.append(lambda cell, calType, tm: _(
				calTypes.nameByIndex(calType),
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "a":
			funcs.append(
				lambda cell, calType, tm:
					core.weekDayNameAb[cell.weekDay]
			)
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "A":
			funcs.append(
				lambda cell, calType, tm:
					core.weekDayName[cell.weekDay]
			)
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "b" or c1 == "h":  # FIXME
			def f(cell, calType, tm):
				module, ok = calTypes[calType]
				if not ok:
					raise RuntimeError(f"cal type '{calType}' not found")
				return module.getMonthNameAb(cell.dates[calType][1])
			funcs.append(f)
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "B":
			def f(cell, calType, tm):
				module, ok = calTypes[calType]
				if not ok:
					raise RuntimeError(f"cal type '{calType}' not found")
				return module.getMonthName(cell.dates[calType][1])
			funcs.append(f)
			pyFmt += "%s"
			i += 2
			continue
		# elif c1 == "c":
		# 	TODO: locale's date and time (e.g., Thu Mar    3 23:05:25 2005)
		# elif c1 == "x":
		# 	TODO: locale's date representation (e.g., 12/31/99)
		elif c1 == "C":
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][0] // 100,
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "D":  # %m/%d/%y
			funcs += [
				lambda cell, calType, tm: _(
					cell.dates[calType][1],
					fillZero=2,
				),
				lambda cell, calType, tm: _(
					cell.dates[calType][2],
					fillZero=2,
				),
				lambda cell, calType, tm: _(
					cell.dates[calType][0] % 100,
					fillZero=2,
				),
			]
			pyFmt += "%s/%s/%s"
			i += 2
			continue
		elif c1 == "e":  # day of month, space padded; same as %_d
			funcs.append(lambda cell, calType, tm: _(
				cell.dates[calType][2],
				fillZero=2,
			))
			pyFmt += "%2s"
			i += 2
			continue
		elif c1 == "F":  # %Y-%m-%d
			funcs += [
				lambda cell, calType, tm: _(
					cell.dates[calType][0],
					fillZero=4,
				),
				lambda cell, calType, tm: _(
					cell.dates[calType][1],
					fillZero=2,
				),
				lambda cell, calType, tm: _(
					cell.dates[calType][2],
					fillZero=2,
				),
			]
			pyFmt += "%s-%s-%s"
			i += 2
			continue
		elif c1 == "g":  # not affected by calType!
			funcs.append(lambda cell, calType, tm: _(
				isow_year(cell.jd) % 100,
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "G":  # not affected by calType!
			funcs.append(lambda cell, calType, tm: _(
				isow_year(cell.jd),
				fillZero=4,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "V":  # not affected by calType!
			funcs.append(lambda cell, calType, tm: _(
				isow(cell.jd),
				fillZero=2,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "u":
			funcs.append(lambda cell, calType, tm: _(
				cell.jd % 7 + 1,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "w":
			funcs.append(lambda cell, calType, tm: _(
				(cell.jd + 1) % 7
			))  # jwday
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "W":
			def weekNumberMonday(cell, calType, tm):
				jd0 = to_jd(cell.dates[calType][0], 1, 1, calType)
				return _(
					(cell.jd - jd0 + jd0 % 7) // 7,
					fillZero=2,
				)
			funcs.append(weekNumberMonday)
			pyFmt += "%s"
			i += 2
			continue
		# elif c1 == "U":  # FIXME
		# 	funcs.append(lambda cell, calType, tm: _())
		# 	pyFmt += "%s"
		# 	i += 2
		# 	continue
		elif c1 == "j":
			funcs.append(lambda cell, calType, tm: _(
				cell.jd - to_jd(cell.dates[calType][0], 1, 1, calType) + 1,
				fillZero=3,
			))
			pyFmt += "%s"
			i += 2
			continue
		elif c1 == "n":
			pyFmt += "\n"
			i += 2
			continue
		elif c1 == "t":
			pyFmt += "\t"
			i += 2
			continue
		elif c1 == "z":
			def tz(cell, calType, tm):
				m = int(
					getUtcOffsetByGDate(*cell.dates[core.GREGORIAN]) / 60
				)
				return _(m // 60, fillZero=2) + _(m % 60, fillZero=2)
			funcs.append(tz)
			pyFmt += "%s"
			i += 2
			continue
		# elif c1 == "Z":  # alphabetic time zone abbreviation (e.g., EDT)
		elif c1 == ":":
			c2 = format[i + 2]
			if c2 == "z":  # %:z
				def tz(cell, calType, tm):
					m = int(
						getUtcOffsetByGDate(*cell.dates[core.GREGORIAN]) / 60
					)
					return _(m // 60, fillZero=2) + ":" + _(m % 60, fillZero=2)
				funcs.append(tz)
				pyFmt += "%s"
				i += 3
				continue
			# %::z , %:::z
			# elif c2 == ":":  # FIXME
		elif hasTime:
			if c1 == "H":
				funcs.append(lambda cell, calType, tm: _(
					tm[0],
					fillZero=2,
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "I":
				funcs.append(lambda cell, calType, tm: _(
					(tm[0] - 1) % 12 + 1,
					fillZero=2,
				))  # FIXME
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "k":
				funcs.append(lambda cell, calType, tm: _(
					tm[0],
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "l":
				funcs.append(lambda cell, calType, tm: _(
					(tm[0] - 1) % 12 + 1
				))  # FIXME
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "r":  # %I:%M:%s PM
				funcs.append(
					lambda cell, calType, tm:
						_((tm[0] - 1) % 12 + 1, fillZero=2) + ":" +
						_(tm[1], fillZero=2) + ":" +
						_(tm[2], fillZero=2) + " " +
						_("AM" if tm[0] < 12 else "PM")
				)
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "R":  # %H:%M
				funcs.append(
					lambda cell, calType, tm:
						_(tm[0], fillZero=2) + ":" +
						_(tm[1], fillZero=2)
				)
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "M":
				funcs.append(lambda cell, calType, tm: _(
					tm[1],
					fillZero=2,
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "S":
				funcs.append(lambda cell, calType, tm: _(
					int(tm[2]),
					fillZero=2,
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "s":  # seconds since 1970-01-01 00:00:00 UTC
				# funcs.append(lambda cell, calType, tm: _(
				# 	int(time.mktime(
				# 		a[2:7] + (
				# 			int(tm[2]),
				# 			0,
				# 			0,
				# 			1,
				# 		),
				# 	)),
				# ))
				funcs.append(lambda cell, calType, tm: _(
					core.getEpochFromJhms(cell.jd, *tm),
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "N":
				funcs.append(lambda cell, calType, tm: _(
					int(tm[2] * 1000000000 % 1000000000),
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "p":
				funcs.append(lambda cell, calType, tm: _(
					"AM" if tm[0] < 12 else "PM",
				))
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "P":
				funcs.append(lambda cell, calType, tm: _(
					"AM" if tm[0] < 12 else "PM"
				).lower())
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "T":  # %%H:%M:%S
				funcs.append(
					lambda cell, calType, tm:
						_(tm[0], fillZero=2) + ":" +
						_(tm[1], fillZero=2) + ":" +
						_(tm[2], fillZero=2)
				)
				pyFmt += "%s"
				i += 2
				continue
			elif c1 == "X":  # locale's time representation (e.g., 23:13:48)
				funcs.append(
					lambda cell, calType, tm:
						_(tm[0], fillZero=2) + ":" +
						_(tm[1], fillZero=2) + ":" +
						_(tm[2], fillZero=2)
				)
				pyFmt += "%s"
				i += 2
				continue
		pyFmt += ("%" + c1)
		i += 2
	return (pyFmt, funcs)  # compiledFmt
