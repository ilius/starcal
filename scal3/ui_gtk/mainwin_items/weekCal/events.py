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

from time import time as now
from typing import TYPE_CHECKING

from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.utils import GLibError, pixbufFromFile

from .column import Column

if TYPE_CHECKING:
	from scal3.color_utils import ColorType
	from scal3.timeline.box import Box as TimeLineBox
	from scal3.ui_gtk.drawing import ImageContext

	from .pytypes import WeekCalType

__all__ = [
	"EventsBoxColumn",
	"EventsCountColumn",
	"EventsIconColumn",
	"EventsTextColumn",
]


class EventsIconColumn(Column):
	objName = "eventsIcon"
	desc = _("Events Icon")
	widthOption = conf.wcal_eventsIcon_width
	optionsPageSpacing = 20

	def drawColumn(self, cr: ImageContext) -> None:
		status = self.wcal.status
		assert status is not None
		self.drawBg(cr)
		# ---
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		# ---
		# rowH = h / 7
		# itemW = w - conf.wcalPadding.v
		iconSizeMax = conf.wcalEventIconSizeMax.v
		for i in range(7):
			c = status[i]
			iconList = c.getWeekEventIcons()
			if not iconList:
				continue
			n = len(iconList)
			scaleFact = min(
				1.0,
				h / iconSizeMax,
				w / (n * iconSizeMax),
			)
			x0 = (w / scaleFact - (n - 1) * iconSizeMax) / 2
			y0 = (2 * i + 1) * h / (14 * scaleFact)
			if rtl:
				iconList.reverse()  # FIXME
			for iconIndex, icon in enumerate(iconList):
				try:
					pix = pixbufFromFile(icon, size=iconSizeMax)
				except GLibError:
					log.exception("error in pixbufFromFile")
					continue
				if pix is None:
					log.error(f"{pix=}, {icon=}")
					continue
				pix_w = pix.get_width()
				pix_h = pix.get_height()
				x1 = x0 + iconIndex * iconSizeMax - pix_w / 2
				y1 = y0 - pix_h / 2
				cr.scale(scaleFact, scaleFact)
				gdk.cairo_set_source_pixbuf(cr, pix, x1, y1)
				cr.rectangle(x1, y1, pix_w, pix_h)
				cr.fill()
				cr.scale(1 / scaleFact, 1 / scaleFact)


class EventsCountColumn(Column):
	objName = "eventsCount"
	desc = _("Events Count")
	widthOption = conf.wcal_eventsCount_width
	expandOption = conf.wcal_eventsCount_expand
	optionsPageSpacing = 40

	def getDayTextData(self, i: int) -> list[tuple[str, ColorType | None]]:
		status = self.wcal.status
		assert status is not None
		n = len(status[i].getEventsData())
		# FIXME: item.show[1]
		if n > 0:
			line = _("{eventCount} events").format(eventCount=_(n))
		else:
			line = ""
		return [
			(line, None),
		]

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		# ---
		# w = self.w.get_allocation().width
		# h = self.w.get_allocation().height
		# ---
		self.drawTextList(
			cr,
			[self.getDayTextData(i) for i in range(7)],
		)


