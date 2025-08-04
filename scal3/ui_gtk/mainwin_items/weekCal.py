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
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj

log = logger.get()

from math import pi
from time import time as now
from typing import TYPE_CHECKING, Any, Protocol

import cairo
from gi.repository.PangoCairo import show_layout

from scal3 import core, ui
from scal3.cal_types import calTypes
from scal3.font import Font
from scal3.locale_man import rtl, rtlSgn
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui.font import getOptionsFont
from scal3.ui_gtk import (
	gdk,
	getScrollValue,
	gtk,
	pack,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj import CalBase
from scal3.ui_gtk.customize import (
	CustomizableCalBox,
	newSubPageButton,
)
from scal3.ui_gtk.drawing import (
	drawOutlineRoundedRect,
	drawRoundedRect,
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.mywidgets import MyFontButton
from scal3.ui_gtk.option_ui.spin import FloatSpinOptionUI, IntSpinOptionUI
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.toolbox import (
	CustomizableToolBox,
	LabelToolBoxItem,
	ToolBoxItem,
)
from scal3.ui_gtk.utils import GLibError, pixbufFromFile

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import GObject

	from scal3.color_utils import ColorType
	from scal3.option import Option
	from scal3.pytypes import WeekStatusType
	from scal3.timeline.box import Box as TimeLineBox
	from scal3.ui.pytypes import WeekCalDayNumOptionsDict
	from scal3.ui_gtk.drawing import (
		ImageContext,
	)
	from scal3.ui_gtk.option_ui.base import OptionUI
	from scal3.ui_gtk.pytypes import CustomizableCalObjType, StackPageType
	from scal3.ui_gtk.starcal_types import MainWinType
	from scal3.ui_gtk.toolbox import (
		BaseToolBoxItem,
	)

__all__ = ["CalObj"]


class ColumnParent(Protocol):
	def set_child_packing(
		self,
		child: gtk.Widget,
		expand: bool,
		fill: bool,
		padding: int,
		pack_type: gtk.PackType,
	) -> None: ...


# class WeekCalType(Protocol, ColumnParent):
# 	status
# 	def updateStatus(self)


class ColumnBase(CustomizableCalObj):
	itemListCustomizable = False
	autoButtonPressHandler = True
	widthOption: Option[int] | None = None
	expandOption: Option[bool] | None = None
	fontOption: Option[str | None] | None = None

	def __init__(self) -> None:
		super().__init__()
		self.colParent: ColumnParent | None = None
		self.calType = 0

	def getFontFamily(self) -> str:
		option = self.fontOption
		if option and option.v:
			return option.v
		return ""

	def onWidthChange(self) -> None:
		# if self.objName:
		# 	self.updatePacking()
		self.w.queue_resize()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.font import FontFamilyOptionUI

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		option: OptionUI
		# ----
		if self.widthOption is not None:
			widthOption = self.widthOption
			option = IntSpinOptionUI(
				option=widthOption,
				bounds=(1, 999),
				step=1,
				label=_("Width"),
				live=True,
				onChangeFunc=self.onWidthChange,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.expandOption is not None:
			expandOption = self.expandOption
			option = CheckOptionUI(
				option=expandOption,
				label=_("Expand"),
				live=True,
				onChangeFunc=self.onExpandCheckClick,
			)
			pack(optionsWidget, option.getWidget())
		# ----
		if self.fontOption is not None:
			fontOption = self.fontOption
			option = FontFamilyOptionUI(
				option=fontOption,
				hasAuto=True,
				label=_("Font Family"),
				onChangeFunc=self.onFontChange,
			)
			option.updateWidget()  # done inside Live*OptionUI classes
			pack(optionsWidget, option.getWidget())
			previewText = self.getFontPreviewText()
			if previewText:
				option.setPreviewText(previewText)
		# ----
		self.addExtraOptionsWidget(optionsWidget)
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onFontChange(self) -> None:
		self.onDateChange()

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		pass

	def updatePacking(self) -> None:
		if self.colParent is None:
			return
		self.colParent.set_child_packing(
			self.w,
			self.expand,
			self.expand,
			0,
			gtk.PackType.START,
		)

	def onExpandCheckClick(self) -> None:
		option = self.expandOption
		assert option is not None
		self.expand = option.v
		self.updatePacking()
		self.w.queue_draw()

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		return ""


class ColumnDrawingArea(gtk.DrawingArea):
	def __init__(self, getWidth: Callable[[], int]) -> None:
		gtk.DrawingArea.__init__(self)
		self.getWidth = getWidth

	def do_get_preferred_width(self) -> tuple[int, int]:
		# must return minimum_size, natural_size
		width = self.getWidth()
		return width, width


class Column(ColumnBase):
	colorizeHolidayText = False
	showCursor = False
	truncateText = False

	def __init__(self, wcal: CalObj) -> None:
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
				y1 = y0 + rowH / 2
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
					rowH,  # offset
					0,
					0,
					0,
					0,
				)
				cr.rectangle(0, y0, w, rowH)
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
				for line, color in data:
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
						color = conf.holidayColor.v  # noqa: PLW2901
					if not color:
						color = conf.textColor.v  # noqa: PLW2901
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


class MainMenuToolBoxItem(ToolBoxItem):
	hasOptions = True

	def __init__(self, wcal: CalObj) -> None:
		ToolBoxItem.__init__(
			self,
			name="mainMenu",
			imageNameDynamic=True,
			desc=_("Main Menu"),
			enableTooltip=True,
			continuousClick=False,
			onPress=self.onButtonPress,
		)
		self._wcal = wcal

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.updateImage()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.file import IconChooserOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		# ---
		option = IconChooserOptionUI(
			option=conf.wcal_toolbar_mainMenu_icon,
			label=_("Icon"),
			live=True,
			onChangeFunc=self.updateImage,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updateImage(self) -> None:
		self.setIconFile(conf.wcal_toolbar_mainMenu_icon.v)
		self.build()
		self.showHide()

	def getMenuPos(self) -> tuple[int, int]:
		wcal = self._wcal
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		coords = self.w.translate_coordinates(wcal.w, 0, 0)
		assert coords is not None
		x0, y0 = coords
		return (
			x0 if rtl else x0 + w,
			y0 + h // 2,
		)

	def onButtonPress(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		x, y = self.getMenuPos()
		self._wcal.s.emit(
			"popup-main-menu",
			x,
			y,
		)


class WeekNumToolBoxItem(LabelToolBoxItem):
	def __init__(self) -> None:
		LabelToolBoxItem.__init__(
			self,
			name="weekNum",
			onClick=self.onClick,
			desc=("Week Number"),
			continuousClick=False,
		)
		self.label.set_direction(gtk.TextDirection.LTR)

	def updateLabel(self) -> None:
		if conf.wcal_toolbar_weekNum_negative.v:
			n = ui.cells.current.weekNumNeg
		else:
			n = ui.cells.current.weekNum
		self.label.set_label(_(n))

	def onDateChange(self) -> None:
		super().onDateChange()
		self.updateLabel()

	def onClick(self, _w: gtk.Widget) -> None:
		conf.wcal_toolbar_weekNum_negative.v = not conf.wcal_toolbar_weekNum_negative.v
		self.updateLabel()
		ui.saveLiveConf()


# FIXME: multi-inheritance


class ToolbarColumn(CustomizableToolBox, ColumnBase):
	vertical = True
	desc = _("Toolbar (Vertical)")
	autoButtonPressHandler = False
	optionsPageSpacing = 5

	def __init__(self, wcal: CalObj) -> None:
		CustomizableToolBox.__init__(self, wcal)
		ColumnBase.__init__(self)
		self.defaultItems: list[BaseToolBoxItem] = [
			MainMenuToolBoxItem(wcal),
			WeekNumToolBoxItem(),
			ToolBoxItem(
				name="backward4",
				imageName="go-top.svg",
				onClick=wcal.goBackward4,
				desc="Backward 4 Weeks",
			),
			ToolBoxItem(
				name="backward",
				imageName="go-up.svg",
				onClick=wcal.goBackward,
				desc="Previous Week",
			),
			ToolBoxItem(
				name="today",
				imageName="go-home.svg",
				onClick=wcal.goToday,
				desc="Today",
				continuousClick=False,
			),
			ToolBoxItem(
				name="forward",
				imageName="go-down.svg",
				onClick=wcal.goForward,
				desc="Next Week",
			),
			ToolBoxItem(
				name="forward4",
				imageName="go-bottom.svg",
				onClick=wcal.goForward4,
				desc="Forward 4 Weeks",
			),
		]
		self.defaultItemsDict = {item.objName: item for item in self.defaultItems}
		if not ud.wcalToolbarData["items"]:
			ud.wcalToolbarData["items"] = [
				(item.objName, True) for item in self.defaultItems
			]
		self.setDict(ud.wcalToolbarData)

	def updateVars(self) -> None:
		super().updateVars()
		ud.wcalToolbarData = self.getDict()


class WeekDaysColumn(Column):
	objName = "weekDays"
	desc = _("Week Days")
	widthOption = conf.wcal_weekDays_width
	expandOption = conf.wcal_weekDays_expand
	fontOption = conf.wcalFont_weekDays
	colorizeHolidayText = True
	showCursor = True
	optionsPageSpacing = 20

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[
				[
					(core.getWeekDayN(i), None),
				]
				for i in range(7)
			],
		)
		self.drawCursorFg(cr)

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		return _(", ").join([_(core.getWeekDayN(i)) for i in range(7)])


class PluginsTextColumn(Column):
	objName = "pluginsText"
	desc = _("Plugins Text")
	fontOption = conf.wcalFont_pluginsText
	expand = True
	truncateText = False
	optionsPageSpacing = 20

	def getTextListByIndex(self, i: int) -> list[tuple[str, ColorType | None]]:
		status = self.wcal.status
		assert status is not None
		return [
			(line, None)
			for line in status[i]
			.getPluginsText(
				firstLineOnly=conf.wcal_pluginsText_firstLineOnly.v,
			)
			.split("\n")
		]

	def drawColumn(self, cr: ImageContext) -> None:
		self.drawBg(cr)
		self.drawTextList(
			cr,
			[self.getTextListByIndex(i) for i in range(7)],
		)

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI

		# -----
		option = CheckOptionUI(
			option=conf.wcal_pluginsText_firstLineOnly,
			label=_("Only first line of text"),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())

	def getFontPreviewText(self) -> str:  # noqa: PLR6301
		for occurData in ui.cells.current.getPluginsData():
			return occurData[1].replace("\n", " ")
		return ""


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

	def __init__(self, wcal: CalObj) -> None:
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


class DaysOfMonthFontButton(MyFontButton):
	styleClass = "daysOfMonthFontButton"

	def __init__(self) -> None:
		MyFontButton.__init__(self, dragAndDrop=True)
		self.get_style_context().add_class(self.styleClass)

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		# make the font of Button smaller by a factor of 0.5
		font = ui.getFont(scale=0.5)
		return (
			"."
			+ DaysOfMonthFontButton.styleClass
			+ " "
			+ cssTextStyle(
				font=font,
			)
		)


class DaysOfMonthCalTypeParamBox(gtk.Box):
	def __init__(
		self,
		wcal: CalObj,
		index: int,
		calType: int,
		options: WeekCalDayNumOptionsDict,
		sgroupLabel: gtk.SizeGroup,
		sgroupFont: gtk.SizeGroup,
	) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.wcal = wcal
		self.colParent = wcal
		self.index = index
		self.calType = calType
		# ------
		module = calTypes[calType]
		if module is None:
			raise RuntimeError(f"cal type '{calType}' not found")
		label = gtk.Label(label=_(module.desc, ctx="calendar") + "  ")
		label.set_xalign(0)
		pack(self, label)
		sgroupLabel.add_widget(label)
		# ---
		label = gtk.Label(label=f'<span font-size="small">{_("Font")}</span>')
		label.set_use_markup(True)
		self.fontCheck = gtk.CheckButton()
		self.fontCheck.add(label)
		pack(self, gtk.Label(), 1, 1)
		pack(self, self.fontCheck)
		# ---
		self.fontb = DaysOfMonthFontButton()
		pack(self, self.fontb)
		sgroupFont.add_widget(self.fontb)
		# ----
		self.set(options)
		# ----
		self.fontCheck.connect("clicked", self.onChange)
		self.fontb.connect("font-set", self.onChange)

	def get(self) -> WeekCalDayNumOptionsDict:
		return {
			"font": (self.fontb.getFont() if self.fontCheck.get_active() else None),
		}

	def set(self, data: WeekCalDayNumOptionsDict) -> None:
		font = getOptionsFont(data)
		self.fontCheck.set_active(bool(font))
		if not font:
			font = ui.getFont()
		self.fontb.setFont(font)

	def onChange(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		conf.wcalTypeParams.v[self.index] = self.get()
		self.wcal.w.queue_draw()


class DaysOfMonthColumn(Column):
	colorizeHolidayText = True
	showCursor = True
	widthOption = conf.wcal_daysOfMonth_width
	expandOption = conf.wcal_daysOfMonth_expand

	def __init__(
		self,
		wcal: CalObj,
		cgroup: DaysOfMonthColumnGroup,
		calType: int,
		index: int,
	) -> None:
		Column.__init__(self, wcal)
		self.cgroup = cgroup
		self.calType = calType
		self.index = index

	def drawColumn(self, cr: ImageContext) -> None:
		status = self.wcal.status
		assert status is not None
		self.drawBg(cr)
		font = getOptionsFont(conf.wcalTypeParams.v[self.index])
		self.drawTextList(
			cr,
			[
				[
					(
						_(status[i].dates[self.calType][2], calType=self.calType),
						None,
					),
				]
				for i in range(7)
			],
			font=font,
		)
		self.drawCursorFg(cr)


# FIXME: multi-inheritance!
class DaysOfMonthColumnGroup(CustomizableCalBox, ColumnBase):
	objName = "daysOfMonth"
	desc = _("Days of Month")
	optionsPageSpacing = 15

	def __init__(self, wcal: CalObj) -> None:
		CustomizableCalBox.__init__(self, vertical=False)
		ColumnBase.__init__(self)
		self.initVars()
		self.wcal = wcal
		self.colParent: ColumnParent = wcal.box
		self.updateCols()
		self.updateDirection()
		self.show()

	def updateDirection(self) -> None:
		self.w.set_direction(ud.textDirDict[conf.wcal_daysOfMonth_dir.v])
		# set_direction does not apply to existing children.
		# that's why we remove children(columns) and add them again
		box = self.box
		columns = box.get_children()
		for col in columns:
			box.remove(col)
		for col in columns:
			pack(box, col, 1, 1)

	def onWidthChange(self) -> None:
		ColumnBase.onWidthChange(self)
		for item in self.items:
			assert isinstance(item, Column), f"{item=}"
			item.onWidthChange()

	def addExtraOptionsWidget(self, optionsWidget: gtk.Box) -> None:
		from scal3.ui_gtk.option_ui.direction import DirectionOptionUI

		# ---
		option = DirectionOptionUI(
			option=conf.wcal_daysOfMonth_dir,
			onChangeFunc=self.updateDirection,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		frame = gtk.Frame()
		frame.set_label(_("Calendars"))
		self.typeOptionsVbox = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing // 2,
		)
		self.typeOptionsVbox.set_border_width(5)
		frame.add(self.typeOptionsVbox)
		frame.show_all()
		pack(optionsWidget, frame)
		self.updateTypeOptionsWidget()  # FIXME

	# overwrites method from ColumnBase
	def updatePacking(self) -> None:
		ColumnBase.updatePacking(self)
		for item in self.items:
			assert isinstance(item, Column), f"{item=}"
			item.expand = self.expand
			item.updatePacking()

	def getWidth(self) -> int:
		widthOption = self.widthOption
		if widthOption is None:
			raise ValueError("widthProp is None")
		count = len(self.box.get_children())
		return int(count * widthOption.v)

	def updateCols(self) -> None:
		# self.foreach(gtk.DrawingArea.destroy)
		# ^^^ Couses tray icon crash in gnome3
		# self.foreach(lambda child: self.remove(child))
		# ^^^ Couses tray icon crash in gnome3
		# --------
		columns = self.items
		n = len(columns)
		n2 = len(calTypes.active)

		if len(conf.wcalTypeParams.v) < n2:
			while len(conf.wcalTypeParams.v) < n2:
				log.info("appending to wcalTypeParams")
				conf.wcalTypeParams.v.append(
					{
						"font": None,
					},
				)

		if n > n2:
			for i in range(n2, n):
				columns[i].w.destroy()
		elif n < n2:
			for i in range(n, n2):
				col = DaysOfMonthColumn(self.wcal, self, 0, i)
				col.colParent = self.box
				pack(self.box, col.w, 1, 1)
				columns.append(col)
		for i, calType in enumerate(calTypes.active):
			col2 = columns[i]
			assert isinstance(col2, ColumnBase)
			col2.calType = calType
			col2.show()

	def updateTypeOptionsWidget(self) -> None:
		if not hasattr(self, "typeOptionsVbox"):
			return
		vbox = self.typeOptionsVbox
		for child in vbox.get_children():
			child.destroy()
		# ---
		n = len(calTypes.active)
		while len(conf.wcalTypeParams.v) < n:
			conf.wcalTypeParams.v.append(
				{
					"font": None,
				},
			)
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		sgroupFont = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for i, calType in enumerate(calTypes.active):
			# try:
			options = conf.wcalTypeParams.v[i]
			# except IndexError:
			# --
			hbox = DaysOfMonthCalTypeParamBox(
				self.wcal,
				i,
				calType,
				options,
				sgroupLabel,
				sgroupFont,
			)
			pack(vbox, hbox)
		# ---
		vbox.show_all()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.updateCols()
		self.updateTypeOptionsWidget()


class MoonStatusColumn(Column):
	objName = "moonStatus"
	desc = _("Moon Status")
	widthOption = conf.wcal_moonStatus_width
	showCursor = False
	optionsPageSpacing = 40

	def __init__(self, wcal: CalObj) -> None:
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


class CalObj(CalBase):
	objName = "weekCal"
	desc = _("Week Calendar")
	vertical = False
	expand = True
	optionsPageSpacing = 10
	itemListSeparatePage = True
	itemsPageTitle = _("Columns")
	itemsPageButtonBorder = 15
	myKeys = CalBase.myKeys | {
		"up",
		"down",
		"left",
		"right",
		"page_up",
		"k",
		"p",
		"page_down",
		"j",
		"n",
		"end",
		"f10",
		"m",
	}

	def do_get_preferred_height(self) -> tuple[int, int]:  # noqa: PLR6301
		return 0, int(conf.winHeight.v / 3)

	def __init__(self, win: MainWinType) -> None:
		super().__init__()
		self.box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.w: gtk.Widget = self.box
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.parentWin = win
		# self.items: list[ColumnBase] = []
		self.initCal()
		# ----------------------
		self.w.connect("scroll-event", self.scroll)
		self.w.connect("button-press-event", self.onButtonPress)
		# -----
		# set in self.updateStatus
		self.status: WeekStatusType | None = None
		self.cellIndex = 0
		# -----
		defaultItems: list[ColumnBase] = [
			ToolbarColumn(self),
			WeekDaysColumn(self),
			PluginsTextColumn(self),
			EventsIconColumn(self),
			EventsCountColumn(self),
			EventsTextColumn(self),
			EventsBoxColumn(self),
			DaysOfMonthColumnGroup(self),
			MoonStatusColumn(self),
		]
		defaultItemsDict = {item.objName: item for item in defaultItems}
		itemNames = list(defaultItemsDict)
		for name, enable in conf.wcalItems.v:
			item = defaultItemsDict.get(name)
			if item is None:
				log.info(f"weekCal item '{name}' does not exist")
				continue
			item.enable = enable
			self.appendItem(item)
			itemNames.remove(name)
		for name in itemNames:
			item = defaultItemsDict[name]
			item.enable = False
			self.appendItem(item)

	def appendItem(self, item: CustomizableCalObjType) -> None:
		super().appendItem(item)
		if item.loaded:
			pack(self.box, item.w, item.expand, item.expand)
			item.showHide()

	def repackAll(self) -> None:
		box = self.box
		for child in box.get_children():
			box.remove(child)
		for item in self.items:
			if item.loaded:
				pack(box, item.w, item.expand, item.expand)
				item.showHide()

	def moveItem(self, i: int, j: int) -> None:
		CustomizableCalObj.moveItem(self, i, j)
		self.repackAll()

	def insertItemWidget(self, _i: int) -> None:
		self.repackAll()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI
		from scal3.ui_gtk.option_ui.check_mix import CheckColorOptionUI
		from scal3.ui_gtk.option_ui.color import ColorOptionUI

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		option: OptionUI
		# -----
		option = FloatSpinOptionUI(
			option=conf.wcalTextSizeScale,
			bounds=(0.01, 1),
			digits=3,
			step=0.1,
			label=_("Text Size Scale"),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		option = CheckColorOptionUI(
			CheckOptionUI(option=conf.wcalGrid, label=_("Grid")),
			ColorOptionUI(option=conf.wcalGridColor, useAlpha=True),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		option = CheckColorOptionUI(
			CheckOptionUI(
				option=conf.wcalUpperGradientEnable,
				label=_("Row's Upper Gradient"),
			),
			ColorOptionUI(option=conf.wcalUpperGradientColor, useAlpha=True),
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(optionsWidget, option.getWidget())
		# ------------
		pageVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=20)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		option = FloatSpinOptionUI(
			option=conf.wcalCursorLineWidthFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Line Width Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(pageVBox, option.getWidget())
		# ---
		option = FloatSpinOptionUI(
			option=conf.wcalCursorRoundingFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Rounding Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.w.queue_draw,
		)
		pack(pageVBox, option.getWidget())
		# ---
		pageVBox.show_all()
		# ---
		page = StackPage()
		page.pageWidget = pageVBox
		page.pageName = "cursor"
		page.pageTitle = _("Cursor")
		page.pageLabel = _("Cursor")
		page.pageIcon = ""
		self.subPages = [page]
		# ---
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button, padding=10)
		# ---------
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def getSubPages(self) -> list[StackPageType]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		assert self.subPages is not None
		return self.subPages

	def updateVars(self) -> None:
		CustomizableCalBox.updateVars(self)
		conf.wcalItems.v = self.getItemsData()

	def updateStatus(self) -> None:
		self.status = ui.cells.getCurrentWeekStatus()
		index = ui.cells.current.jd - self.status[0].jd
		if index > 6:
			log.info(f"warning: drawCursorFg: {index = }")
			return
		self.cellIndex = index

	def onConfigChange(self) -> None:
		self.updateStatus()
		super().onConfigChange()
		self.w.queue_draw()

	def onDateChange(self) -> None:
		self.updateStatus()
		super().onDateChange()
		self.w.queue_draw()
		# for item in self.items:
		# 	item.queue_draw()

	def goBackward4(self, _obj: GObject.Object) -> None:
		self.jdPlus(-28)

	def goBackward(self, _obj: GObject.Object) -> None:
		self.jdPlus(-7)

	def goForward(self, _obj: GObject.Object) -> None:
		self.jdPlus(7)

	def goForward4(self, _obj: GObject.Object) -> None:
		self.jdPlus(28)

	def itemContainsGdkWindow(self, item: gtk.Widget, col_win: gdk.Window) -> bool:
		if col_win == item.get_window():
			return True
		if isinstance(item, gtk.Container):
			for child in item.get_children():
				if self.itemContainsGdkWindow(child, col_win):
					return True
		return False

	def findColumnWidgetByGdkWindow(self, col_win: gdk.Window) -> ColumnBase | None:
		for item in self.items:
			if isinstance(item, gtk.Box):
				# right now only DaysOfMonthColumnGroup
				for child in item.get_children():
					if self.itemContainsGdkWindow(child, col_win):
						return child
			elif self.itemContainsGdkWindow(item.w, col_win):
				assert isinstance(item, ColumnBase), f"{item=}"
				return item
		return None

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		assert self.status is not None
		col = self.findColumnWidgetByGdkWindow(gevent.get_window())
		if not col:
			return False
		if not col.autoButtonPressHandler:
			return False
		# ---
		# stub for gevent.get_coords() is wrong!
		x_col = int(gevent.x)
		y_col = int(gevent.y)
		# x_col is relative to the column, not to the weekCal
		# y_col is relative to the column, but also to the weekCal,
		# 		because we have nothing above columns
		# ---
		i = int(y_col * 7.0 / self.w.get_allocation().height)
		cell = self.status[i]
		self.gotoJd(cell.jd)
		if gevent.type == gdk.EventType.DOUBLE_BUTTON_PRESS:
			self.s.emit("double-button-press")
		if gevent.button == 3:
			coords = col.w.translate_coordinates(self.w, x_col, y_col)
			assert coords is not None
			x, y = coords
			self.s.emit("popup-cell-menu", x, y)
		return True

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		if kname == "up":
			self.jdPlus(-1)
		elif kname == "down":
			self.jdPlus(1)
		elif kname == "left":
			self.jdPlus(rtlSgn() * 7)
		elif kname == "right":
			self.jdPlus(rtlSgn() * -7)
		elif kname == "end":
			assert self.status is not None
			self.gotoJd(self.status[-1].jd)
		elif kname in {"page_up", "k", "p"}:
			self.jdPlus(-7)
		elif kname in {"page_down", "j", "n"}:
			self.jdPlus(7)
		elif kname in {"f10", "m"}:
			if gevent.state & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.s.emit("popup-cell-menu", *self.getCellPos())
			else:
				self.s.emit("popup-main-menu", *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool | None:
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-1)
			return None
		if d == "down":
			self.jdPlus(1)
			return None
		return False

	def getCellPos(self, *_args: Any) -> tuple[int, int]:
		alloc = self.w.get_allocation()
		return (
			int(alloc.width / 2),
			int((ui.cells.current.weekDayIndex + 1) * alloc.height / 7),
		)

	def getToolbar(self) -> ToolbarColumn | None:
		for item in self.items:
			if item.enable and isinstance(item.objName, ToolbarColumn):
				return item
		return None

	def getMainMenuPos(self) -> tuple[int, int]:
		toolbar = self.getToolbar()
		if toolbar:
			for item in toolbar.items:
				if item.enable and isinstance(item, MainMenuToolBoxItem):
					return item.getMenuPos()
		if rtl:
			return self.w.get_allocation().width, 0

		return 0, 0
