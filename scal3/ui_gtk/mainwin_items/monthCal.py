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

from time import localtime
from time import time as now

import sys
import os
from math import sqrt

from scal3.utils import myRaise
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
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.cal_base import CalBase


class MonthCalTypeParamBox(gtk.HBox):
	def getCellPagePlus(self, cell, plus):
		return ui.getMonthPlus(cell, plus)

	def __init__(self, cal, index, mode, params, sgroupLabel, sgroupFont):
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
		from scal3.ui_gtk.mywidgets import MyFontButton, MyColorButton
		gtk.HBox.__init__(self)
		self.cal = cal
		self.index = index
		self.mode = mode
		######
		label = gtk.Label(_(calTypes[mode].desc) + '  ')
		label.set_alignment(0, 0.5)
		pack(self, label)
		sgroupLabel.add_widget(label)
		###
		pack(self, gtk.Label(''), 1, 1)
		pack(self, gtk.Label(_('position')))
		###
		spin = FloatSpinButton(-99, 99, 1)
		self.spinX = spin
		pack(self, spin)
		###
		spin = FloatSpinButton(-99, 99, 1)
		self.spinY = spin
		pack(self, spin)
		####
		pack(self, gtk.Label(''), 1, 1)
		###
		fontb = MyFontButton(cal)
		self.fontb = fontb
		pack(self, fontb)
		sgroupFont.add_widget(fontb)
		####
		colorb = MyColorButton()
		self.colorb = colorb
		pack(self, colorb)
		####
		self.set(params)
		####
		self.spinX.connect('changed', self.onChange)
		self.spinY.connect('changed', self.onChange)
		fontb.connect('font-set', self.onChange)
		colorb.connect('color-set', self.onChange)

	def get(self):
		return {
			'pos': (
				self.spinX.get_value(),
				self.spinY.get_value(),
			),
			'font': self.fontb.get_font_name(),
			'color': self.colorb.get_color(),
		}

	def set(self, data):
		self.spinX.set_value(data['pos'][0])
		self.spinY.set_value(data['pos'][1])
		self.fontb.set_font_name(data['font'])
		self.colorb.set_color(data['color'])

	def onChange(self, obj=None, event=None):
		ui.mcalTypeParams[self.index] = self.get()
		self.cal.queue_draw()