class EventsTextColumn(Column):
	objName = "eventsText"
	desc = _("Events Text")
	fontOption = conf.wcalFont_eventsText
	expand = True
	truncateText = False
	optionsPageSpacing = 20

	def getDayTextData(self, i: int) -> list[tuple[str, ColorType | None]]:
		from scal3.xml_utils import escape

		assert self.wcal.status is not None
		data = []
		currentTime = now()
		for item in self.wcal.status[i].getEventsData():
			if not item.show[1]:
				continue
			line = (
				"".join(item.text) if conf.wcal_eventsText_showDesc.v else item.text[0]
			)
			line = escape(line)
			if item.time:
				line = item.time + " " + line
			color: ColorType | None = None
			if conf.wcal_eventsText_colorize.v:
				color = item.color
			if item.time_epoch[1] < currentTime:
				if conf.wcal_eventsText_pastColorEnable.v:
					color = conf.wcal_eventsText_pastColor.v
			elif item.time_epoch[0] <= currentTime:  # noqa: SIM102
				if conf.wcal_eventsText_ongoingColorEnable.v:
					color = conf.wcal_eventsText_ongoingColor.v
			data.append((line, color))
		return data

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[self.getDayTextData(i) for i in range(7)],
		)

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		return ""  # TODO

	def onEventColorChange(self) -> None:
		self.onDateChange()

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.check_mix import CheckColorOptionUI
		from scal3.ui_gtk.option_ui.color import ColorOptionUI

		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)

		pack(
			optionsWidget,
			CheckColorOptionUI(
				CheckOptionUI(
					option=conf.wcal_eventsText_pastColorEnable,
					label=_("Past Event Color"),
				),
				ColorOptionUI(
					option=conf.wcal_eventsText_pastColor,
					useAlpha=True,
				),
				live=True,
				onChangeFunc=self.onEventColorChange,
				checkSizeGroup=sizeGroup,
			).getWidget(),
		)

		pack(
			optionsWidget,
			CheckColorOptionUI(
				CheckOptionUI(
					option=conf.wcal_eventsText_ongoingColorEnable,
					label=_("Ongoing Event Color"),
				),
				ColorOptionUI(
					option=conf.wcal_eventsText_ongoingColor,
					useAlpha=True,
				),
				live=True,
				onChangeFunc=self.onEventColorChange,
				checkSizeGroup=sizeGroup,
			).getWidget(),
		)

		pack(
			optionsWidget,
			CheckOptionUI(
				option=conf.wcal_eventsText_colorize,
				label=_("Use color of event group\nfor event text"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			).getWidget(),
		)

		pack(
			optionsWidget,
			CheckOptionUI(
				option=conf.wcal_eventsText_showDesc,
				label=_("Show Description"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			).getWidget(),
		)


class EventsBoxColumn(Column):
	objName = "eventsBox"
	desc = _("Events Box")
	fontOption = conf.wcalFont_eventsBox
	expand = True  # FIXME
	optionsPageSpacing = 40

	def __init__(self, wcal: WeekCalType) -> None:
		self.boxes: list[TimeLineBox] | None = None
		self.padding = 2
		self.timeWidth = 7 * 86400
		self.boxEditing = None
		# -----
		Column.__init__(self, wcal)
		# -----
		self.w.connect("realize", lambda _w: self.updateData())

	def updateData(self) -> None:
		from scal3.time_utils import getEpochFromJd
		from scal3.timeline.box import calcEventBoxes

		assert self.wcal.status is not None
		self.timeStart = getEpochFromJd(self.wcal.status[0].jd)
		self.pixelPerSec = self.w.get_allocation().height / self.timeWidth
		# ^^^ unit: pixel / second
		self.borderTm = 0
		# tbox.boxEditBorderWidth / self.pixelPerSec # second
		self.boxes = calcEventBoxes(
			self.timeStart,
			self.timeStart + self.timeWidth,
			self.pixelPerSec,
			self.borderTm,
		)

	def onDateChange(self) -> None:
		super().onDateChange()
		self.updateData()
		self.w.queue_draw()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.updateData()
		self.w.queue_draw()

	def drawBox(self, cr: ImageContext, box: TimeLineBox) -> None:
		from scal3.ui_gtk import timeline_box as tbox

		# ---
		x = box.y
		y = box.x
		w = box.h
		h = box.w
		# ---
		tbox.drawBoxBG(cr, box, x, y, w, h)
		tbox.drawBoxText(cr, box, x, y, w, h, self.w)

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		if not self.boxes:
			return
		# ---
		alloc = self.w.get_allocation()
		w = alloc.width
		# h = alloc.height
		# ---
		for box in self.boxes:
			box.setPixelValues(
				self.timeStart,
				self.pixelPerSec,
				self.padding,
				w - 2 * self.padding,
			)
			self.drawBox(cr, box)
