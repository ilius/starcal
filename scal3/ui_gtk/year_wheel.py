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
from scal3.ui_gtk.button_drawing import Button
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
		# self.closeFunc = closeFunc
		self.connect("draw", self.onDraw)
		self.connect("scroll-event", self.onScroll)
		self.connect("button-press-event", self.onButtonPress)
		# self.connect("motion-notify-event", self.onMotionNotify)
		# self.connect("button-release-event", self.onButtonRelease)
		self.connect("key-press-event", self.onKeyPress)
		# self.connect("event", show_event)

		iconSize = 20
		self.buttons = [
			Button(
				imageName="go-home.svg",
				onPress=self.onHomeClick,
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="left",
				yalign="buttom",
			),
			Button(
				imageName="resize-small.svg",
				onPress=self.startResize,
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="right",
				yalign="buttom",
			),
			Button(
				imageName="application-exit.svg",
				onPress=closeFunc,
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="right",
				yalign="top",
			)
		]

	def onHomeClick(self, arg=None):
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
		win = self.get_window()
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr)
		finally:
			win.end_draw_frame(dctx)

	def drawWithContext(self, cr: "cairo.Context"):
		width = float(self.get_allocation().width)
		height = float(self.get_allocation().height)
		dia = min(width, height)
		maxR = dia / 2
		minR = self.innerCircleRatio * maxR
		x0 = (width - dia) / 2
		y0 = (height - dia) / 2
		cx = x0 + maxR
		cy = y0 + maxR
		####
		# self.angleOffset
		# self.bgColor
		# self.wheelBgColor
		# self.lineColor
		# self.lineWidth
		# self.textColor
		####
		cr.rectangle(0, 0, width, height)
		fillColor(cr, self.bgColor)
		####
		calsN = len(calTypes.active)
		deltaR = (maxR - minR) / calsN
		calType0 = calTypes.active[0]
		jd0 = to_jd(ui.todayCell.year, 1, 1, calType0)
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
			cx, cy,
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
				cx, cy,
				maxR,
				maxR - minR,
				springAngle + index * pi / 2,
				springAngle + (index + 1) * pi / 2,
			)
			fillColor(cr, color)

		def calcAngles(jd: int) -> Tuple[float, float]:
			angle = angle0 + 2 * pi * (jd - jd0) / yearLen  # radians
			# angleD = angle * 180 / pi
			centerAngle = angle + avgDeltaAngle / 2
			return angle, centerAngle

		####
		for index, calType in enumerate(calTypes.active):
			dr = index * deltaR
			r = maxR - dr
			cx0 = x0 + dr
			cy0 = y0 + dr
			###
			drawCircleOutline(cr, cx, cy, r, self.lineWidth)
			fillColor(cr, self.lineColor)
			####
			year0, month0, day0 = jd_to(jd0, calType)
			ym0 = year0 * 12 + (month0 - 1)
			cr.set_line_width(self.lineWidth)
			for ym in range(ym0, ym0 + 12):
				year, mm1 = divmod(ym, 12)
				month = mm1 + 1
				jd = to_jd(year, month, 1, calType)
				angle, centerAngle = calcAngles(jd)
				d = self.lineWidth
				sepX, sepY = goAngle(
					cx, cy,
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
					text=getMonthName(calType, month, year),
					maxSize=(layoutMaxW, layoutMaxH),
					maximizeScale=0.6,  # noqa: FURB120
					# truncate=False,
				)
				layoutW, layoutH = layout.get_pixel_size()
				lx, ly = goAngle(
					cx, cy,
					centerAngle,
					(r - deltaR / 3),
				)
				lx, ly = goAngle(
					lx, ly,
					angle - pi / 2,
					layoutW / 2,
				)
				lx, ly = goAngle(
					lx, ly,
					angle,
					layoutH / 2,
				)
				cr.move_to(lx, ly)
				# cr.save()
				rotateAngle = centerAngle + pi / 2
				cr.rotate(rotateAngle)
				setColor(cr, self.textColor)
				show_layout(cr, layout)
				cr.rotate(-rotateAngle)
				# cr.restore()

				if month == 1:
					t_year = ui.cell.dates[calType][0]
					self.drawYearStartLine(
						t_year, 1,
						cr, cx, cy,
						angle, centerAngle, r, deltaR,
					)
					self.drawYearStartLine(
						t_year + 1, -1,
						cr, cx, cy,
						angle, centerAngle, r, deltaR,
					)
			#####
			drawCircleOutline(cr, cx, cy, minR, self.lineWidth)
			fillColor(cr, self.lineColor)
			###

		######
		for button in self.buttons:
			button.draw(cr, width, height)

	def drawYearStartLine(self, year, direction, cr, cx, cy, angle, centerAngle, r, deltaR):
		layout = newTextLayout(
			self,
			text=_(year),
			maxSize=(
				deltaR * 0.50,
				deltaR * 0.25,
			),
			maximizeScale=1.0,
			# truncate=False,
		)
		layoutW, layoutH = layout.get_pixel_size()
		tickX, tickY = goAngle(
			cx, cy,
			angle,
			r - deltaR * 0.75,  # FIXME
		)
		layoutX, layoutY = goAngle(
			tickX, tickY,
			angle + direction * pi / 2,
			(1 - direction) * layoutH / 2.5,  # factor should be between 2 and 3
		)
		cr.move_to(layoutX, layoutY)
		rotateAngle = centerAngle - pi / 12
		cr.rotate(rotateAngle)
		setColor(cr, self.yearStartLineColor)
		show_layout(cr, layout)
		cr.rotate(-rotateAngle)

	def onScroll(self, widget, gevent):
		d = getScrollValue(gevent)
		# log.debug("onScroll", d)
		self.angleOffset += (-1 if d == "up" else 1) * self.scrollRotateDegree
		self.queue_draw()
		return True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		k = gdk.keyval_name(gevent.keyval).lower()
		# log.debug("%.3f"%now())
		if k in ("space", "home"):
			self.onHomeClick()
		# elif k=="right":
		# 	pass
		# elif k=="left":
		# 	pass
		# elif k=="down":
		# 	self.stopMovingAnim()
		elif k in ("q", "escape"):
			self.closeFunc()
		# elif k in ("plus", "equal", "kp_add"):
		# 	self.keyboardZoom(True)
		# elif k in ("minus", "kp_subtract"):
		# 	self.keyboardZoom(False)
		else:
			# log.debug(k)
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
					button.onPress(gevent)
					return True
			# self.begin_move_drag(
			# 	gevent.button,
			# 	int(gevent.x_root),
			# 	int(gevent.y_root),
			# 	gevent.time,
			# )
			# return True
		# elif gevent.button==3:
		# 	pass
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
		size = min(ud.workAreaW, ud.workAreaH) * 0.9
		self.resize(size, size)
		self.move(
			(ud.workAreaW - size) / 2,
			(ud.workAreaH - size) / 2,
		)
		self.set_title(self.desc)
		self.set_decorated(False)
		self.connect("delete-event", self.onCloseClick)
		self.connect("button-press-event", self.onButtonPress)
		###
		self._widget = YearWheel(self.onCloseClick)
		self.connect("key-press-event", self._widget.onKeyPress)
		self.add(self._widget)
		self._widget.show()
		self.appendItem(self._widget)

	def onCloseClick(self, arg=None, event=None):
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
	# locale_man.langActive = ""
	# _ = locale_man.loadTranslator()
	ui.init()
	win = YearWheelWindow()
	win.show()
	gtk.main()
