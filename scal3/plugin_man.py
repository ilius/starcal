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

import sys
from time import strftime
from time import localtime
from os.path import isfile, dirname, join, split, splitext, isabs


from scal3.path import *
from scal3.json_utils import *
from scal3.time_utils import getJdListFromEpochRange
from scal3.ics import getEpochByIcsTime, getIcsDateByJd
from scal3.cal_types import (
	calTypes,
	jd_to,
	to_jd,
	convert,
	GREGORIAN,
	gregorian,
)
from scal3.date_utils import ymdRange
from scal3.locale_man import tr as _
from scal3.locale_man import getMonthName
from scal3.ics import icsTmFormat, icsHeader
from scal3.s_object import *

try:
	import logging
	log = logging.getLogger(APP_NAME)
except Exception:
	from scal3.utils import FallbackLogger
	log = FallbackLogger()

# FIXME
pluginsTitleByName = {
	"pray_times": _("Islamic Pray Times"),
}

pluginClassByName = {}


def registerPlugin(cls):
	assert cls.name
	pluginClassByName[cls.name] = cls
	return cls


def getPlugPath(_file):
	return _file if isabs(_file) else join(plugDir, _file)


class BasePlugin(SObj):
	name = None
	external = False
	loaded = True
	params = (
		# "calType",
		"title",  # previously "desc"
		"enable",
		"show_date",
		"default_enable",
		"default_show_date",
		"about",
		"authors",
		"hasConfig",
		"hasImage",
		"lastDayMerge",
	)
	essentialParams = (  # FIXME
		"title",
	)

	def getArgs(self):
		return {
			"_file": self.file,
			"enable": self.enable,
			"show_date": self.show_date,
		}

	def __bool__(self):
		return self.enable  # FIXME

	def __init__(
		self,
		_file,
	):
		self.file = _file
		######
		self.calType = GREGORIAN
		self.title = ""
		###
		self.enable = False
		self.show_date = False
		##
		self.default_enable = False
		self.default_show_date = False
		###
		self.about = ""
		self.authors = []
		self.hasConfig = False
		self.hasImage = False
		self.lastDayMerge = True

	def getData(self):
		data = JsonSObj.getData(self)
		data["calType"] = calTypes.names[self.calType]
		return data

	def setData(self, data):
		if "enable" not in data:
			data["enable"] = data.get("default_enable", self.default_enable)
		###
		if "show_date" not in data:
			data["show_date"] = data.get("default_show_date", self.default_show_date)
		###
		title = data.get("title")
		if title:
			data["title"] = _(title)
		###
		about = data.get("about")
		if about:
			data["about"] = _(about)
		###
		authors = data.get("authors")
		if authors:
			data["authors"] = [_(author) for author in authors]
		#####
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				# raise ValueError(f"Invalid calType: '{calType}'")
				log.error(
					f"Plugin \"{_file}\" needs calendar module " +
					f"\"{calType}\" that is not loaded!\n"
				)
				self.calType = None
			del data["calType"]
		#####
		JsonSObj.setData(self, data)

	def clear(self):
		pass

	def load(self):
		pass

	def getText(self, year, month, day):
		return ""

	def updateCell(self, c):
		module, ok = calTypes[self.calType]
		if not ok:
			raise RuntimeError(f"cal type '{self.calType}' not found")

		y, m, d = c.dates[self.calType]
		text = ""
		t = self.getText(y, m, d)
		if t:
			text += t
		if self.lastDayMerge and d >= module.minMonthLen:
			# and d <= module.maxMonthLen:
			ny, nm, nd = jd_to(c.jd + 1, self.calType)
			if nm > m or ny > y:
				nt = self.getText(y, m, d + 1)
				if nt:
					text += nt
		if text:
			c.addPluginText(text)

	def onCurrentDateChange(self, gdate):
		pass

	def exportToIcs(self, fileName, startJd, endJd):
		currentTimeStamp = strftime(icsTmFormat)
		self.load()  # FIXME
		calType = self.calType
		icsText = icsHeader
		for jd in range(startJd, endJd):
			myear, mmonth, mday = jd_to(jd, calType)
			dayText = self.getText(myear, mmonth, mday)
			if dayText:
				gyear, gmonth, gday = jd_to(jd, GREGORIAN)
				gyear2, gmonth2, gday2 = jd_to(jd + 1, GREGORIAN)
				#######
				icsText += "\n".join([
					"BEGIN:VEVENT",
					"CREATED:" + currentTimeStamp,
					"LAST-MODIFIED:" + currentTimeStamp,
					"DTSTART;VALUE=DATE:" + getIcsDateByJd(jd),
					"DTEND;VALUE=DATE:" + getIcsDateByJd(jd + 1),
					"SUMMARY:" + dayText,
					"END:VEVENT",
				]) + "\n"
		icsText += "END:VCALENDAR\n"
		open(fileName, "w", encoding="utf-8").write(icsText)


