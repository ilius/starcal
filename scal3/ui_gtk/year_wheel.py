#!/usr/bin/python
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

import sys

import math
from math import pi, sin, cos

from scal3.cal_types import calTypes, to_jd, jd_to
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import getMonthName
from scal3.season import getSpringJdAfter

from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.drawing import *
from scal3.ui_gtk import gtk_ud as ud


@registerSignals
class YearWheel(gtk.DrawingArea, ud.BaseCalObj):
	_name = "yearWheel"
	desc = _("Year Wheel")
	###
	scrollRotateDegree = 1
	###
	bgColor = (0, 0, 0, 255)
	wheelBgColor = (255, 255, 255, 30)
	lineColor = (255, 255, 255, 50)
	yearStartLineColor = (255, 255, 0, 255)
	lineWidth = 2.0
	textColor = (255, 255, 255, 255)
	innerCircleRatio = 0.6
	###
	todayIndicatorEnable = True
	todayIndicatorColor = (255, 0, 0, 255)
	todayIndicatorWidth = 0.5
	###
	centerR = 3
	centerColor = (255, 0, 0, 255)
	###
	springColor = (0, 255, 0, 15)
	summerColor = (255, 0, 0, 15)
	autumnColor = (255, 255, 0, 15)
	winterColor = (0, 0, 255, 15)
	###

	def __init__(self, closeFunc):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		###
		self.closeFunc = closeFunc
		self.angleOffset = 0.0
		###
		#self.closeFunc = closeFunc
		self.connect("draw", self.onDraw)
		self.connect("scroll-event", self.onScroll)
		self.connect("button-press-event", self.onButtonPress)
		#self.connect("motion-notify-event", self.onMotionNotify)
		#self.connect("button-release-event", self.onButtonRelease)
		self.connect("key-press-event", self.keyPress)
		#self.connect("event", show_event)

		self.buttons = [
			Button("home.png", self.homeClicked, 1, -1, False),
			Button("resize-small.png", self.startResize, -1, -1, False),
			Button("exit.png", closeFunc, -1, 1, False)
		]

	def homeClicked(self, arg=None):
		self.angleOffset = 0.0
		self.queue_draw()

	def startResize(self, gevent):
		self.get_parent().begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def onDraw(self, widget=None, event=None):
		cr = self.get_window().cairo_create()
		width = float(self.get_allocation().width)
		height = float(self.get_allocation().height)
		dia = min(width, height)
		maxR = float(dia) / 2
		minR = self.innerCircleRatio * maxR
		x0 = (width - dia) / 2
		y0 = (height - dia) / 2
		cx = x0 + maxR
		cy = y0 + maxR
		####
		#self.angleOffset
		#self.bgColor
		#self.wheelBgColor
		#self.lineColor
		#self.lineWidth
		#self.textColor
		####
		cr.rectangle(0, 0, width, height)
		fillColor(cr, self.bgColor)
		####
		calsN = len(calTypes.active)
		deltaR = (maxR - minR) / float(calsN)
		mode0 = calTypes.active[0]
		jd0 = to_jd(ui.todayCell.year, 1, 1, mode0)
		yearLen = calTypes.primaryModule().avgYearLen
		angle0 = self.angleOffset * pi / 180 - pi / 2
		avgDeltaAngle = 2 * pi / 12
		####
		if self.todayIndicatorEnable:
			drawLineLengthAngle(
				cr,
				cx,
				cy,
				maxR,  # FIXME
				angle0 + 2 * pi * (ui.todayCell.jd - jd0) / yearLen,
				self.todayIndicatorWidth,
			)
			fillColor(cr, self.todayIndicatorColor)
		####
		drawCircle(cr, cx, cy, self.centerR)
		fillColor(cr, self.centerColor)
		####
		drawCircleOutline(
			cr,
			cx,
			cy,
			maxR,
			maxR - minR,
		)
		fillColor(cr, self.wheelBgColor)
		####
		spinngJd = getSpringJdAfter(jd0)
		springAngle = angle0 + 2 * pi * (spinngJd - jd0) / yearLen  # radians
		for index, color in enumerate((
			self.springColor,
			self.summerColor,
			self.autumnColor,
			self.winterColor,
		)):
			drawArcOutline(
				cr,
				cx,
				cy,
				maxR,
				maxR - minR,
				springAngle + index * pi / 2,
				springAngle + (index + 1) * pi / 2,
			)
			fillColor(cr, color)
		####
		for index, mode in enumerate(calTypes.active):
			dr = index * deltaR
			r = maxR - dr
			cx0 = x0 + dr
			cy0 = y0 + dr
			###
			drawCircleOutline(cr, cx, cy, r, self.lineWidth)
			fillColor(cr, self.lineColor)
			####
			year0, month0, day0 = jd_to(jd0, mode)
			ym0 = year0 * 12 + (month0 - 1)
			cr.set_line_width(self.lineWidth)
			for ym in range(ym0, ym0 + 12):
				year, month = divmod(ym, 12); month += 1
				jd = to_jd(year, month, 1, mode)
				angle = angle0 + 2 * pi * (jd - jd0) / yearLen  # radians
				#angleD = angle * 180 / pi
				d = self.lineWidth
				sepX, sepY = goAngle(
					cx,
					cy,
					angle,
					r - d * 0.2,  # FIXME
				)
				drawLineLengthAngle(
					cr,
					sepX,
					sepY,
					deltaR - d * 0.2,  # FIXME
					angle + pi,
					d,
				)
				fillColor(
					cr,
					self.yearStartLineColor if month == 1 else self.lineColor,
				)
				###
				layoutMaxW = (r - deltaR) * 2.0 * pi / 12.0
				layoutMaxH = deltaR
				layout = newTextLayout(
					self,
					text=getMonthName(mode, month, year),
					maxSize=(layoutMaxW, layoutMaxH),
					maximizeScale=0.6,
					truncate=False,
				)
				layoutW, layoutH = layout.get_pixel_size()
				centerAngle = angle + avgDeltaAngle / 2
				lx, ly = goAngle(
					cx,
					cy,
					centerAngle,
					(r - deltaR / 3),
				)
				lx, ly = goAngle(
					lx,
					ly,
					angle - pi / 2,
					layoutW / 2,
				)
				lx, ly = goAngle(
					lx,
					ly,
					angle,
					layoutH / 2,
				)
				cr.move_to(
					lx,
					ly,
				)
				#cr.save()
				rotateAngle = centerAngle + pi / 2
				cr.rotate(rotateAngle)
				setColor(cr, self.textColor); show_layout(cr, layout)
				cr.rotate(-rotateAngle)
				#cr.restore()

				if month == 1:
					layout = newTextLayout(
						self,
						text=_(year),
						maxSize=(
							deltaR * 0.50,
							deltaR * 0.25,
						),
						maximizeScale=1.0,
						truncate=False,
					)
					yearX, yearY = goAngle(
						cx,
						cy,
						angle + 0.02 * pi / 12,
						r - deltaR * 0.75,  # FIXME
					)
					cr.move_to(
						yearX,
						yearY,
					)
					rotateAngle = centerAngle - pi / 12
					cr.rotate(rotateAngle)
					setColor(cr, self.yearStartLineColor); show_layout(cr, layout)
					cr.rotate(-rotateAngle)
			#####
			drawCircleOutline(cr, cx, cy, minR, self.lineWidth)
			fillColor(cr, self.lineColor)
			###
		######
		for button in self.buttons:
			button.draw(cr, width, height)

	def onScroll(self, widget, gevent):
		d = getScrollValue(gevent)
		#print("onScroll", d)
		self.angleOffset += (-1 if d == "up" else 1) * self.scrollRotateDegree
		self.queue_draw()
		return True

	def keyPress(self, arg, gevent):
		k = gdk.keyval_name(gevent.keyval).lower()
		#print("%.3f"%now())
		if k in ("space", "home"):
			self.homeClicked()
		#elif k=="right":
		#	pass
		#elif k=="left":
		#	pass
		#elif k=="down":
		#	self.stopMovingAnim()
		elif k in ("q", "escape"):
			self.closeFunc()
		#elif k in ("plus", "equal", "kp_add"):
		#	self.keyboardZoom(True)
		#elif k in ("minus", "kp_subtract"):
		#	self.keyboardZoom(False)
		else:
			#print(k)
			return False
		self.queue_draw()
		return True

	def onButtonPress(self, obj, gevent):
		x = gevent.x
		y = gevent.y
		w = self.get_allocation().width
		h = self.get_allocation().height
		if gevent.button == 1:
			for button in self.buttons:
				if button.contains(x, y, w, h):
					button.func(gevent)
					return True
			#self.begin_move_drag(
			#	gevent.button,
			#	int(gevent.x_root),
			#	int(gevent.y_root),
			#	gevent.time,
			#)
			#return True
		#elif gevent.button==3:
		#	pass
		return False


