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
from __future__ import annotations

import os
import os.path
import re
import subprocess
import sys
import typing
from contextlib import suppress
from os.path import isdir, isfile, join
from time import localtime
from time import time as now
from typing import Any, NamedTuple

import scal3
from scal3 import locale_man, logger, s_object
from scal3.cal_types import GREGORIAN, calTypes, jd_to, to_jd
from scal3.date_utils import (
	dateEncode,
	jwday,
)
from scal3.json_utils import (
	dataToCompactJson,
	dataToPrettyJson,
	loadModuleConfig,
	saveModuleConfig,
)
from scal3.locale_man import tr as _
from scal3.path import (
	APP_NAME,
	confDir,
	plugDir,
	plugDirUser,
	sourceDir,
	sysConfDir,
)
from scal3.plugin_man import loadPlugin
from scal3.time_utils import getJhmsFromEpoch

try:
	__file__  # noqa: B018
except NameError:
	import inspect

	__file__ = join(os.path.dirname(inspect.getfile(scal3)), "core.py")

__all__ = [
	"APP_NAME",
	"COMMAND",
	"GREGORIAN",
	"VERSION",
	"allPlugList",
	"compressLongInt",
	"eventTextSep",
	"firstWeekDay",
	"firstWeekDayAuto",
	"fs",
	"getAbsWeekNumberFromJd",
	"getCompactTime",
	"getCurrentJd",
	"getDeletedPluginsTable",
	"getPluginsTable",
	"getStartJdOfAbsWeekNumber",
	"getWeekDateFromJd",
	"getWeekDay",
	"getWeekDayAuto",
	"getWeekNumber",
	"getWeekNumberByJd",
	"holidayWeekDays",
	"init",
	"jd_to",
	"jd_to_primary",
	"jwday",
	"log",
	"plugIndex",
	"primary_to_jd",
	"restart",
	"saveConf",
	"stopRunningThreads",
	"updatePlugins",
	"weekDayName",
	"weekDayNameAb",
	"weekNumberModeAuto",
]

VERSION = "3.2.4"

# BRANCH = join(sourceDir, "branch")
# FIXME: figure out a policy for updating it

APP_DESC = "StarCalendar"
COMMAND = APP_NAME
homePage = "http://ilius.github.io/starcal/"


# __plugin_api_get__ = [
# 	"VERSION", "APP_NAME", "APP_DESC", "COMMAND",
# 	"homePage", "osName",
# 	"jd_to_primary", "primary_to_jd",
# ]
# __plugin_api_set__ = []

# def pluginCanGet(funcClass):
# 	global __plugin_api_get__
# 	__plugin_api_get__.append(funcClass.__name__)
# 	return funcClass

# def pluginCanSet(funcClass):
# 	global __plugin_api_set__
# 	__plugin_api_set__.append(funcClass.__name__)

# ________________ Defining user core configuration ________________ #

sysConfPath = join(sysConfDir, "core.json")

confPath = join(confDir, "core.json")

confParams = (
	"version",
	"allPlugList",
	"plugIndex",
	"activeCalTypes",
	"inactiveCalTypes",
	"holidayWeekDays",
	"firstWeekDayAuto",
	"firstWeekDay",
	"weekNumberModeAuto",
	"weekNumberMode",
)

confDecoders = {
	"allPlugList": lambda pdataList: [loadPlugin(**pdata) for pdata in pdataList],
}

confEncoders = {
	"allPlugList": lambda plugList: [
		plug.getArgs() for plug in plugList if plug is not None
	],
}


def loadConf() -> None:
	global version, prefVersion, activeCalTypes, inactiveCalTypes  # noqa: PLW0602
	# -----------
	loadModuleConfig(__name__)
	# -----------
	if "version" in globals():
		prefVersion = version
		del version
	else:
		prefVersion = ""
	# -----------
	with suppress(NameError):
		# activeCalTypes and inactiveCalType might be
		# loaded from json config file
		calTypes.activeNames = activeCalTypes
		calTypes.inactiveNames = inactiveCalTypes

	activeCalTypes = inactiveCalTypes = None
	calTypes.update()


def saveConf() -> None:
	global activeCalTypes, inactiveCalTypes
	activeCalTypes, inactiveCalTypes = (
		calTypes.activeNames,
		calTypes.inactiveNames,
	)
	saveModuleConfig(__name__)
	activeCalTypes = inactiveCalTypes = None


log = logger.get()

fs: s_object.FileSystem | None = None

# ____________________________________________________________________ #
# __________________ class and function defenitions __________________ #


