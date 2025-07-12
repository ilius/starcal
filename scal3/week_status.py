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
from scal3.pytypes import CellType

if typing.TYPE_CHECKING:
	from scal3.pytypes import CellCacheType

__all__ = ["WeekStatus"]


class WeekStatus(list[CellType]):
	__slots__ = [
		"absWeekNumber",
	]

	# list (of 7 cells)
	def __init__(self, cells: CellCacheType, absWeekNumber: int) -> None:
		self.absWeekNumber = absWeekNumber
		startJd = core.getStartJdOfAbsWeekNumber(absWeekNumber)
		endJd = startJd + 7
		# self.startJd = startJd
		# self.startDate = core.jd_to_primary(self.startJd)
		# self.weekNumberOfYear = core.getWeekNumber(*self.startDate)
		# ---------
		# list.__init__(self, [
		# 	cells.getCell(jd) for jd in range(startJd, endJd)
		# ])
		list.__init__(self, [])
		for jd in range(startJd, endJd):
			# log.debug("WeekStatus", jd)
			self.append(cells.getCell(jd))
