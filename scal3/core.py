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
from time import localtime
from time import time as now

import sys
import os
import subprocess
from subprocess import Popen
from io import StringIO
import os.path
from os.path import join, isfile, isdir

import scal3
from scal3.path import *
from scal3.time_utils import *
from scal3.date_utils import *
from scal3.os_utils import *
from scal3.json_utils import *
from scal3.utils import *

from scal3 import logger
from scal3.cal_types import calTypes, DATE_GREG, getSysDate
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import localTz
from scal3.plugin_man import *


try:
	__file__
except NameError:
	import inspect
	__file__ = join(os.path.dirname(inspect.getfile(scal3)), "core.py")


VERSION = "3.1.9"
# BRANCH = join(sourceDir, "branch") # FIXME: figure out a policy for updating it
APP_DESC = "StarCalendar"
COMMAND = APP_NAME
homePage = "http://ilius.github.io/starcal/"
osName = getOsName()
userDisplayName = getUserDisplayName()


#__plugin_api_get__ = [
#	"VERSION", "APP_NAME", "APP_DESC", "COMMAND",
#	"homePage", "osName", "userDisplayName"
#	"jd_to_primary", "primary_to_jd",
#]
#__plugin_api_set__ = []

#def pluginCanGet(funcClass):
#	global __plugin_api_get__
#	__plugin_api_get__.append(funcClass.__name__)
#	return funcClass

#def pluginCanSet(funcClass):
#	global __plugin_api_set__
#	__plugin_api_set__.append(funcClass.__name__)

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
	"debugMode",
)

confDecoders = {
	"allPlugList": lambda pdataList: [
		loadPlugin(**pdata) for pdata in pdataList
	],
}

confEncoders = {
	"allPlugList": lambda plugList: [
		plug.getArgs() for plug in plugList if plug is not None
	],
}


def loadConf():
	global version, prefVersion, activeCalTypes, inactiveCalTypes
	###########
	loadModuleJsonConf(__name__)
	###########
	try:
		version
	except NameError:
		prefVersion = ""
	else:
		prefVersion = version
		del version
	###########
	try:
		# activeCalTypes and inactiveCalType might be
		# loaded from json config file
		calTypes.activeNames = activeCalTypes
		calTypes.inactiveNames = inactiveCalType
	except NameError:
		pass
	activeCalTypes = inactiveCalTypes = None
	calTypes.update()


def saveConf():
	global activeCalTypes, inactiveCalTypes
	activeCalTypes, inactiveCalTypes = (
		calTypes.activeNames,
		calTypes.inactiveNames,
	)
	saveModuleJsonConf(__name__)
	activeCalTypes = inactiveCalTypes = None


log = logger.get()


def myRaise(File=None):
	typ, value, tback = sys.exc_info()
	text = "line %s: %s: %s\n" % (
		tback.tb_lineno,
		typ.__name__,
		value,
	)
	if File:
		text = "File \"%s\", " % File + text
	log.error(text)


# ____________________________________________________________________ #
# __________________ class and function defenitions __________________ #


def popen_output(cmd):
	return Popen(cmd, stdout=subprocess.PIPE).communicate()[0]


def getVersion():
	gitDir = os.path.join(rootDir, ".git")
	if os.path.isdir(gitDir):
		try:
			outputB, error = subprocess.Popen(
				[
					"git",
					"--git-dir", gitDir,
					"describe",
					"--always",
				],
				stdout=subprocess.PIPE,
			).communicate()
		except:
			myRaise()
		else:
			# if error != None:
			#	sys.stderr.write(error)
			version = outputB.decode("utf-8").strip()
			if version:
				return version
	return VERSION


def primary_to_jd(y, m, d):
	return calTypes.primaryModule().to_jd(y, m, d)


def jd_to_primary(jd):
	return calTypes.primaryModule().jd_to(jd)


def getCurrentJd():
	# time.time() and mktime(localtime()) both return GMT, not local
	module, ok = calTypes[DATE_GREG]
	if not ok:
		raise RuntimeError("cal type %r not found" % DATE_GREG)
	y, m, d = localtime()[:3]
	return module.to_jd(y, m, d)