def getVersion() -> str:
	try:
		from packaging.version import parse as parse_version
	except ImportError:
		from pkg_resources import parse_version

	if isfile(join(sourceDir, "VERSION")):
		with open(join(sourceDir, "VERSION"), encoding="utf-8") as _file:
			return _file.read().strip()

	gitDir = os.path.join(sourceDir, ".git")
	if not os.path.isdir(gitDir):
		return VERSION
	try:
		outputB, _error = subprocess.Popen(
			[  # noqa: S603, S607
				"git",
				"--git-dir",
				gitDir,
				"describe",
				"--always",
			],
			stdout=subprocess.PIPE,
		).communicate()
	except Exception:
		return VERSION

	gitVersionRaw = outputB.decode("utf-8").strip()
	if not gitVersionRaw:
		return VERSION

	# Python believes:
	# 3.1.12-15-gd50399ea	< 3.1.12
	# 3.1.12dev15+d50399ea	< 3.1.12
	# 3.1.12.dev15+d50399ea	< 3.1.12
	# 3.1.12post15+d50399ea	> 3.1.12
	# 3.1.12.post15+d50399ea	> 3.1.12
	# so the only way to make it work is to use "post"
	# if error != None:
	# 	sys.stderr.write(error)

	gitVersion = re.sub(
		r"-([0-9]+)-g([0-9a-f]{6,8})",
		r"post\1+\2",
		gitVersionRaw,
	)
	if parse_version(gitVersion) > parse_version(VERSION):
		return gitVersion

	return VERSION


def primary_to_jd(y: int, m: int, d: int) -> int:
	return to_jd(y, m, d, calTypes.primary)


def jd_to_primary(jd: int) -> tuple[int, int, int]:
	return jd_to(jd, calTypes.primary)


def getCurrentJd() -> int:
	# time.time() and mktime(localtime()) both return GMT, not local
	if GREGORIAN not in calTypes:
		raise RuntimeError(f"cal type {GREGORIAN=} not found")
	y, m, d = localtime()[:3]
	return to_jd(y, m, d, GREGORIAN)


# def getWeekDateHmsFromEpoch(epoch: int) -> tuple[int, int, int, int, int]:
# 	jd, hms = getJhmsFromEpoch(epoch)
# 	absWeekNumber, weekDay = getWeekDateFromJd(jd)
# 	return (absWeekNumber, weekDay, hms.h, hms.m, hms.s)


def getMonthWeekNth(jd: int, calType: int) -> tuple[int, int, int]:
	if calType not in calTypes:
		raise RuntimeError(f"cal type '{calType}' not found")
	_year, month, day = jd_to(jd, calType)
	_absWeekNumber, weekDay = getWeekDateFromJd(jd)
	# --
	dayDiv = (day - 1) // 7
	return month, dayDiv, weekDay


def getWeekDay(y: int, m: int, d: int) -> int:
	return jwday(primary_to_jd(y, m, d) - firstWeekDay)


def getWeekDayN(i: int) -> int:
	# 0 <= i < 7	(0 = first day)
	return weekDayName[(i + firstWeekDay) % 7]


def getWeekDayAuto(
	number: int,
	localize: bool = True,
	abbreviate: bool = False,
	relative: bool = True,
) -> str:
	if relative:
		number = (number + firstWeekDay) % 7

	if not localize:
		if abbreviate:
			return weekDayNameAbEnglish[number]
		return weekDayNameEnglish[number]

	if abbreviate:
		return weekDayNameAb[number]

	return weekDayName[number]


# week number in year
def getWeekNumberByJdAndYear(jd: int, year: int) -> int:
	if (
		primary_to_jd(year + 1, 1, 1) - jd < 7
		and getWeekNumber(*jd_to_primary(jd + 14)) == 3
	):
		return 1
	# ---
	absWeekNum, _weekDay = getWeekDateFromJd(jd)
	(
		ystartAbsWeekNum,
		ystartWeekDay,
	) = getWeekDateFromJd(primary_to_jd(year, 1, 1))
	weekNum = absWeekNum - ystartAbsWeekNum + 1
	# ---
	if weekNumberMode < 7 and ystartWeekDay > (weekNumberMode - firstWeekDay) % 7:
		weekNum -= 1
		if weekNum == 0:
			weekNum = getWeekNumber(*jd_to_primary(jd - 7)) + 1
	# ---
	return weekNum


def getWeekNumber(year: int, month: int, day: int) -> int:
	jd = primary_to_jd(year, month, day)
	return getWeekNumberByJdAndYear(jd, year)


