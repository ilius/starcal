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

from typing import TYPE_CHECKING

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _

if TYPE_CHECKING:
	from scal3.pytypes import CellType, MonthStatusType

__all__ = ["getMonthDesc"]


pluginName = "MonthCal"

# ------------------------


# TODO: write test for it
def getMonthDesc(status: MonthStatusType | None = None) -> str:
	if not status:
		status = ui.cells.getCurrentMonthStatus()
	first: CellType | None = None
	last: CellType | None = None
	for i in range(6):
		for j in range(7):
			c = status[i][j]
			if first:
				if c.month == status.month:
					last = c
					continue
				break
			if c.month == status.month:
				first = c
	assert first is not None
	assert last is not None
	text = ""
	for calType in calTypes.active:
		if text:
			text += "\n"
		if calType == calTypes.primary:
			y, m = first.dates[calType][:2]  # = (status.year, status.month)
			text += getMonthName(calType, m) + " " + _(y)
		else:
			y1, m1 = first.dates[calType][:2]
			y2, m2 = last.dates[calType][:2]
			dy = y2 - y1
			if dy == 0:
				dm = m2 - m1
			elif dy == 1:
				dm = m2 + 12 - m1
			else:
				raise RuntimeError(f"{y1=}, {m1=}, {y2=}, {m2=}")
			if dm == 0:
				text += getMonthName(calType, m1) + " " + _(y1)
			elif dm == 1:
				if dy == 0:
					text += (
						getMonthName(calType, m1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, m2)
						+ " "
						+ _(y1)
					)
				else:
					text += (
						getMonthName(calType, m1)
						+ " "
						+ _(y1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, m2)
						+ " "
						+ _(y2)
					)
			elif dm == 2:
				if dy == 0:
					text += (
						getMonthName(calType, m1)
						+ _(",")
						+ " "
						+ getMonthName(calType, m1 + 1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, m2)
						+ " "
						+ _(y1)
					)
				elif m1 == 11:
					text += (
						getMonthName(calType, m1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, m1 + 1)
						+ " "
						+ _(y1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, 1)
						+ " "
						+ _(y2)
					)
				elif m1 == 12:
					text += (
						getMonthName(calType, m1)
						+ " "
						+ _(y1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, 1)
						+ " "
						+ _("and")
						+ " "
						+ getMonthName(calType, 2)
						+ " "
						+ _(y2)
					)
	return text
