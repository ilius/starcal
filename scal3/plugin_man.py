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

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.filesystem import null_fs

log = logger.get()

import json
from os.path import isabs, isfile, join, split, splitext
from time import localtime, strftime

from scal3.cal_types import (
	GREGORIAN,
	calTypes,
	gregorian,
	jd_to,
)
from scal3.ics import getEpochByIcsTime, getIcsDateByJd, icsHeader, icsTmFormat
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.path import APP_NAME, plugDir
from scal3.s_object import SObjTextModel
from scal3.time_utils import getJdListFromEpochRange

if TYPE_CHECKING:
	from scal3.pytypes import CellType, PluginType

try:
	import logging

	log = logging.getLogger(APP_NAME)
except Exception:
	log.exception("Failed to setup logging")
	from scal3.logger import FallbackLogger

	log = FallbackLogger()


__all__ = ["BaseJsonPlugin", "loadPlugin"]

# FIXME
pluginsTitleByName = {
	"pray_times": _("Islamic Pray Times"),
}

pluginClassByName: dict[str, type[BasePlugin]] = {}


def registerPlugin[T: BasePlugin](cls: type[T]) -> type[T]:
	assert cls.name
	pluginClassByName[cls.name] = cls
	return cls


def getPlugPath(_file: str) -> str:
	return _file if isabs(_file) else join(plugDir, _file)


class BasePlugin(SObjTextModel):
	name: str = ""
	external = False
	loaded = True
	params = [
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
	]
	essentialParams = ["title"]  # FIXME

	def getArgs(self) -> dict[str, Any]:
		return {
			"_file": self.file,
			"enable": self.enable,
			"show_date": self.show_date,
		}

	def __bool__(self) -> bool:
		return self.enable  # FIXME

	def __init__(
		self,
		_file: str,
	) -> None:
		self.file = _file
		# ------
		self.calType: int | None = GREGORIAN
		self.title = ""
		# ---
		self.enable = False
		self.show_date = False
		# --
		self.default_enable = False
		self.default_show_date = False
		# ---
		self.about = ""
		self.authors: list[str] = []
		self.hasConfig = False
		self.hasImage = False
		self.lastDayMerge = True

	def open_configure(self) -> None:
		pass

	# open_about returns True only if overriden by external plugin
	def open_about(self) -> bool:  # noqa: PLR6301
		return False

	def getDict(self) -> dict[str, Any]:
		data = SObjTextModel.getDict(self)
		if self.calType is not None:
			data["calType"] = calTypes.names[self.calType]
		return data

	def setDict(self, data: dict[str, Any]) -> None:
		if "enable" not in data:
			data["enable"] = data.get("default_enable", self.default_enable)
		# ---
		if "show_date" not in data:
			data["show_date"] = data.get("default_show_date", self.default_show_date)
		# ---
		title = data.get("title")
		if title:
			data["title"] = _(title)
		# ---
		about = data.get("about")
		if about:
			data["about"] = _(about)
		# ---
		authors = data.get("authors")
		if authors:
			data["authors"] = [_(author) for author in authors]
		# -----
		if "calType" in data:
			calType = data["calType"]
			try:
				self.calType = calTypes.names.index(calType)
			except ValueError:
				# raise ValueError(f"Invalid calType: '{calType}'")
				log.error(
					f'Plugin "{self.file}" needs calendar module '
					f'"{calType}" that is not loaded!\n',
				)
				self.calType = None
			del data["calType"]
		# -----
		SObjTextModel.setDict(self, data)

	def loadData(self) -> None:
		pass

	def clear(self) -> None:
		pass

	def getText(  # noqa: PLR6301
		self,
		year: int,  # noqa: ARG002
		month: int,  # noqa: ARG002
		day: int,  # noqa: ARG002
	) -> str:
		return ""

	def updateCell(self, c: CellType) -> None:
		if self.calType is None:
			return
		module = calTypes[self.calType]
		if module is None:
			raise RuntimeError(f"cal type '{self.calType}' not found")

		y, m, d = c.dates[self.calType]
		text = ""
		t = self.getText(y, m, d)
		if t:
			text += t
		if self.lastDayMerge and d >= module.minMonthLen:
			# and d <= module.maxMonthLen:
			ny, nm, _nd = jd_to(c.jd + 1, self.calType)
			if nm > m or ny > y:
				nt = self.getText(y, m, d + 1)
				if nt:
					text += nt
		if text:
			plug: PluginType = self
			c.addPluginText(plug, text)

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:
		pass

	def exportToIcs(self, fileName: str, startJd: int, endJd: int) -> None:
		if self.calType is None:
			log.error("self.calType is None")
			return
		currentTimeStamp = strftime(icsTmFormat)
		self.load(0, fs=null_fs)
		calType = self.calType
		icsText = icsHeader
		for jd in range(startJd, endJd):
			myear, mmonth, mday = jd_to(jd, calType)
			dayText = self.getText(myear, mmonth, mday)
			if dayText:
				icsText += (
					"\n".join(
						[
							"BEGIN:VEVENT",
							"CREATED:" + currentTimeStamp,
							"LAST-MODIFIED:" + currentTimeStamp,
							"DTSTART;VALUE=DATE:" + getIcsDateByJd(jd),
							"DTEND;VALUE=DATE:" + getIcsDateByJd(jd + 1),
							"SUMMARY:" + dayText,
							"END:VEVENT",
						],
					)
					+ "\n"
				)
		icsText += "END:VCALENDAR\n"
		with open(fileName, "w", encoding="utf-8") as _file:
			_file.write(icsText)


