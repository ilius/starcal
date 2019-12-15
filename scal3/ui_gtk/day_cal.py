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

from scal3.cal_types import calTypes
from scal3 import core
from scal3.core import log
from scal3.locale_man import rtl, rtlSgn, getMonthName
from scal3.locale_man import tr as _
from scal3 import ui
from scal3.monthcal import getCurrentMonthStatus

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import pixbufFromFile
from scal3.ui_gtk.button_drawing import Button
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.stack import StackPage


class DayCal(gtk.DrawingArea, CalBase):
	_name = "dayCal"
	desc = _("Day Calendar")
	itemListCustomizable = False
	backgroundColorParam = ""
	dayParamsParam = ""
	monthParamsParam = ""
	weekdayParamsParam = ""
	weekdayAbbreviateParam = ""
	weekdayUppercaseParam = ""
	weekdayUppercaseParam = ""
	buttonsEnableParam = ""
	buttonsParam = ""
	eventIconSizeParam = ""
	eventTotalSizeRatioParam = ""

	myKeys = CalBase.myKeys + (
		"up", "down",
		"right", "left",
		"page_up",
		"k", "p",
		"page_down",
		"j", "n",
		#"end",
		"f10", "m",
	)

	def getBackgroundColor(self):
		if self.backgroundColorParam:
			return getattr(ui, self.backgroundColorParam)
		return ui.bgColor

	def getDayParams(self, allCalTypes=False):
		params = getattr(ui, self.dayParamsParam)
		if allCalTypes:
			n = len(calTypes.active)
			while len(params) < n:
				params.append({
					"enable": False,
					"pos": (0, 0),
					"font": ui.getFont(3.0),
					"color": ui.textColor,
				})
		return params

	def getMonthParams(self, allCalTypes=False):
		params = getattr(ui, self.monthParamsParam)
		if allCalTypes:
			n = len(calTypes.active)
			while len(params) < n:
				params.append({
					"enable": False,
					"pos": (0, 0),
					"font": ui.getFont(2.0),
					"color": ui.textColor,
				})
		return params

	def getWeekDayParams(self):
		return getattr(ui, self.weekdayParamsParam)

	def getButtonsEnable(self):
		return getattr(ui, self.buttonsEnableParam)

	def getButtons(self):
		return [
			Button(
				imageName=d.get("imageName", ""),
				onPress=getattr(self, d["onClick"]),
				x=d["pos"][0],
				y=d["pos"][1],
				autoDir=d["autoDir"],
				iconName=d.get("iconName", ""),
				iconSize=d.get("iconSize", 16),
				xalign=d.get("xalign", "left"),
				yalign=d.get("yalign", "top"),
			)
			for d in getattr(ui, self.buttonsParam)
		]

	def startMove(self, gevent):
		win = self.getWindow()
		if not win:
			return
		win.begin_move_drag(
			1,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def startResize(self, gevent):
		win = self.getWindow()
		if not win:
			return
		win.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def openCustomize(self, gevent):
		if ui.mainWin:
			ui.mainWin.customizeShow()

	def updateTypeParamsWidget(self):
		from scal3.ui_gtk.cal_type_params import CalTypeParamWidget
		dayParams = self.getDayParams(allCalTypes=True)
		monthParams = self.getMonthParams(allCalTypes=True)
		try:
			vbox = self.dayMonthParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		###
		subPages = []
		###
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for index, calType in enumerate(calTypes.active):
			module, ok = calTypes[calType]
			if not ok:
				raise RuntimeError(f"cal type '{calType}' not found")
			##
			pageWidget = VBox(spacing=5)
			###
			dayWidget = CalTypeParamWidget(
				self.dayParamsParam,
				self,
				dayParams[index],
				sgroupLabel=sgroupLabel,
				index=index,
				calType=calType,
				hasEnable=True,
				hasAlign=True,
				enableTitleLabel=_("Day of Month"),
				useFrame=True,
			)
			pack(pageWidget, dayWidget)
			###
			monthWidget = CalTypeParamWidget(
				self.monthParamsParam,
				self,
				monthParams[index],
				sgroupLabel=sgroupLabel,
				index=index,
				calType=calType,
				hasEnable=True,
				hasAlign=True,
				hasAbbreviate=True,
				hasUppercase=True,
				enableTitleLabel=_("Month Name"),
				useFrame=True,
			)
			monthWidget.show_all()
			page = StackPage()
			page.pageWidget = monthWidget
			page.pageName = module.name + "." + "month"
			page.pageTitle = _("Month Name") + " - " + _(module.desc)
			page.pageLabel = _("Month Name")
			page.pageExpand = False
			subPages.append(page)
			pack(pageWidget, newSubPageButton(self, page), padding=4)
			###
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			page.pageTitle = _(module.desc)
			page.pageLabel = _(module.desc)
			page.pageExpand = False
			subPages.append(page)
			pack(vbox, newSubPageButton(self, page), padding=4)
		###
		vbox.show_all()
		return subPages

	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self._window = None
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.subPages = None
		######################
		#self.kTime = 0
		######################
		self.connect("draw", self.drawAll)
		self.connect("button-press-event", self.onButtonPress)
		#self.connect("screen-changed", self.screenChanged)
		self.connect("scroll-event", self.scroll)

	def getWindow(self):
		return self._window

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			SpinPrefItem,
			CheckPrefItem,
			ColorPrefItem,
		)
		from scal3.ui_gtk.cal_type_params import TextParamWidget
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox()
		subPages = []
		####
		if self.backgroundColorParam:
			prefItem = ColorPrefItem(
				ui,
				self.backgroundColorParam,
				useAlpha=False,
				live=True,
				onChangeFunc=self.queue_draw,
			)
			hbox = HBox()
			pack(hbox, gtk.Label(label=_("Background") + ": "))
			pack(hbox, prefItem.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(optionsWidget, hbox)
		####
		prefItem = CheckPrefItem(
			ui,
			self.buttonsEnableParam,
			label=_("Show buttons"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		########
		self.dayMonthParamsVbox = VBox()
		pack(optionsWidget, self.dayMonthParamsVbox)
		subPages += self.updateTypeParamsWidget()
		####
		if self.weekdayParamsParam:
			params = self.getWeekDayParams()
			pageWidget = VBox(spacing=5)
			###
			testParamsWidget = TextParamWidget(
				self.weekdayParamsParam,
				self,
				params,
				sgroupLabel=None,
				desc=_("Week Day"),
				hasEnable=True,
				hasAlign=True,
			)
			pack(pageWidget, testParamsWidget)
			###
			if self.weekdayAbbreviateParam:
				prefItem = CheckPrefItem(
					ui,
					self.weekdayAbbreviateParam,
					label=_("Abbreviate"),
					live=True,
					onChangeFunc=self.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			if self.weekdayUppercaseParam:
				prefItem = CheckPrefItem(
					ui,
					self.weekdayUppercaseParam,
					label=_("Uppercase"),
					live=True,
					onChangeFunc=self.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			###
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "dayCal.weekday"
			page.pageTitle = _("Week Day")
			page.pageLabel = _("Week Day")
			page.pageExpand = False
			subPages.append(page)
			button = newSubPageButton(self, page)
			pack(optionsWidget, button, padding=4)
		########
		vbox = VBox(spacing=10)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "dayCal.events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events")
		page.pageExpand = False
		subPages.append(page)
		button = newSubPageButton(self, page)
		pack(optionsWidget, button, padding=4)
		###
		prefItem = SpinPrefItem(
			ui,
			self.eventIconSizeParam,
			5, 999,
			digits=1, step=1,
			label=_("Icon Size"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(vbox, prefItem.getWidget())
		###
		prefItem = SpinPrefItem(
			ui,
			self.eventTotalSizeRatioParam,
			0, 1,
			digits=3, step=0.01,
			label=_("Total Size Ratio"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(vbox, prefItem.getWidget())
		###
		vbox.show_all()
		########
		self.subPages = subPages
		self.optionsWidget = optionsWidget
		###
		self.optionsWidget.show_all()
		return self.optionsWidget

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		return subPages

	def getRenderPos(self, params, x0, y0, w, h, fontw, fonth):
		xalign = params.get("xalign")
		yalign = params.get("yalign")

		if not xalign or xalign == "center":
			x = x0 + w / 2 - fontw / 2 + params["pos"][0]
		elif xalign == "left":
			x = x0 + params["pos"][0]
		elif xalign == "right":
			x = x0 + w - fontw - params["pos"][0]
		else:
			x = x0 + w / 2 - fontw / 2 + params["pos"][0]
			log.error(f"invalid xalign = {xalign}")

		if not yalign or yalign == "center":
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
		elif yalign == "top":
			y = y0 + params["pos"][1]
		elif yalign == "buttom":
			y = y0 + h - fonth - params["pos"][1]
		else:
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
			log.error(f"invalid yalign = {yalign}")

		return (x, y)

	def getCell(self) -> ui.Cell:
		return ui.cell

	def drawAll(self, widget=None, cr=None, cursor=True):
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

	def drawEventIcons(
		self, cr: "cairo.Context",
		c: ui.Cell,
		w: int, h: int,
		x0: int, y0: int,
	):
		from math import ceil
		iconList = c.getDayEventIcons()
		if not iconList:
			return
		iconsN = len(iconList)

		maxTotalSize = getattr(ui, self.eventTotalSizeRatioParam) * min(w, h)
		sideCount = int(ceil(sqrt(iconsN)))
		iconSize = min(
			getattr(ui, self.eventIconSizeParam),
			maxTotalSize / sideCount,
		)
		totalSize = sideCount * iconSize
		x1 = x0 + w - iconSize / 2
		y1 = y0 + h / 2 - totalSize / 2 + iconSize / 2
		# icons are show in right-middle side of window
		for index, icon in enumerate(iconList):
			try:
				pix = pixbufFromFile(icon, size=iconSize)
			except GLibError:
				log.exception("")
				continue
			sqX, sqY = divmod(index, sideCount)
			pix_w, pix_h = pix.get_width(), pix.get_height()
			x2 = x1 - sqX * iconSize - pix_w / 2
			y2 = y1 + sqY * iconSize - pix_h / 2
			gdk.cairo_set_source_pixbuf(cr, pix, x2, y2)
			cr.rectangle(x2, y2, iconSize, iconSize)
			cr.fill()

	def drawWithContext(self, cr: "cairo.Context", cursor: bool):
		#gevent = gtk.get_current_event()
		w = self.get_allocation().width
		h = self.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, self.getBackgroundColor())
		#####
		c = self.getCell()
		x0 = 0
		y0 = 0
		########
		self.drawEventIcons(cr, c, w, h, x0, y0)
		# ### Drawing numbers inside every cell
		#cr.rectangle(
		#	x0-w/2.0+1,
		#	y0-h/2.0+1,
		#	w-1,
		#	h-1,
		#)
		####
		for calType, params in zip(
			calTypes.active,
			self.getDayParams(),
		):
			if not params.get("enable", True):
				continue
			layout = newTextLayout(
				self,
				_(c.dates[calType][2], calType),
				ui.getParamsFont(params),
			)
			fontw, fonth = layout.get_pixel_size()
			if calType == calTypes.primary and c.holiday:
				setColor(cr, ui.holidayColor)
			else:
				setColor(cr, params["color"])
			font_x, font_y = self.getRenderPos(params, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		for calType, params in zip(
			calTypes.active,
			self.getMonthParams(),
		):
			if not params.get("enable", True):
				continue
			month = c.dates[calType][1]  # type: int
			abbreviate = params.get("abbreviate", False)
			uppercase = params.get("uppercase", False)
			text = getMonthName(calType, month, abbreviate=abbreviate)
			if uppercase:
				text = text.upper()
			layout = newTextLayout(
				self,
				text,
				ui.getParamsFont(params),
			)
			fontw, fonth = layout.get_pixel_size()
			setColor(cr, params["color"])
			font_x, font_y = self.getRenderPos(params, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		if self.weekdayParamsParam:
			params = self.getWeekDayParams()
			if params.get("enable", True):
				abbreviate = False
				if self.weekdayAbbreviateParam:
					abbreviate = getattr(ui, self.weekdayAbbreviateParam)
				text = core.getWeekDayAuto(c.weekDay, abbreviate=abbreviate, relative=False)
				if self.weekdayUppercaseParam:
					if getattr(ui, self.weekdayUppercaseParam):
						text = text.upper()
				daynum = newTextLayout(
					self,
					text,
					ui.getParamsFont(params),
				)
				fontw, fonth = daynum.get_pixel_size()
				setColor(cr, params["color"])
				font_x, font_y = self.getRenderPos(params, x0, y0, w, h, fontw, fonth)
				cr.move_to(font_x, font_y)
				show_layout(cr, daynum)

		if self.getButtonsEnable():
			for button in self.getButtons():
				button.draw(cr, w, h)

	def onButtonPress(self, obj, gevent):
		b = gevent.button
		x, y = gevent.x, gevent.y
		###
		if gevent.type == TWO_BUTTON_PRESS:
			self.emit("double-button-press")
		if b == 1 and self.getButtonsEnable():
			w = self.get_allocation().width
			h = self.get_allocation().height
			for button in self.getButtons():
				if button.contains(x, y, w, h):
					button.onPress(gevent)
					return True
		if b == 3:
			self.emit("popup-cell-menu", gevent.time, x, y)
		return True

	def jdPlus(self, p):
		ui.jdPlus(p)
		self.onDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		#if kname.startswith("alt"):
		#	return True
		if kname == "up":
			self.jdPlus(-1)
		elif kname == "down":
			self.jdPlus(1)
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
		elif kname in ("page_up", "k", "p"):
			self.jdPlus(-1)  # FIXME
		elif kname in ("page_down", "j", "n"):
			self.jdPlus(1)  # FIXME
		#elif kname in ("f10", "m"):  # FIXME
		#	if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
		#		# Simulate right click (key beside Right-Ctrl)
		#		self.emit("popup-cell-menu", gevent.time, *self.getCellPos())
		#	else:
		#		self.emit("popup-main-menu", gevent.time, *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, widget, gevent):
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-1)
		elif d == "down":
			self.jdPlus(1)
		else:
			return False

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		self.updateTypeParamsWidget() # why is this needed? FIXME
