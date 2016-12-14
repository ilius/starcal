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

import time
from time import time as now

import sys, os

from scal3.utils import myRaise
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl

from scal3.cal_types import calTypes

from scal3 import core
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk.mywidgets.font_family_combo import FontFamilyCombo

from scal3.ui_gtk import gtk_ud as ud

from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.customize import CustomizableCalObj, CustomizableCalBox
from scal3.ui_gtk.toolbar import ToolbarItem, CustomizableToolbar

def show_event(widget, gevent):
	print(type(widget), gevent.type.value_name)#, gevent.get_value()#, gevent.send_event


class ColumnBase(CustomizableCalObj):
	customizeWidth = False
	customizeFont = False
	autoButtonPressHandler = True
	##
	getWidthAttr = lambda self: 'wcal_%s_width'%self._name
	getWidthValue = lambda self: getattr(ui, self.getWidthAttr(), None)
	setWidthValue = lambda self, value: setattr(ui, self.getWidthAttr(), value)
	setWidthWidget = lambda self, value: self.set_property('width-request', value)
	##
	getFontAttr = lambda self: 'wcalFont_%s'%self._name
	getFontValue = lambda self: getattr(ui, self.getFontAttr(), None)
	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		if self.customizeWidth:
			self.setWidthWidget(self.getWidthValue())
	def widthSpinChanged(self, spin):
		if self._name:
			value = spin.get_value()
			self.setWidthValue(value)
			self.setWidthWidget(value)
	def fontFamilyComboChanged(self, combo):
		if self._name:
			setattr(ui, self.getFontAttr(), combo.get_value())
			self.onDateChange()
	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.VBox()
		####
		if self.customizeWidth:
			value = self.getWidthValue()
			###
			hbox = gtk.HBox()
			pack(hbox, gtk.Label(_('Width')))
			spin = IntSpinButton(0, 999)
			pack(hbox, spin)
			spin.set_value(value)
			spin.connect('changed', self.widthSpinChanged)
			pack(self.optionsWidget, hbox)
		####
		if self.customizeFont:
			hbox = gtk.HBox()
			pack(hbox, gtk.Label(_('Font Family')))
			combo = FontFamilyCombo(hasAuto=True)
			combo.set_value(self.getFontValue())
			pack(hbox, combo)
			combo.connect('changed', self.fontFamilyComboChanged)
			pack(self.optionsWidget, hbox)
		####
		self.optionsWidget.show_all()



class Column(gtk.DrawingArea, ColumnBase):
	colorizeHolidayText = False
	showCursor = False
	truncateText = False
	def __init__(self, wcal):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		#self.connect('button-press-event', self.buttonPress)
		#self.connect('event', show_event)
		self.wcal = wcal
	def getContext(self):
		return self.get_window().cairo_create()
	def drawBg(self, cr):
		w = self.get_allocation().width
		h = self.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		rowH = h/7.0
		for i in range(7):
			c = self.wcal.status[i]
			y0 = i*rowH
			if c.jd == ui.todayCell.jd:
				cr.rectangle(0, i*rowH, w, rowH)
				fillColor(cr, ui.todayCellColor)
			if self.showCursor and c.jd == ui.cell.jd:
				drawCursorBg(cr, 0, y0, w, rowH)
				fillColor(cr, ui.cursorBgColor)
		if ui.wcalGrid:
			w = self.get_allocation().width
			h = self.get_allocation().height
			setColor(cr, ui.wcalGridColor)
			###
			cr.rectangle(w-1, 0, 1, h)
			cr.fill()
			###
			for i in range(1, 7):
				cr.rectangle(0, i*rowH, w, 1)
				cr.fill()
	def drawCursorFg(self, cr):
		w = self.get_allocation().width
		h = self.get_allocation().height
		rowH = h/7.0
		for i in range(7):
			c = self.wcal.status[i]
			y0 = i*rowH
			if self.showCursor and c.jd == ui.cell.jd:
				drawCursorOutline(cr, 0, y0, w, rowH)
				fillColor(cr, ui.cursorOutColor)
	def drawTextList(self, cr, textData, font=None):
		w = self.get_allocation().width
		h = self.get_allocation().height
		###
		rowH = h/7.0
		itemW = w - ui.wcalPadding
		if font is None:
			fontName = self.getFontValue()
			fontSize = ui.getFont()[-1] ## FIXME
			font = [fontName, False, False, fontSize] if fontName else None
		for i in range(7):
			data = textData[i]
			if data:
				linesN = len(data)
				lineH = rowH/linesN
				lineI = 0
				if len(data[0]) < 2:
					print(self._name)
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
					layoutX = (w-layoutW)/2.0
					layoutY = i*rowH + (lineI+0.5)*lineH - layoutH/2.0
					cr.move_to(layoutX, layoutY)
					if self.colorizeHolidayText and self.wcal.status[i].holiday:
						color = ui.holidayColor
					if not color:
						color = ui.textColor
					setColor(cr, color)
					show_layout(cr, layout)
					lineI += 1
	def buttonPress(self, widget, gevent):
		return False
	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()