def getWeekNumberByJd(jd: int) -> int:
	year, _month, _day = jd_to_primary(jd)
	return getWeekNumberByJdAndYear(jd, year)


# FIXME
# def getYearWeeksCount(year: int) -> int:
# 	return getWeekNumberByJd(primary_to_jd(year+1, 1, 1) - 7)


# def getJdFromWeek(year: int, weekNumber: int) -> int:  # FIXME
# 	# weekDay == 0
# 	wd0 = getWeekDay(year, 1, 1) - 1
# 	wn0 = getWeekNumber(year, 1, 1, False)
# 	jd0 = primary_to_jd(year, 1, 1)
# 	return jd0 - wd0 + (weekNumber - wn0) * 7


def getWeekDateFromJd(jd: int) -> tuple[int, int]:
	"""Return (absWeekNumber, weekDay)."""
	return divmod(jd - firstWeekDay + 1, 7)


def getAbsWeekNumberFromJd(jd: int) -> int:
	return getWeekDateFromJd(jd)[0]


def getStartJdOfAbsWeekNumber(absWeekNumber: int) -> int:
	return absWeekNumber * 7 + firstWeekDay - 1


# def getLocaleWeekNumberMode():
# 	return (int(popen_output(["locale", "week-1stweek"]))-1)%8
# 	# will be 7 for farsi (OK)
# 	# will be 6 for english (usa) (NOT OK, must be 4)
# 	# return int(popen_output(f"LANG={locale_man.lang} locale first_weekday"))-1
# 	# locale week-1stweek:
# 	#	en_US.UTF-8             7
# 	#	en_GB.UTF-8             4
# 	#	fa_IR.UTF-8             0


# ------------------------------------------------------


def validatePlugList() -> None:
	n = len(allPlugList)
	i = 0
	while i < n:
		if allPlugList[i] is None:
			allPlugList.pop(i)
			n -= 1
			with suppress(NameError):
				plugIndex.remove(i)
		else:
			i += 1
	# -----
	n = len(allPlugList)
	m = len(plugIndex)
	i = 0
	while i < m:
		if plugIndex[i] < n:
			i += 1
		else:
			plugIndex.pop(i)
			m -= 1


def initPlugins(fs: s_object.FileSystem) -> None:
	# log.debug("----------------------- initPlugins")
	# Assert that user configuarion for plugins is OK
	validatePlugList()
	# ------------------------
	names = [os.path.split(plug.file)[1] for plug in allPlugList]
	# newPlugs = []#????????
	for direc in (plugDir, plugDirUser):
		if not fs.isdir(direc):
			continue
		for fname in fs.listdir(direc):
			if fname in names + [
				"__init__.py",
				"README.md",
			]:
				continue
			if fname.startswith("."):
				continue
			_name, ext = os.path.splitext(fname)
			if ext in {".txt", ".pyc"}:
				continue
			path = f"{direc}/{fname}"
			# if path in path:
			# 	# The plugin is not new, currently exists in allPlugList
			# 	log.warning(f"plugin {path!r} already exists.")
			# 	continue
			if not isfile(path):
				continue
			plug = loadPlugin(path)
			if plug is None:
				log.error(f"failed to load plugin {path}")
				continue
			plugIndex.append(len(allPlugList))
			allPlugList.append(plug)
	# Assert again that final plugins are OK
	validatePlugList()
	updatePlugins()


def updatePlugins() -> None:
	for i in plugIndex:
		plug = allPlugList[i]
		if plug is None:
			continue
		if plug.enable:
			plug.load()
		else:
			plug.clear()


class PluginTuple(NamedTuple):
	index: int
	enable: bool
	show_date: bool
	title: str


def getPluginsTable() -> list[list]:
	# returns a list of [i, enable, show_date, description]
	table = []
	for index in plugIndex:
		plug = allPlugList[index]
		table.append(
			PluginTuple(
				index=index,
				enable=plug.enable,
				show_date=plug.show_date,
				title=plug.title,
			),
		)
	return table


def getDeletedPluginsTable() -> list[list]:
	"""Returns a list of (index description)."""
	table = []
	for i, plug in enumerate(allPlugList):
		try:
			plugIndex.index(i)
		except ValueError:  # noqa: PERF203
			table.append((i, plug.title))
	return table


# _____________________________________________________ #


def restart() -> typing.NoReturn:
	"""Will not return from function."""
	from scal3.utils import restartLow

	os.environ["LANG"] = locale_man.sysLangDefault
	restartLow()


# _____________________________________________________ #


