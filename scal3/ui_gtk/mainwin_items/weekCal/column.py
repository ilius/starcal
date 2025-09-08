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

log = logger.get()

from typing import TYPE_CHECKING

import cairo
from gi.repository.PangoCairo import show_layout

from scal3 import ui
from scal3.font import Font
from scal3.ui import conf
from scal3.ui_gtk import gdk
from scal3.ui_gtk.drawing import (
	drawOutlineRoundedRect,
	drawRoundedRect,
	fillColor,
	newTextLayout,
	setColor,
)

from .base import ColumnBase, ColumnDrawingArea

if TYPE_CHECKING:
	from scal3.color_utils import ColorType
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.drawing import ImageContext

	from .pytypes import ColumnParent, WeekCalType

__all__ = ["Column"]


class Column(ColumnBase):
	colorizeHolidayText = False
	showCursor = False
	truncateText = False

	def __init__(self, wcal: WeekCalType) -> None:
		super().__init__()
		self.dr = ColumnDrawingArea(self.getWidth)
		self.w: gtk.Widget = self.dr
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		self.w.connect("draw", self.onExposeEvent)
		# self.w.connect("button-press-event", self.onButtonPress)
		# self.w.connect("event", show_event)
		self.wcal = wcal
		self.colParent: ColumnParent = wcal  # type: ignore[assignment]
		if self.expandOption is not None:
			expandOption = self.expandOption
			assert expandOption is not None
			self.expand = expandOption.v

	def getWidth(self) -> int:
		widthOption = self.widthOption
		if widthOption is None:
			assert self.expand, f"{self=}"
			return 0
		return int(widthOption.v)

	def onExposeEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		if ui.disableRedraw:
			return
		if self.wcal.status is None:
			self.wcal.updateStatus()
		win = self.w.get_window()
		assert win is not None
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

	def drawBg(self, cr: ImageContext) -> None:
		status = self.wcal.status
		assert status is not None
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, conf.bgColor.v)
		rowH = h / 7
		for i in range(7):
			c = status[i]
			if c.jd == ui.cells.today.jd:
				cr.rectangle(
					0,
					i * rowH,
					w,
					rowH,
				)
				fillColor(cr, conf.todayCellColor.v)
			if self.showCursor and c.jd == ui.cells.current.jd:
				self.drawCursorBg(
					cr,
					0,  # x0
					i * rowH,  # y0
					w,  # width
					rowH,  # height
				)
				fillColor(cr, conf.cursorBgColor.v)

		if conf.wcalUpperGradientEnable.v:
			for rowI in range(7):
				y0 = rowI * rowH
				height = rowH * conf.wcalUpperGradientSize.v
				y1 = y0 + height
				gradient = cairo.LinearGradient(0, y0, 0, y1)
				gc = conf.wcalUpperGradientColor.v
				gradient.add_color_stop_rgba(
					0,  # offset
					gc.red / 255,
					gc.green / 255,
					gc.blue / 255,
					gc.alpha / 255,
				)
				gradient.add_color_stop_rgba(
					height,  # offset
					0,
					0,
					0,
					0,
				)
				cr.rectangle(0, y0, w, height)
				cr.set_source(gradient)
				cr.fill()

				del gradient

		if conf.wcalGrid.v:
			setColor(cr, conf.wcalGridColor.v)
			# ---
			cr.rectangle(
				w - 1,
				0,
				1,
				h,
			)
			cr.fill()
			# ---
			for i in range(1, 7):
				cr.rectangle(
					0,
					i * rowH,
					w,
					1,
				)
				cr.fill()

	@staticmethod
	def drawCursorOutline(
		cr: ImageContext,
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	) -> None:
		cursorRadius = conf.wcalCursorRoundingFactor.v * min(cw, ch) * 0.5
		cursorLineWidth = conf.wcalCursorLineWidthFactor.v * min(cw, ch) * 0.5
		drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius, cursorLineWidth)

	@staticmethod
	def drawCursorBg(
		cr: ImageContext,
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	) -> None:
		cursorRadius = conf.wcalCursorRoundingFactor.v * min(cw, ch) * 0.5
		drawRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius)

	def drawCursorFg(self, cr: ImageContext) -> None:
		if not self.showCursor:
			return
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		rowH = h / 7
		self.drawCursorOutline(
			cr,
			0,  # x0
			self.wcal.cellIndex * rowH,  # y0
			w,  # width
			rowH,  # height
		)
		fillColor(cr, conf.cursorOutColor.v)

	def drawTextList(
		self,
		cr: ImageContext,
		textData: list[list[tuple[str, ColorType | None]]],
		font: Font | None = None,
	) -> None:
		status = self.wcal.status
		assert status is not None
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		# ---
		rowH = h / 7
		itemW = w - conf.wcalPadding.v
		if font is None:
			fontName = self.getFontFamily()
			fontSize = ui.getFont().size  # FIXME
			font = Font(family=fontName, size=fontSize) if fontName else None
		for i in range(7):
			data = textData[i]
			if data:
				linesN = len(data)
				lineH = rowH / linesN
				lineI = 0
				if len(data[0]) < 2:
					log.info(self.objName)
				for line, color_ in data:
					color = color_
					layout = newTextLayout(
						self.w,
						text=line,
						font=font,
						maxSize=(itemW, lineH),
						maximizeScale=conf.wcalTextSizeScale.v,
						truncate=self.truncateText,
					)
					if not layout:
						continue
					layoutW, layoutH = layout.get_pixel_size()
					layoutX = (w - layoutW) / 2
					layoutY = i * rowH + (lineI + 0.5) * lineH - layoutH / 2
					cr.move_to(layoutX, layoutY)
					if self.colorizeHolidayText and status[i].holiday:
						color = conf.holidayColor.v
					if not color:
						color = conf.textColor.v
					setColor(cr, color)
					show_layout(cr, layout)
					lineI += 1

	def onButtonPress(self, _w: gtk.Widget, _ge: gdk.EventButton) -> bool:  # noqa: PLR6301
		return False

	def onDateChange(self) -> None:
		super().onDateChange()
		self.w.queue_draw()

	def drawColumn(self, cr: ImageContext) -> None:
		pass