class BaseJsonPlugin(BasePlugin, SObjTextModel):
	def save(self) -> None:  # json file self.file is read-only
		pass


class DummyExternalPlugin(BasePlugin):
	name = "external"  # FIXME
	external = True
	loaded = False
	enable = False
	show_date = False
	about = ""
	authors = []

	def __repr__(self) -> str:
		return f"loadPlugin({self.file!r}, enable=False, show_date=False)"

	def __init__(self, _file: str, title: str) -> None:
		self.file = _file
		self.title = title
		self.hasConfig = False
		self.hasImage = False


def loadExternalPlugin(
	file: str,
	**data: object,
) -> PluginType | None:
	file = getPlugPath(file)
	fname = split(file)[-1]
	if not isfile(file):
		log.error(f'plugin file "{file}" not found! maybe removed?')
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
	# ---
	name = splitext(fname)[0]
	# ---
	if not data.get("enable"):
		return DummyExternalPlugin(
			file,
			pluginsTitleByName.get(name, name),
		)
	# ---
	mainFile: str = data.get("mainFile")  # type: ignore[assignment]
	if not mainFile:
		log.error(f'invalid external plugin "{file}"')
		return None
	# ---
	mainFile = getPlugPath(mainFile)
	# ---
	pyEnv = {
		"__file__": mainFile,
		"BasePlugin": BasePlugin,
		"BaseJsonPlugin": BaseJsonPlugin,
	}
	try:
		with open(mainFile, encoding="utf-8") as fp:
			exec(fp.read(), pyEnv)
	except Exception:
		log.error(f'error while loading external plugin "{file}"')
		log.exception("")
		return None
	# ---
	cls: type[PluginType] | None = pyEnv.get("TextPlugin")  # type: ignore[assignment]
	if cls is None:
		log.error(f'invalid external plugin "{file}", no TextPlugin class')
		return None
	# ---
	try:
		plugin = cls(file)
	except Exception:
		log.error(f'error while loading external plugin "{file}"')
		log.exception("")
		return None

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
	plugin.setDict(data)
	plugin.onCurrentDateChange(localtime()[:3])
	return plugin


@registerPlugin
class HolidayPlugin(BaseJsonPlugin):
	name = "holiday"

	def __init__(self, _file: str) -> None:
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = True  # FIXME
		self.holidays: dict[int, list[tuple[int, int] | tuple[int, int, int]]] = {}

	def setDict(self, data: dict[str, Any]) -> None:
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
					if not isinstance(row, list | tuple):
						log.error(f"Bad type for holiday item '{row}'")
						continue
					if len(row) not in {2, 3}:
						log.error(f"Bad length for holiday item '{row}'")
						continue
					calTypeHolidays.append(tuple(row))
				self.holidays[calType] = calTypeHolidays
			del data["holidays"]
		else:
			log.error(f'no "holidays" key in holiday plugin "{self.file}"')
		# ---
		BaseJsonPlugin.setDict(self, data)

	def dateIsHoliday(self, calType: int, y: int, m: int, d: int, jd: int) -> bool:
		module = calTypes[calType]
		if module is None:
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
				hy is None
				and self.lastDayMerge
				and d == hd - 1
				and hd >= module.minMonthLen
			):
				ny, nm, _nd = jd_to(jd + 1, calType)
				if (ny, nm) > (y, m):
					return True

		return False

	def updateCell(self, c: CellType) -> None:
		if not c.holiday:
			for calType in self.holidays:
				y, m, d = c.dates[calType]
				if self.dateIsHoliday(calType, y, m, d, c.jd):
					c.holiday = True
					return

	def exportToIcs(self, fileName: str, startJd: int, endJd: int) -> None:
		currentTimeStamp = strftime(icsTmFormat)
		icsText = icsHeader

		for jd in range(startJd, endJd):
			isHoliday = False
			for calType in self.holidays:
				myear, mmonth, mday = jd_to(jd, calType)
				if (mmonth, mday) in self.holidays[calType]:
					isHoliday = True
					break
				if (myear, mmonth, mday) in self.holidays[calType]:
					isHoliday = True
					break
			if isHoliday:
				icsText += (
					"\n".join(
						[
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
						],
					)
					+ "\n"
				)
		icsText += "END:VCALENDAR\n"
		with open(fileName, "w", encoding="utf-8") as _file:
			_file.write(icsText)

	# def getJdList(self, startJd, endJd):