def compressLongInt(num: int) -> str:
	"""Num must be less than 2**64."""
	from base64 import b64encode
	from struct import pack

	return (
		b64encode(
			pack("L", num % 2**64).rstrip(b"\x00"),
		)[:-3]
		.decode("ascii")
		.replace("/", "_")
	)


def getCompactTime(maxDays: int = 1000, minSec: float = 0.1) -> str:
	return compressLongInt(
		int(
			now() % (maxDays * 24 * 3600) / minSec,
		),
	)


def epochDateTimeEncode(epoch: int) -> str:
	jd, hms = getJhmsFromEpoch(epoch)
	return dateEncode(jd_to_primary(jd)) + f" {hms:HMS}"


def stopRunningThreads() -> None:
	"""Stopping running timer threads."""
	import threading

	for thread in threading.enumerate():
		# if thread.__class__.__name__ == "_Timer":
		try:
			cancel = thread.cancel
		except AttributeError:  # noqa: PERF203
			log.debug(f"Thread {thread} has no cancel function")
		else:
			log.info(f"stopping thread {thread.name}")
			cancel()


def dataToJson(data: Any) -> str:
	return (
		dataToCompactJson(data, useAsciiJson)
		if useCompactJson
		else dataToPrettyJson(data, useAsciiJson)
	)


def init() -> None:
	global VERSION, fs
	from scal3.s_object import DefaultFileSystem

	VERSION = getVersion()  # right place?

	fs = DefaultFileSystem(confDir)
	loadConf()
	initPlugins(fs)


# ___________________________________________________________________________ #
# __________________ End of class and function defenitions __________________ #


if len(sys.argv) > 1:
	if sys.argv[1] in {"--help", "-h"}:
		log.info("No help implemented yet!")
		sys.exit(0)
	elif sys.argv[1] == "--version":
		log.info(getVersion())
		sys.exit(0)

log.info(f"Local Time Zone: {locale_man.localTzStr}")

# holidayWeekDay=6  # 6 means last day of week ( 0 means first day of week)
# thDay = (tr("First day"), tr("2nd day"), tr("3rd day"), tr("4th day"),\
# 	tr("5th day"), tr("6th day"), tr("Last day"))
# holidayWeekEnable = True

libDir = join(sourceDir, "lib")
if isdir(libDir):
	sys.path.insert(0, libDir)
	major, minor, patch = sys.version_info
	pyVersion = f"{major}.{minor}"
	pyLibDir = join(libDir, pyVersion)
	if isdir(pyLibDir):
		sys.path.insert(0, pyLibDir)
	del pyVersion, pyLibDir


# ___________________________________________________________________________ #
# __________________________ Default Configuration __________________________ #

allPlugList = []
plugIndex = []

holidayWeekDays = [0]  # 0 means Sunday (5 means Friday)
# [5] or [4,5] in Iran
# [0] in most of contries
firstWeekDayAuto = True
firstWeekDay = 0  # 0 means Sunday (6 means Saturday)
weekNumberModeAuto = False  # not used yet
weekNumberMode = 7

# 0: First week contains first Sunday of year
# 4: First week contains first Thursday of year (ISO 8601, Gnome Clock)
# 6: First week contains first Saturday of year
# 7: First week contains first day of year
# 8: as Locale
# 1971(53), 1972(52), 1977, 1982, 1983, 1988, 1993, 1994
# 1999(53),2000(52),2005(53),2010(53),2011(52),2016(53),2021,2022,2027,2028

# ___________________________________________________________________________ #


useCompactJson = False  # TODO: add to Preferences
useAsciiJson = False
eventTextSep = ": "  # use to separate summary from description for display

# ___________________________________________________________________________ #


licenseText = _("__license__")
if licenseText in {"__license__", ""}:
	with open(f"{sourceDir}/license-dialog", encoding="utf-8") as fp:
		licenseText = fp.read()

aboutText = _("aboutText")
if aboutText in {"aboutText", ""}:
	with open(f"{sourceDir}/about", encoding="utf-8") as fp:
		aboutText = fp.read()


weekDayNameEnglish = (
	"Sunday",
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
)
weekDayNameAbEnglish = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")

weekDayName = tuple(_(name) for name in weekDayNameEnglish)
weekDayNameAb = tuple(
	_(name, nums=True, ctx="abbreviation", default=weekDayNameAbEnglish[i])
	for i, name in enumerate(weekDayNameEnglish)
)

# if firstWeekDayAuto and os.sep=="/":	# only if unix
# 	firstWeekDay = getLocaleFirstWeekDay()

# TODO
# if weekNumberModeAuto and os.sep=="/":
# 	weekNumberMode = getLocaleWeekNumberMode()