class BaseJsonPlugin(BasePlugin, JsonSObj):
	def save(self):  # json file self.file is read-only
		pass


class DummyExternalPlugin(BasePlugin):
	name = "external"  # FIXME
	external = True
	loaded = False
	enable = False
	show_date = False
	about = ""
	authors = []
	hasConfig = False
	hasImage = False

	def __repr__(self):
		return f"loadPlugin({self.file!r}, enable=False, show_date=False)"

	def __init__(self, _file, title):
		self.file = _file
		self.title = title


def loadExternalPlugin(_file, **data):
	_file = getPlugPath(_file)
	fname = split(_file)[-1]
	if not isfile(_file):
		log.error(f"plugin file \"{_file}\" not found! maybe removed?")
		# try:
		# 	plugIndex.remove(
		return None  # FIXME
		# plug = BaseJsonPlugin(
		# 	_file,
		# 	calType=0,
		# 	title="Failed to load plugin",
		# 	enable=enable,
		# 	show_date=show_date,
		# )
		# plug.external = True
		# return plug
	###
	direc = dirname(_file)
	name = splitext(fname)[0]
	###
	if not data.get("enable"):
		return DummyExternalPlugin(
			_file,
			pluginsTitleByName.get(name, name),
		)
	###
	mainFile = data.get("mainFile")
	if not mainFile:
		log.error(f"invalid external plugin \"{_file}\"")
		return
	###
	mainFile = getPlugPath(mainFile)
	###
	pyEnv = {
		"__file__": mainFile,
		"BasePlugin": BasePlugin,
		"BaseJsonPlugin": BaseJsonPlugin,
	}
	try:
		with open(mainFile, encoding="utf-8") as fp:
			exec(fp.read(), pyEnv)
	except Exception:
		log.error(f"error while loading external plugin \"{_file}\"")
		log.exception("")
		return
	###
	cls = pyEnv.get("TextPlugin")
	if cls is None:
		log.error(f"invalid external plugin \"{_file}\", no TextPlugin class")
		return
	###
	try:
		plugin = cls(_file)
	except Exception:
		log.error(f"error while loading external plugin \"{_file}\"")
		log.exception("")
		return

	# sys.path.insert(0, direc)
	# try:
	# 	mod = __import__(name)
	# except:
	# 	log.exception("")
	# 	return None
	# finally:
	# 	sys.path.pop(0)
	# mod.module_init(sourceDir, )  # FIXME
	# try:
	# 	plugin = mod.TextPlugin(_file)
	# except:
	# 	log.exception("")
	# 	# log.debug(dir(mod))
	# 	return
	plugin.external = True
	plugin.setData(data)
	plugin.onCurrentDateChange(localtime()[:3])
	return plugin


