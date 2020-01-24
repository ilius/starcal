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

import time
from time import time as now

import sys
import os

from typing import Tuple, List, Callable, Optional

from scal3.path import pixDir, svgDir
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, rtlSgn

from scal3.cal_types import calTypes

from scal3 import core
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.mywidgets import MyFontButton

from scal3.ui_gtk import gtk_ud as ud

from scal3.ui_gtk.utils import pixbufFromFile
from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.customize import (
	CustomizableCalObj,
	CustomizableCalBox,
	newSubPageButton,
)

#from scal3.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar
from scal3.ui_gtk.toolbox import (
	ToolBoxItem as ToolbarItem,
	CustomizableToolBox as CustomizableToolbar,
	LabelToolBoxItem,
)



def show_event(widget, gevent):
	log.info(f"{type(widget)}, {gevent.type.value_name}")
	#, gevent.get_value()#, gevent.send_event


class ColumnBase(CustomizableCalObj):
	customizeWidth = False
	customizeExpand = False
	customizeFont = False
	customizePastTextColor = False
	autoButtonPressHandler = True
	##

	def __init__(self):
		pass

	def getWidthAttr(self):
		return f"wcal_{self._name}_width"

	def getWidthValue(self):
		return getattr(ui, self.getWidthAttr(), None)

	def getExpandAttr(self):
		return f"wcal_{self._name}_expand"

	def getExpandValue(self):
		return getattr(ui, self.getExpandAttr(), None)

	def getFontAttr(self):
		return f"wcalFont_{self._name}"

	def getFontValue(self):
		return getattr(ui, self.getFontAttr(), None)

	def getPastTextColorAttr(self):
		return f"wcalPastTextColor_{self._name}"

	def getPastTextColorValue(self):
		return getattr(ui, self.getPastTextColorAttr(), None)

	def getPastTextColorEnableAttr(self):
		return f"wcalPastTextColorEnable_{self._name}"

	def getPastTextColorEnableValue(self):
		return getattr(ui, self.getPastTextColorEnableAttr(), None)

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)

	def onWidthChange(self):
		# if self._name:
		#	self.updatePacking()
		self.queue_resize()

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			SpinPrefItem,
			CheckPrefItem,
			ColorPrefItem,
			CheckColorPrefItem,
			FontFamilyPrefItem,
		)
		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = VBox(spacing=self.optionsPageSpacing)
		####
		if self.customizeWidth:
			prefItem = SpinPrefItem(
				ui,
				self.getWidthAttr(),
				1, 999,
				digits=1, step=1,
				label=_("Width"),
				live=True,
				onChangeFunc=self.onWidthChange,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		if self.customizeExpand:
			prefItem = CheckPrefItem(
				ui,
				self.getExpandAttr(),
				_("Expand"),
				live=True,
				onChangeFunc=self.onExpandCheckClick,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		if self.customizeFont:
			prefItem = FontFamilyPrefItem(
				ui,
				self.getFontAttr(),
				hasAuto=True,
				label=_("Font Family"),
				onChangeFunc=self.onDateChange,
			)
			prefItem.updateWidget()  # done inside Live*PrefItem classes
			pack(optionsWidget, prefItem.getWidget())
		####
		if self.customizePastTextColor:
			prefItem = CheckColorPrefItem(
				CheckPrefItem(
					ui,
					self.getPastTextColorEnableAttr(),
					_("Past Event Color"),
				),
				ColorPrefItem(
					ui,
					self.getPastTextColorAttr(),
					useAlpha=True,
				),
				live=True,
				onChangeFunc=self.onDateChange,
			)
			pack(optionsWidget, prefItem.getWidget())
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updatePacking(self):
		self._parent.set_child_packing(
			self,
			self.expand,
			self.expand,
			0,
			gtk.PackType.START,
		)

	def onExpandCheckClick(self):
		self.expand = self.getExpandValue()
		self.updatePacking()
		self.queue_draw()


class Column(gtk.DrawingArea, ColumnBase):
	colorizeHolidayText = False
	showCursor = False
	truncateText = False

	def __init__(self, wcal):
		gtk.DrawingArea.__init__(self)
		ColumnBase.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		#self.connect("button-press-event", self.onButtonPress)
		#self.connect("event", show_event)
		self.wcal = wcal
		self._parent = wcal
		if self.customizeExpand:
			self.expand = self.getExpandValue()

	def do_get_preferred_width(self):
		# must return minimum_size, natural_size
		width = self.getWidthValue()
		if width is None:
			return 0, 0
		return width, width

	def onExposeEvent(self, widget=None, event=None):
		if ui.disableRedraw:
			return
		if self.wcal.status is None:
			self.wcal.updateStatus()
		win = self.get_window()
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawColumn(cr)
		except Exception:
			log.exception("error in drawColumn:")
		finally:
			win.end_draw_frame(dctx)

	def drawBg(self, cr: "cairo.Context"):
		alloc = self.get_allocation()
		w = alloc.width
		h = alloc.height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		rowH = h / 7
		for i in range(7):
			c = self.wcal.status[i]
			if c.jd == ui.todayCell.jd:
				cr.rectangle(
					0,
					i * rowH,
					w,
					rowH,
				)
				fillColor(cr, ui.todayCellColor)
			if self.showCursor and c.jd == ui.cell.jd:
				self.drawCursorBg(
					cr,
					0, # x0
					i * rowH, # y0
					w, # width
					rowH, # height
				)
				fillColor(cr, ui.cursorBgColor)
		if ui.wcalGrid:
			setColor(cr, ui.wcalGridColor)
			###
			cr.rectangle(
				w - 1,
				0,
				1,
				h,
			)
			cr.fill()
			###
			for i in range(1, 7):
				cr.rectangle(
					0,
					i * rowH,
					w,
					1,
				)
				cr.fill()

	def drawCursorOutline(
		self,
		cr: "cairo.Context",
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	):
		cursorRadius = ui.wcalCursorRoundingFactor * min(cw, ch) * 0.5
		cursorLineWidth = ui.wcalCursorLineWidthFactor * min(cw, ch) * 0.5
		drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius, cursorLineWidth)

	def drawCursorBg(
		self,
		cr: "cairo.Context",
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	):
		cursorRadius = ui.wcalCursorRoundingFactor * min(cw, ch) * 0.5
		drawRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius)

	def drawCursorFg(self, cr: "cairo.Context"):
		if not self.showCursor:
			return
		alloc = self.get_allocation()
		w = alloc.width
		h = alloc.height
		rowH = h / 7
		self.drawCursorOutline(
			cr,
			0, # x0
			self.wcal.cellIndex * rowH, # y0
			w, # width
			rowH, # height
		)
		fillColor(cr, ui.cursorOutColor)
		return

	def drawTextList(
		self,
		cr: "cairo.Context",
		textData: List[List[str]],
		font: Optional[Tuple[str, bool, bool, float]] = None,
	):
		alloc = self.get_allocation()
		w = alloc.width
		h = alloc.height
		###
		rowH = h / 7
		itemW = w - ui.wcalPadding
		if font is None:
			fontName = self.getFontValue()
			fontSize = ui.getFont()[-1]  # FIXME
			font = [fontName, False, False, fontSize] if fontName else None
		for i in range(7):
			data = textData[i]
			if data:
				linesN = len(data)
				lineH = rowH / linesN
				lineI = 0
				if len(data[0]) < 2:
					log.info(self._name)
				for line, color in data:
					layout = newTextLayout(
						self,
						text=line,
						font=font,
						maxSize=(itemW, lineH),
						maximizeScale=ui.wcalTextSizeScale,
						truncate=self.truncateText,
					)
					if not layout:
						continue
					layoutW, layoutH = layout.get_pixel_size()
					layoutX = (w - layoutW) / 2
					layoutY = i * rowH + (lineI + 0.5) * lineH - layoutH / 2
					cr.move_to(layoutX, layoutY)
					if self.colorizeHolidayText and self.wcal.status[i].holiday:
						color = ui.holidayColor
					if not color:
						color = ui.textColor
					setColor(cr, color)
					show_layout(cr, layout)
					lineI += 1

	def onButtonPress(self, widget, gevent):
		return False

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def drawColumn(self, cr: "cairo.Context"):
		pass


