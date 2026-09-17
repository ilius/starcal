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

from typing import TYPE_CHECKING, Any

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.color_utils import RGBA
from scal3.locale_man import getMonthName, rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import (
	WindowEdge,
	begin_resize_drag,
	connect_draw,
	gdk,
	getScrollValue,
	gtk,
)
from scal3.ui_gtk.button_drawing import Button, SVGButton
from scal3.ui_gtk.cal_obj import CalBase
from scal3.ui_gtk.day_cal.drawing import DayCalDrawing
from scal3.ui_gtk.day_cal.options import DayCalOptions

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.color_utils import ColorType
	from scal3.option import ListOption, Option
	from scal3.pytypes import CellType
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		DayCalTypeBaseOptionsDict,
		DayCalTypeDayOptionsDict,
		DayCalTypeWMOptionsDict,
		DayCalWidgetButtonDict,
		PieGeoDict,
	)
	from scal3.ui_gtk.button_drawing import BaseButton
	from scal3.ui_gtk.day_cal.types import ParentWindowType
	from scal3.ui_gtk.drawing import ImageContext
	from scal3.ui_gtk.pytypes import StackPageType

__all__ = ["DayCal"]


class DayCal(CalBase):
	objName = "dayCal"
	desc = _("Day Calendar")
	itemListCustomizable = False

	backgroundColor: Option[ColorType] | None = None
	dayOptions: ListOption[DayCalTypeDayOptionsDict] | None = None
	monthOptions: ListOption[DayCalTypeWMOptionsDict] | None = None
	weekdayOptions: Option[DayCalTypeWMOptionsDict] | None = None
	weekdayLocalize: Option[bool] | None = None
	weekdayAbbreviate: Option[bool] | None = None
	weekdayUppercase: Option[bool] | None = None

	widgetButtonsEnable: Option[bool] | None = None
	widgetButtonsSize: Option[int] | None = None
	widgetButtonsOpacity: Option[float] | None = None
	widgetButtons: ListOption[DayCalWidgetButtonDict] | None = None

	navButtonsEnable: Option[bool] | None = None
	navButtonsGeo: Option[ButtonGeoDict] | None = None
	navButtonsOpacity: Option[float] | None = None

	eventIconSize: Option[int] | None = None
	eventTotalSizeRatio: Option[float] | None = None

	seasonPieEnable: Option[bool] | None = None
	seasonPieGeo: Option[PieGeoDict] | None = None
	seasonPieColors: dict[str, Option[ColorType]] | None = None
	seasonPieTextColor: Option[ColorType] | None = None

	myKeys = CalBase.myKeys | {
		"up",
		"down",
		"right",
		"left",
		"page_up",
		"k",
		"p",
		"page_down",
		"j",
		"n",
		# "end",
		"f10",
		"m",
	}

	def __init__(self, win: ParentWindowType) -> None:
		super().__init__()
		self.w: gtk.Widget = gtk.DrawingArea()
		# FIXME: rename one of these two attrs:
		self.parentWin = win
		self.myWin: gtk.Window | None = None
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self._allButtons: list[BaseButton] = []
		# ----------------------
		self.drawing = DayCalDrawing(self)
		self.options = DayCalOptions(self)
		# ----------------------
		# self.kTime = 0
		# ----------------------
		connect_draw(self.w, self.drawAll)
		self.w.connect("button-press-event", self.onButtonPress)
		# self.connect("screen-changed", self.screenChanged)
		self.w.connect("scroll-event", self.scroll)

	def getWidget(self) -> gtk.Widget:
		return self.w

	def getBackgroundColor(self) -> ColorType:
		if self.backgroundColor:
			return self.backgroundColor.v
		return conf.bgColor.v

	def getDayOptions(
		self, allCalTypes: bool = False
	) -> list[DayCalTypeDayOptionsDict]:
		if not self.dayOptions:
			return []
		options = self.dayOptions.v
		if allCalTypes:
			n = len(calTypes.active)
			while len(options) < n:
				options.append(
					{
						"enable": False,
						"pos": (0, 0),
						"font": ui.getFont(3.0),
						"color": conf.textColor.v,
						"xalign": "center",
						"yalign": "center",
						"localize": False,
					},
				)
		return options

	def getMonthOptions(
		self,
		allCalTypes: bool = False,
	) -> list[DayCalTypeWMOptionsDict]:
		if not self.monthOptions:
			return []
		options = self.monthOptions.v
		if allCalTypes:
			n = len(calTypes.active)
			while len(options) < n:
				options.append(
					{
						"enable": False,
						"pos": (0, 0),
						"font": ui.getFont(2.0),
						"color": conf.textColor.v,
						"xalign": "center",
						"yalign": "center",
						"abbreviate": False,
						"uppercase": False,
					},
				)
		return options

	def getWidgetButtons(self) -> list[BaseButton]:
		if not self.widgetButtonsEnable:
			return []
		if not self.widgetButtonsEnable.v:
			return []
		assert self.widgetButtons is not None
		iconSize = self.widgetButtonsSize.v if self.widgetButtonsSize else 16
		opacity = self.widgetButtonsOpacity.v if self.widgetButtonsOpacity else 1.0
		return [
			Button(
				onPress=getattr(self, d["onClick"]),
				imageName=d.get("imageName", ""),
				x=d["pos"][0],
				y=d["pos"][1],
				autoDir=d["autoDir"],
				iconName=d.get("iconName", ""),
				iconSize=iconSize,
				# d.get("iconSize", self.widgetButtonsSize.v),
				xalign=d.get("xalign", "left"),
				yalign=d.get("yalign", "top"),
				opacity=opacity,
			)
			for d in self.widgetButtons.v
		]

	navButtonsRaw = [
		{
			# "imageName": "go-previous.svg",
			"imageName": "list-remove.svg",
			"onClick": "prevDayClicked",
		},
		{
			"imageName": "go-home.svg",
			"onClick": "goToday",
		},
		{
			# "imageName": "go-next.svg",
			"imageName": "list-add.svg",
			"onClick": "nextDayClicked",
		},
	]
	navButtonsRTLRaw = [
		{
			# "imageName": "go-previous.svg",
			"imageName": "list-add.svg",
			"onClick": "nextDayClicked",
		},
		{
			"imageName": "go-home.svg",
			"onClick": "goToday",
		},
		{
			# "imageName": "go-next.svg",
			"imageName": "list-remove.svg",
			"onClick": "prevDayClicked",
		},
	]

	def getNavButtons(self) -> list[BaseButton]:
		if not self.navButtonsEnable:
			return []

		if not self.navButtonsEnable.v:
			return []

		if not self.navButtonsGeo:
			return []

		assert self.navButtonsOpacity is not None

		buttonsRaw = self.navButtonsRaw
		geo = self.navButtonsGeo.v
		if rtl and geo.get("autoDir", True):
			buttonsRaw = self.navButtonsRTLRaw

		opacity = self.navButtonsOpacity.v
		iconSize = geo["size"]
		spacing = geo["spacing"]
		xc, y = geo["pos"]
		xalign = geo["xalign"]
		yalign = geo["yalign"]

		count = len(buttonsRaw)
		totalWidth = iconSize * count + spacing * (count - 1)
		x_start = xc - totalWidth / 2
		x_delta = iconSize + spacing

		red, green, blue = conf.textColor.v[:3]
		rectangleColor = RGBA(red, green, blue, int(opacity * 0.7))

		return [
			SVGButton(
				onPress=getattr(self, d["onClick"]),
				imageName=d.get("imageName", ""),
				x=x_start + index * x_delta,
				y=y,
				autoDir=False,
				iconSize=iconSize,
				xalign=xalign,
				yalign=yalign,
				opacity=opacity,
				rectangleColor=rectangleColor,
			)
			for index, d in enumerate(buttonsRaw)
		]

	def getAllButtons(self) -> list[BaseButton]:
		return self.getWidgetButtons() + self.getNavButtons()

	def startMove(self, gevent: gdk.EventButton, button: int = 1) -> None:
		log.debug(f"DayCal.startMove: {gevent=}")
		win = self.getWindow()
		if not win:
			return
		win.begin_move_drag(
			button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def startResize(self, gevent: gdk.EventButton) -> None:
		win = self.getWindow()
		if not win:
			return
		begin_resize_drag(
			win,
			WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def openCustomize(self, w: gtk.Widget) -> None:
		if self.parentWin:
			self.parentWin.customizeShow(w)

	def prevDayClicked(self, _ge: gdk.EventButton | None = None) -> None:
		self.jdPlus(-1)

	def nextDayClicked(self, _ge: gdk.EventButton | None = None) -> None:
		self.jdPlus(1)

	def getWindow(self) -> gtk.Window:
		assert self.myWin is not None
		return self.myWin

	@classmethod
	def getCell(cls) -> CellType:
		return ui.cells.current

	@staticmethod
	def getRenderPos(
		options: DayCalTypeBaseOptionsDict,
		x0: float,
		y0: float,
		w: float,
		h: float,
		fontw: float,
		fonth: float,
	) -> tuple[float, float]:
		xalign = options.get("xalign")
		yalign = options.get("yalign")

		if not xalign or xalign == "center":
			x = x0 + w / 2 - fontw / 2 + options["pos"][0]
		elif xalign == "left":
			x = x0 + options["pos"][0]
		elif xalign == "right":
			x = x0 + w - fontw - options["pos"][0]
		else:
			x = x0 + w / 2 - fontw / 2 + options["pos"][0]
			log.error(f"invalid {xalign=}")

		if not yalign or yalign == "center":
			y = y0 + h / 2 - fonth / 2 + options["pos"][1]
		elif yalign == "top":
			y = y0 + options["pos"][1]
		elif yalign == "buttom":
			y = y0 + h - fonth - options["pos"][1]
		else:
			y = y0 + h / 2 - fonth / 2 + options["pos"][1]
			log.error(f"invalid {yalign=}")

		return (x, y)

	@staticmethod
	def getMonthName(
		c: CellType,
		calType: int,
		options: DayCalTypeWMOptionsDict,
	) -> str:
		month: int = c.dates[calType][1]
		abbreviate: bool = options.get("abbreviate", False)
		uppercase: bool = options.get("uppercase", False)
		text = getMonthName(calType, month, abbreviate=abbreviate)
		if uppercase:
			text = text.upper()
		return text

	def iterMonthOptions(self) -> Iterable[tuple[int, DayCalTypeWMOptionsDict]]:
		return (
			(calType, options)
			for calType, options in zip(
				calTypes.active,
				self.getMonthOptions(),
				strict=False,
			)
			if options.get("enable", True)
		)

	def getWeekdayLocalize(self) -> bool:
		if self.weekdayLocalize:
			return self.weekdayLocalize.v
		return True

	def getWeekdayAbbreviate(self) -> bool:
		if self.weekdayAbbreviate:
			return self.weekdayAbbreviate.v
		return False

	def drawAll(
		self,
		_widget: gtk.Widget | None = None,
		cr: ImageContext | None = None,
		cursor: bool = True,
	) -> None:
		if cr is None:
			self.w.queue_draw()
			return
		self._allButtons = self.drawing.drawAll(cr, cursor)

	def getOptionsWidget(self) -> gtk.Widget | None:
		return self.options.getOptionsWidget()

	def getSubPages(self) -> list[StackPageType]:
		return self.options.getSubPages()

	def onButtonPress(self, _obj: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		x, y = gevent.x, gevent.y

		double = gevent.type == gdk.EventType.DOUBLE_BUTTON_PRESS

		if b == 1:
			buttons = self._allButtons
			if buttons:
				w = self.w.get_allocation().width
				h = self.w.get_allocation().height
				for button in buttons:
					if button.contains(x, y, w, h):
						if not double:
							button.onPress(gevent)
						return True

		if b == 3:
			self.s.emit("popup-cell-menu", x, y)

		if double:
			self.s.emit("double-button-press")

		return True

	def jdPlus(self, p: int) -> None:
		ui.cells.jdPlus(p)
		self.broadcastDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		# if kname.startswith("alt"):
		# 	return True
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
		elif kname in {"page_up", "k", "p"}:
			self.jdPlus(-1)  # FIXME
		elif kname in {"page_down", "j", "n"}:
			self.jdPlus(1)  # FIXME
		# elif kname in ("f10", "m"):  # FIXME
		# 	if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
		# 		# Simulate right click (key beside Right-Ctrl)
		# 		self.s.emit("popup-cell-menu", *self.getCellPos())
		# 	else:
		# 		self.s.emit("popup-main-menu", *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool:
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-1)
			return False
		if d == "down":
			self.jdPlus(1)
			return False
		return False

	def getCellPos(self, *_args: Any) -> tuple[int, int]:
		alloc = self.w.get_allocation()
		return (
			int(alloc.width / 2),
			int(alloc.height / 2),
		)

	def onDateChange(self) -> None:
		super().onDateChange()
		self.w.queue_draw()

	# def onConfigChange(self) -> None:
	# 	super().onConfigChange()
	# 	# TODO: if active cal types are changed, we should re-order buttons
	# 	# hide extra buttons, and possibly add new buttons with their pages
	# 	# in Customize window
