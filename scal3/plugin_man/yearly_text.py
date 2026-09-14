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
from typing import Any

from scal3.cal_types import calTypes
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.plugin_man.base import BaseJsonPlugin, getPlugPath, log, registerPlugin

__all__ = ["YearlyTextPlugin"]


@registerPlugin
class YearlyTextPlugin(BaseJsonPlugin):
	name = "yearlyText"
	params = BaseJsonPlugin.params + ["dataFile"]

	def __init__(self, file: str) -> None:
		BaseJsonPlugin.__init__(
			self,
			file,
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
			for line_ in lines[1:]:
				line = line_.strip()
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
			raise ValueError(f'invalid plugin dataFile extension "{ext}"')
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
