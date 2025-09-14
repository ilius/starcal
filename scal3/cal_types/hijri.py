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

# Islamic (Hijri) calendar: http://en.wikipedia.org/wiki/Islamic_calendar

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Final

from scal3 import logger
from scal3.option import Option

if TYPE_CHECKING:
	from scal3.cal_types.pytypes import OptionTuple, TranslateFunc

__all__ = [
	"desc",
	"getMonthLen",
	"hijriUseDB",
	"jd_to",
	"monthDb",
	"monthDbExpiredIgnoreFile",
	"monthName",
	"name",
	"to_jd",
	"to_jd_c",
]

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
monthNameContext: Option[str] = Option("month-name")


def getMonthName(
	m: int,
	y: int | None = None,  # noqa: ARG001
) -> str:
	return monthName[m - 1]


def getMonthNameAb(
	tr: TranslateFunc,
	m: int,
	y: int | None = None,  # noqa: ARG001
) -> str:
	fullEn = monthName[m - 1]
	abbr = tr(fullEn, ctx="abbreviation")
	if abbr != fullEn:
		return abbr
	return monthNameAb[m - 1]


epoch = 1948440
minMonthLen = 29
maxMonthLen = 30
avgYearLen = 354.3666  # FIXME

hijriUseDB: Final[Option[bool]] = Option(True)


options: list[OptionTuple] = [
	(
		hijriUseDB,
		bool,
		"Use Hijri month length data (Iranian official calendar)",
	),
]
optionButtons = [
	(
		"Tune Hijri Monthes",
		"hijri",
		"tuneHijriMonthes",
	),
]


import os
from collections import OrderedDict
from math import ceil, floor
from os.path import isfile, join

from scal3.config_utils import loadSingleConfig, saveSingleConfig
from scal3.json_utils import dataToPrettyJson
from scal3.path import confDir, modDir, sysConfDir

monthDbExpiredIgnoreFile = join(confDir, "hijri-expired-ignore")


oldDbPath = f"{confDir}/hijri.db"
if isfile(oldDbPath):
	os.remove(oldDbPath)


confOptions: Final[dict[str, Option[Any]]] = {
	"hijriUseDB": hijriUseDB,
}

# Here load user options (hijriUseDB) from file
sysConfPath = f"{sysConfDir}/{name}.json"
loadSingleConfig(sysConfPath, confOptions)


confPath = f"{confDir}/{name}.json"
loadSingleConfig(confPath, confOptions)


def ifloor(x: float) -> int:
	return floor(x)


def iceil(x: float) -> int:
	return ceil(x)


def save() -> None:
	"""Save user options to file."""
	saveSingleConfig(
		confPath,
		confOptions,
	)


class MonthDbHolder:
	def __init__(self) -> None:
		self.startDate = (1426, 2, 1)  # hijriDbInitH
		self.startJd = 2453441  # hijriDbInitJD
		self.endJd = self.startJd  # hijriDbEndJD
		self.expJd: int | None = None
		self.monthLenByYm: dict[int, int] = {}  # hijriMonthLen
		self.userDbPath = join(confDir, "hijri-monthes.json")
		self.sysDbPath = f"{modDir}/hijri-monthes.json"

	def setMonthLenByYear(self, monthLenByYear: dict[int, list[int]]) -> None:
		self.endJd = self.startJd
		self.monthLenByYm = {}
		for year, lenList in monthLenByYear.items():
			for month, mLen in enumerate(lenList):
				if mLen == 0:
					continue
				if mLen < 0:
					raise ValueError(f"invalid {mLen = }")
				self.monthLenByYm[year * 12 + month] = mLen
				self.endJd += mLen
		if self.expJd is None:
			self.expJd = self.endJd

	def setDict(self, data: dict[str, Any]) -> None:
		self.startDate = tuple(data["startDate"])
		self.startJd = data["startJd"]
		self.expJd = data.get("expJd")
		# ---
		monthLenByYear = {}
		for row in data["monthLen"]:
			monthLenByYear[row[0]] = row[1:]
		self.setMonthLenByYear(monthLenByYear)

	def load(self) -> None:
		with open(self.sysDbPath, encoding="utf-8") as fp:
			data = json.loads(fp.read())
		self.origVersion = data["version"]
		# --
		if isfile(self.userDbPath):
			with open(self.userDbPath, encoding="utf-8") as fp:
				userData = json.loads(fp.read())
			if userData["origVersion"] >= self.origVersion:
				data = userData
			else:
				log.info(f"---- ignoring user's old db {self.userDbPath}")
		self.setDict(data)

	def getMonthLenByYear(self) -> dict[int, list[int]]:
		monthLenByYear = {}
		for ym, mLen in sorted(self.monthLenByYm.items()):
			year, month0 = divmod(ym, 12)
			if year not in monthLenByYear:
				monthLenByYear[year] = [0] * month0
			monthLenByYear[year].append(mLen)
		return monthLenByYear

	def save(self) -> None:
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

	def getMonthLenList(self) -> list[tuple[int, int, int]]:
		"""
		Returns a list of (index, ym, mLen).
		where ym is year * 12 + month - 1.
		"""
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

	def getDateFromJd(self, jd: int) -> tuple[int, int, int] | None:
		if not self.endJd >= jd >= self.startJd:
			return None
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
	def getJdFromDate(year: int, month: int, day: int) -> int | None:
		ym = year * 12 + month - 1
		y0, m0, _d0 = monthDb.startDate
		if ym - 1 not in monthDb.monthLenByYm:
			return None
		ym0 = y0 * 12 + m0 - 1
		jd = monthDb.startJd
		for ymi in range(ym0, ym):
			jd += monthDb.monthLenByYm[ymi]
		return jd + day - 1


monthDb = MonthDbHolder()
monthDb.load()
# monthDb.save()

# ---------------------------------------------------------------------


def isLeap(year: int) -> bool:
	return (((year * 11) + 14) % 30) < 11


def to_jd_c(year: int, month: int, day: int) -> int:
	return (
		day
		+ iceil(29.5 * (month - 1))
		+ (year - 1) * 354
		+ (11 * year + 3) // 30
		+ epoch
	)


def to_jd(year: int, month: int, day: int) -> int:
	if hijriUseDB.v:
		jd = monthDb.getJdFromDate(year, month, day)
		if jd is not None:
			return jd
	return to_jd_c(year, month, day)


def jd_to(jd: int) -> tuple[int, int, int]:
	assert isinstance(jd, int), f"{jd=}"
	if hijriUseDB.v:
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


def getMonthLen(year: int, month: int) -> int:
	# if `hijriUseDB.v`:
	# 	try:
	# 		return monthDb.monthLenByYm[y*12+m]
	# 	except KeyError:
	# 		pass
	if month == 12:
		return to_jd(year + 1, 1, 1) - to_jd(year, 12, 1)

	return to_jd(year, month + 1, 1) - to_jd(year, month, 1)
