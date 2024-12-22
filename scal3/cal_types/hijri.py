#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
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

# Islamic (Hijri) calendar: http://en.wikipedia.org/wiki/Islamic_calendar

from scal3 import logger

log = logger.get()

name = "hijri"
desc = "Hijri(Islamic)"
origLang = "ar"

monthName = (
	"Muharram",
	"Safar",
	"Rabīʽ 1",  # noqa: RUF001
	"Rabīʽ 2",  # noqa: RUF001
	"Jumadā 1",
	"Jumadā 2",
	"Rajab",
	"Shaʿbān",
	"Ramaḍān",
	"Shawwāl",
	"Ḏū'l-Qaʿdah",
	"Ḏū'l-Ḥijjah",
)

monthNameAb = (
	"Moh",
	"Saf",
	"Rb1",
	"Rb2",
	"Jm1",
	"Jm2",
	"Raj",
	"Shb",
	"Ram",
	"Shw",
	"DhQ",
	"DhH",
)


def getMonthName(m, y=None):  # noqa: ARG001
	return monthName[m - 1]


def getMonthNameAb(tr, m, y=None):  # noqa: ARG001
	fullEn = monthName[m - 1]
	abbr = tr(fullEn, ctx="abbreviation")
	if abbr != fullEn:
		return abbr
	return monthNameAb[m - 1]


epoch = 1948440
minMonthLen = 29
maxMonthLen = 30
avgYearLen = 354.3666  # FIXME

hijriUseDB = True


options = (
	(
		"hijriUseDB",
		bool,
		"Use Hijri month length data (Iranian official calendar)",
	),
	(
		"button",
		"Tune Hijri Monthes",
		"hijri",
		"tuneHijriMonthes",
	),
)


import os
from collections import OrderedDict
from math import ceil, floor
from os.path import isfile, join

from scal3.json_utils import (
	dataToPrettyJson,
	jsonToData,
	loadJsonConf,
	saveJsonConf,
)
from scal3.path import confDir, modDir, sysConfDir

monthDbExpiredIgnoreFile = join(confDir, "hijri-expired-ignore")


oldDbPath = f"{confDir}/hijri.db"
if isfile(oldDbPath):
	os.remove(oldDbPath)


# Here load user options (hijriUseDB) from file
sysConfPath = f"{sysConfDir}/{name}.json"
loadJsonConf(__name__, sysConfPath)


confPath = f"{confDir}/{name}.json"
loadJsonConf(__name__, confPath)


def ifloor(x: float) -> int:
	return floor(x)


def iceil(x: float) -> int:
	return ceil(x)


def save():
	"""Save user options to file."""
	saveJsonConf(
		__name__,
		confPath,
		("hijriUseDB",),
	)