def getWeekDateHmsFromEpoch(epoch):
	jd, hour, minute, sec = getJhmsFromEpoch(epoch)
	absWeekNumber, weekDay = getWeekDateFromJd(jd)
	return (absWeekNumber, weekDay, hour, minute, sec)


def getMonthWeekNth(jd, mode):
	module, ok = calTypes[mode]
	if not ok:
		raise RuntimeError("cal type %r not found" % mode)
	year, month, day = module.jd_to(jd)
	absWeekNumber, weekDay = getWeekDateFromJd(jd)
	##
	dayDiv, dayMode = divmod(day - 1, 7)
	return month, dayDiv, weekDay


def getWeekDay(y, m, d):
	return jwday(primary_to_jd(y, m, d) - firstWeekDay)


def getWeekDayN(i):
	# 0 <= i < 7	(0 = first day)
	return weekDayName[(i + firstWeekDay) % 7]


def getWeekDayAuto(i, abr=False):
	if abr:
		return weekDayNameAb[(i + firstWeekDay) % 7]
	else:
		return weekDayName[(i + firstWeekDay) % 7]


def getLocaleFirstWeekDay():
	return int(popen_output(["locale", "first_weekday"])) - 1


# week number in year
def getWeekNumberByJdAndDate(jd, year, month, day):
	if primary_to_jd(year + 1, 1, 1) - jd < 7:  # FIXME
		if getWeekNumber(*jd_to_primary(jd + 14)) == 3:
			return 1
	###
	absWeekNum, weekDay = getWeekDateFromJd(jd)
	(
		ystartAbsWeekNum,
		ystartWeekDay,
	) = getWeekDateFromJd(primary_to_jd(year, 1, 1))
	weekNum = absWeekNum - ystartAbsWeekNum + 1
	###
	if weekNumberMode < 7:
		if ystartWeekDay > (weekNumberMode - firstWeekDay) % 7:
			weekNum -= 1
			if weekNum == 0:
				weekNum = getWeekNumber(*jd_to_primary(jd - 7)) + 1
	###
	return weekNum


def getWeekNumber(year, month, day):
	jd = primary_to_jd(year, month, day)
	return getWeekNumberByJdAndDate(jd, year, month, day)


def getWeekNumberByJd(jd):
	year, month, day = jd_to_primary(jd)
	return getWeekNumberByJdAndDate(jd, year, month, day)

# FIXME
# def getYearWeeksCount(year):
#	return getWeekNumberByJd(primary_to_jd(year+1, 1, 1) - 7)


def getJdFromWeek(year, weekNumber):  # FIXME
	# weekDay == 0
	wd0 = getWeekDay(year, 1, 1) - 1
	wn0 = getWeekNumber(year, 1, 1, False)
	jd0 = primary_to_jd(year, 1, 1)
	return jd0 - wd0 + (weekNumber - wn0) * 7


def getWeekDateFromJd(jd):
	"""
	return (absWeekNumber, weekDay)
	"""
	return divmod(jd - firstWeekDay + 1, 7)


def getAbsWeekNumberFromJd(jd):
	return getWeekDateFromJd(jd)[0]


def getStartJdOfAbsWeekNumber(absWeekNumber):
	return absWeekNumber * 7 + firstWeekDay - 1


#def getLocaleWeekNumberMode():##????????????
#	return (int(popen_output(["locale", "week-1stweek"]))-1)%8
	## will be 7 for farsi (OK)
	## will be 6 for english (usa) (NOT OK, must be 4)
	#return int(popen_output("LANG=%s locale first_weekday"%locale_man.lang))-1
	## locale week-1stweek:
	##	en_US.UTF-8             7
	##	en_GB.UTF-8             4
	##	fa_IR.UTF-8             0


######################################################

def validatePlugList():
	global allPlugList, plugIndex
	n = len(allPlugList)
	i = 0
	while i < n:
		if allPlugList[i] is None:
			allPlugList.pop(i)
			n -= 1
			try:
				plugIndex.remove(i)
			except ValueError:
				pass
		else:
			i += 1
	#####
	n = len(allPlugList)
	m = len(plugIndex)
	i = 0
	while i < m:
		if plugIndex[i] < n:
			i += 1
		else:
			plugIndex.pop(i)
			m -= 1