class MainMenuToolbarItem(ToolbarItem):
	hasOptions = True

	def __init__(self, wcal):
		ToolbarItem.__init__(
			self,
			name="mainMenu",
			imageNameDynamic=True,
			onClick=None,
			desc=_("Main Menu"),
			enableTooltip=True,
			continuousClick=False,
			onPress=self.onButtonPress,
		)
		self._wcal = wcal

	def onConfigChange(self, *a, **kw):
		ToolbarItem.onConfigChange(self, *a, **kw)
		self.updateImage()

	def getOptionsWidget(self) -> gtk.Widget:
		from os.path import isabs
		from scal3.ui_gtk.mywidgets.icon import IconSelectButton
		from scal3.ui_gtk.pref_utils import IconChooserPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = VBox(spacing=self.optionsPageSpacing)
		###
		prefItem = IconChooserPrefItem(
			ui,
			"wcal_toolbar_mainMenu_icon",
			label=_("Icon"),
			live=True,
			onChangeFunc=self.updateImage
		)
		pack(optionsWidget, prefItem.getWidget())
		###
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updateImage(self):
		self.setIconFile(ui.wcal_toolbar_mainMenu_icon)
		self.build()
		self.showHide()

	def getMenuPos(self):
		wcal = self._wcal
		w = self.get_allocation().width
		h = self.get_allocation().height
		x0, y0 = self.translate_coordinates(wcal, 0, 0)
		return (
			x0 if rtl else x0 + w,
			y0 + h // 2,
		)

	def onButtonPress(self, widget=None, gevent=None):
		x, y = self.getMenuPos()
		self._wcal.emit(
			"popup-main-menu",
			0,
			x,
			y,
		)



