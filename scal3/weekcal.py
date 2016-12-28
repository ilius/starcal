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

#from scal3.locale_man import tr as _

from scal3 import core
from scal3.core import myRaise, getMonthName, getMonthLen, pixDir

from scal3 import ui

pluginName = 'WeekCal'


class WeekStatus(list):
	# list (of 7 cells)
	def __init__(self, cellCache, absWeekNumber):
		self.absWeekNumber = absWeekNumber
		startJd = core.getStartJdOfAbsWeekNumber(absWeekNumber)
		endJd = startJd + 7
		#self.startJd = startJd
		#self.startDate = core.jd_to_primary(self.startJd)
		#self.weekNumberOfYear = core.getWeekNumber(*self.startDate)
		#########
		#list.__init__(self, [cellCache.getCell(jd) for jd in range(startJd, endJd)])
		list.__init__(self, [])
		for jd in range(startJd, endJd):
			#print('WeekStatus', jd)
			self.append(cellCache.getCell(jd))

	def allCells(self):
		return self


def setParamsFunc(cell):
	cell.absWeekNumber, cell.weekDayIndex = core.getWeekDateFromJd(cell.jd)


def getWeekStatus(absWeekNumber):
	return ui.cellCache.getCellGroup(
		pluginName,
		absWeekNumber,
	)


def getCurrentWeekStatus():
	return ui.cellCache.getCellGroup(
		pluginName,
		ui.cell.absWeekNumber,
	)

########################

ui.cellCache.registerPlugin(
	pluginName,
	setParamsFunc,
	WeekStatus,
)