class MonthDbHolder:
	def __init__(self):
		self.startDate = (1426, 2, 1)  # hijriDbInitH
		self.startJd = 2453441  # hijriDbInitJD
		self.endJd = self.startJd  # hijriDbEndJD
		self.expJd = None
		self.monthLenByYm = {}  # hijriMonthLen
		self.userDbPath = join(confDir, "hijri-monthes.json")
		self.sysDbPath = f"{modDir}/hijri-monthes.json"

	def setMonthLenByYear(self, monthLenByYear):
		self.endJd = self.startJd
		self.monthLenByYm = {}
		for y in monthLenByYear:
			lst = monthLenByYear[y]
			for m, ml in enumerate(lst):
				if ml == 0:
					continue
				if ml < 0:
					raise ValueError(f"invalid {ml = }")
				self.monthLenByYm[y * 12 + m] = ml
				self.endJd += ml
		if self.expJd is None:
			self.expJd = self.endJd

	def setData(self, data):
		self.startDate = tuple(data["startDate"])
		self.startJd = data["startJd"]
		self.expJd = data.get("expJd", None)
		# ---
		monthLenByYear = {}
		for row in data["monthLen"]:
			monthLenByYear[row[0]] = row[1:]
		self.setMonthLenByYear(monthLenByYear)

	def load(self):
		with open(self.sysDbPath, encoding="utf-8") as fp:
			data = jsonToData(fp.read())
		self.origVersion = data["version"]
		# --
		if isfile(self.userDbPath):
			with open(self.userDbPath, encoding="utf-8") as fp:
				userData = jsonToData(fp.read())
			if userData["origVersion"] >= self.origVersion:
				data = userData
			else:
				log.info(f"---- ignoring user's old db {self.userDbPath}")
		self.setData(data)

	def getMonthLenByYear(self):
		monthLenByYear = {}
		for ym, mLen in sorted(self.monthLenByYm.items()):
			year, month0 = divmod(ym, 12)
			if year not in monthLenByYear:
				monthLenByYear[year] = [0] * month0
			monthLenByYear[year].append(mLen)
		return monthLenByYear

	def save(self):
		mLenData = [
			[year] + mLenList for year, mLenList in self.getMonthLenByYear().items()
		]
		text = dataToPrettyJson(
			OrderedDict(
				[
					("origVersion", self.origVersion),
					("startDate", self.startDate),
					("startJd", self.startJd),
					("monthLen", mLenData),
					("expJd", self.expJd),
				],
			),
		)
		with open(self.userDbPath, "w", encoding="utf-8") as f:
			f.write(text)

	def getMonthLenList(self):
		"""Returns a list of (index, ym, mLen)."""
		return [
			(
				index,
				ym,
				self.monthLenByYm[ym],
			)
			for index, ym in enumerate(
				sorted(
					self.monthLenByYm,
				),
			)
		]

	def getDateFromJd(self, jd):
		if not self.endJd >= jd >= self.startJd:
			return
		y, m, d = self.startDate
		ym = y * 12 + m - 1
		startJd = self.startJd
		while jd > startJd:
			monthLen = self.monthLenByYm[ym]
			jdm0 = jd - monthLen

			if jdm0 <= startJd - d:
				d = d + jd - startJd
				break

			if startJd - d < jdm0 <= startJd:
				ym += 1
				d = d + jd - startJd - monthLen
				break

			# assert(jdm0 > startJd)
			ym += 1
			jd -= monthLen

		year, mm = divmod(ym, 12)
		return (year, mm + 1, d)

	@staticmethod
	def getJdFromDate(year, month, day):
		ym = year * 12 + month - 1
		y0, m0, _d0 = monthDb.startDate
		if ym - 1 not in monthDb.monthLenByYm:
			return
		ym0 = y0 * 12 + m0 - 1
		jd = monthDb.startJd
		for ymi in range(ym0, ym):
			jd += monthDb.monthLenByYm[ymi]
		return jd + day - 1


monthDb = MonthDbHolder()
monthDb.load()
# monthDb.save()

# ---------------------------------------------------------------------


def isLeap(year):
	return (((year * 11) + 14) % 30) < 11


def to_jd_c(year, month, day):
	return (
		day
		+ iceil(29.5 * (month - 1))
		+ (year - 1) * 354
		+ (11 * year + 3) // 30
		+ epoch
	)


def to_jd(year, month, day):
	if hijriUseDB:
		jd = monthDb.getJdFromDate(year, month, day)
		if jd is not None:
			return jd
	return to_jd_c(year, month, day)


def jd_to(jd):
	if hijriUseDB:
		# jd = ifloor(jd)
		date = monthDb.getDateFromJd(jd)
		if date:
			return date
	year = ifloor(((30 * (jd - 1 - epoch)) + 10646) // 10631)
	month = min(
		12,
		iceil(
			(jd + 0.5 - to_jd_c(year, 1, 1)) / 29.5,
		),
	)
	day = jd - to_jd_c(year, month, 1) + 1
	return year, month, day


def getMonthLen(y, m):
	# if hijriUseDB:
	# 	try:
	# 		return monthDb.monthLenByYm[y*12+m]
	# 	except KeyError:
	# 		pass
	if m == 12:
		return to_jd(y + 1, 1, 1) - to_jd(y, 12, 1)

	return to_jd(y, m + 1, 1) - to_jd(y, m, 1)