class MainMenuToolbarItem(ToolbarItem):
	def __init__(self):
		ToolbarItem.__init__(self, 'mainMenu', None, '', _('Main Menu'), enableTooltip=False)
		self.connect('clicked', self.onClicked)
		self.updateImage()
	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.icon import IconSelectButton
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.VBox()
		###
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(_('Icon')+'  '))
		self.iconSelect = IconSelectButton()
		self.iconSelect.set_filename(ui.wcal_toolbar_mainMenu_icon)
		self.iconSelect.connect('changed', self.onIconChanged)
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.optionsWidget, hbox)
		self.optionsWidget.show_all()
	def updateImage(self):
		from scal3.ui_gtk.utils import imageFromFile
		self.set_property('label-widget', imageFromFile(ui.wcal_toolbar_mainMenu_icon))
		self.show_all()
	def getMenuPos(self):
		wcal = self.get_parent().get_parent()
		w = self.get_allocation().width
		h = self.get_allocation().height
		x0, y0 = self.translate_coordinates(wcal, 0, 0)
		return (
			x0 if rtl else x0+w,
			y0+h,
		)
	def onClicked(self, widget=None):
		x, y = self.getMenuPos()
		self.get_parent().get_parent().emit(
			'popup-main-menu',
			0,
			x,
			y,
		)
	def onIconChanged(self, widget, icon):
		if not icon:
			icon = ui.wcal_toolbar_mainMenu_icon_default
			self.iconSelect.set_filename(icon)
		ui.wcal_toolbar_mainMenu_icon = icon
		self.updateImage()


class WeekNumToolbarItem(ToolbarItem):
	def __init__(self):
		ToolbarItem.__init__(self, 'weekNum', None, self.onClicked, ('Week Number'))
		self.label = gtk.Label()
		self.label.set_direction(gtk.TextDirection.LTR)
		self.set_property('label-widget', self.label)
	def updateLabel(self):
		if ui.wcal_toolbar_weekNum_negative:
			n = ui.cell.weekNumNeg
		else:
			n = ui.cell.weekNum
		self.label.set_label(_(n))
	def onDateChange(self, *a, **ka):
		ToolbarItem.onDateChange(self, *a, **ka)
		self.updateLabel()
	def onClicked(self, *a):
		ui.wcal_toolbar_weekNum_negative = not ui.wcal_toolbar_weekNum_negative
		self.updateLabel()
		ui.saveLiveConf()


@registerSignals
class ToolbarColumn(CustomizableToolbar, ColumnBase):
	autoButtonPressHandler = False
	defaultItems = [
		MainMenuToolbarItem(),
		WeekNumToolbarItem(),
		ToolbarItem('backward4', 'goto_top', 'goBackward4', 'Backward 4 Weeks'),
		ToolbarItem('backward', 'go_up', 'goBackward', 'Previous Week'),
		ToolbarItem('today', 'home', 'goToday', 'Today'),
		ToolbarItem('forward', 'go_down', 'goForward', 'Next Week'),
		ToolbarItem('forward4', 'goto_bottom', 'goForward4', 'Forward 4 Weeks'),
	]
	defaultItemsDict = dict([(item._name, item) for item in defaultItems])
	def __init__(self, wcal):
		CustomizableToolbar.__init__(self, wcal, True, True)
		if not ud.wcalToolbarData['items']:
			ud.wcalToolbarData['items'] = [(item._name, True) for item in self.defaultItems]
		self.setData(ud.wcalToolbarData)
	def updateVars(self):
		CustomizableToolbar.updateVars(self)
		ud.wcalToolbarData = self.getData()


