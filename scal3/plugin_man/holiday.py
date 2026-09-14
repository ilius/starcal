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

from time import strftime
from typing import TYPE_CHECKING, Any

from scal3.cal_types import calTypes, jd_to
from scal3.ics import getIcsDateByJd, icsHeader, icsTmFormat
from scal3.locale_man import tr as _
from scal3.plugin_man.base import BaseJsonPlugin, log, registerPlugin

if TYPE_CHECKING:
	from scal3.pytypes import CellType

__all__ = ["HolidayPlugin"]


@registerPlugin
class HolidayPlugin(BaseJsonPlugin):
	name = "holiday"

	def __init__(self, file: str) -> None:
		BaseJsonPlugin.__init__(
			self,
			file,
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
		with open(fileName, "w", encoding="utf-8") as file:
			file.write(icsText)

	# def getJdList(self, startJd, endJd):