@registerSignals
class YearWheelWindow(gtk.Window, ud.BaseCalObj):
	_name = "yearWheelWin"
	desc = _("Year Wheel")

	def __init__(self):
		gtk.Window.__init__(self)
		self.initVars()
		ud.windowList.appendItem(self)
		###
		size = min(ud.screenW, ud.screenH) * 0.9
		self.resize(size, size)
		self.move(
			(ud.screenW - size) / 2,
			(ud.screenH - size) / 2,
		)
		self.set_title(self.desc)
		self.set_decorated(False)
		self.connect("delete-event", self.closeClicked)
		self.connect("button-press-event", self.onButtonPress)
		###
		self._widget = YearWheel(self.closeClicked)
		self.connect("key-press-event", self._widget.keyPress)
		self.add(self._widget)
		self._widget.show()
		self.appendItem(self._widget)

	def closeClicked(self, arg=None, event=None):
		if ui.mainWin:
			self.hide()
		else:
			self.destroy()
			core.stopRunningThreads()
			gtk.main_quit()
		return True

	def onButtonPress(self, obj, gevent):
		if gevent.button == 1:
			self.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
			return True
		return False


if __name__ == "__main__":
	#locale_man.langActive = ""
	#_ = locale_man.loadTranslator()
	ui.init()
	win = YearWheelWindow()
	win.show()
	gtk.main()
