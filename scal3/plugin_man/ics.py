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

from os.path import splitext

from scal3.cal_types import GREGORIAN, gregorian
from scal3.ics import getEpochByIcsTime
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.plugin_man.base import BasePlugin, log, registerPlugin
from scal3.time_utils import getJdListFromEpochRange

__all__ = ["IcsTextPlugin"]


@registerPlugin
class IcsTextPlugin(BasePlugin):
	name = "ics"

	def __init__(
		self,
		file: str,
		enable: bool = True,
		show_date: bool = False,
		all_years: bool = False,
	) -> None:
		title = splitext(file)[0]
		self.ymd: dict[tuple[int, int, int], str] | None = None
		self.md: dict[tuple[int, int], str] | None = None
		self.all_years = all_years
		BasePlugin.__init__(
			self,
			file,
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
