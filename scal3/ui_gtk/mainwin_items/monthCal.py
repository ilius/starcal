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

from scal3 import logger
log = logger.get()

from time import localtime
from time import time as now

import sys
import os
from math import sqrt

from typing import Tuple, Callable

from scal3 import cal_types
from scal3.cal_types import calTypes
from scal3 import core
from scal3.core import log
from scal3.locale_man import rtl, rtlSgn
from scal3.locale_man import tr as _
from scal3 import ui
from scal3.monthcal import getCurrentMonthStatus

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.utils import pixbufFromFile
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.stack import StackPage


@registerSignals
class CalObj(gtk.DrawingArea, CalBase):
	_name = "monthCal"
	desc = _("Month Calendar")
	expand = True
	itemListCustomizable = False
	optionsPageSpacing = 5
	cx = [0, 0, 0, 0, 0, 0, 0]
	myKeys = CalBase.myKeys + (
		"up", "down",
		"right", "left",
		"page_up",
		"k", "p",
		"page_down",
		"j", "n",
		"end",
		"f10", "m",
	)

	def updateTypeParamsWidget(self):
		from scal3.ui_gtk.cal_type_params import CalTypeParamWidget
		try:
			vbox = self.typeParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		###
		subPages = [self.cursorPage]
		n = len(calTypes.active)
		while len(ui.mcalTypeParams) < n:
			ui.mcalTypeParams.append({
				"pos": (0, 0),
				"font": ui.getFont(0.6),
				"color": ui.textColor,
			})
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for index, calType in enumerate(calTypes.active):
			module, ok = calTypes[calType]
			if not ok:
				raise RuntimeError(f"cal type '{calType}' not found")
			###
			# try:
			params = ui.mcalTypeParams[index]
			# except IndexError:
			##
			pageWidget = CalTypeParamWidget(
				"mcalTypeParams",
				self,
				params,
				sgroupLabel=sgroupLabel,
				index=index,
				calType=calType,
				hasEnable=(index > 0),
			)
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			page.pageTitle = _(module.desc)
			page.pageLabel = _(module.desc)
			page.pageExpand = False
			subPages.append(page)
			button = newSubPageButton(self, page, borderWidth=7)
			pack(vbox, button, padding=3)
		###
		vbox.show_all()
		self.subPages = subPages

	def drawCursorOutline(self, cr, cx0, cy0, cw, ch):
		cursorRadius = ui.mcalCursorRoundingFactor * min(cw, ch) * 0.5
		cursorLineWidth = ui.mcalCursorLineWidthFactor * min(cw, ch) * 0.5
		drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius, cursorLineWidth)

	def drawCursorBg(self, cr, cx0, cy0, cw, ch):
		cursorRadius = ui.mcalCursorRoundingFactor * min(cw, ch) * 0.5
		drawRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius)

	def __init__(self, win):
		self.win = win
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		######################
		# self.kTime = 0
		######################
		self.connect("draw", self.drawAll)
		self.connect("button-press-event", self.onButtonPress)
		# self.connect("screen-changed", self.screenChanged)
		self.connect("scroll-event", self.scroll)
		######################
		# self.updateTextWidth()

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		from scal3.ui_gtk.pref_utils import (
			SpinPrefItem,
			CheckPrefItem,
			ColorPrefItem,
			CheckColorPrefItem,
		)
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox(spacing=self.optionsPageSpacing)
		#######
		labelSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		prefItem = SpinPrefItem(
			ui,
			"mcalLeftMargin",
			0, 999,
			digits=1, step=1,
			label=_("Left Margin"),
			labelSizeGroup=labelSizeGroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = SpinPrefItem(
			ui,
			"mcalTopMargin",
			0, 999,
			digits=1, step=1,
			label=_("Top Margin"),
			labelSizeGroup=labelSizeGroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		########
		prefItem = CheckColorPrefItem(
			CheckPrefItem(ui, "mcalGrid", _("Grid")),
			ColorPrefItem(ui, "mcalGridColor", True),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		hbox = prefItem.getWidget()
		pack(optionsWidget, hbox)
		############
		pageVBox = VBox(spacing=20)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		prefItem = SpinPrefItem(
			ui,
			"mcalCursorLineWidthFactor",
			0, 1,
			digits=2, step=0.1,
			label=_("Line Width Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(pageVBox, prefItem.getWidget())
		###
		prefItem = SpinPrefItem(
			ui,
			"mcalCursorRoundingFactor",
			0, 1,
			digits=2, step=0.1,
			label=_("Rounding Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(pageVBox, prefItem.getWidget())
		###
		pageVBox.show_all()
		###
		page = StackPage()
		page.pageWidget = pageVBox
		page.pageName = "cursor"
		page.pageTitle = _("Cursor")
		page.pageLabel = _("Cursor")
		page.pageIcon = ""
		self.cursorPage = page
		###
		button = newSubPageButton(self, page, borderWidth=7)
		pack(optionsWidget, button, padding=5)
		########
		self.optionsWidget = optionsWidget
		####
		self.typeParamsVbox = VBox()
		pack(optionsWidget, self.typeParamsVbox, padding=5)
		optionsWidget.show_all()
		self.updateTypeParamsWidget()  # FIXME
		return optionsWidget

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		return self.subPages

	def drawAll(self, widget=None, cursor=True):
		win = self.get_window()
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr, cursor)
		finally:
			win.end_draw_frame(dctx)

	def drawWithContext(self, cr: "cairo.Context", cursor: bool):
		# gevent = gtk.get_current_event()
		# FIXME: must enhance (only draw few cells, not all cells)
		self.calcCoord()
		w = self.get_allocation().width
		h = self.get_allocation().height
		wx = ui.winX
		wy = ui.winY
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		status = getCurrentMonthStatus()
		# ################################## Drawing Border
		if ui.mcalTopMargin > 0:
			# ### Drawing border top background
			# mcalMenuCellBgColor == borderColor
			cr.rectangle(0, 0, w, ui.mcalTopMargin)
			fillColor(cr, ui.borderColor)
			# ###### Drawing weekDays names
			setColor(cr, ui.borderTextColor)
			dx = 0
			wdayAb = (self.wdaysWidth > w)
			for i in range(7):
				wday = newTextLayout(self, core.getWeekDayAuto(i, abbreviate=wdayAb))
				try:
					fontw, fonth = wday.get_pixel_size()
				except Exception:
					log.exception("")
					fontw, fonth = wday.get_pixel_size()
				cr.move_to(
					self.cx[i] - fontw / 2,
					(ui.mcalTopMargin - fonth) / 2 - 1,
				)
				show_layout(cr, wday)
			# ###### Drawing "Menu" label
			setColor(cr, ui.menuTextColor)
			text = newTextLayout(self, _("Menu"))
			fontw, fonth = text.get_pixel_size()
			if rtl:
				cr.move_to(
					w - (ui.mcalLeftMargin + fontw) / 2 - 3,
					(ui.mcalTopMargin - fonth) / 2 - 1,
				)
			else:
				cr.move_to(
					(ui.mcalLeftMargin - fontw) / 2,
					(ui.mcalTopMargin - fonth) / 2 - 1,
				)
			show_layout(cr, text)
		if ui.mcalLeftMargin > 0:
			# ### Drawing border left background
			if rtl:
				cr.rectangle(
					w - ui.mcalLeftMargin,
					ui.mcalTopMargin,
					ui.mcalLeftMargin,
					h - ui.mcalTopMargin,
				)
			else:
				cr.rectangle(
					0,
					ui.mcalTopMargin,
					ui.mcalLeftMargin,
					h - ui.mcalTopMargin,
				)
			fillColor(cr, ui.borderColor)
			# ### Drawing week numbers
			setColor(cr, ui.borderTextColor)
			for i in range(6):
				lay = newTextLayout(self, _(status.weekNum[i]))
				fontw, fonth = lay.get_pixel_size()
				if rtl:
					cr.move_to(
						w - (ui.mcalLeftMargin + fontw) / 2,
						self.cy[i] - fonth / 2 + 2,
					)
				else:
					cr.move_to(
						(ui.mcalLeftMargin - fontw) / 2,
						self.cy[i] - fonth / 2 + 2,
					)
				show_layout(cr, lay)
		selectedCellPos = ui.cell.monthPos
		if ui.todayCell.inSameMonth(ui.cell):
			tx, ty = ui.todayCell.monthPos  # today x and y
			x0 = self.cx[tx] - self.dx / 2
			y0 = self.cy[ty] - self.dy / 2
			cr.rectangle(x0, y0, self.dx, self.dy)
			fillColor(cr, ui.todayCellColor)
		iconSizeMax = ui.mcalEventIconSizeMax
		for yPos in range(6):
			for xPos in range(7):
				c = status[yPos][xPos]
				x0 = self.cx[xPos]
				y0 = self.cy[yPos]
				cellInactive = (c.month != ui.cell.month)
				cellHasCursor = (cursor and (xPos, yPos) == selectedCellPos)
				if cellHasCursor:
					# ### Drawing Cursor
					cx0 = x0 - self.dx / 2 + 1
					cy0 = y0 - self.dy / 2 + 1
					cw = self.dx - 1
					ch = self.dy - 1
					# ####### Circular Rounded
					self.drawCursorBg(cr, cx0, cy0, cw, ch)
					fillColor(cr, ui.cursorBgColor)
				# ###### end of Drawing Cursor
				if not cellInactive:
					iconList = c.getMonthEventIcons()
					if iconList:
						iconsN = len(iconList)
						scaleFact = 1 / sqrt(iconsN)
						fromRight = 0
						for index, icon in enumerate(iconList):
							# if len(iconList) > 1  # FIXME
							try:
								pix = pixbufFromFile(icon, size=iconSizeMax)
							except Exception:
								log.exception("")
								continue
							pix_w = pix.get_width()
							pix_h = pix.get_height()
							# right buttom corner ???
							# right side:
							x1 = (
								x0 + self.dx / 2
							) / scaleFact - fromRight - pix_w
							# buttom side:
							y1 = (y0 + self.dy / 2) / scaleFact - pix_h
							cr.scale(scaleFact, scaleFact)
							gdk.cairo_set_source_pixbuf(cr, pix, x1, y1)
							cr.rectangle(x1, y1, pix_w, pix_h)
							cr.fill()
							cr.scale(1 / scaleFact, 1 / scaleFact)
							fromRight += pix_w
				# ## Drawing numbers inside every cell
				# cr.rectangle(
				# 	x0 - self.dx / 2 + 1,
				# 	y0 - self.dy / 2 + 1,
				# 	self.dx - 1,
				# 	self.dy - 1,
				# )
				calType = calTypes.primary
				params = ui.mcalTypeParams[0]
				daynum = newTextLayout(
					self,
					_(c.dates[calType][2], calType),
					ui.getParamsFont(params),
				)
				fontw, fonth = daynum.get_pixel_size()
				if cellInactive:
					setColor(cr, ui.inactiveColor)
				elif c.holiday:
					setColor(cr, ui.holidayColor)
				else:
					setColor(cr, params["color"])
				cr.move_to(
					x0 - fontw / 2 + params["pos"][0],
					y0 - fonth / 2 + params["pos"][1],
				)
				show_layout(cr, daynum)
				if not cellInactive:
					for calType, params in ui.getActiveMonthCalParams()[1:]:
						if not params.get("enable", True):
							continue
						daynum = newTextLayout(
							self,
							_(c.dates[calType][2], calType),
							ui.getParamsFont(params),
						)
						fontw, fonth = daynum.get_pixel_size()
						setColor(cr, params["color"])
						cr.move_to(
							x0 - fontw / 2 + params["pos"][0],
							y0 - fonth / 2 + params["pos"][1],
						)
						show_layout(cr, daynum)
					if cellHasCursor:
						# ### Drawing Cursor Outline
						cx0 = x0 - self.dx / 2 + 1
						cy0 = y0 - self.dy / 2 + 1
						cw = self.dx - 1
						ch = self.dy - 1
						# ####### Circular Rounded
						self.drawCursorOutline(cr, cx0, cy0, cw, ch)
						fillColor(cr, ui.cursorOutColor)
						# ### end of Drawing Cursor Outline
		# ############## end of drawing cells
		# ### drawGrid
		if ui.mcalGrid:
			setColor(cr, ui.mcalGridColor)
			for i in range(7):
				cr.rectangle(
					self.cx[i] + rtlSgn() * self.dx / 2,
					0,
					1,
					h,
				)
				cr.fill()
			for i in range(6):
				cr.rectangle(
					0,
					self.cy[i] - self.dy / 2,
					w,
					1,
				)
				cr.fill()
		return False

	def updateTextWidth(self):
		# update width of week days names to be able to find out
		# whether or not they should be shortened for the UI
		lay = newTextLayout(self)
		wm = 0  # max width
		for i in range(7):
			wday = core.weekDayName[i]
			lay.set_markup(text=wday, length=-1)
			w = lay.get_pixel_size()[0]  # FIXME
			# w = lay.get_pixel_extents()[0]  # FIXME
			# log.debug(w,)
			if w > wm:
				wm = w
		self.wdaysWidth = wm * 7 + ui.mcalLeftMargin
		# self.wdaysWidth = wm * 7 * 0.7 + ui.mcalLeftMargin
		# log.debug("max =", wm, "     wdaysWidth =", self.wdaysWidth)

	def onButtonPress(self, obj, gevent):
		# self.winActivate() #?????????
		b = gevent.button
		x, y, = self.get_pointer()
		# foo, x, y, flags = self.get_window().get_pointer()
		self.pointer = (x, y)
		if b == 2:
			return False
		xPos = -1
		yPos = -1
		for i in range(7):
			if abs(x - self.cx[i]) <= self.dx / 2:
				xPos = i
				break
		for i in range(6):
			if abs(y - self.cy[i]) <= self.dy / 2:
				yPos = i
				break
		status = getCurrentMonthStatus()
		if yPos == -1 or xPos == -1:
			self.emit("popup-main-menu", gevent.time, gevent.x, gevent.y)
		elif yPos >= 0 and xPos >= 0:
			cell = status[yPos][xPos]
			self.changeDate(*cell.dates[calTypes.primary])
			if gevent.type == TWO_BUTTON_PRESS:
				self.emit("double-button-press")
			if b == 3 and cell.month == ui.cell.month:  # right click on a normal cell
				# self.emit("popup-cell-menu", gevent.time, *self.getCellPos())
				self.emit("popup-cell-menu", gevent.time, gevent.x, gevent.y)
		return True

	def calcCoord(self):  # calculates coordidates (x and y of cells centers)
		w = self.get_allocation().width
		h = self.get_allocation().height
		# self.cx is centers x, self.cy is centers y
		if rtl:
			self.cx = [
				(w - ui.mcalLeftMargin) * (13 - 2 * i) / 14
				for i in range(7)
			]
		else:
			self.cx = [
				ui.mcalLeftMargin + (
					(w - ui.mcalLeftMargin)
					* (1 + 2 * i)
					/ 14
				)
				for i in range(7)
			]
		self.cy = [
			ui.mcalTopMargin + (h - ui.mcalTopMargin) * (1 + 2 * i) / 12
			for i in range(6)
		]
		self.dx = (w - ui.mcalLeftMargin) / 7  # delta x
		self.dy = (h - ui.mcalTopMargin) / 6  # delta y

	def monthPlus(self, p):
		ui.monthPlus(p)
		self.onDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		# if kname.startswith("alt"):
		# 	return True
		if kname == "up":
			self.jdPlus(-7)
		elif kname == "down":
			self.jdPlus(7)
		elif kname == "right":
			if rtl:
				self.jdPlus(-1)
			else:
				self.jdPlus(1)
		elif kname == "left":
			if rtl:
				self.jdPlus(1)
			else:
				self.jdPlus(-1)
		elif kname == "end":
			self.changeDate(
				ui.cell.year,
				ui.cell.month,
				cal_types.getMonthLen(ui.cell.year, ui.cell.month, calTypes.primary),
			)
		elif kname in ("page_up", "k", "p"):
			self.monthPlus(-1)
		elif kname in ("page_down", "j", "n"):
			self.monthPlus(1)
		elif kname in ("f10", "m"):
			if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.emit("popup-cell-menu", gevent.time, *self.getCellPos())
			else:
				self.emit("popup-main-menu", gevent.time, *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, widget, gevent):
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-7)
		elif d == "down":
			self.jdPlus(7)
		else:
			return False

	def getCellPos(self, *args):
		return (
			int(self.cx[ui.cell.monthPos[0]]),
			int(self.cy[ui.cell.monthPos[1]] + self.dy / 2),
		)

	def getMainMenuPos(self, *args):  # FIXME
		if rtl:
			return (
				int(self.get_allocation().width - ui.mcalLeftMargin / 2),
				int(ui.mcalTopMargin / 2),
			)
		else:
			return (
				int(ui.mcalLeftMargin / 2),
				int(ui.mcalTopMargin / 2),
			)

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		self.updateTextWidth()
		self.updateTypeParamsWidget()


if __name__ == "__main__":
	win = gtk.Dialog()
	cal = CalObj()
	win.add_events(gdk.EventMask.ALL_EVENTS_MASK)
	pack(win.vbox, cal, 1, 1)
	win.vbox.show_all()
	win.resize(600, 400)
	win.set_title(cal.desc)
	win.run()