@registerPlugin
class HolidayPlugin(BaseJsonPlugin):
	name = "holiday"

	def __init__(self, _file):
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = True  # FIXME
		self.holidays = {}

	def setData(self, data):
		if "holidays" in data:
			for calTypeName in data["holidays"]:
				try:
					calType = calTypes.names.index(calTypeName)
				except ValueError:
					continue
				calTypeHolidays = []
				for row in data["holidays"][calTypeName]:
					if isinstance(row, str):  # comment
						continue
					if not isinstance(row, (list, tuple)):
						log.error(f"Bad type for holiday item '{row}'")
						continue
					if len(row) not in (2, 3):
						log.error(f"Bad length for holiday item '{row}'")
						continue
					calTypeHolidays.append(tuple(row))
				self.holidays[calType] = calTypeHolidays
			del data["holidays"]
		else:
			log.error(f"no \"holidays\" key in holiday plugin \"{self.file}\"")
		###
		BaseJsonPlugin.setData(self, data)

	def dateIsHoliday(self, calType, y, m, d, jd):
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")

		for item in self.holidays[calType]:
			if len(item) == 2:
				hm, hd = item
				hy = None
			elif len(item) == 3:
				hy, hm, hd = item
			else:
				log.error(f"bad holiday item '{item}'")
				continue

			if hy is not None and hy != y:
				continue

			if hm != m:
				continue

			if d == hd:
				return True

			if (
				hy is None and
				self.lastDayMerge and
				d == hd - 1 and
				hd >= module.minMonthLen
			):
				ny, nm, nd = jd_to(jd + 1, calType)
				if (ny, nm) > (y, m):
					return True

		return False

	def updateCell(self, c):
		if not c.holiday:
			for calType in self.holidays:
				y, m, d = c.dates[calType]
				if self.dateIsHoliday(calType, y, m, d, c.jd):
					c.holiday = True
					return

	def exportToIcs(self, fileName, startJd, endJd):
		currentTimeStamp = strftime(icsTmFormat)
		icsText = icsHeader

		for jd in range(startJd, endJd):
			isHoliday = False
			for calType in self.holidays.keys():
				myear, mmonth, mday = jd_to(jd, calType)
				if (mmonth, mday) in self.holidays[calType]:
					isHoliday = True
					break
				if (myear, mmonth, mday) in self.holidays[calType]:
					isHoliday = True
					break
			if isHoliday:
				gyear, gmonth, gday = jd_to(jd, GREGORIAN)
				gyear2, gmonth2, gday2 = jd_to(jd + 1, GREGORIAN)
				#######
				icsText += "\n".join([
					"BEGIN:VEVENT",
					"CREATED:" + currentTimeStamp,
					"LAST-MODIFIED:" + currentTimeStamp,
					"DTSTART;VALUE=DATE:" + getIcsDateByJd(jd),
					"DTEND;VALUE=DATE:" + getIcsDateByJd(jd + 1),
					"CATEGORIES:Holidays",
					"TRANSP:TRANSPARENT",
					# TRANSPARENT because being in holiday time,
					# does not make you busy!
					# see http://www.kanzaki.com/docs/ical/transp.html
					"SUMMARY:" + _("Holiday"),
					"END:VEVENT",
				]) + "\n"
		icsText += "END:VCALENDAR\n"
		open(fileName, "w", encoding="utf-8").write(icsText)

	# def getJdList(self, startJd, endJd):


@registerPlugin
class YearlyTextPlugin(BaseJsonPlugin):
	name = "yearlyText"
	params = BaseJsonPlugin.params + (
		"dataFile",
	)

	def __init__(self, _file):
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.dataFile = ""

	def setData(self, data):
		if "dataFile" in data:
			self.dataFile = getPlugPath(data["dataFile"])
			del data["dataFile"]
		else:
			log.error(
				f"no \"dataFile\" key in yearly text plugin \"{self.file}\""
			)
		####
		BaseJsonPlugin.setData(self, data)

	def clear(self):
		# yearlyData is a list of size 13 or 0, each item being a list
		# except for last item (index 12) which is a dict
		self.yearlyData = []

	def load(self):
		# log.debug(f"YearlyTextPlugin({self._file}).load()")
		yearlyData = []
		module, ok = calTypes[self.calType]
		if not ok:
			raise RuntimeError(f"cal type '{self.calType}' not found")
		for j in range(12):
			monthDb = []
			for k in range(module.maxMonthLen):
				monthDb.append("")
			yearlyData.append(monthDb)
		# last item is a dict of dates (y, m, d) and the description of day:
		yearlyData.append({})
		ext = splitext(self.dataFile)[1].lower()
		if ext == ".txt":
			sep = "\t"
			with open(self.dataFile, encoding="utf-8") as fp:
				lines = fp.read().split("\n")
			for line in lines[1:]:
				line = line.strip()
				if not line:
					continue
				if line[0] == "#":
					continue
				parts = line.split("\t")
				if len(parts) < 2:
					log.error(f"bad plugin data line: {line}")
					continue
				date = parts[0].split("/")
				text = "\t".join(parts[1:])
				if len(date) == 3:
					y = int(date[0])
					m = int(date[1])
					d = int(date[2])
					yearlyData[12][(y, m, d)] = text
				elif len(date) == 2:
					m = int(date[0])
					d = int(date[1])
					yearlyData[m - 1][d - 1] = text
				else:
					raise IOError(f"Bad line in data file {self.dataFile}:\n{line}")
		else:
			raise ValueError(f"invalid plugin dataFile extention \"{ext}\"")
		self.yearlyData = yearlyData

	def getBasicYearlyText(month, day):
		item = yearlyData[month - 1]

	def getText(self, year, month, day):
		yearlyData = self.yearlyData
		if not yearlyData:
			return ""
		calType = self.calType
		# if calType != calTypes.primary:
		# 	year, month, day = convert(year, month, day, calTypes.primary, calType)
		text = ""
		item = yearlyData[month - 1]
		if len(item) > day - 1:
			text = item[day - 1]
		if self.show_date and text:
			text = (
				_(day) +
				" " +
				getMonthName(calType, month) +
				": " +
				text
			)
		if len(yearlyData) > 12:
			text2 = yearlyData[12].get((year, month, day), "")
			if text2:
				if text:
					text += "\n"
				if self.show_date:
					text2 = (
						_(day) +
						" " +
						getMonthName(calType, month, year) +
						" " +
						_(year) +
						": " +
						text2
					)
				text += text2
		return text