@registerSignals
class WeekDaysColumn(Column):
	_name = 'weekDays'
	desc = _('Week Days')
	colorizeHolidayText = True
	showCursor = True
	customizeWidth = True
	customizeFont = True
	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect('draw', self.onExposeEvent)
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				[
					(core.getWeekDayN(i), ''),
				]
				for i in range(7)
			],
		)
		self.drawCursorFg(cr)


@registerSignals
class PluginsTextColumn(Column):
	_name = 'pluginsText'
	desc = _('Plugins Text')
	expand = True
	customizeFont = True
	truncateText = False
	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect('draw', self.onExposeEvent)
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				[
					(line, '') for line in self.wcal.status[i].pluginsText.split('\n')
				]
				for i in range(7)
			]
		)


@registerSignals
class EventsIconColumn(Column):
	_name = 'eventsIcon'
	desc = _('Events Icon')
	maxPixH = 26.0
	maxPixW = 26.0
	customizeWidth = True
	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect('draw', self.onExposeEvent)
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
		self.drawBg(cr)
		###
		w = self.get_allocation().width
		h = self.get_allocation().height
		###
		rowH = h/7.0
		itemW = w - ui.wcalPadding
		for i in range(7):
			c = self.wcal.status[i]
			iconList = c.getWeekEventIcons()
			if not iconList:
				continue
			n = len(iconList)
			scaleFact = min(
				1.0,
				h / self.maxPixH,
				w / (n * self.maxPixW),
			)
			x0 = (w/scaleFact - (n-1)*self.maxPixW) / 2.0
			y0 = (2*i + 1) * h / (14.0*scaleFact)
			if rtl:
				iconList.reverse()## FIXME
			for iconIndex, icon in enumerate(iconList):
				try:
					pix = GdkPixbuf.Pixbuf.new_from_file(icon)
				except:
					myRaise(__file__)
					continue
				pix_w = pix.get_width()
				pix_h = pix.get_height()
				x1 = x0 + iconIndex*self.maxPixW - pix_w/2.0
				y1 = y0 - pix_h/2.0
				cr.scale(scaleFact, scaleFact)
				gdk.cairo_set_source_pixbuf(cr, pix, x1, y1)
				cr.rectangle(x1, y1, pix_w, pix_h)
				cr.fill()
				cr.scale(1.0/scaleFact, 1.0/scaleFact)


