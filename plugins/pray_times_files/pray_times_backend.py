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

# import pray_times_upstream as upstream
from pray_times_upstream import PrayTimes as PrayTimesUpstream

__all__ = [
	"timeNames",
	"methodsList",
	"PrayTimes",
]

timeNames = (
	("imsak", "Imsak"),
	("fajr", "Fajr"),
	("sunrise", "Sunrise"),
	("dhuhr", "Dhuhr"),
	("asr", "Asr"),
	("sunset", "Sunset"),
	("maghrib", "Maghrib"),
	("isha", "Isha"),
	("midnight", "Midnight"),
	("timezone", "Time Zone"),
)

class Method:
	def __init__(
		self,
		name,
		desc,
		fajr=15,
		isha=15,
		maghrib="0 min",
		midnight="Standard",
	):
		self.name = name
		self.desc = desc
		self.fajr = fajr
		self.isha = isha
		self.maghrib = maghrib
		self.midnight = midnight

	def __repr__(self):
		return (
			f"Method(name={self.name!r}, desc={self.desc!r}, "
			f"fajr={self.fajr!r}, isha={self.isha!r}, "
			f"maghrib={self.maghrib!r}, midnight={self.midnight!r})"
		)


_rawMethodsList = PrayTimesUpstream.methods
methodsList = []
for key in (
	"MWL", "ISNA", "Egypt", "Makkah",
	"Karachi", "Tehran", "Jafari",
):
	raw = _rawMethodsList[key]
	methodsList.append(Method(
		name=key,
		desc=raw["name"],
		fajr=raw["params"]["fajr"],
		isha=raw["params"]["isha"],
	))
methodsDict = {m.name: m for m in methodsList}

from pprint import pprint
pprint(methodsList)


class PrayTimes(PrayTimesUpstream):
	def __init__(
		self,
		methodName="",
		lat=0,
		lng=0,
		elv=0,
		imsak="",
	):

		PrayTimesUpstream.__init__(self, method=methodName)

		self.method = methodsDict[methodName]
		self.lat = lat
		self.lng = lng
		self.elv = elv

		if imsak:
			self.settings["imsak"] = imsak

	def getTimesByJd(self, jd, utcOffset):
		"""
		return prayer times for a given julian day
		"""
		#if time.daylight and time.gmtime(core.getEpochFromJd(jd)):
		# log.debug(time.gmtime((jd-2440588)*(24*3600)).tm_isdst)
		self.timeZone = utcOffset
		self.jDate = jd - 0.5 - self.lng / (15 * 24)
		times = self.computeTimes()
		# print(times)

		times["timezone"] = f"GMT{utcOffset:+.1f}"
		# ^^^ utcOffset is not timeZone FIXME

		return times