# TODO: add checkbox/bool: holiday=False
@registerPlugin
class IcsTextPlugin(BasePlugin):
	name = "ics"

	def __init__(self, _file, enable=True, show_date=False, all_years=False):
		title = splitext(_file)[0]
		self.ymd = None
		self.md = None
		self.all_years = all_years
		BasePlugin.__init__(
			self,
			_file,
		)
		self.calType = GREGORIAN
		self.title = title
		self.enable = enable
		self.show_date = show_date

	def clear(self):
		self.ymd = None
		self.md = None

	def load(self):
		with open(self.file, encoding="utf-8") as fp:
			lines = fp.read().replace("\r", "").split("\n")
		n = len(lines)
		i = 0
		while True:
			try:
				if lines[i] == "BEGIN:VEVENT":
					break
			except IndexError:
				log.error(f"bad ics file \"{self.fpath}\"")
				return
			i += 1
		SUMMARY = ""
		DESCRIPTION = ""
		DTSTART = None
		DTEND = None
		if self.all_years:
			md = {}
			while True:
				i += 1
				try:
					line = lines[i]
				except IndexError:
					break
				if line == "END:VEVENT":
					if SUMMARY and DTSTART and DTEND:
						text = SUMMARY
						if DESCRIPTION:
							text += "\n" + DESCRIPTION
						for jd in getJdListFromEpochRange(DTSTART, DTEND):
							y, m, d = gregorian.jd_to(jd)
							md[(m, d)] = text
					else:
						log.error(
							f"unsupported ics event, SUMMARY={SUMMARY}, " +
							f"DTSTART={DTSTART}, DTEND={DTEND}"
						)
					SUMMARY = ""
					DESCRIPTION = ""
					DTSTART = None
					DTEND = None
				elif line.startswith("SUMMARY:"):
					SUMMARY = line[8:].replace("\\,", ",").replace("\\n", "\n")
				elif line.startswith("DESCRIPTION:"):
					DESCRIPTION = line[12:].replace("\\,", ",").replace("\\n", "\n")
				elif line.startswith("DTSTART;"):
					# if not line.startswith("DTSTART;VALUE=DATE;"):
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					icsTime = line.split(":")[-1]
					# if len(icsTime)!=8:
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					try:
						DTSTART = getEpochByIcsTime(icsTime)
					except Exception:
						log.error(f"unsupported ics line: {line}")
						log.exception("")
						continue
				elif line.startswith("DTEND;"):
					# if not line.startswith("DTEND;VALUE=DATE;"):
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					icsTime = line.split(":")[-1]
					# if len(icsTime)!=8:
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					try:
						DTEND = getEpochByIcsTime(icsTime)
					except Exception:
						log.error(f"unsupported ics line: {line}")
						log.exception("")
						continue
			self.ymd = None
			self.md = md
		else:  # not self.all_years
			ymd = {}
			while True:
				i += 1
				try:
					line = lines[i]
				except IndexError:
					break
				if line == "END:VEVENT":
					if SUMMARY and DTSTART and DTEND:
						text = SUMMARY
						if DESCRIPTION:
							text += "\n" + DESCRIPTION
						for jd in getJdListFromEpochRange(DTSTART, DTEND):
							y, m, d = gregorian.jd_to(jd)
							ymd[(y, m, d)] = text
					SUMMARY = ""
					DESCRIPTION = ""
					DTSTART = None
					DTEND = None
				elif line.startswith("SUMMARY:"):
					SUMMARY = line[8:].replace("\\,", ",").replace("\\n", "\n")
				elif line.startswith("DESCRIPTION:"):
					DESCRIPTION = line[12:].replace("\\,", ",").replace("\\n", "\n")
				elif line.startswith("DTSTART"):
					# if not line.startswith("DTSTART;VALUE=DATE"):
					# 	log.error("unsupported ics line: {line}")
					# 	continue
					icsTime = line.split(":")[-1]
					# if len(icsTime)!=8:
					# 	log.error("unsupported ics line: {line}")
					# 	continue
					try:
						DTSTART = getEpochByIcsTime(icsTime)
					except Exception:
						log.error(f"unsupported ics line: {line}")
						log.exception("")
						continue
				elif line.startswith("DTEND"):
					# if not line.startswith("DTEND;VALUE=DATE;"):
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					icsTime = line.split(":")[-1]
					# if len(icsTime)!=8:
					# 	log.error(f"unsupported ics line: {line}")
					# 	continue
					try:
						DTEND = getEpochByIcsTime(icsTime)
					except Exception:
						log.error(f"unsupported ics line: {line}")
						log.exception("")
						continue
			self.ymd = ymd
			self.md = None

	def getText(self, y, m, d):
		if self.ymd:
			if (y, m, d) in self.ymd:
				if self.show_date:
					return (
						_(d) +
						" " +
						getMonthName(self.calType, m) +
						" " +
						_(y) +
						": " +
						self.ymd[(y, m, d)]
					)
				else:
					return self.ymd[(y, m, d)]
		if self.md:
			if (m, d) in self.md:
				if self.show_date:
					return (
						_(d) +
						" " +
						getMonthName(self.calType, m) +
						" " +
						_(y) +
						": " +
						self.ymd[(y, m, d)]
					)
				else:
					return self.md[(m, d)]
		return ""

	def open_configure(self):
		pass

	def open_about(self):
		pass

