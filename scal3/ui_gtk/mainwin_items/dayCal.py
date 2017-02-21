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


class DayCalTypeParamBox(gtk.HBox):
	def __init__(self, cal, index, mode, params, sgroupLabel, sgroupFont):
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
		from scal3.ui_gtk.mywidgets import MyFontButton, MyColorButton
		gtk.HBox.__init__(self)
		self.cal = cal
		self.index = index
		self.mode = mode
		######
		label = gtk.Label(_(calTypes[mode].desc) + "  ")
		label.set_alignment(0, 0.5)
		pack(self, label)
		sgroupLabel.add_widget(label)
		###
		pack(self, gtk.Label(""), 1, 1)
		pack(self, gtk.Label(_("position")))
		###
		spin = FloatSpinButton(-999, 999, 1)
		self.spinX = spin
		pack(self, spin)
		###
		spin = FloatSpinButton(-999, 999, 1)
		self.spinY = spin
		pack(self, spin)
		####
		pack(self, gtk.Label(""), 1, 1)
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
		self.spinX.connect("changed", self.onChange)
		self.spinY.connect("changed", self.onChange)
		fontb.connect("font-set", self.onChange)
		colorb.connect("color-set", self.onChange)

	def get(self):
		return {
			"pos": (self.spinX.get_value(), self.spinY.get_value()),
			"font": self.fontb.get_font_name(),
			"color": self.colorb.get_color()
		}

	def set(self, data):
		self.spinX.set_value(data["pos"][0])
		self.spinY.set_value(data["pos"][1])
		self.fontb.set_font_name(data["font"])
		self.colorb.set_color(data["color"])

	def onChange(self, obj=None, event=None):
		ui.dcalTypeParams[self.index] = self.get()
		self.cal.queue_draw()


@registerSignals
class CalObj(gtk.DrawingArea, CalBase):
	_name = "dayCal"
	desc = _("Day Calendar")
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

	def heightSpinChanged(self, spin):
		v = spin.get_value()
		self.set_property("height-request", v)
		ui.dcalHeight = v

	def updateTypeParamsWidget(self):
		try:
			vbox = self.typeParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		###
		n = len(calTypes.active)
		while len(ui.dcalTypeParams) < n:
			ui.dcalTypeParams.append({
				"pos": (0, 0),
				"font": ui.getFont(3.0),
				"color": ui.textColor,
			})
		sgroupLabel = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		for i, mode in enumerate(calTypes.active):
			#try:
			params = ui.dcalTypeParams[i]
			#except IndexError:
			##
			hbox = DayCalTypeParamBox(self, i, mode, params, sgroupLabel, sgroupFont)
			pack(vbox, hbox)
		###
		vbox.show_all()

	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.set_property("height-request", ui.dcalHeight)
		######################
		#self.kTime = 0
		######################
		self.connect("draw", self.drawAll)
		self.connect("button-press-event", self.buttonPress)
		#self.connect("screen-changed", self.screenChanged)
		self.connect("scroll-event", self.scroll)

	def optionsWidgetCreate(self):
		from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
		from scal3.ui_gtk.pref_utils import CheckPrefItem, ColorPrefItem
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.VBox()
		####
		hbox = gtk.HBox()
		spin = IntSpinButton(1, 9999)
		spin.set_value(ui.dcalHeight)
		spin.connect("changed", self.heightSpinChanged)
		pack(hbox, gtk.Label(_("Height")))
		pack(hbox, spin)
		pack(self.optionsWidget, hbox)
		########
		frame = gtk.Frame()
		frame.set_label(_("Calendars"))
		self.typeParamsVbox = gtk.VBox()
		frame.add(self.typeParamsVbox)
		frame.show_all()
		pack(self.optionsWidget, frame)
		self.optionsWidget.show_all()
		self.updateTypeParamsWidget()## FIXME

	def drawAll(self, widget=None, cr=None, cursor=True):
		#gevent = gtk.get_current_event()
		w = self.get_allocation().width
		h = self.get_allocation().height
		if not cr:
			cr = self.get_window().cairo_create()
			#cr.set_line_width(0)#??????????????
			#cr.scale(0.5, 0.5)
		cr.rectangle(0, 0, w, h)
		fillColor(cr, ui.bgColor)
		#####
		c = ui.cell
		x0 = 0
		y0 = 0
		dx = w
		dy = h
		########
		iconList = c.getDayEventIcons()
		if iconList:
			iconsN = len(iconList)
			scaleFact = 3.0 / sqrt(iconsN)
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
				## right buttom corner ?????????????????????
				x1 = (x0 + dx) / scaleFact - fromRight - pix_w # right side
				y1 = (y0 + dy / 2) / scaleFact - pix_h / 2 # middle
				cr.scale(scaleFact, scaleFact)
				gdk.cairo_set_source_pixbuf(cr, pix, x1, y1)
				cr.rectangle(x1, y1, pix_w, pix_h)
				cr.fill()
				cr.scale(1 / scaleFact, 1 / scaleFact)
				fromRight += pix_w
		#### Drawing numbers inside every cell
		#cr.rectangle(
		#	x0-dx/2.0+1,
		#	y0-self.dy/2.0+1,
		#	dx-1,
		#	dy-1,
		#)
		mode = calTypes.primary
		params = ui.dcalTypeParams[0]
		daynum = newTextLayout(
			self,
			_(c.dates[mode][2], mode),
			params["font"],
		)
		fontw, fonth = daynum.get_pixel_size()
		if c.holiday:
			setColor(cr, ui.holidayColor)
		else:
			setColor(cr, params["color"])
		cr.move_to(
			x0 + dx / 2 - fontw / 2 + params["pos"][0],
			y0 + dy / 2 - fonth / 2 + params["pos"][1],
		)
		show_layout(cr, daynum)
		####
		for mode, params in ui.getActiveDayCalParams()[1:]:
			daynum = newTextLayout(self, _(c.dates[mode][2], mode), params["font"])
			fontw, fonth = daynum.get_pixel_size()
			setColor(cr, params["color"])
			cr.move_to(
				x0 + dx / 2 - fontw / 2 + params["pos"][0],
				y0 + dy / 2 - fonth / 2 + params["pos"][1],
			)
			show_layout(cr, daynum)

	def buttonPress(self, obj, gevent):
		b = gevent.button
		#x, y, mask = col_win.get_pointer()
		x, y = self.get_pointer()
		#y += 10
		###
		if gevent.type == TWO_BUTTON_PRESS:
			self.emit("2button-press")
		if b == 3:
			self.emit("popup-cell-menu", gevent.time, x, y)
		return True

	def jdPlus(self, p):
		ui.jdPlus(p)
		self.onDateChange()

	def keyPress(self, arg, gevent):
		#print("keyPress")
		if CalBase.keyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval).lower()
		#print("keyPress", kname)
		#if kname.startswith("alt"):
		#	return True
		## How to disable Alt+Space of metacity ?????????????????????
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
		self.updateTypeParamsWidget()