@registerSignals
class CalObj(gtk.DrawingArea, CalBase):
	_name = 'monthCal'
	desc = _('Month Calendar')
	cx = [0, 0, 0, 0, 0, 0, 0]
	myKeys = CalBase.myKeys + (
		'up', 'down',
		'right', 'left',
		'page_up',
		'k', 'p',
		'page_down',
		'j', 'n',
		'end',
		'f10', 'm',
	)

	def heightSpinChanged(self, spin):
		v = spin.get_value()
		self.set_property('height-request', v)
		ui.mcalHeight = v

	def leftMarginSpinChanged(self, spin):
		ui.mcalLeftMargin = spin.get_value()
		self.queue_draw()

	def topMarginSpinChanged(self, spin):
		ui.mcalTopMargin = spin.get_value()
		self.queue_draw()

	def updateTypeParamsWidget(self):
		try:
			vbox = self.typeParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		###
		n = len(calTypes.active)
		while len(ui.mcalTypeParams) < n:
			ui.mcalTypeParams.append({
				'pos': (0, 0),
				'font': ui.getFont(0.6),
				'color': ui.textColor,
			})
		sgroupLabel = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		for i, mode in enumerate(calTypes.active):
			#try:
			params = ui.mcalTypeParams[i]
			#except IndexError:
			##
			hbox = MonthCalTypeParamBox(
				self,
				i,
				mode,
				params,
				sgroupLabel,
				sgroupFont,
			)
			pack(vbox, hbox)
		###
		vbox.show_all()

	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.set_property('height-request', ui.mcalHeight)
		######################
		#self.kTime = 0
		######################
		self.connect('draw', self.drawAll)
		self.connect('button-press-event', self.buttonPress)
		#self.connect('screen-changed', self.screenChanged)
		self.connect('scroll-event', self.scroll)
		######################
		#self.updateTextWidth()

	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		from scal3.ui_gtk.pref_utils import CheckPrefItem, ColorPrefItem
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.VBox()
		####
		hbox = gtk.HBox()
		spin = IntSpinButton(1, 9999)
		spin.set_value(ui.mcalHeight)
		spin.connect('changed', self.heightSpinChanged)
		pack(hbox, gtk.Label(_('Height')))
		pack(hbox, spin)
		pack(self.optionsWidget, hbox)
		####
		hbox = gtk.HBox(spacing=3)
		##
		pack(hbox, gtk.Label(_('Left Margin')))
		spin = IntSpinButton(0, 99)
		spin.set_value(ui.mcalLeftMargin)
		spin.connect('changed', self.leftMarginSpinChanged)
		pack(hbox, spin)
		##
		pack(hbox, gtk.Label(_('Top')))
		spin = IntSpinButton(0, 99)
		spin.set_value(ui.mcalTopMargin)
		spin.connect('changed', self.topMarginSpinChanged)
		pack(hbox, spin)
		##
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.optionsWidget, hbox)
		########
		hbox = gtk.HBox(spacing=3)
		####
		item = CheckPrefItem(ui, 'mcalGrid', _('Grid'))
		item.updateWidget()
		gridCheck = item._widget
		pack(hbox, gridCheck)
		gridCheck.item = item
		####
		colorItem = ColorPrefItem(ui, 'mcalGridColor', True)
		colorItem.updateWidget()
		pack(hbox, colorItem._widget)
		gridCheck.colorb = colorItem._widget
		gridCheck.connect('clicked', self.gridCheckClicked)
		colorItem._widget.item = colorItem
		colorItem._widget.connect('color-set', self.gridColorChanged)
		colorItem._widget.set_sensitive(ui.mcalGrid)
		####
		pack(self.optionsWidget, hbox)
		########
		frame = gtk.Frame()
		frame.set_label(_('Calendars'))
		self.typeParamsVbox = gtk.VBox()
		frame.add(self.typeParamsVbox)
		frame.show_all()
		pack(self.optionsWidget, frame)
		self.optionsWidget.show_all()
		self.updateTypeParamsWidget()## FIXME

	def drawAll(self, widget=None, cr=None, cursor=True):
		#gevent = gtk.get_current_event()
		#?????? Must enhance (only draw few cells, not all cells)
		self.calcCoord()
		w = self.get_allocation().width
		h = self.get_allocation().height
		if not cr:
			cr = self.get_window().cairo_create()
			#cr.set_line_width(0)#??????????????
			#cr.scale(0.5, 0.5)
		wx = ui.winX
		wy = ui.winY
		#if ui.bgUseDesk: # FIXME: should be re-implemented
		#	from scal3.ui_gtk import desktop
		#	from scal3.ui_gtk import wallpaper
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		status = getCurrentMonthStatus()
		#################################### Drawing Border
		if ui.mcalTopMargin > 0:
			##### Drawing border top background
			##menuBgColor == borderColor ##???????????????
			cr.rectangle(0, 0, w, ui.mcalTopMargin)
			fillColor(cr, ui.borderColor)
			######## Drawing weekDays names
			setColor(cr, ui.borderTextColor)
			dx = 0
			wdayAb = (self.wdaysWidth > w)
			for i in range(7):
				wday = newTextLayout(self, core.getWeekDayAuto(i, wdayAb))
				try:
					fontw, fonth = wday.get_pixel_size()
				except:
					myRaise(__file__)
					fontw, fonth = wday.get_pixel_size()
				cr.move_to(
					self.cx[i] - fontw / 2,
					(ui.mcalTopMargin - fonth) / 2 - 1,
				)
				show_layout(cr, wday)
			######## Drawing "Menu" label
			setColor(cr, ui.menuTextColor)
			text = newTextLayout(self, _('Menu'))
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
			##### Drawing border left background
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
			##### Drawing week numbers
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
			tx, ty = ui.todayCell.monthPos ## today x and y
			x0 = self.cx[tx] - self.dx / 2
			y0 = self.cy[ty] - self.dy / 2
			cr.rectangle(x0, y0, self.dx, self.dy)
			fillColor(cr, ui.todayCellColor)
		for yPos in range(6):
			for xPos in range(7):
				c = status[yPos][xPos]
				x0 = self.cx[xPos]
				y0 = self.cy[yPos]
				cellInactive = (c.month != ui.cell.month)
				cellHasCursor = (cursor and (xPos, yPos) == selectedCellPos)
				if cellHasCursor:
					##### Drawing Cursor
					cx0 = x0 - self.dx / 2 + 1
					cy0 = y0 - self.dy / 2 + 1
					cw = self.dx - 1
					ch = self.dy - 1
					######### Circular Rounded
					drawCursorBg(cr, cx0, cy0, cw, ch)
					fillColor(cr, ui.cursorBgColor)
				######## end of Drawing Cursor
				if not cellInactive:
					iconList = c.getMonthEventIcons()
					if iconList:
						iconsN = len(iconList)
						scaleFact = 1 / sqrt(iconsN)
						fromRight = 0
						for index, icon in enumerate(iconList):
							## if len(iconList) > 1 ## FIXME
							try:
								pix = GdkPixbuf.Pixbuf.new_from_file(icon)
							except:
								myRaise(__file__)
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
				#### Drawing numbers inside every cell
				#cr.rectangle(
				#	x0-self.dx / 2+1,
				#	y0-self.dy / 2+1,
				#	self.dx-1,
				#	self.dy-1,
				#)
				mode = calTypes.primary
				params = ui.mcalTypeParams[0]
				daynum = newTextLayout(
					self,
					_(c.dates[mode][2], mode),
					params['font'],
				)
				fontw, fonth = daynum.get_pixel_size()
				if cellInactive:
					setColor(cr, ui.inactiveColor)
				elif c.holiday:
					setColor(cr, ui.holidayColor)
				else:
					setColor(cr, params['color'])
				cr.move_to(
					x0 - fontw / 2 + params['pos'][0],
					y0 - fonth / 2 + params['pos'][1],
				)
				show_layout(cr, daynum)
				if not cellInactive:
					for mode, params in ui.getActiveMonthCalParams()[1:]:
						daynum = newTextLayout(
							self,
							_(c.dates[mode][2], mode),
							params['font'],
						)
						fontw, fonth = daynum.get_pixel_size()
						setColor(cr, params['color'])
						cr.move_to(
							x0 - fontw / 2 + params['pos'][0],
							y0 - fonth / 2 + params['pos'][1],
						)
						show_layout(cr, daynum)
					if cellHasCursor:
						##### Drawing Cursor Outline
						cx0 = x0 - self.dx / 2 + 1
						cy0 = y0 - self.dy / 2 + 1
						cw = self.dx - 1
						ch = self.dy - 1
						######### Circular Rounded
						drawCursorOutline(cr, cx0, cy0, cw, ch)
						fillColor(cr, ui.cursorOutColor)
						##### end of Drawing Cursor Outline
		################ end of drawing cells
		##### drawGrid
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
		wm = 0 ## max width
		for i in range(7):
			lay.set_markup(core.weekDayName[i])
			w = lay.get_pixel_size()[0] ## ????????
			#w = lay.get_pixel_extents()[0] ## ????????
			#print(w,)
			if w > wm:
				wm = w
		self.wdaysWidth = wm * 7 + ui.mcalLeftMargin
		#self.wdaysWidth = wm * 7 * 0.7 + ui.mcalLeftMargin
		#print('max =', wm, '     wdaysWidth =', self.wdaysWidth)

	def buttonPress(self, obj, gevent):
		## self.winActivate() #?????????
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
			self.emit('popup-main-menu', gevent.time, gevent.x, gevent.y)
		elif yPos >= 0 and xPos >= 0:
			cell = status[yPos][xPos]
			self.changeDate(*cell.dates[calTypes.primary])
			if gevent.type == TWO_BUTTON_PRESS:
				self.emit('2button-press')
			if b == 3 and cell.month == ui.cell.month:## right click on a normal cell
				#self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
				self.emit('popup-cell-menu', gevent.time, gevent.x, gevent.y)
		return True

	def calcCoord(self):## calculates coordidates (x and y of cells centers)
		w = self.get_allocation().width
		h = self.get_allocation().height
		if rtl:
			self.cx = [
				(w - ui.mcalLeftMargin) * (13 - 2 * i) / 14
				for i in range(7)
			] ## centers x
		else:
			self.cx = [
				ui.mcalLeftMargin + (
					(w - ui.mcalLeftMargin)
					* (1 + 2 * i)
					/ 14
				)
				for i in range(7)
			] ## centers x
		self.cy = [
			ui.mcalTopMargin + (h - ui.mcalTopMargin) * (1 + 2 * i) / 12
			for i in range(6)
		] ## centers y
		self.dx = (w - ui.mcalLeftMargin) / 7  # delta x
		self.dy = (h - ui.mcalTopMargin) / 6  # delta y

	def monthPlus(self, p):
		ui.monthPlus(p)
		self.onDateChange()

	def keyPress(self, arg, gevent):
		#print('keyPress')
		if CalBase.keyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		#print('keyPress', kname)
		#if kname.startswith('alt'):
		#	return True
		## How to disable Alt+Space of metacity ?????????????????????
		if kname == 'up':
			self.jdPlus(-7)
		elif kname == 'down':
			self.jdPlus(7)
		elif kname == 'right':
			if rtl:
				self.jdPlus(-1)
			else:
				self.jdPlus(1)
		elif kname == 'left':
			if rtl:
				self.jdPlus(1)
			else:
				self.jdPlus(-1)
		elif kname == 'end':
			self.changeDate(
				ui.cell.year,
				ui.cell.month,
				core.getMonthLen(ui.cell.year, ui.cell.month, calTypes.primary),
			)
		elif kname in ('page_up', 'k', 'p'):
			self.monthPlus(-1)
		elif kname in ('page_down', 'j', 'n'):
			self.monthPlus(1)
		elif kname in ('f10', 'm'):
			if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
			else:
				self.emit('popup-main-menu', gevent.time, *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, widget, gevent):
		d = getScrollValue(gevent)
		if d == 'up':
			self.jdPlus(-7)
		elif d == 'down':
			self.jdPlus(7)
		else:
			return False

	def getCellPos(self, *args):
		return (
			int(self.cx[ui.cell.monthPos[0]]),
			int(self.cy[ui.cell.monthPos[1]] + self.dy / 2),
		)

	def getMainMenuPos(self, *args):## FIXME
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


if __name__ == '__main__':
	win = gtk.Dialog(parent=None)
	cal = CalObj()
	win.add_events(gdk.EventMask.ALL_EVENTS_MASK)
	pack(win.vbox, cal, 1, 1)
	win.vbox.show_all()
	win.resize(600, 400)
	win.set_title(cal.desc)
	win.run()
