#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger
from scal3.color_utils import RGBA
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj

log = logger.get()


from math import pi
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import core, ui
from scal3.cal_types import calTypes, jd_to, to_jd
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.season import getSpringJdAfter
from scal3.ui_gtk import gdk, getScrollValue, gtk
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.button_drawing import Button
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.drawing import (
	ImageContext,
	drawArcOutline,
	drawCircle,
	drawCircleOutline,
	drawLineLengthAngle,
	fillColor,
	goAngle,
	newTextLayout,
	setColor,
)

if TYPE_CHECKING:
	from collections.abc import Callable


__all__ = ["YearWheelWindow"]


class YearWheel(CustomizableCalObj):
	objName = "yearWheel"
	desc = _("Year Wheel")
	# ---
	scrollRotateDegree = 1
	# ---
	bgColor = RGBA(0, 0, 0, 255)
	wheelBgColor = RGBA(255, 255, 255, 30)
	lineColor = RGBA(255, 255, 255, 50)
	yearStartLineColor = RGBA(255, 255, 0, 255)
	lineWidth = 2.0
	textColor = RGBA(255, 255, 255, 255)
	innerCircleRatio = 0.6
	# ---
	todayIndicatorEnable = True
	todayIndicatorColor = RGBA(255, 0, 0, 255)
	todayIndicatorWidth = 0.5
	# ---
	centerR = 3
	centerColor = RGBA(255, 0, 0, 255)
	# ---
	springColor = RGBA(0, 255, 0, 15)
	summerColor = RGBA(255, 0, 0, 15)
	autumnColor = RGBA(255, 255, 0, 15)
	winterColor = RGBA(0, 0, 255, 15)
	# ---

	def __init__(self, closeFunc: Callable[[], None]) -> None:
		super().__init__()
		self.w = gtk.DrawingArea()
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		# ---
		self.closeFunc = closeFunc
		self.angleOffset = 0.0
		# ---
		# self.closeFunc = closeFunc
		self.w.connect("draw", self.onDraw)
		self.w.connect("scroll-event", self.onScroll)
		self.w.connect("button-press-event", self.onButtonPress)
		# self.w.connect("motion-notify-event", self.onMotionNotify)
		# self.w.connect("button-release-event", self.onButtonRelease)
		self.w.connect("key-press-event", self.onKeyPress)
		# self.w.connect("event", show_event)

		iconSize = 20
		self.buttons = [
			Button(
				onPress=self.onHomeClick,
				imageName="go-home.svg",
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="left",
				yalign="buttom",
			),
			Button(
				onPress=self.startResize,
				imageName="resize-small.svg",
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="right",
				yalign="buttom",
			),
			Button(
				onPress=self.onCloseClick,
				imageName="application-exit.svg",
				x=1,
				y=1,
				autoDir=False,
				iconSize=iconSize,
				xalign="right",
				yalign="top",
			),
		]

	def onCloseClick(self, _e: gdk.EventButton) -> None:
		self.closeFunc()

	def onHomeClick(self, _e: gdk.EventButton | None = None) -> None:
		self.angleOffset = 0.0
		self.w.queue_draw()

	def startResize(self, gevent: gdk.EventButton) -> None:
		win = self.w.get_parent()
		if win is None:
			return
		assert isinstance(win, gtk.Window), f"{win=}"
		win.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def onDraw(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		win = self.w.get_window()
		if win is None:
			return
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

	def drawWithContext(self, cr: ImageContext) -> None:
		alloc = self.w.get_allocation()
		width = float(alloc.width)
		height = float(alloc.height)
		dia = min(width, height)
		maxR = dia / 2
		minR = self.innerCircleRatio * maxR
		x0 = (width - dia) / 2
		y0 = (height - dia) / 2
		cx = x0 + maxR
		cy = y0 + maxR
		# ----
		# self.angleOffset
		# self.bgColor
		# self.wheelBgColor
		# self.lineColor
		# self.lineWidth
		# self.textColor
		# ----
		cr.rectangle(0, 0, width, height)
		fillColor(cr, self.bgColor)
		# ----
		calsN = len(calTypes.active)
		deltaR = (maxR - minR) / calsN
		calType0 = calTypes.active[0]
		jd0 = to_jd(ui.cells.today.year, 1, 1, calType0)
		yearLen = calTypes.primaryModule().avgYearLen
		angle0 = self.angleOffset * pi / 180 - pi / 2
		avgDeltaAngle = 2 * pi / 12
		# ----
		if self.todayIndicatorEnable:
			drawLineLengthAngle(
				cr,
				cx,
				cy,
				maxR,  # FIXME
				angle0 + 2 * pi * (ui.cells.today.jd - jd0) / yearLen,
				self.todayIndicatorWidth,
			)
			fillColor(cr, self.todayIndicatorColor)
		# ----
		drawCircle(cr, cx, cy, self.centerR)
		fillColor(cr, self.centerColor)
		# ----
		drawCircleOutline(
			cr,
			cx,
			cy,
			maxR,
			maxR - minR,
		)
		fillColor(cr, self.wheelBgColor)
		# ----
		spinngJd = getSpringJdAfter(jd0)
		springAngle = angle0 + 2 * pi * (spinngJd - jd0) / yearLen  # radians
		for index, color in enumerate(
			(
				self.springColor,
				self.summerColor,
				self.autumnColor,
				self.winterColor,
			),
		):
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

		def calcAngles(jd: int) -> tuple[float, float]:
			angle = angle0 + 2 * pi * (jd - jd0) / yearLen  # radians
			# angleD = angle * 180 / pi
			centerAngle = angle + avgDeltaAngle / 2
			return angle, centerAngle

		# ----
		for index, calType in enumerate(calTypes.active):
			dr = index * deltaR
			r = maxR - dr
			# ---
			drawCircleOutline(cr, cx, cy, r, self.lineWidth)
			fillColor(cr, self.lineColor)
			# ----
			year0, month0, _day0 = jd_to(jd0, calType)
			ym0 = year0 * 12 + (month0 - 1)
			cr.set_line_width(self.lineWidth)
			for ym in range(ym0, ym0 + 12):
				year, mm1 = divmod(ym, 12)
				month = mm1 + 1
				jd = to_jd(year, month, 1, calType)
				angle, centerAngle = calcAngles(jd)
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
				# ---
				layoutMaxW = (r - deltaR) * 2.0 * pi / 12.0
				layoutMaxH = deltaR
				layout = newTextLayout(
					self.w,
					text=getMonthName(calType, month, year),
					maxSize=(layoutMaxW, layoutMaxH),
					maximizeScale=0.6,
					# truncate=False,
				)
				assert layout is not None
				layoutW, layoutH = layout.get_pixel_size()
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
				cr.move_to(lx, ly)
				# cr.save()
				rotateAngle = centerAngle + pi / 2
				cr.rotate(rotateAngle)
				setColor(cr, self.textColor)
				show_layout(cr, layout)
				cr.rotate(-rotateAngle)
				# cr.restore()

				if month == 1:
					t_year = ui.cells.current.dates[calType][0]
					self.drawYearStartLine(
						t_year,
						1,
						cr,
						cx,
						cy,
						angle,
						centerAngle,
						r,
						deltaR,
					)
					self.drawYearStartLine(
						t_year + 1,
						-1,
						cr,
						cx,
						cy,
						angle,
						centerAngle,
						r,
						deltaR,
					)
			# -----
			drawCircleOutline(cr, cx, cy, minR, self.lineWidth)
			fillColor(cr, self.lineColor)
			# ---

		# ------
		for button in self.buttons:
			button.draw(cr, width, height)

	def drawYearStartLine(
		self,
		year: int,
		direction: int,
		cr: ImageContext,
		cx: float,
		cy: float,
		angle: float,
		centerAngle: float,
		r: float,
		deltaR: float,
	) -> None:
		layout = newTextLayout(
			self.w,
			text=_(year),
			maxSize=(
				deltaR * 0.50,
				deltaR * 0.25,
			),
			maximizeScale=1.0,
			# truncate=False,
		)
		assert layout is not None
		_layoutW, layoutH = layout.get_pixel_size()
		tickX, tickY = goAngle(
			cx,
			cy,
			angle,
			r - deltaR * 0.75,  # FIXME
		)
		layoutX, layoutY = goAngle(
			tickX,
			tickY,
			angle + direction * pi / 2,
			(1 - direction) * layoutH / 2.5,  # factor should be between 2 and 3
		)
		cr.move_to(layoutX, layoutY)
		rotateAngle = centerAngle - pi / 12
		cr.rotate(rotateAngle)
		setColor(cr, self.yearStartLineColor)
		show_layout(cr, layout)
		cr.rotate(-rotateAngle)

	def onScroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool:
		d = getScrollValue(gevent)
		# log.debug("onScroll", d)
		self.angleOffset += (-1 if d == "up" else 1) * self.scrollRotateDegree
		self.w.queue_draw()
		return True

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		keyName = gdk.keyval_name(gevent.keyval)
		if not keyName:
			return False
		keyName = keyName.lower()
		# log.debug("%.3f"%now())
		if keyName in {"space", "home"}:
			self.onHomeClick()
		# elif k=="right":
		# 	pass
		# elif k=="left":
		# 	pass
		# elif k=="down":
		# 	self.stopMovingAnim()
		elif keyName in {"q", "escape"}:
			self.closeFunc()
		# elif k in ("plus", "equal", "kp_add"):
		# 	self.keyboardZoom(True)
		# elif k in ("minus", "kp_subtract"):
		# 	self.keyboardZoom(False)
		else:
			# log.debug(k)
			return False
		self.w.queue_draw()
		return True

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		x = gevent.x
		y = gevent.y
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
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


class YearWheelWindow(CalObjWidget):
	objName = "yearWheelWin"
	desc = _("Year Wheel")

	def __init__(self) -> None:
		self.w: gtk.Window = gtk.Window()
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		size = int(min(ud.workAreaW, ud.workAreaH) * 0.9)
		self.w.resize(size, size)
		self.w.move(
			int((ud.workAreaW - size) / 2),
			int((ud.workAreaH - size) / 2),
		)
		self.w.set_title(self.desc)
		self.w.set_decorated(False)
		self.w.connect("delete-event", self.onDeleteEvent)
		self.w.connect("button-press-event", self.onButtonPress)
		# ---
		self._widget = yearWheel = YearWheel(self.onCloseClick)
		self.w.connect("key-press-event", yearWheel.onKeyPress)
		self.w.add(yearWheel.w)
		yearWheel.show()
		self.appendItem(yearWheel)

	def onDeleteEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		self.onCloseClick()
		return True

	def onCloseClick(self) -> None:
		if ui.mainWin:
			self.hide()
		else:
			self.w.destroy()
			core.stopRunningThreads()
			gtk.main_quit()

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 1:
			self.w.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
			return True
		return False


if __name__ == "__main__":
	from scal3.cell import init as initCell

	# locale_man.langActive = ""
	# _ = locale_man.loadTranslator()
	ui.init()
	initCell()
	win = YearWheelWindow()
	win.show()
	gtk.main()