class WeekNumToolbarItem(LabelToolBoxItem):
	def __init__(self):
		LabelToolBoxItem.__init__(
			self,
			name="weekNum",
			onClick=self.onClick,
			desc=("Week Number"),
			continuousClick=False,
		)
		self.label.set_direction(gtk.TextDirection.LTR)

	def updateLabel(self):
		if ui.wcal_toolbar_weekNum_negative:
			n = ui.cell.weekNumNeg
		else:
			n = ui.cell.weekNum
		self.label.set_label(_(n))

	def onDateChange(self, *a, **ka):
		LabelToolBoxItem.onDateChange(self, *a, **ka)
		self.updateLabel()

	def onClick(self, *a):
		ui.wcal_toolbar_weekNum_negative = not ui.wcal_toolbar_weekNum_negative
		self.updateLabel()
		ui.saveLiveConf()


@registerSignals
class ToolbarColumn(CustomizableToolbar, ColumnBase):
	autoButtonPressHandler = False
	optionsPageSpacing = 5

	def __init__(self, wcal):
		CustomizableToolbar.__init__(self, wcal, vertical=True)
		ColumnBase.__init__(self)
		self.defaultItems = [
			MainMenuToolbarItem(wcal),
			WeekNumToolbarItem(),
			ToolbarItem(
				name="backward4",
				imageName="go-top.svg",
				onClick="goBackward4",
				desc="Backward 4 Weeks",
			),
			ToolbarItem(
				name="backward",
				imageName="go-up.svg",
				onClick="goBackward",
				desc="Previous Week",
			),
			ToolbarItem(
				name="today",
				imageName="go-home.svg",
				onClick="goToday",
				desc="Today",
				continuousClick=False,
			),
			ToolbarItem(
				name="forward",
				imageName="go-down.svg",
				onClick="goForward",
				desc="Next Week",
			),
			ToolbarItem(
				name="forward4",
				imageName="go-bottom.svg",
				onClick="goForward4",
				desc="Forward 4 Weeks",
			),
		]
		self.defaultItemsDict = {
			item._name: item for item in self.defaultItems
		}
		if not ud.wcalToolbarData["items"]:
			ud.wcalToolbarData["items"] = [
				(item._name, True)
				for item in self.defaultItems
			]
		self.setData(ud.wcalToolbarData)

	def updateVars(self):
		CustomizableToolbar.updateVars(self)
		ud.wcalToolbarData = self.getData()


@registerSignals
class WeekDaysColumn(Column):
	_name = "weekDays"
	desc = _("Week Days")
	colorizeHolidayText = True
	showCursor = True
	customizeWidth = True
	customizeExpand = True
	customizeFont = True
	optionsPageSpacing = 20

	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect("draw", self.onExposeEvent)

	def drawColumn(self, cr):
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				[
					(core.getWeekDayN(i), ""),
				]
				for i in range(7)
			],
		)
		self.drawCursorFg(cr)


