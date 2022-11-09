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

from scal3.cal_types import calTypes, getMonthLen
from scal3 import core
from scal3.core import (
	getMonthName,
	getWeekDay,
	getWeekNumberByJd,
)
from scal3.locale_man import rtl, rtlSgn
from scal3.locale_man import tr as _
from scal3 import ui

pluginName = "MonthCal"


class MonthStatus(list):  # FIXME
	# self[sy<6][sx<7] of cells
	# list (of 6 lists, each list containing 7 cells)
	def __init__(self, cellCache, year, month):
		self.year = year
		self.month = month
		self.monthLen = getMonthLen(year, month, calTypes.primary)
		self.offset = getWeekDay(year, month, 1)  # month start offset
		initJd = core.primary_to_jd(year, month, 1)
		self.weekNum = [
			getWeekNumberByJd(initJd + i * 7)
			for i in range(6)
		]
		#########
		startJd, endJd = core.getJdRangeForMonth(year, month, calTypes.primary)
		tableStartJd = startJd - self.offset
		#####
		list.__init__(self, [
			[
				cellCache.getCell(
					tableStartJd + yPos * 7 + xPos
				)
				for xPos in range(7)
			] for yPos in range(6)
		])

	# needed? FIXME
	# def getDayCell(self, day):
	# 	yPos, xPos = divmod(day + self.offset - 1, 7)
	# 	return self[yPos][xPos]

	def allCells(self):
		ls = []
		for row in self:
			ls += row
		return ls


def setParamsFunc(cell):
	offset = getWeekDay(cell.year, cell.month, 1)  # month start offset
	yPos, xPos = divmod(offset + cell.day - 1, 7)
	cell.monthPos = (xPos, yPos)
	###
	"""
	if yPos==0:
		cell.monthPosPrev = (xPos, 5)
	else:
		cell.monthPosPrev = None
	###
	if yPos==5:
		cell.monthPosNext = (xPos, 0)
	else:
		cell.monthPosNext = None
	"""


def getMonthStatus(year, month):
	return ui.cellCache.getCellGroup(
		pluginName,
		year,
		month,
	)


def getCurrentMonthStatus():
	return ui.cellCache.getCellGroup(
		pluginName,
		ui.cell.year,
		ui.cell.month,
	)

########################


# TODO: write test for it
def getMonthDesc(status=None):
	if not status:
		status = getCurrentMonthStatus()
	first = None
	last = None
	for i in range(6):
		for j in range(7):
			c = status[i][j]
			if first:
				if c.month == status.month:
					last = c
				else:
					break
			else:
				if c.month == status.month:
					first = c
				else:
					continue
	text = ""
	for calType in calTypes.active:
		if text != "":
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
						getMonthName(calType, m1) +
						" " + _("and") + " " +
						getMonthName(calType, m2) +
						" " +
						_(y1)
					)
				else:
					text += (
						getMonthName(calType, m1) + " " + _(y1) +
						" " + _("and") + " " +
						getMonthName(calType, m2) + " " + _(y2)
					)
			elif dm == 2:
				if dy == 0:
					text += (
						getMonthName(calType, m1) +
						_(",") + " " +
						getMonthName(calType, m1 + 1) +
						" " + _("and") + " " +
						getMonthName(calType, m2) +
						" " +
						_(y1)
					)
				else:
					if m1 == 11:
						text += (
							getMonthName(calType, m1) +
							" " + _("and") + " " +
							getMonthName(calType, m1 + 1) +
							" " +
							_(y1) +
							" " + _("and") + " " +
							getMonthName(calType, 1) +
							" " +
							_(y2)
						)
					elif m1 == 12:
						text += (
							getMonthName(calType, m1) +
							" " +
							_(y1) +
							" " +
							_("and") +
							" " +
							getMonthName(calType, 1) +
							" " +
							_("and") +
							" " +
							getMonthName(calType, 2) +
							" " +
							_(y2)
						)
	return text


########################

ui.cellCache.registerPlugin(
	pluginName,
	setParamsFunc,
	MonthStatus,
)
