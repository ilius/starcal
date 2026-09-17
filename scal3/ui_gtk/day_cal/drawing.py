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

from math import isqrt
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import logger

log = logger.get()

from scal3 import core
from scal3.cal_types import calTypes
from scal3.drawing import getAbsPos
from scal3.locale_man import langHasUppercase, textNumEncode
from scal3.locale_man import tr as _
from scal3.season import getSeasonNamePercentFromJd
from scal3.ui import conf
from scal3.ui.font import getOptionsFont
from scal3.ui_gtk import GLibError, gdk
from scal3.ui_gtk.drawing import (
	drawPieOutline,
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.utils import pixbufFromFile

if TYPE_CHECKING:
	from scal3.pytypes import CellType
	from scal3.ui_gtk.button_drawing import BaseButton
	from scal3.ui_gtk.day_cal.cal import DayCal
	from scal3.ui_gtk.drawing import ImageContext

__all__ = ["DayCalDrawing"]


class DayCalDrawing:
	"""Drawing routines for DayCal."""

	def __init__(self, dayCal: DayCal) -> None:
		self.dayCal = dayCal

	def drawAll(self, cr: ImageContext, cursor: bool) -> list[BaseButton]:
		return self.drawWithContext(cr, cursor)

	def drawWithContext(self, cr: ImageContext, _cursor: bool) -> list[BaseButton]:
		dayCal = self.dayCal
		widget = dayCal.getWidget()
		w = widget.get_allocation().width
		h = widget.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, dayCal.getBackgroundColor())
		# -----
		c = dayCal.getCell()
		x0 = 0
		y0 = 0
		# --------
		self.drawEventIcons(cr, c, w, h, x0, y0)
		# Drawing numbers inside every cell
		# cr.rectangle(
		# 	x0-w/2.0+1,
		# 	y0-h/2.0+1,
		# 	w-1,
		# 	h-1,
		# )
		# ----
		for calType, doptions in zip(
			calTypes.active,
			dayCal.getDayOptions(),
			strict=False,
		):
			if not doptions.get("enable", True):
				continue
			dayNum = c.dates[calType][2]
			if doptions.get("localize", False):
				dayStr = _(dayNum)
			else:
				dayStr = str(dayNum)
			layout = newTextLayout(
				widget,
				dayStr,
				getOptionsFont(doptions),
			)
			assert layout is not None
			fontw, fonth = layout.get_pixel_size()
			if calType == calTypes.primary and c.holiday:
				setColor(cr, conf.holidayColor.v)
			else:
				setColor(cr, doptions["color"])
			font_x, font_y = dayCal.getRenderPos(doptions, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		for calType, moptions in dayCal.iterMonthOptions():
			text = dayCal.getMonthName(c, calType, moptions)
			layout = newTextLayout(
				widget,
				text,
				getOptionsFont(moptions),
			)
			assert layout is not None
			fontw, fonth = layout.get_pixel_size()
			setColor(cr, moptions["color"])
			font_x, font_y = dayCal.getRenderPos(moptions, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		if dayCal.weekdayOptions:
			woptions = dayCal.weekdayOptions.v
			if woptions.get("enable", True):
				text = core.getWeekDayAuto(
					c.weekDay,
					localize=dayCal.getWeekdayLocalize(),
					abbreviate=dayCal.getWeekdayAbbreviate(),
					relative=False,
				)
				if (
					langHasUppercase
					and dayCal.weekdayUppercase
					and dayCal.weekdayUppercase.v
				):
					text = text.upper()
				daynum = newTextLayout(
					widget,
					text,
					getOptionsFont(woptions),
				)
				assert daynum is not None
				fontw, fonth = daynum.get_pixel_size()
				setColor(cr, woptions["color"])
				font_x, font_y = dayCal.getRenderPos(
					woptions,
					x0,
					y0,
					w,
					h,
					fontw,
					fonth,
				)
				cr.move_to(font_x, font_y)
				show_layout(cr, daynum)

		self.drawSeasonPie(cr, w, h)

		buttons = dayCal.getAllButtons()
		for button in buttons:
			button.draw(cr, w, h)
		return buttons

	def drawEventIcons(
		self,
		cr: ImageContext,
		c: CellType,
		w: int,
		h: int,
		x0: int,
		y0: int,
	) -> None:
		dayCal = self.dayCal
		if not dayCal.eventTotalSizeRatio:
			return
		assert dayCal.eventIconSize
		iconList = c.getDayEventIcons()
		if not iconList:
			return
		iconsN = len(iconList)

		maxTotalSize = dayCal.eventTotalSizeRatio.v * min(w, h)
		sideCount = isqrt(iconsN - 1) + 1
		iconSize = min(
			dayCal.eventIconSize.v,
			int(maxTotalSize / sideCount),
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

	def drawSeasonPie(self, cr: ImageContext, w: float, h: float) -> None:
		dayCal = self.dayCal
		if not dayCal.seasonPieEnable:
			return

		if not dayCal.seasonPieEnable.v:
			return

		assert dayCal.seasonPieGeo is not None
		assert dayCal.seasonPieColors is not None
		assert dayCal.seasonPieTextColor is not None

		seasonName, seasonFrac = getSeasonNamePercentFromJd(
			dayCal.getCell().jd,
			conf.seasonPBar_southernHemisphere.v,
		)

		geo = dayCal.seasonPieGeo.v
		color = dayCal.seasonPieColors[seasonName].v
		textColor = dayCal.seasonPieTextColor.v
		if not textColor:
			textColor = conf.textColor.v

		size = geo["size"]
		radius = size / 2
		x, y = geo["pos"]
		x, y = getAbsPos(
			size,
			size,
			w,
			h,
			x,
			y,
			geo["xalign"],
			geo["yalign"],
			autoDir=False,
		)

		xc = x + radius
		yc = y + radius

		startOffset = geo["startAngle"] / 360

		drawPieOutline(
			cr,
			xc,
			yc,
			radius,
			geo["thickness"] * radius,
			startOffset,
			startOffset + seasonFrac,
		)
		fillColor(cr, color)

		textSize = size * (1 - geo["thickness"])
		layout = newTextLayout(
			dayCal.getWidget(),
			textNumEncode(
				f"%{int(seasonFrac * 100)}",
				# changeSpecialChars=True,
			),
			maxSize=(textSize, textSize),
		)
		assert layout is not None
		font_w, font_h = layout.get_pixel_size()
		setColor(cr, textColor)
		cr.move_to(xc - font_w / 2, yc - font_h / 2)
		show_layout(cr, layout)