@registerSignals
class PluginsTextColumn(Column):
	_name = "pluginsText"
	desc = _("Plugins Text")
	expand = True
	customizeFont = True
	truncateText = False
	optionsPageSpacing = 20

	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect("draw", self.onExposeEvent)

	def getTextListByIndex(self, i: int) -> List[str]:
		return [
			(line, "")
			for line in self.wcal.status[i].getPluginsText(
				firstLineOnly=ui.wcal_pluginsText_firstLineOnly,
			).split("\n")
		]

	def drawColumn(self, cr):
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				self.getTextListByIndex(i)
				for i in range(7)
			]
		)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = Column.getOptionsWidget(self)
		#####
		prefItem = CheckPrefItem(
			ui,
			"wcal_pluginsText_firstLineOnly",
			label=_("Only first line of text"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		#####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget


@registerSignals
class EventsIconColumn(Column):
	_name = "eventsIcon"
	desc = _("Events Icon")
	customizeWidth = True
	optionsPageSpacing = 20

	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect("draw", self.onExposeEvent)

	def drawColumn(self, cr):
		self.drawBg(cr)
		###
		w = self.get_allocation().width
		h = self.get_allocation().height
		###
		rowH = h / 7
		itemW = w - ui.wcalPadding
		iconSizeMax = ui.wcalEventIconSizeMax
		for i in range(7):
			c = self.wcal.status[i]
			iconList = c.getWeekEventIcons()
			if not iconList:
				continue
			n = len(iconList)
			scaleFact = min(
				1.0,
				h / iconSizeMax,
				w / (n * iconSizeMax),
			)
			x0 = (w / scaleFact - (n - 1) * iconSizeMax) / 2
			y0 = (2 * i + 1) * h / (14 * scaleFact)
			if rtl:
				iconList.reverse()  # FIXME
			for iconIndex, icon in enumerate(iconList):
				try:
					pix = pixbufFromFile(icon, size=iconSizeMax)
				except GLibError:
					log.exception("")
					continue
				pix_w = pix.get_width()
				pix_h = pix.get_height()
				x1 = x0 + iconIndex * iconSizeMax - pix_w / 2
				y1 = y0 - pix_h / 2
				cr.scale(scaleFact, scaleFact)
				gdk.cairo_set_source_pixbuf(cr, pix, x1, y1)
				cr.rectangle(x1, y1, pix_w, pix_h)
				cr.fill()
				cr.scale(1 / scaleFact, 1 / scaleFact)


@registerSignals
class EventsCountColumn(Column):
	_name = "eventsCount"
	desc = _("Events Count")
	customizeWidth = True
	customizeExpand = True
	optionsPageSpacing = 40

	def __init__(self, wcal):
		Column.__init__(self, wcal)
		##
		self.connect("draw", self.onExposeEvent)

	def getOptionsWidget(self) -> gtk.Widget:
		optionsWidget = Column.getOptionsWidget(self)
		optionsWidget.show_all()
		return optionsWidget

	def getDayTextData(self, i):
		n = len(self.wcal.status[i].getEventsData())
		# FIXME: item["show"][1]
		if n > 0:
			line = _("{eventCount} events").format(eventCount=_(n))
		else:
			line = ""
		return [
			(line, None),
		]

	def drawColumn(self, cr):
		self.drawBg(cr)
		###
		w = self.get_allocation().width
		h = self.get_allocation().height
		###
		self.drawTextList(
			cr,
			[
				self.getDayTextData(i)
				for i in range(7)
			],
		)


@registerSignals
class EventsTextColumn(Column):
	_name = "eventsText"
	desc = _("Events Text")
	expand = True
	customizeFont = True
	truncateText = False
	customizePastTextColor = True
	optionsPageSpacing = 20

	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect("draw", self.onExposeEvent)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = Column.getOptionsWidget(self)
		#####
		prefItem = CheckPrefItem(
			ui,
			"wcal_eventsText_colorize",
			label=_("Use color of event group\nfor event text"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		#####
		prefItem = CheckPrefItem(
			ui,
			"wcal_eventsText_showDesc",
			label=_("Show Description"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		#####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget


	def getDayTextData(self, i):
		from scal3.xml_utils import escape
		data = []
		currentTime = now()
		for item in self.wcal.status[i].getEventsData():
			if not item["show"][1]:
				continue
			line = (
				"".join(item["text"]) if ui.wcal_eventsText_showDesc
				else item["text"][0]
			)
			line = escape(line)
			if item["time"]:
				line = item["time"] + " " + line
			color = ""
			if ui.wcal_eventsText_colorize:
				color = item["color"]
			if ui.wcalPastTextColorEnable_eventsText and \
				item["time_epoch"][1] < currentTime:
				color = ui.wcalPastTextColor_eventsText
			data.append((line, color))
		return data

	def drawColumn(self, cr):
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				self.getDayTextData(i)
				for i in range(7)
			],
		)


@registerSignals
class EventsBoxColumn(Column):
	_name = "eventsBox"
	desc = _("Events Box")
	expand = True  # FIXME
	customizeFont = True
	optionsPageSpacing = 40

	def __init__(self, wcal):
		self.boxes = None
		self.padding = 2
		self.timeWidth = 7 * 24 * 3600
		self.boxEditing = None
		#####
		Column.__init__(self, wcal)
		#####
		self.connect("realize", lambda w: self.updateData())
		self.connect("draw", self.onExposeEvent)

	def updateData(self):
		from scal3.time_utils import getEpochFromJd
		from scal3.ui_gtk import timeline_box as tbox
		from scal3.timeline.box import calcEventBoxes
		self.timeStart = getEpochFromJd(self.wcal.status[0].jd)
		self.pixelPerSec = self.get_allocation().height / self.timeWidth
		# ^^^ unit: pixel / second
		self.borderTm = 0 ## tbox.boxEditBorderWidth / self.pixelPerSec ## second
		self.boxes = calcEventBoxes(
			self.timeStart,
			self.timeStart + self.timeWidth,
			self.pixelPerSec,
			self.borderTm,
		)

	def onDateChange(self, *a, **kw):
		Column.onDateChange(self, *a, **kw)
		self.updateData()
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		Column.onConfigChange(self, *a, **kw)
		self.updateData()
		self.queue_draw()

	def drawBox(self, cr, box):
		from scal3.ui_gtk import timeline_box as tbox
		###
		x = box.y
		y = box.x
		w = box.h
		h = box.w
		###
		tbox.drawBoxBG(cr, box, x, y, w, h)
		tbox.drawBoxText(cr, box, x, y, w, h, self)

	def drawColumn(self, cr):
		self.drawBg(cr)
		if not self.boxes:
			return
		###
		alloc = self.get_allocation()
		w = alloc.width
		h = alloc.height
		###
		for box in self.boxes:
			box.setPixelValues(
				self.timeStart,
				self.pixelPerSec,
				self.padding,
				w - 2 * self.padding,
			)
			self.drawBox(cr, box)


class DaysOfMonthFontButton(MyFontButton):
	styleClass = "daysOfMonthFontButton"

	def __init__(self):
		MyFontButton.__init__(self, dragAndDrop=True)
		self.get_style_context().add_class(self.styleClass)

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle
		# make the font of Button smaller by a factor of 0.5
		font = ui.getFont(scale=0.5)
		return "." + DaysOfMonthFontButton.styleClass + " " + cssTextStyle(
			font=font,
		)


class DaysOfMonthCalTypeParamBox(gtk.Box):
	def __init__(self, wcal, index, calType, params, sgroupLabel, sgroupFont):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.wcal = wcal
		self._parent = wcal
		self.index = index
		self.calType = calType
		######
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		label = gtk.Label(label=_(module.desc) + "  ")
		label.set_xalign(0)
		pack(self, label)
		sgroupLabel.add_widget(label)
		###
		label = gtk.Label(label=f'<span font-size="small">{_("Font")}</span>')
		label.set_use_markup(True)
		self.fontCheck = gtk.CheckButton()
		self.fontCheck.add(label)
		pack(self, gtk.Label(), 1, 1)
		pack(self, self.fontCheck)
		###
		self.fontb = DaysOfMonthFontButton()
		pack(self, self.fontb)
		sgroupFont.add_widget(self.fontb)
		####
		self.set(params)
		####
		self.fontCheck.connect("clicked", self.onChange)
		self.fontb.connect("font-set", self.onChange)

	def get(self):
		return {
			"font": (
				self.fontb.get_font()
				if self.fontCheck.get_active()
				else None
			),
		}

	def set(self, data):
		font = ui.getParamsFont(data)
		self.fontCheck.set_active(bool(font))
		if not font:
			font = ui.getFont()
		self.fontb.set_font(font)

	def onChange(self, obj=None, event=None):
		ui.wcalTypeParams[self.index] = self.get()
		self.wcal.queue_draw()


@registerSignals
class DaysOfMonthColumn(Column):
	colorizeHolidayText = True
	showCursor = True

	def __init__(self, wcal, cgroup, calType, index):
		Column.__init__(self, wcal)
		self.cgroup = cgroup
		self.calType = calType
		self.index = index
		###
		self.connect("draw", self.onExposeEvent)

	def getWidthAttr(self):
		return "wcal_daysOfMonth_width"

	def drawColumn(self, cr):
		self.drawBg(cr)
		font = ui.getParamsFont(ui.wcalTypeParams[self.index])
		self.drawTextList(
			cr,
			[
				[
					(
						_(self.wcal.status[i].dates[self.calType][2], self.calType),
						"",
					)
				]
				for i in range(7)
			],
			font=font,
		)
		self.drawCursorFg(cr)


@registerSignals
class DaysOfMonthColumnGroup(gtk.Box, CustomizableCalBox, ColumnBase):
	_name = "daysOfMonth"
	desc = _("Days of Month")
	customizeWidth = True
	customizeExpand = True
	optionsPageSpacing = 15

	def updateDirection(self):
		self.set_direction(ud.textDirDict[ui.wcal_daysOfMonth_dir])
		# FIXME: not working, needs restarting starcal to be applied

	def __init__(self, wcal):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		ColumnBase.__init__(self)
		self.initVars()
		self.wcal = wcal
		self._parent = wcal
		self.updateCols()
		self.updateDirection()
		self.show()

	def onWidthChange(self):
		ColumnBase.onWidthChange(self)
		for child in self.get_children():
			child.onWidthChange()

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import DirectionPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = ColumnBase.getOptionsWidget(self)
		###
		prefItem = DirectionPrefItem(
			ui,
			"wcal_daysOfMonth_dir",
			onChangeFunc=self.updateDirection,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		frame = gtk.Frame()
		frame.set_label(_("Calendars"))
		self.typeParamsVbox = VBox(spacing=self.optionsPageSpacing // 2)
		self.typeParamsVbox.set_border_width(5)
		frame.add(self.typeParamsVbox)
		frame.show_all()
		pack(optionsWidget, frame)
		self.updateTypeParamsWidget()## FIXME
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	# overwrites method from ColumnBase
	def updatePacking(self):
		ColumnBase.updatePacking(self)
		for child in self.get_children():
			child.expand = self.expand
			child.updatePacking()

	def do_get_preferred_width(self):
		childWidth = self.getWidthValue()
		if childWidth is None:
			raise ValueError("childWidth is None")
		count = len(self.get_children())
		width = count * childWidth
		return width, width

	def updateCols(self):
		#self.foreach(gtk.DrawingArea.destroy)
		# ^^^ Couses tray icon crash in gnome3
		#self.foreach(lambda child: self.remove(child))
		# ^^^ Couses tray icon crash in gnome3
		########
		columns = self.get_children()
		n = len(columns)
		n2 = len(calTypes.active)

		if len(ui.wcalTypeParams) < n2:
			while len(ui.wcalTypeParams) < n2:
				log.info("appending to wcalTypeParams")
				ui.wcalTypeParams.append({
					"font": None,
				})

		width = self.getWidthValue()
		if n > n2:
			for i in range(n2, n):
				columns[i].destroy()
		elif n < n2:
			for i in range(n, n2):
				col = DaysOfMonthColumn(self.wcal, self, 0, i)
				col._parent = self
				pack(self, col, 1, 1)
				columns.append(col)
		for i, calType in enumerate(calTypes.active):
			col = columns[i]
			col.calType = calType
			col.show()

	def updateTypeParamsWidget(self):
		try:
			vbox = self.typeParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		###
		n = len(calTypes.active)
		while len(ui.wcalTypeParams) < n:
			ui.wcalTypeParams.append({
				"font": None,
			})
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for i, calType in enumerate(calTypes.active):
			#try:
			params = ui.wcalTypeParams[i]
			#except IndexError:
			##
			hbox = DaysOfMonthCalTypeParamBox(
				self.wcal,
				i,
				calType,
				params,
				sgroupLabel,
				sgroupFont,
			)
			pack(vbox, hbox)
		###
		vbox.show_all()

	def onConfigChange(self, *a, **ka):
		ColumnBase.onConfigChange(self, *a, **ka)
		self.updateCols()
		self.updateTypeParamsWidget()


@registerSignals
class MoonStatusColumn(Column):
	_name = "moonStatus"
	desc = _("Moon Status")
	showCursor = False
	customizeWidth = True
	optionsPageSpacing = 40

	def __init__(self, wcal):
		from scal3.ui_gtk.utils import pixbufFromFile
		Column.__init__(self, wcal)
		self.connect("draw", self.onExposeEvent)
		self.showPhaseNumber = False

	def drawColumn(self, cr):
		from math import cos
		from scal3.moon import getMoonPhase

		alloc = self.get_allocation()
		w = alloc.width
		h = alloc.height
		itemW = w - ui.wcalPadding
		rowH = h / 7

		imgSize = min(rowH, itemW)
		scaleFact = 1

		imgMoonSize = imgSize * 0.9296875
		# imgBorder = (imgSize-imgMoonSize) / 2
		imgRadius = imgMoonSize / 2
		###
		# it's ok because pixbufFromFile uses cache
		moonPixbuf = pixbufFromFile("full_moon_128px.png", size=imgSize)
		###
		imgItemW = itemW / scaleFact
		imgRowH = rowH / scaleFact
		imgCenterX = w / 2 / scaleFact
		###
		self.drawBg(cr)
		###
		cr.set_line_width(0)
		cr.scale(scaleFact, scaleFact)

		def draw_arc(
			imgCenterY: float,
			arcScale: float,
			upwards: bool,
			clockWise: bool,
		):
			if arcScale is None: # None means infinity
				if upwards:
					cr.move_to(imgCenterX, imgCenterY + imgRadius)
					cr.line_to(imgCenterX, imgCenterY - imgRadius)
				else:
					cr.move_to(imgCenterX, imgCenterY - imgRadius)
					cr.line_to(imgCenterX, imgCenterY + imgRadius)
				return
			startAngle, endAngle = pi / 2.0, 3 * pi / 2.0
			if upwards:
				startAngle, endAngle = endAngle, startAngle
			cr.save()
			cr.translate(imgCenterX, imgCenterY)
			try:
				cr.scale(imgRadius * arcScale, imgRadius)
			except Exception as e:
				raise ValueError(f"{e}: invalid scale factor {arcScale}")
			arc = cr.arc_negative if clockWise else cr.arc
			arc(
				0, # center X
				0, # center Y
				1, # radius
				startAngle, # start angle
				endAngle, # end angle
			)
			cr.restore()

		for index in range(7):
			bigPhase = getMoonPhase(
				self.wcal.status[index].jd,
				ui.wcal_moonStatus_southernHemisphere,
			)
			# 0 <= bigPhase < 2

			imgCenterY = (index + 0.5) * imgRowH

			gdk.cairo_set_source_pixbuf(
				cr,
				moonPixbuf,
				imgCenterX - imgRadius,
				imgCenterY - imgRadius,
			)

			phase = bigPhase % 1

			draw_arc(
				imgCenterY,
				1, # arc scale factor
				False, # upwards
				bigPhase < 1, # clockWise
			)
			draw_arc(
				imgCenterY,
				None if phase == 0.5 else abs(cos(phase * pi)), # arc scale factor
				True, # upwards
				phase > 0.5, # clockWise
			)
			cr.fill()

			if self.showPhaseNumber:
				layout = newTextLayout(
					self,
					text=f"{bigPhase:.1f}",
					maxSize=(imgItemW * 0.8, imgRowH * 0.8),
				)
				layoutW, layoutH = layout.get_pixel_size()
				layoutX = imgCenterX - layoutW * 0.4
				layoutY = imgCenterY - layoutH * 0.4
				cr.move_to(layoutX, layoutY)
				setColor(cr, (255, 0, 0))
				show_layout(cr, layout)

		cr.scale(1 / scaleFact, 1 / scaleFact)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = ColumnBase.getOptionsWidget(self)
		####
		prefItem = CheckPrefItem(
			ui,
			"wcal_moonStatus_southernHemisphere",
			label=_("Southern Hemisphere"),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget


@registerSignals
class CalObj(gtk.Box, CustomizableCalBox, CalBase):
	_name = "weekCal"
	desc = _("Week Calendar")
	expand = True
	optionsPageSpacing = 10
	itemsPageEnable = True
	itemsPageTitle = _("Columns")
	itemsPageButtonBorder = 15
	myKeys = CalBase.myKeys + (
		"up", "down",
		"left", "right",
		"page_up",
		"k", "p",
		"page_down",
		"j", "n",
		"end",
		"f10", "m",
	)
	signals = CalBase.signals

	def getCellPagePlus(self, cell, plus):
		return ui.cellCache.getCell(cell.jd + 7 * plus)

	def __init__(self):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.windowToItemDict = {}
		######################
		self.connect("scroll-event", self.scroll)
		###
		self.connect("button-press-event", self.onButtonPress)
		#####
		# set in self.updateStatus
		self.status = None
		self.cellIndex = 0
		#####
		defaultItems = [
			ToolbarColumn(self),
			WeekDaysColumn(self),
			PluginsTextColumn(self),
			EventsIconColumn(self),
			EventsCountColumn(self),
			EventsTextColumn(self),
			EventsBoxColumn(self),
			DaysOfMonthColumnGroup(self),
			MoonStatusColumn(self),
		]
		defaultItemsDict = dict([(item._name, item) for item in defaultItems])
		itemNames = list(defaultItemsDict.keys())
		for name, enable in ui.wcalItems:
			item = defaultItemsDict.get(name)
			if item is None:
				log.info(f"weekCal item '{name}' does not exist")
				continue
			item.enable = enable
			self.appendItem(item)
			itemNames.remove(name)
		for name in itemNames:
			item = defaultItemsDict[name]
			item.enable = False
			self.appendItem(item)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			SpinPrefItem,
			CheckPrefItem,
			ColorPrefItem,
			CheckColorPrefItem,
		)

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = VBox(spacing=self.optionsPageSpacing)
		#####
		prefItem = SpinPrefItem(
			ui,
			"wcalTextSizeScale",
			0.01, 1,
			digits=3, step=0.1,
			label=_("Text Size Scale"),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		###
		prefItem = CheckColorPrefItem(
			CheckPrefItem(ui, "wcalGrid", _("Grid")),
			ColorPrefItem(ui, "wcalGridColor", useAlpha=True),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		############
		pageVBox = VBox(spacing=20)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		prefItem = SpinPrefItem(
			ui,
			"wcalCursorLineWidthFactor",
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
			"wcalCursorRoundingFactor",
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
		self.subPages = [page]
		###
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button, padding=10)
		#########
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()

	def updateVars(self):
		CustomizableCalBox.updateVars(self)
		ui.wcalItems = self.getItemsData()

	def updateStatus(self):
		from scal3.weekcal import getCurrentWeekStatus
		self.status = getCurrentWeekStatus()
		index = ui.cell.jd - self.status[0].jd
		if index > 6:
			log.info(f"warning: drawCursorFg: index = {index}")
			return
		self.cellIndex = index

	def onConfigChange(self, *a, **kw):
		self.updateStatus()
		CalBase.onConfigChange(self, *a, **kw)
		self.queue_draw()

	def onDateChange(self, *a, **kw):
		self.updateStatus()
		CustomizableCalBox.onDateChange(self, *a, **kw)
		self.queue_draw()
		#for item in self.items:
		#	item.queue_draw()

	def goBackward4(self, obj=None):
		self.jdPlus(-28)

	def goBackward(self, obj=None):
		self.jdPlus(-7)

	def goForward(self, obj=None):
		self.jdPlus(7)

	def goForward4(self, obj=None):
		self.jdPlus(28)

	def itemContainsGdkWindow(self, item, col_win):
		if col_win == item.get_window():
			return True
		if isinstance(item, gtk.Container):
			for child in item.get_children():
				if self.itemContainsGdkWindow(child, col_win):
					return True
		return False

	def findColumnWidgetByGdkWindow(self, col_win):
		for item in self.items:
			if isinstance(item, gtk.Box):
				# right now only DaysOfMonthColumnGroup
				for child in item.get_children():
					if self.itemContainsGdkWindow(child, col_win):
						return child
			else:
				if self.itemContainsGdkWindow(item, col_win):
					return item

	def onButtonPress(self, widget, gevent):
		# gevent is Gdk.EventButton
		col = self.findColumnWidgetByGdkWindow(gevent.get_window())
		if not col:
			return False
		if not col.autoButtonPressHandler:
			return False
		###
		x_col, y_col = gevent.get_coords()
		# x_col is relative to the column, not to the weekCal
		# y_col is relative to the column, but also to the weekCal,
		# 		because we have nothing above columns
		###
		i = int(y_col * 7.0 / self.get_allocation().height)
		cell = self.status[i]
		self.gotoJd(cell.jd)
		if gevent.type == TWO_BUTTON_PRESS:
			self.emit("double-button-press")
		if gevent.button == 3:
			x, y = col.translate_coordinates(self, x_col, y_col)
			self.emit("popup-cell-menu", gevent.time, x, y)
		return True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "up":
			self.jdPlus(-1)
		elif kname == "down":
			self.jdPlus(1)
		elif kname == "left":
			self.jdPlus(rtlSgn() * 7)
		elif kname == "right":
			self.jdPlus(rtlSgn() * -7)
		elif kname == "end":
			self.gotoJd(self.status[-1].jd)
		elif kname in ("page_up", "k", "p"):
			self.jdPlus(-7)
		elif kname in ("page_down", "j", "n"):
			self.jdPlus(7)
		elif kname in ("f10", "m"):
			if gevent.state & gdk.ModifierType.SHIFT_MASK:
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
			self.jdPlus(-1)
		elif d == "down":
			self.jdPlus(1)
		else:
			return False

	def getCellPos(self, *args):
		alloc = self.get_allocation()
		return (
			int(alloc.width / 2),
			(ui.cell.weekDayIndex + 1) * alloc.height / 7,
		)

	def getToolbar(self):
		for item in self.items:
			if item.enable and item._name == "toolbar":
				return item

	def getMainMenuPos(self, *args):
		toolbar = self.getToolbar()
		if toolbar:
			for item in toolbar.items:
				if item.enable and item._name == "mainMenu":
					return item.getMenuPos()
		if rtl:
			return self.get_allocation().width, 0
		else:
			return 0, 0


if __name__ == "__main__":
	ui.init()
	win = gtk.Dialog()
	cal = CalObj()
	win.add_events(gdk.EventMask.ALL_EVENTS_MASK)
	pack(win.vbox, cal, 1, 1)
	win.vbox.show_all()
	win.resize(600, 400)
	win.set_title(cal.desc)
	cal.onConfigChange()
	win.run()