@registerPlugin
class YearlyTextPlugin(BaseJsonPlugin):
	name = "yearlyText"
	params = BaseJsonPlugin.params + ["dataFile"]

	def __init__(self, _file: str) -> None:
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.dataFile = ""
		self.yearlyData: list[list[str]] = []
		self.yearlyDateData: dict[tuple[int, int, int], str] = {}

	def setDict(self, data: dict[str, Any]) -> None:
		if "dataFile" in data:
			self.dataFile = getPlugPath(data["dataFile"])
			del data["dataFile"]
		else:
			log.error(
				f'no "dataFile" key in yearly text plugin "{self.file}"',
			)
		# ----
		BaseJsonPlugin.setDict(self, data)

	def clear(self) -> None:
		# yearlyData is a list of size 13 or 0, each item being a list
		# except for last item (index 12) which is a dict
		self.yearlyData = []
		self.yearlyDateData = {}

	def loadData(self) -> None:
		if self.calType is None:
			return
		# log.debug(f"YearlyTextPlugin({self._file}).load()")
		module = calTypes[self.calType]
		if module is None:
			raise RuntimeError(f"cal type '{self.calType}' not found")
		yearlyData = [[""] * module.maxMonthLen for _j in range(12)]
		# a dict of dates (y, m, d) and the description of day:
		yearlyDateData: dict[tuple[int, int, int], str] = {}
		ext = splitext(self.dataFile)[1].lower()
		if ext == ".txt":
			# sep = "\t"
			with open(self.dataFile, encoding="utf-8") as fp:
				lines = fp.read().split("\n")
			for line in lines[1:]:
				line = line.strip()  # noqa: PLW2901
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
					yearlyDateData[y, m, d] = text
				elif len(date) == 2:
					m = int(date[0])
					d = int(date[1])
					yearlyData[m - 1][d - 1] = text
				else:
					raise OSError(f"Bad line in data file {self.dataFile}:\n{line}")
		else:
			raise ValueError(f'invalid plugin dataFile extention "{ext}"')
		self.yearlyData = yearlyData
		self.yearlyDateData = yearlyDateData

	# def getBasicYearlyText(month, day):
	# 	item = self.yearlyData[month - 1]
	# 	return item

	def getText(self, year: int, month: int, day: int) -> str:
		if self.calType is None:
			return ""
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
			text = _(day) + " " + getMonthName(calType, month) + ": " + text
		if self.yearlyDateData:
			text2 = self.yearlyDateData.get((year, month, day), "")
			if text2:
				if text:
					text += "\n"
				if self.show_date:
					text2 = (
						_(day)
						+ " "
						+ getMonthName(calType, month, year)
						+ " "
						+ _(year)
						+ ": "
						+ text2
					)
				text += text2
		return text


