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

from os.path import isabs, join
from time import strftime
from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.cal_types import GREGORIAN, calTypes, jd_to
from scal3.filesystem import null_fs
from scal3.ics import getIcsDateByJd, icsHeader, icsTmFormat
from scal3.locale_man import tr as _
from scal3.path import APP_NAME, plugDir
from scal3.s_object import SObjTextModel

if TYPE_CHECKING:
	from scal3.pytypes import CellType, PluginType

log = logger.get()

try:
	import logging

	log = logging.getLogger(APP_NAME)
except Exception:
	log.exception("Failed to setup logging")
	from scal3.logger import FallbackLogger

	log = FallbackLogger()


__all__ = [
	"BaseJsonPlugin",
	"BasePlugin",
	"DummyExternalPlugin",
	"getPlugPath",
	"pluginClassByName",
	"pluginsTitleByName",
	"registerPlugin",
]

# FIXME
pluginsTitleByName = {
	"pray_times": _("Islamic Pray Times"),
}

pluginClassByName: dict[str, type[BasePlugin]] = {}


def registerPlugin[T: BasePlugin](cls: type[T]) -> type[T]:
	assert cls.name
	pluginClassByName[cls.name] = cls
	return cls


def getPlugPath(file: str) -> str:
	return file if isabs(file) else join(plugDir, file)


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
		file: str,
	) -> None:
		self.file = file
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

	# open_about returns True only if overridden by external plugin
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
		self.s_load(0, fs=null_fs)
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
		with open(fileName, "w", encoding="utf-8") as file:
			file.write(icsText)


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

	def __init__(self, file: str, title: str) -> None:
		self.file = file
		self.title = title
		self.hasConfig = False
		self.hasImage = False