@registerSignals
class EventsCountColumn(Column):
	_name = 'eventsCount'
	desc = _('Events Count')
	customizeWidth = True
	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.expand = ui.wcal_eventsCount_expand
		##
		self.connect('draw', self.onExposeEvent)
	def optionsWidgetCreate(self):
		if self.optionsWidget:
			return
		Column.optionsWidgetCreate(self)
		#####
		hbox = gtk.HBox()
		check = gtk.CheckButton(_('Expand'))
		check.set_active(ui.wcal_eventsCount_expand)
		check.connect('clicked', self.expandCheckClicked)
		pack(hbox, check)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.optionsWidget, hbox)
		self.optionsWidget.show_all()
	def expandCheckClicked(self, check):
		active = check.get_active()
		self.expand = ui.wcal_eventsCount_expand = active
		self.wcal.set_child_packing(self, active, active, 0, gtk.PACK_START)
		self.queue_draw()
	def getDayTextData(self, i):
		n = len(self.wcal.status[i].eventsData)
		## item['show'][1] FIXME
		if n > 0:
			line = _('%s events')%_(n)
		else:
			line = ''
		return [
			(line, None),
		]
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
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
	_name = 'eventsText'
	desc = _('Events Text')
	expand = True
	customizeFont = True
	truncateText = False
	def __init__(self, wcal):
		Column.__init__(self, wcal)
		self.connect('draw', self.onExposeEvent)
	def optionsWidgetCreate(self):
		if self.optionsWidget:
			return
		Column.optionsWidgetCreate(self)
		#####
		hbox = gtk.HBox()
		check = gtk.CheckButton(_('Show Description'))
		check.set_active(ui.wcal_eventsText_showDesc)
		pack(hbox, check)
		pack(hbox, gtk.Label(''), 1, 1)
		check.connect('clicked', self.descCheckClicked)
		pack(self.optionsWidget, hbox)
		##
		hbox = gtk.HBox()
		check = gtk.CheckButton(_('Colorize'))
		check.set_active(ui.wcal_eventsText_colorize)
		pack(hbox, check)
		pack(hbox, gtk.Label(''), 1, 1)
		check.connect('clicked', self.colorizeCheckClicked)
		pack(self.optionsWidget, hbox)
		##
		self.optionsWidget.show_all()
	def descCheckClicked(self, check):
		ui.wcal_eventsText_showDesc = check.get_active()
		self.queue_draw()
	def colorizeCheckClicked(self, check):
		ui.wcal_eventsText_colorize = check.get_active()
		self.queue_draw()
	def getDayTextData(self, i):
		from scal3.xml_utils import escape
		data = []
		for item in self.wcal.status[i].eventsData:
			if not item['show'][1]:
				continue
			line = ''.join(item['text']) if ui.wcal_eventsText_showDesc else item['text'][0]
			line = escape(line)
			if item['time']:
				line = item['time'] + ' ' + line
			color = item['color'] if ui.wcal_eventsText_colorize else ''
			data.append((line, color))
		return data
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
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
	_name = 'eventsBox'
	desc = _('Events Box')
	expand = True ## FIXME
	customizeFont = True
	def __init__(self, wcal):
		self.boxes = None
		self.padding = 2
		self.timeWidth = 7*24*3600
		self.boxEditing = None
		#####
		Column.__init__(self, wcal)
		#####
		self.connect('realize', lambda w: self.updateData())
		self.connect('draw', self.onExposeEvent)
	def updateData(self):
		from scal3.time_utils import getEpochFromJd
		from scal3.ui_gtk import timeline_box as tbox
		self.timeStart = getEpochFromJd(self.wcal.status[0].jd)
		self.pixelPerSec = float(self.get_allocation().height) / self.timeWidth ## pixel/second
		self.borderTm = 0 ## tbox.boxMoveBorder / self.pixelPerSec ## second
		self.boxes = tbox.calcEventBoxes(
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
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
		self.drawBg(cr)
		if not self.boxes:
			return
		###
		w = self.get_allocation().width
		h = self.get_allocation().height
		###
		for box in self.boxes:
			box.setPixelValues(
				self.timeStart,
				self.pixelPerSec,
				self.padding,
				w - 2*self.padding,
			)
			self.drawBox(cr, box)


class WcalTypeParamBox(gtk.HBox):
	def __init__(self, wcal, index, mode, params, sgroupLabel, sgroupFont):
		from scal3.ui_gtk.mywidgets import MyFontButton
		gtk.HBox.__init__(self)
		self.wcal = wcal
		self.index = index
		self.mode = mode
		######
		label = gtk.Label(_(calTypes[mode].desc)+'  ')
		label.set_alignment(0, 0.5)
		pack(self, label)
		sgroupLabel.add_widget(label)
		###
		self.fontCheck = gtk.CheckButton(_('Font'))
		pack(self, gtk.Label(''), 1, 1)
		pack(self, self.fontCheck)
		###
		self.fontb = MyFontButton(wcal)
		pack(self, self.fontb)
		sgroupFont.add_widget(self.fontb)
		####
		self.set(params)
		####
		self.fontCheck.connect('clicked', self.onChange)
		self.fontb.connect('font-set', self.onChange)
	get = lambda self: {
		'font': self.fontb.get_font_name() if self.fontCheck.get_active() else None,
	}
	def set(self, data):
		font = data['font']
		self.fontCheck.set_active(bool(font))
		if not font:
			font = ui.getFont()
		self.fontb.set_font_name(font)
	def onChange(self, obj=None, event=None):
		ui.wcalTypeParams[self.index] = self.get()
		self.wcal.queue_draw()

@registerSignals
class DaysOfMonthColumn(Column):
	colorizeHolidayText = True
	showCursor = True
	def __init__(self, wcal, cgroup, mode, index):
		Column.__init__(self, wcal)
		self.cgroup = cgroup
		self.mode = mode
		self.index = index
		###
		self.connect('draw', self.onExposeEvent)
	def onExposeEvent(self, widget=None, event=None):
		cr = self.getContext()
		self.drawBg(cr)
		try:
			font = ui.wcalTypeParams[self.index]['font']
		except:
			font = None
		self.drawTextList(
			cr,
			[
				[
					(
						_(self.wcal.status[i].dates[self.mode][2], self.mode),
						'',
					)
				]
				for i in range(7)
			],
			font=font,
		)
		self.drawCursorFg(cr)

@registerSignals
class DaysOfMonthColumnGroup(gtk.HBox, CustomizableCalBox, ColumnBase):
	_name = 'daysOfMonth'
	desc = _('Days of Month')
	customizeWidth = True
	updateDir = lambda self: self.set_direction(ud.textDirDict[ui.wcal_daysOfMonth_dir])
	def __init__(self, wcal):
		gtk.HBox.__init__(self)
		self.initVars()
		self.wcal = wcal
		self.updateCols()
		self.updateDir()
		self.show()
	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.direction_combo import DirectionComboBox
		if self.optionsWidget:
			return
		ColumnBase.optionsWidgetCreate(self)
		###
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(_('Direction')))
		combo = DirectionComboBox()
		pack(hbox, combo)
		combo.setValue(ui.wcal_daysOfMonth_dir)
		combo.connect('changed', self.dirComboChanged)
		pack(self.optionsWidget, hbox)
		####
		frame = gtk.Frame()
		frame.set_label(_('Calendars'))
		self.typeParamsVbox = gtk.VBox()
		frame.add(self.typeParamsVbox)
		frame.show_all()
		pack(self.optionsWidget, frame)
		self.updateTypeParamsWidget()## FIXME
		####
		self.optionsWidget.show_all()
	def setWidthWidget(self, value):## overwrites method from ColumnBase
		for child in self.get_children():
			child.set_property('width-request', value)
	def dirComboChanged(self, combo):
		ui.wcal_daysOfMonth_dir = combo.getValue()
		self.updateDir()
	def updateCols(self):
		#self.foreach(gtk.DrawingArea.destroy)## Couses crash tray icon in gnome3
		#self.foreach(lambda child: self.remove(child))## Couses crash tray icon in gnome3
		########
		columns = self.get_children()
		n = len(columns)
		n2 = len(calTypes.active)
		width = self.getWidthValue()
		if n > n2:
			for i in range(n2, n):
				columns[i].destroy()
		elif n < n2:
			for i in range(n, n2):
				col = DaysOfMonthColumn(self.wcal, self, 0, i)
				pack(self, col)
				columns.append(col)
		for i, mode in enumerate(calTypes.active):
			col = columns[i]
			col.mode = mode
			col.show()
			col.set_property('width-request', width)
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
				'font': None,
			})
		sgroupLabel = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		for i, mode in enumerate(calTypes.active):
			#try:
			params = ui.wcalTypeParams[i]
			#except IndexError:
			##
			hbox = WcalTypeParamBox(self.wcal, i, mode, params, sgroupLabel, sgroupFont)
			pack(vbox, hbox)
		###
		vbox.show_all()
	def onConfigChange(self, *a, **ka):
		ColumnBase.onConfigChange(self, *a, **ka)
		self.updateCols()
		self.updateTypeParamsWidget()



