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

from scal3 import logger

log = logger.get()

import typing

from scal3 import core
from scal3.cal_types import calTypes
from scal3.date_utils import getJdRangeForMonth
from scal3.pytypes import CellType

if typing.TYPE_CHECKING:
	from scal3.pytypes import CellCacheType

__all__ = ["MonthStatus"]


class MonthStatus(list[list[CellType]]):  # FIXME
	__slots__ = [
		"month",
		"offset",
		"weekNum",
		"year",
	]

	# self[sy<6][sx<7] of cells
	# list (of 6 lists, each list containing 7 cells)
	def __init__(
		self,
		cells: CellCacheType,
		year: int,
		month: int,
	) -> None:
		self.year = year
		self.month = month
		self.offset = core.getWeekDay(year, month, 1)  # month start offset
		initJd = core.primary_to_jd(year, month, 1)
		self.weekNum = [core.getWeekNumberByJd(initJd + i * 7) for i in range(6)]
		# ---------
		startJd, _endJd = getJdRangeForMonth(year, month, calTypes.primary)
		tableStartJd = startJd - self.offset
		# -----
		list.__init__(
			self,
			[
				[
					cells.getCell(
						tableStartJd + yPos * 7 + xPos,
					)
					for xPos in range(7)
				]
				for yPos in range(6)
			],
		)

	# needed? FIXME
	# def getDayCell(self, day):
	# 	yPos, xPos = divmod(day + self.offset - 1, 7)
	# 	return self[yPos][xPos]