def initPlugins():
	# log.debug("----------------------- initPlugins")
	global allPlugList, plugIndex
	# Assert that user configuarion for plugins is OK
	validatePlugList()
	########################
	names = [os.path.split(plug.file)[1] for plug in allPlugList]
	# newPlugs = []#????????
	for direc in (plugDir, plugDirUser):
		if not isdir(direc):
			continue
		for fname in os.listdir(direc):
			if fname in names + [
				"__init__.py",
				"README",
			]:
				continue
			if fname.startswith("."):
				continue
			name, ext = os.path.splitext(fname)
			if ext in (".txt", ".pyc"):
				continue
			path = "%s/%s" % (direc, fname)
			# if path in path:
			#	# The plugin is not new, currently exists in allPlugList
			#	log.warning("plugin "%s" already exists."%path)
			#	continue
			if not isfile(path):
				continue
			plug = loadPlugin(path)
			if plug is None:
				print('failed to load plugin', path)
				continue
			# try:
			plugIndex.append(len(allPlugList))
			allPlugList.append(plug)
			#except:
			#	myRaise(__file__)
	# Assert again that final plugins are OK
	validatePlugList()
	updatePlugins()


def getHolidayPlugins():
	hPlugs = []
	for i in plugIndex:
		plug = allPlugList[i]
		if hasattr(plug, "holidays"):
			hPlugs.append(plug)
	return hPlugs


def updatePlugins():
	for i in plugIndex:
		plug = allPlugList[i]
		if plug is None:
			continue
		if plug.enable:
			plug.load()
		else:
			plug.clear()


def getPluginsTable():
	# returns a list of [i, enable, show_date, description]
	table = []
	for i in plugIndex:
		plug = allPlugList[i]
		table.append([i, plug.enable, plug.show_date, plug.title])
	return table


def getDeletedPluginsTable():
	"""
	returns a list of (index description)
	"""
	table = []
	for i, plug in enumerate(allPlugList):
		try:
			plugIndex.index(i)
		except ValueError:
			table.append((i, plug.title))
	return table


def convertAllPluginsToIcs(startYear, endYear):
	module, ok = calTypes[DATE_GREG]
	if not ok:
		raise RuntimeError("cal type %r not found" % DATE_GREG)
	startJd = module.to_jd(startYear, 1, 1)
	endJd = module.to_jd(endYear + 1, 1, 1)
	namePostfix = "-%d-%d" % (startYear, endYear)
	for plug in core.allPlugList:
		if isinstance(plug, HolidayPlugin):
			convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix)
		elif isinstance(plug, BuiltinTextPlugin):
			convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix)
		else:
			print("Ignoring unsupported plugin %s" % plug.file)

# _____________________________________________________ #


def restart():
	"""
	will not return from function
	"""
	os.environ["LANG"] = locale_man.sysLangDefault
	restartLow()

# _____________________________________________________ #


def mylocaltime(sec=None, mode=None):
	from scal3.cal_types import convert
	if mode is None:  # DATE_GREG
		return list(localtime(sec))
	t = list(localtime(sec))
	t[:3] = convert(t[0], t[1], t[2], DATE_GREG, mode)
	return t


def compressLongInt(num):
	from struct import pack
	from base64 import b64encode
	return b64encode(
		pack("L", num % 2 ** 64).rstrip(b"\x00")
	)[:-3].decode("ascii").replace("/", "_")


def getCompactTime(maxDays=1000, minSec=0.1):
	return compressLongInt(
		int(
			now() % (maxDays * 24 * 3600) / minSec
		)
	)


def floatJdEncode(jd, mode):
	jd, hour, minute, second = getJhmsFromEpoch(getEpochFromJd(jd))
	module, ok = calTypes[mode]
	if not ok:
		raise RuntimeError("cal type %r not found" % mode)
	return "%s %s" % (
		dateEncode(module.jd_to(jd)),
		timeEncode((hour, minute, second)),
	)


def epochDateTimeEncode(epoch):
	jd, hour, minute, sec = getJhmsFromEpoch(epoch)
	return "%s, %s" % (
		dateEncode(jd_to_primary(jd)),
		timeEncode((hour, minute, sec)),
	)