# TODO: add checkbox/bool: holiday=False
@registerPlugin
class IcsTextPlugin(BasePlugin):
	name = "ics"

	def __init__(
		self,
		_file: str,
		enable: bool = True,
		show_date: bool = False,
		all_years: bool = False,
	) -> None:
		title = splitext(_file)[0]
		self.ymd: dict[tuple[int, int, int], str] | None = None
		self.md: dict[tuple[int, int], str] | None = None
		self.all_years = all_years
		BasePlugin.__init__(
			self,
			_file,
		)
		self.calType = GREGORIAN
		self.title = title
		self.enable = enable
		self.show_date = show_date

	def clear(self) -> None:
		self.ymd = None
		self.md = None

	@staticmethod
	def _findVeventBegin(lines: list[str]) -> int:
		for i, line in enumerate(lines):
			if line == "BEGIN:VEVENT":
				return i
		return -1

	def _loadAllYears(self, lines: list[str], lineNum: int) -> None:
		SUMMARY = ""
		DESCRIPTION = ""
		DTSTART = None
		DTEND = None
		md = {}
		while True:
			lineNum += 1
			try:
				line = lines[lineNum]
			except IndexError:
				break
			if line == "END:VEVENT":
				if SUMMARY and DTSTART and DTEND:
					text = SUMMARY
					if DESCRIPTION:
						text += "\n" + DESCRIPTION
					for jd in getJdListFromEpochRange(DTSTART, DTEND):
						_y, m, d = gregorian.jd_to(jd)
						md[m, d] = text
				else:
					log.error(
						f"unsupported ics event, {SUMMARY=}, {DTSTART=}, {DTEND}=",
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
					log.exception(f"unsupported ics line: {line}")
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
					log.exception(f"unsupported ics line: {line}")
					continue
		self.ymd = None
		self.md = md

	def _loadYMD(self, lines: list[str], lineNum: int) -> None:
		SUMMARY = ""
		DESCRIPTION = ""
		DTSTART = None
		DTEND = None
		ymd = {}
		while True:
			lineNum += 1
			try:
				line = lines[lineNum]
			except IndexError:
				break
			if line == "END:VEVENT":
				if SUMMARY and DTSTART and DTEND:
					text = SUMMARY
					if DESCRIPTION:
						text += "\n" + DESCRIPTION
					for jd in getJdListFromEpochRange(DTSTART, DTEND):
						y, m, d = gregorian.jd_to(jd)
						ymd[y, m, d] = text
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

	def loadData(self) -> None:
		with open(self.file, encoding="utf-8") as fp:
			lines = fp.read().replace("\r", "").split("\n")
		lineNum = self._findVeventBegin(lines)
		if lineNum < 0:
			log.error(f'bad ics file "{self.file}"')
			return
		if self.all_years:
			self._loadAllYears(lines, lineNum)
		else:
			self._loadYMD(lines, lineNum)

	def getText(self, y: int, m: int, d: int) -> str:
		if self.calType is None:
			return ""

		if self.ymd and (y, m, d) in self.ymd:
			if self.show_date:
				return (
					_(d)
					+ " "
					+ getMonthName(self.calType, m)
					+ " "
					+ _(y)
					+ ": "
					+ self.ymd[y, m, d]
				)
			return self.ymd[y, m, d]

		if self.md and (m, d) in self.md:
			if not self.show_date:
				return self.md[m, d]
			text = _(d) + " " + getMonthName(self.calType, m) + " " + _(y)
			if self.ymd:
				text += ": " + self.ymd[y, m, d]
			return text

		return ""


# class EveryDayTextPlugin(BaseJsonPlugin):
# class RandomTextPlugin(BaseJsonPlugin):


# must not rename _file argument
def loadPlugin(_file: str | None = None, **kwargs: Any) -> PluginType | None:
	if not _file:
		log.error(f"plugin file is empty! {kwargs=}")
		return None
	file = getPlugPath(_file)
	if not isfile(file):
		log.error(f'error while loading plugin "{file}": no such file!\n')
		return None
	ext = splitext(file)[1].lower()
	# ----
	# FIXME: should ics plugins require a json file too?
	if ext == ".ics":
		return IcsTextPlugin(file, **kwargs)
	# ----
	if ext == ".md":
		return None
	if ext != ".json":
		log.error(
			f"unsupported plugin extention {ext}, new style plugins have a json file",
		)
		return None
	try:
		with open(file, encoding="utf-8") as fp:
			text = fp.read()
	except Exception as e:
		log.error(
			f'error while reading plugin file "{file}": {e}',
		)
		return None
	try:
		data = json.loads(text)
	except Exception:
		log.error(f'invalid json file "{file}"')
		log.exception("")
		return None
	# ----
	data.update(kwargs)  # FIXME
	# ----
	name = data.get("type")
	if not name:
		log.error(f'invalid plugin "{file}", no "type" key')
		return None
	# ----
	if name == "external":
		return loadExternalPlugin(file, **data)
	# ----
	try:
		cls = pluginClassByName[name]
	except KeyError:
		log.error(f'invald plugin type "{name}" in file "{file}"')
		return None
	# ----
	for param in cls.essentialParams:
		if not data.get(param):
			log.error(
				f'invalid plugin "{file}": param "{param}" is missing',
			)
			return None
	# ----
	plug = cls(file)
	plug.setDict(data)
	# ----
	return plug
