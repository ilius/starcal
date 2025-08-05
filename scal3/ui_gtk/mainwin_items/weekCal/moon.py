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

from math import pi
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gdk, pack
from scal3.ui_gtk.drawing import newTextLayout, setColor
from scal3.ui_gtk.utils import pixbufFromFile

from .column import Column

if TYPE_CHECKING:
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.drawing import ImageContext

	from .pytypes import WeekCalType

__all__ = ["MoonStatusColumn"]


class MoonStatusColumn(Column):
	objName = "moonStatus"
	desc = _("Moon Status")
	widthOption = conf.wcal_moonStatus_width
	showCursor = False
	optionsPageSpacing = 40

	def __init__(self, wcal: WeekCalType) -> None:
		Column.__init__(self, wcal)
		self.showPhaseNumber = False

	def drawColumn(self, cr: ImageContext) -> None:
		from math import cos

		from scal3.moon import getMoonPhase

		status = self.wcal.status
		assert status is not None

		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		itemW = w - conf.wcalPadding.v
		rowH = h / 7

		imgSize = int(min(rowH, itemW))
		scaleFact = 1

		imgMoonSize = imgSize * 0.9296875
		# imgBorder = (imgSize-imgMoonSize) / 2
		imgRadius: float = imgMoonSize / 2
		# ---
		# it's ok because pixbufFromFile uses cache
		moonPixbuf = pixbufFromFile("full_moon_128px.png", size=imgSize)
		assert moonPixbuf is not None
		# ---
		imgItemW = itemW / scaleFact
		imgRowH = rowH / scaleFact
		imgCenterX: float = w / 2 / scaleFact
		# ---
		self.drawBg(cr)
		# ---
		cr.set_line_width(0)
		cr.scale(scaleFact, scaleFact)

		def draw_arc(
			imgCenterY: float,
			arcScale: float | None,
			upwards: bool,
			clockWise: bool,
		) -> None:
			if arcScale is None:  # None means infinity
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
				raise ValueError(f"{e}: invalid scale factor {arcScale}") from None
			arc = cr.arc_negative if clockWise else cr.arc
			arc(
				0,  # center X
				0,  # center Y
				1,  # radius
				startAngle,  # start angle
				endAngle,  # end angle
			)
			cr.restore()

		for index in range(7):
			bigPhase = getMoonPhase(
				status[index].jd,
				conf.wcal_moonStatus_southernHemisphere.v,
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
				1,  # arc scale factor
				False,  # upwards
				bigPhase < 1,  # clockWise
			)
			draw_arc(
				imgCenterY,
				None if phase == 0.5 else abs(cos(phase * pi)),
				True,
				phase > 0.5,
			)
			cr.fill()

			if self.showPhaseNumber:
				layout = newTextLayout(
					self.w,
					text=f"{bigPhase:.1f}",
					maxSize=(imgItemW * 0.8, imgRowH * 0.8),
				)
				assert layout is not None
				layoutW, layoutH = layout.get_pixel_size()
				layoutX = imgCenterX - layoutW * 0.4
				layoutY = imgCenterY - layoutH * 0.4
				cr.move_to(layoutX, layoutY)
				setColor(cr, (255, 0, 0))
				show_layout(cr, layout)

		cr.scale(1 / scaleFact, 1 / scaleFact)

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI

		# ----
		option = CheckOptionUI(
			option=conf.wcal_moonStatus_southernHemisphere,
			label=_("Southern Hemisphere"),
			live=True,
			onChangeFunc=self.onSouthernHemisphereChange,
		)
		pack(optionsWidget, option.getWidget())

	def onSouthernHemisphereChange(self) -> None:
		self.onDateChange()