def fixStrForFileName(fname):
	fname = fname.replace("/", "_").replace("\\", "_")
	#if osName=="win":  # FIXME
	return fname


def openUrl(url):
	if osName == "win":
		return Popen([url])
	if osName == "mac":
		return Popen(["open", url])
	try:
		Popen(["xdg-open", url])
	except:
		myRaise()
	else:
		return
	#if not url.startswith("http"):  # FIXME
	#	return
	try:
		import webbrowser
		return webbrowser.open(url)
	except ImportError:
		pass
	try:
		import gnomevfs
		return gnomevfs.url_show(url)
	except ImportError:
		pass
	for command in ("gnome-www-browser", "firefox", "iceweasel", "konqueror"):
		try:
			Popen([command, url])
		except:
			pass
		else:
			return


def stopRunningThreads():
	"""
	Stopping running timer threads
	"""
	import threading
	for thread in threading.enumerate():
		# if thread.__class__.__name__ == "_Timer":
		try:
			cancel = thread.cancel
		except AttributeError:
			pass
		else:
			print("stopping thread %s" % thread.getName())
			cancel()


def dataToJson(data):
	return dataToCompactJson(data, useAsciiJson) if useCompactJson \
		else dataToPrettyJson(data, useAsciiJson)


def init():
	global VERSION
	VERSION = getVersion()  # right place?
	loadConf()
	initPlugins()


def prefIsOlderThan(v):
	return versionLessThan(prefVersion, v)


# ___________________________________________________________________________ #
# __________________ End of class and function defenitions __________________ #


if len(sys.argv) > 1:
	if sys.argv[1] in ("--help", "-h"):
		print("No help implemented yet!")
		sys.exit(0)
	elif sys.argv[1] == "--version":
		print(VERSION)
		sys.exit(0)


#holidayWeekDay=6  # 6 means last day of week ( 0 means first day of week)
#thDay = (tr("First day"), tr("2nd day"), tr("3rd day"), tr("4th day"),\
#	tr("5th day"), tr("6th day"), tr("Last day"))
#holidayWeekEnable = True

libDir = join(rootDir, "lib")
if isdir(libDir):
	sys.path.insert(libDir)
	pyVersion = "%d.%d" % tuple(sys.version_info[:2])
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
weekNumberModeAuto = False	# ????????????
weekNumberMode = 7

# 0: First week contains first Sunday of year
# 4: First week contains first Thursday of year (ISO 8601, Gnome Clock)
# 6: First week contains first Saturday of year
# 7: First week contains first day of year
# 8: as Locale
# 1971(53), 1972(52), 1977, 1982, 1983, 1988, 1993, 1994
# 1999(53),2000(52),2005(53),2010(53),2011(52),2016(53),2021,2022,2027,2028

# ___________________________________________________________________________ #

debugMode = False
useCompactJson = False	# FIXME
useAsciiJson = False
eventTextSep = ": "  # use to seperate summary from description for display
eventTrashLastTop = True


# ___________________________________________________________________________ #


licenseText = _("licenseText")
if licenseText in ("licenseText", ""):
	licenseText = open(
		"%s/license-dialog" % rootDir,
		encoding="utf-8",
	).read()

aboutText = _("aboutText")
if aboutText in ("aboutText", ""):
	aboutText = open("%s/about" % rootDir, encoding="utf-8").read()


weekDayName = (
	_("Sunday"),
	_("Monday"),
	_("Tuesday"),
	_("Wednesday"),
	_("Thursday"),
	_("Friday"),
	_("Saturday"),
)
weekDayNameAb = (
	_("Sun", nums=True),
	_("Mon", nums=True),
	_("Tue", nums=True),
	_("Wed", nums=True),
	_("Thu", nums=True),
	_("Fri", nums=True),
	_("Sat", nums=True),
)


#if firstWeekDayAuto and os.sep=="/":	# only if unix
#	firstWeekDay = getLocaleFirstWeekDay()

#if weekNumberModeAuto and os.sep=="/":  # FIXME
#	weekNumberMode = getLocaleWeekNumberMode()