# class EveryDayTextPlugin(BaseJsonPlugin):
# class RandomTextPlugin(BaseJsonPlugin):


def loadPlugin(_file=None, **kwargs):
	if not _file:
		log.error("plugin file is empty!")
		return
	_file = getPlugPath(_file)
	if not isfile(_file):
		log.error(f"error while loading plugin \"{_file}\": no such file!\n")
		return
	ext = splitext(_file)[1].lower()
	####
	# FIXME: should ics plugins require a json file too?
	if ext == ".ics":
		return IcsTextPlugin(_file, **kwargs)
	####
	if ext == ".md":
		return
	if ext != ".json":
		log.error(
			f"unsupported plugin extention {ext}" +
			", new style plugins have a json file"
		)
		return
	try:
		with open(_file, encoding="utf-8") as fp:
			text = fp.read()
	except Exception as e:
		log.error(
			f"error while reading plugin file \"{_file}\"" +
			f": {e}"
		)
		return
	try:
		data = jsonToData(text)
	except Exception as e:
		log.error(f"invalid json file \"{_file}\"")
		log.exception("")
		return
	####
	data.update(kwargs)  # FIXME
	####
	name = data.get("type")
	if not name:
		log.error(f"invalid plugin \"{_file}\", no \"type\" key")
		return
	####
	if name == "external":
		return loadExternalPlugin(_file, **data)
	####
	try:
		cls = pluginClassByName[name]
	except KeyError:
		log.error(f"invald plugin type \"{name}\" in file \"{_file}\"")
		return
	####
	for param in cls.essentialParams:
		if not data.get(param):
			log.error(
				f"invalid plugin \"{_file}\"" +
				f": parameter \"{param}\" is missing"
			)
			return
	####
	plug = cls(_file)
	plug.setData(data)
	####
	return plug