@registerSignals
class CalObj(gtk.HBox, CustomizableCalBox, ColumnBase, CalBase):
	_name = 'weekCal'
	desc = _('Week Calendar')
	myKeys = CalBase.myKeys + (
		'up', 'down',
		'page_up',
		'k', 'p',
		'page_down',
		'j', 'n',
		'end',
		'f10', 'm',
	)
	signals = CalBase.signals
	def getCellPagePlus(self, cell, plus):
		return ui.cellCache.getCell(cell.jd + 7*plus)
	def __init__(self):
		gtk.HBox.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.set_property('height-request', ui.wcalHeight)
		self.windowToItemDict = {}
		######################
		self.connect('scroll-event', self.scroll)
		###
		self.connect('button-press-event', self.buttonPress)
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
		]
		defaultItemsDict = dict([(item._name, item) for item in defaultItems])
		itemNames = list(defaultItemsDict.keys())
		for name, enable in ui.wcalItems:
			try:
				item = defaultItemsDict[name]
			except KeyError:
				print('weekCal item %s does not exist'%name)
			else:
				item.enable = enable
				self.appendItem(item)
				itemNames.remove(name)
		for name in itemNames:
			item = defaultItemsDict[name]
			item.enable = False
			self.appendItem(item)
	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
		from scal3.ui_gtk.pref_utils import CheckPrefItem, ColorPrefItem
		if self.optionsWidget:
			return
		ColumnBase.optionsWidgetCreate(self)
		#####
		hbox = gtk.HBox()
		spin = IntSpinButton(1, 9999)
		spin.set_value(ui.wcalHeight)
		spin.connect('changed', self.heightSpinChanged)
		pack(hbox, gtk.Label(_('Height')))
		pack(hbox, spin)
		pack(self.optionsWidget, hbox)
		###
		hbox = gtk.HBox()
		spin = FloatSpinButton(0.01, 1, 2)
		spin.set_value(ui.wcalTextSizeScale)
		spin.connect('changed', self.textSizeScaleSpinChanged)
		pack(hbox, gtk.Label(_('Text Size Scale')))
		pack(hbox, spin)
		pack(self.optionsWidget, hbox)
		########
		hbox = gtk.HBox(spacing=3)
		####
		item = CheckPrefItem(ui, 'wcalGrid', _('Grid'))
		item.updateWidget()
		gridCheck = item._widget
		pack(hbox, gridCheck)
		gridCheck.item = item
		####
		colorItem = ColorPrefItem(ui, 'wcalGridColor', True)
		colorItem.updateWidget()
		pack(hbox, colorItem._widget)
		gridCheck.colorb = colorItem._widget
		gridCheck.connect('clicked', self.gridCheckClicked)
		colorItem._widget.item = colorItem
		colorItem._widget.connect('color-set', self.gridColorChanged)
		colorItem._widget.set_sensitive(ui.wcalGrid)
		####
		pack(self.optionsWidget, hbox)
		###
		self.optionsWidget.show_all()
	def heightSpinChanged(self, spin):
		v = spin.get_value()
		self.set_property('height-request', v)
		ui.wcalHeight = v
	def textSizeScaleSpinChanged(self, spin):
		ui.wcalTextSizeScale = spin.get_value()
		self.queue_draw()
	def updateVars(self):
		CustomizableCalBox.updateVars(self)
		ui.wcalItems = self.getItemsData()
	def updateStatus(self):
		from scal3.weekcal import getCurrentWeekStatus
		self.status = getCurrentWeekStatus()
	def onConfigChange(self, *a, **kw):
		self.updateStatus()
		ColumnBase.onConfigChange(self, *a, **kw)
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
	def buttonPress(self, widget, gevent):
		col_win = gevent.get_window()
		col = None
		for item in self.items:
			if col_win == item.get_window():
				col = item
				break
		if not col:
			return False
		if not col.autoButtonPressHandler:
			return False
		###
		b = gevent.button
		#x, y, mask = col_win.get_pointer()
		x, y = self.get_pointer()
		#y += 10
		###
		i = int(gevent.y * 7.0 / self.get_allocation().height)
		cell = self.status[i]
		self.gotoJd(cell.jd)
		if gevent.type==TWO_BUTTON_PRESS:
			self.emit('2button-press')
		if b == 3:
			self.emit('popup-cell-menu', gevent.time, x, y)
		return True
	def keyPress(self, arg, gevent):
		print('keyPress')
		if CalBase.keyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		print('keyPress', kname)
		if kname=='up':
			self.jdPlus(-1)
		elif kname=='down':
			self.jdPlus(1)
		elif kname=='end':
			self.gotoJd(self.status[-1].jd)
		elif kname in ('page_up', 'k', 'p'):
			self.jdPlus(-7)
		elif kname in ('page_down', 'j', 'n'):
			self.jdPlus(7)
		elif kname in ('f10', 'm'):
			if gevent.state & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
			else:
				self.emit('popup-main-menu', gevent.time, *self.getMainMenuPos())
		else:
			return False
		return True
	def scroll(self, widget, gevent):
		d = getScrollValue(gevent)
		if d=='up':
			self.jdPlus(-1)
		elif d=='down':
			self.jdPlus(1)
		else:
			return False
	getCellPos = lambda self, *args: (
		int(self.get_allocation().width / 2.0),
		(ui.cell.weekDayIndex+1) * self.get_allocation().height / 7.0,
	)
	def getToolbar(self):
		for item in self.items:
			if item.enable and item._name == 'toolbar':
				return item
	def getMainMenuPos(self, *args):
		toolbar = self.getToolbar()
		if toolbar:
			for item in toolbar.items:
				if item.enable and item._name == 'mainMenu':
					return item.getMenuPos()
		if rtl:
			return self.get_allocation().width, 0
		else:
			return 0, 0









if __name__=='__main__':
	win = gtk.Dialog(parent=None)
	cal = CalObj()
	win.add_events(gdk.EventMask.ALL_EVENTS_MASK)
	pack(win.vbox, cal, 1, 1)
	win.vbox.show_all()
	win.resize(600, 400)
	win.set_title(cal.desc)
	cal.onConfigChange()
	win.run()











