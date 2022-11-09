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
from math import isqrt

from scal3.cal_types import calTypes
from scal3 import core
from scal3.core import log
from scal3.locale_man import (
	rtl,
	rtlSgn,
	langHasUppercase,
	getMonthName,
	langSh,
	textNumEncode,
)
from scal3.locale_man import tr as _
from scal3 import ui
from scal3.drawing import getAbsPos
from scal3.monthcal import getCurrentMonthStatus
from scal3.season import getSeasonNamePercentFromJd

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import pixbufFromFile
from scal3.ui_gtk.button_drawing import Button, SVGButton
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
	weekdayLocalizeParam = ""
	weekdayAbbreviateParam = ""
	weekdayUppercaseParam = ""

	widgetButtonsEnableParam = ""
	widgetButtonsParam = ""

	navButtonsEnableParam = ""
	navButtonsGeoParam = ""
	navButtonsOpacityParam = ""

	eventIconSizeParam = ""
	eventTotalSizeRatioParam = ""

	seasonPieEnableParam = ""
	seasonPieGeoParam = ""
	seasonPieColorsParam = None  # Optional[Dict]
	seasonPieTextColorParam = ""

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

	def getWidgetButtons(self):
		if not self.widgetButtonsEnableParam:
			return []
		if not getattr(ui, self.widgetButtonsEnableParam):
			return []
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
			for d in getattr(ui, self.widgetButtonsParam)
		]

	navButtonsRaw = [
		{
			# "imageName": "go-previous.svg",
			"imageName": "list-remove.svg",
			"onClick": "prevDayClicked",
		},
		{
			"imageName": "go-home.svg",
			"onClick": "goToday",
		},
		{
			# "imageName": "go-next.svg",
			"imageName": "list-add.svg",
			"onClick": "nextDayClicked",
		},
	]
	navButtonsRTLRaw = [
		{
			# "imageName": "go-previous.svg",
			"imageName": "list-add.svg",
			"onClick": "nextDayClicked",
		},
		{
			"imageName": "go-home.svg",
			"onClick": "goToday",
		},
		{
			# "imageName": "go-next.svg",
			"imageName": "list-remove.svg",
			"onClick": "prevDayClicked",
		},
	]

	def getNavButtons(self):
		if not self.navButtonsEnableParam:
			return []

		if not getattr(ui, self.navButtonsEnableParam):
			return []

		if not self.navButtonsGeoParam:
			return []

		buttonsRaw = self.navButtonsRaw
		geo = getattr(ui, self.navButtonsGeoParam)
		if rtl and geo["auto_rtl"]:
			buttonsRaw = self.navButtonsRTLRaw

		opacity = getattr(ui, self.navButtonsOpacityParam)
		iconSize = geo["size"]
		spacing = geo["spacing"]
		xc, y = geo["pos"]
		xalign = geo["xalign"]
		yalign = geo["yalign"]

		count = len(buttonsRaw)
		totalWidth = iconSize * count + spacing * (count - 1)
		x_start = xc - totalWidth / 2
		x_delta = iconSize + spacing

		rectangleColor = list(ui.textColor[:3]) + [opacity * 0.7]

		return [
			SVGButton(
				imageName=d.get("imageName", ""),
				onPress=getattr(self, d["onClick"]),
				x=x_start + index * x_delta,
				y=y,
				autoDir=False,
				iconSize=iconSize,
				xalign=xalign,
				yalign=yalign,
				opacity=opacity,
				rectangleColor=rectangleColor,
			)
			for index, d in enumerate(buttonsRaw)
		]

	def getAllButtons(self):
		return self.getWidgetButtons() + self.getNavButtons()

	def startMove(self, gevent, button=1):
		win = self.getWindow()
		if not win:
			return
		win.begin_move_drag(
			button,
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
		if self.win:
			self.win.customizeShow()

	def prevDayClicked(self, gevent):
		self.jdPlus(-1)

	def nextDayClicked(self, gevent):
		self.jdPlus(1)

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
			calTypeDesc = _(module.desc, ctx="calendar")
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
				hasUppercase=langHasUppercase,
				enableTitleLabel=_("Month Name"),
				useFrame=True,
			)
			monthWidget.show_all()
			page = StackPage()
			page.pageWidget = monthWidget
			page.pageName = module.name + "." + "month"
			page.pageTitle = _("Month Name") + " - " + calTypeDesc
			page.pageLabel = _("Month Name")
			page.pageExpand = False
			subPages.append(page)
			pack(pageWidget, newSubPageButton(self, page), padding=4)
			###
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			page.pageTitle = calTypeDesc
			page.pageLabel = calTypeDesc
			page.pageExpand = False
			subPages.append(page)
			self.buttons1.append(newSubPageButton(self, page))
			###
			c = self.getCell()
			dayWidget.setFontPreviewText(
				_(c.dates[calType][2], calTypes.primary),
			)
			monthWidget.setFontPreviewText(
				self.getMonthName(c, calType, monthParams[index]),
			)
		###
		vbox.show_all()
		return subPages

	def __init__(self, win):
		gtk.DrawingArea.__init__(self)
		self.win = win
		self._window = None
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.subPages = None
		self._allButtons = []
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
		###
		buttons1 = self.buttons1 = []
		buttons2 = []
		####
		if self.backgroundColorParam:
			prefItem = ColorPrefItem(
				ui,
				self.backgroundColorParam,
				live=True,
				onChangeFunc=self.queue_draw,
			)
			hbox = HBox()
			pack(hbox, gtk.Label(label=_("Background") + ": "))
			pack(hbox, prefItem.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(optionsWidget, hbox)
		########
		self.dayMonthParamsVbox = VBox()
		pack(optionsWidget, self.dayMonthParamsVbox)
		subPages += self.updateTypeParamsWidget()
		####
		pageWidget = VBox(spacing=5)
		page = StackPage()
		page.pageWidget = pageWidget
		page.pageName = "buttons"
		page.pageTitle = _("Buttons")
		page.pageLabel = _("Buttons")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(self, page))
		###
		if self.widgetButtonsEnableParam:
			prefItem = CheckPrefItem(
				ui,
				self.widgetButtonsEnableParam,
				label=_("Widget buttons"),
				live=True,
				onChangeFunc=self.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		if self.navButtonsEnableParam:
			prefItem = CheckPrefItem(
				ui,
				self.navButtonsEnableParam,
				label=_("Navigation buttons"),
				live=True,
				onChangeFunc=self.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		pageWidget.show_all()
		#####
		if self.weekdayParamsParam:
			params = self.getWeekDayParams()
			pageWidget = VBox(spacing=5)
			###
			weekdayWidget = TextParamWidget(
				self.weekdayParamsParam,
				self,
				params,
				# sgroupLabel=None,
				desc=_("Week Day"),
				hasEnable=True,
				hasAlign=True,
			)
			pack(pageWidget, weekdayWidget)
			###
			if self.weekdayLocalizeParam and langSh != "en":
				prefItem = CheckPrefItem(
					ui,
					self.weekdayLocalizeParam,
					label=_("Localize"),
					live=True,
					onChangeFunc=self.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			if self.weekdayAbbreviateParam:
				prefItem = CheckPrefItem(
					ui,
					self.weekdayAbbreviateParam,
					label=_("Abbreviate"),
					live=True,
					onChangeFunc=self.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			if langHasUppercase and self.weekdayUppercaseParam:
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
			page.pageName = "weekday"
			page.pageTitle = _("Week Day")
			page.pageLabel = _("Week Day")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(self, page))
			###
			c = self.getCell()
			text = core.getWeekDayAuto(
				c.weekDay,
				localize=self.getWeekdayLocalize(),
				abbreviate=self.getWeekdayAbbreviate(),
				relative=False,
			)
			weekdayWidget.setFontPreviewText(text)
		########
		vbox = VBox(spacing=10)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(self, page))
		###
		prefItem = SpinPrefItem(
			ui,
			self.eventIconSizeParam,
			5, 999,
			digits=1, step=1,  # noqa: FURB120
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
		####
		if self.seasonPieEnableParam:
			pageWidget = VBox(spacing=5)
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "seasonPie"
			page.pageTitle = _("Season Pie")
			page.pageLabel = _("Season Pie")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(self, page))
			###
			prefItem = CheckPrefItem(
				ui,
				self.seasonPieEnableParam,
				label=_("Season Pie"),
				live=True,
				onChangeFunc=self.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
			###
			frame = gtk.Frame()
			frame.set_border_width(5)
			frame.set_label(_("Colors"))
			grid = gtk.Grid()
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			grid.set_row_spacing(3)
			grid.set_border_width(5)
			frame.add(grid)
			pack(pageWidget, frame)
			for index, season in enumerate(("Spring", "Summer", "Autumn", "Winter")):
				hbox = HBox(spacing=10)
				label = gtk.Label(label=_(season))
				label.set_xalign(0)
				prefItem = ColorPrefItem(
					ui,
					self.seasonPieColorsParam[season],
					useAlpha=True,
					live=True,
					onChangeFunc=self.queue_draw,
				)
				row_index = index / 2
				column_index = index % 2 * 3
				grid.attach(
					label,
					column_index,
					row_index,
					1, 1,
				)
				grid.attach(
					prefItem.getWidget(),
					column_index + 1,
					row_index,
					1, 1,
				)
				dummyLabel = gtk.Label()
				dummyLabel.set_hexpand(True)
				grid.attach(
					dummyLabel,
					column_index + 2,
					row_index,
					1, 1,
				)
			pageWidget.show_all()
		####
		for buttons in (buttons1, buttons2):
			grid = gtk.Grid()
			grid.set_row_homogeneous(True)
			grid.set_column_homogeneous(True)
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			for index, button in enumerate(buttons):
				grid.attach(
					button,
					index % 2,
					index // 2,
					1, 1,
				)
			grid.show_all()
			pack(optionsWidget, grid, padding=5)
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
			log.error(f"invalid {xalign=}")

		if not yalign or yalign == "center":
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
		elif yalign == "top":
			y = y0 + params["pos"][1]
		elif yalign == "buttom":
			y = y0 + h - fonth - params["pos"][1]
		else:
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
			log.error(f"invalid {yalign=}")

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
		iconList = c.getDayEventIcons()
		if not iconList:
			return
		iconsN = len(iconList)

		maxTotalSize = getattr(ui, self.eventTotalSizeRatioParam) * min(w, h)
		sideCount = isqrt(iconsN - 1) + 1
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
			if pix is None:
				continue
			sqX, sqY = divmod(index, sideCount)
			pix_w, pix_h = pix.get_width(), pix.get_height()
			x2 = x1 - sqX * iconSize - pix_w / 2
			y2 = y1 + sqY * iconSize - pix_h / 2
			gdk.cairo_set_source_pixbuf(cr, pix, x2, y2)
			cr.rectangle(x2, y2, iconSize, iconSize)
			cr.fill()

	def getMonthName(self, c: "ui.Cell", calType: int, params: "Dict[str, Any]"):
		month = c.dates[calType][1]  # type: int
		abbreviate = params.get("abbreviate", False)
		uppercase = params.get("uppercase", False)
		text = getMonthName(calType, month, abbreviate=abbreviate)
		if uppercase:
			text = text.upper()
		return text

	def iterMonthParams(self):
		for calType, params in zip(
			calTypes.active,
			self.getMonthParams(),
		):
			if not params.get("enable", True):
				continue
			yield calType, params

	def getWeekdayLocalize(self) -> bool:
		if self.weekdayLocalizeParam:
			return getattr(ui, self.weekdayLocalizeParam)
		return True

	def getWeekdayAbbreviate(self) -> bool:
		if self.weekdayAbbreviateParam:
			return getattr(ui, self.weekdayAbbreviateParam)
		return False

	def drawSeasonPie(self, cr, w, h):
		if not self.seasonPieEnableParam:
			return

		if not getattr(ui, self.seasonPieEnableParam):
			return

		assert self.seasonPieGeoParam
		assert self.seasonPieColorsParam

		seasonName, seasonFrac = getSeasonNamePercentFromJd(
			self.getCell().jd,
			ui.seasonPBar_southernHemisphere,
		)

		geo = getattr(ui, self.seasonPieGeoParam)
		color = getattr(ui, self.seasonPieColorsParam[seasonName])
		textColor = getattr(ui, self.seasonPieTextColorParam)
		if not textColor:
			textColor = ui.textColor

		size = geo["size"]
		radius = size / 2
		x, y = geo["pos"]
		x, y = getAbsPos(
			size, size,
			w, h,
			x, y,
			geo["xalign"], geo["yalign"],
			autoDir=False,  # noqa: FURB120
		)

		xc = x + radius
		yc = y + radius

		startOffset = geo["startAngle"] / 360

		drawPieOutline(
			cr, xc, yc,
			radius,
			geo["thickness"] * radius,
			startOffset,
			startOffset + seasonFrac,
		)
		fillColor(cr, color)

		textSize = size * (1 - geo["thickness"])
		layout = newTextLayout(
			self,
			textNumEncode(
				f"%{int(seasonFrac * 100)}",
				# changeSpecialChars=True,
			),
			maxSize=(textSize, textSize),
		)
		font_w, font_h = layout.get_pixel_size()
		setColor(cr, textColor)
		cr.move_to(xc - font_w / 2, yc - font_h / 2)
		show_layout(cr, layout)

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

		for calType, params in self.iterMonthParams():
			text = self.getMonthName(c, calType, params)
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
				text = core.getWeekDayAuto(
					c.weekDay,
					localize=self.getWeekdayLocalize(),
					abbreviate=self.getWeekdayAbbreviate(),
					relative=False,
				)
				if langHasUppercase and self.weekdayUppercaseParam:
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

		self.drawSeasonPie(cr, w, h)


		self._allButtons = self.getAllButtons()
		for button in self._allButtons:
			button.draw(cr, w, h)

	def onButtonPress(self, obj, gevent):
		b = gevent.button
		x, y = gevent.x, gevent.y

		double = gevent.type == TWO_BUTTON_PRESS

		if b == 1:
			buttons = self._allButtons
			if buttons:
				w = self.get_allocation().width
				h = self.get_allocation().height
				for button in buttons:
					if button.contains(x, y, w, h):
						if not double:
							button.onPress(gevent)
						return True

		if b == 3:
			self.emit("popup-cell-menu", x, y)

		if double:
			self.emit("double-button-press")

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
		#		self.emit("popup-cell-menu", *self.getCellPos())
		#	else:
		#		self.emit("popup-main-menu", *self.getMainMenuPos())
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

	def getCellPos(self, *args):
		alloc = self.get_allocation()
		return (
			int(alloc.width / 2),
			int(alloc.height / 2),
		)

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		# TODO: if active cal types are changed, we should re-order buttons
		# hide extra buttons, and possibly add new buttons with their pages
		# in Customize window
