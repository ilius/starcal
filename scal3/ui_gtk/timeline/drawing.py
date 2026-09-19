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

from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import logger

log = logger.get()

from scal3 import ui
from scal3.locale_man import localTz
from scal3.time_utils import (
	getJdFromEpoch,
	getUtcOffsetByEpoch,
	getUtcOffsetByJd,
)
from scal3.timeline import conf
from scal3.timeline.utils import dayLen, fontFamily
from scal3.ui_gtk.drawing import (
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.timeline.box import (
	drawBoxBG,
	drawBoxBorder,
	drawBoxText,
)

if TYPE_CHECKING:
	from scal3.timeline.box import Box
	from scal3.timeline.tick import Tick
	from scal3.ui_gtk.drawing import ImageContext
	from scal3.ui_gtk.timeline.widget import TimeLine

__all__ = ["TimeLineDrawing"]


class TimeLineDrawing:
	"""Drawing routines for the timeline widget."""

	def __init__(self, tline: TimeLine) -> None:
		self.tline = tline

	def drawTick(self, cr: ImageContext, tick: Tick, maxTickHeight: float) -> None:
		tickH = tick.height
		tickW = tick.width
		tickH = min(tickH, maxTickHeight)
		# ---
		tickX = tick.pos - tickW / 2.0
		tickY = 1
		cr.rectangle(tickX, tickY, tickW, tickH)
		color = tick.color or conf.fgColor.v
		assert color is not None
		fillColor(cr, color)
		# fillColor never seems to raise exception anymore (in Gtk3)
		# ---
		font = ui.Font(family=fontFamily, size=tick.fontSize)
		# layout = newLimitedWidthTextLayout(
		# 	self,
		# 	tick.label,
		# 	tick.maxLabelWidth,
		# 	font=font,
		# 	truncate=truncateTickLabel,
		# )  # FIXME
		layout = newTextLayout(
			self.tline.getWidget(),
			text=tick.label,
			font=font,
			maxSize=(tick.maxLabelWidth, 0),
			maximizeScale=1.0,
			truncate=conf.truncateTickLabel.v,
		)  # FIXME
		if layout:
			# layout.set_auto_dir(0)  # FIXME
			# log.debug(f"{layout.get_auto_dir() = }")
			layoutW, _layoutH = layout.get_pixel_size()
			layoutX = tick.pos - layoutW / 2.0
			layoutY = tickH * conf.labelYRatio.v
			cr.move_to(layoutX, layoutY)
			# cr.move_to never seems to raise exception anymore
			show_layout(cr, layout)  # with the same tick.color

	def drawBox(self, cr: ImageContext, box: Box) -> None:
		x = box.x
		w = box.w
		y = box.y
		h = box.h
		# ---
		drawBoxBG(cr, box, x, y, w, h)
		drawBoxBorder(cr, box, x, y, w, h)
		drawBoxText(cr, box, x, y, w, h, self.tline.getWidget())

	def drawBoxEditingHelperLines(self, cr: ImageContext) -> None:
		boxEditing = self.tline.getBoxEditing()
		if not boxEditing:
			return
		assert conf.fgColor.v is not None
		_editType, _event, box, _x0, _t0 = boxEditing
		setColor(cr, conf.fgColor.v)
		d = conf.boxEditHelperLineWidth.v
		cr.rectangle(
			box.x,
			0,
			d,
			box.y,
		)
		cr.fill()
		cr.rectangle(
			box.x + box.w - d,
			0,
			d,
			box.y,
		)
		cr.fill()

	def drawAll(self, cr: ImageContext) -> None:
		assert conf.bgColor.v is not None
		data = self.tline.getData()
		assert data is not None
		tline = self.tline
		timeStart = tline.getTimeStart()
		timeWidth = tline.getTimeWidth()
		timeEnd = timeStart + timeWidth
		# ----
		alloc = tline.getWidget().get_allocation()
		width = alloc.width
		height = alloc.height
		pixelPerSec = tline.getPixelPerSec()
		dayPixel = dayLen * pixelPerSec  # pixel
		maxTickHeight = conf.maxTickHeightRatio.v * height
		# -----
		cr.rectangle(0, 0, width, height)
		fillColor(cr, conf.bgColor.v)
		# -----
		setColor(cr, conf.holidayBgBolor.v)
		for x in data.holidays:
			cr.rectangle(x, 0, dayPixel, height)
			cr.fill()
		# -----
		for tick in data.ticks:
			self.drawTick(cr, tick, maxTickHeight)
		# ------
		beforeBoxH = maxTickHeight  # FIXME
		maxBoxH = height - beforeBoxH
		for box in data.boxes:
			box.setPixelValues(timeStart, pixelPerSec, beforeBoxH, maxBoxH)
			self.drawBox(cr, box)
		self.drawBoxEditingHelperLines(cr)
		# Show (possible) Daylight Saving change
		if (
			timeStart > 0
			and 2 * 3600 < timeWidth < 30 * dayLen
			and getUtcOffsetByEpoch(timeStart) != getUtcOffsetByEpoch(timeEnd)
		):
			startJd = getJdFromEpoch(timeStart)
			endJd = getJdFromEpoch(timeEnd)
			lastOffset = getUtcOffsetByJd(startJd, localTz)
			dstChangeJd = None
			deltaSec = 0
			for jd in range(startJd + 1, endJd + 1):
				offset = getUtcOffsetByJd(jd, localTz)
				deltaSec = offset - lastOffset
				if deltaSec != 0:
					dstChangeJd = jd
					break
			if dstChangeJd is not None:
				pass
				# deltaHour = deltaSec / 3600.0
				# dstChangeEpoch = getEpochFromJd(dstChangeJd)
				# log.debug(f"{dstChangeEpoch = }")
			else:
				log.info("dstChangeEpoch not found")

		# Draw Current Time Marker
		dt = tline.getCurrentTime() - timeStart
		if 0 <= dt <= timeWidth:
			setColor(cr, conf.currentTimeMarkerColor.v)
			cr.rectangle(
				dt * pixelPerSec - conf.currentTimeMarkerWidth.v / 2.0,
				0,
				conf.currentTimeMarkerWidth.v,
				conf.currentTimeMarkerHeightRatio.v * height,
			)
			cr.fill()
		# ------
		for button in tline.getButtons():
			button.draw(cr, width, height)
