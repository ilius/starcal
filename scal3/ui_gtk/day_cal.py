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
from scal3.ui import conf
from scal3.ui_gtk.cal_type_params import (
	MonthNameListParamsWidget,
	WeekDayNameParamsWidget,
)
from scal3.ui_gtk.pref_utils import FloatSpinPrefItem, IntSpinPrefItem, PrefItem

log = logger.get()


from math import isqrt
from typing import TYPE_CHECKING, Any, Protocol

from gi.repository.PangoCairo import show_layout

from scal3 import core, ui
from scal3.cal_types import calTypes
from scal3.drawing import getAbsPos
from scal3.locale_man import (
	getMonthName,
	langHasUppercase,
	langSh,
	rtl,
	textNumEncode,
)
from scal3.locale_man import tr as _
from scal3.season import getSeasonNamePercentFromJd
from scal3.ui.font import getParamsFont
from scal3.ui_gtk import (
	TWO_BUTTON_PRESS,
	GLibError,
	gdk,
	getScrollValue,
	gtk,
	pack,
)
from scal3.ui_gtk.button_drawing import BaseButton, Button, SVGButton
from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.customize import newSubPageButton
from scal3.ui_gtk.drawing import (
	ImageContext,
	drawPieOutline,
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import pixbufFromFile

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.cell_type import CellType
	from scal3.color_utils import ColorType
	from scal3.property import Property
	from scal3.ui.pytypes import (
		ButtonGeoDict,
		DayCalTypeBaseParamsDict,
		DayCalTypeDayParamsDict,
		DayCalTypeWMParamsDict,
		PieGeoDict,
	)

__all__ = ["DayCal", "ParentWindowType"]


class ParentWindowType(Protocol):
	w: gtk.Window

	def customizeShow(
		self,
		_widget: gtk.Widget,
	) -> None: ...


class DayCal(CalBase):
	objName = "dayCal"
	desc = _("Day Calendar")
	itemListCustomizable = False

	backgroundColor: Property[ColorType] | None = None
	dayParams: Property[list[DayCalTypeDayParamsDict]] | None = None
	monthParams: Property[list[DayCalTypeWMParamsDict]] | None = None
	weekdayParams: Property[DayCalTypeWMParamsDict] | None = None
	weekdayLocalize: Property[bool] | None = None
	weekdayAbbreviate: Property[bool] | None = None
	weekdayUppercase: Property[bool] | None = None

	widgetButtonsEnable: Property[bool] | None = None
	widgetButtonsSize: Property[int] | None = None
	widgetButtonsOpacity: Property[float] | None = None
	widgetButtons: Property[list[dict[str, Any]]] | None = None

	navButtonsEnable: Property[bool] | None = None
	navButtonsGeo: Property[ButtonGeoDict] | None = None
	navButtonsOpacity: Property[float] | None = None

	eventIconSize: Property[int] | None = None
	eventTotalSizeRatio: Property[float] | None = None

	seasonPieEnable: Property[bool] | None = None
	seasonPieGeo: Property[PieGeoDict] | None = None
	seasonPieColors: dict[str, Property[ColorType]] | None = None
	seasonPieTextColor: Property[ColorType] | None = None

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
		self.w: gtk.DrawingArea = gtk.DrawingArea()
		# FIXME: rename one of these two attrs:
		self.parentWin = win
		self._window: gtk.Window | None = None
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.subPages: list[StackPage] | None = None
		self._allButtons: list[BaseButton] = []
		# ----------------------
		# self.kTime = 0
		# ----------------------
		self.w.connect("draw", self.drawAll)
		self.w.connect("button-press-event", self.onButtonPress)
		# self.connect("screen-changed", self.screenChanged)
		self.w.connect("scroll-event", self.scroll)

	def getBackgroundColor(self) -> ColorType:
		if self.backgroundColor:
			return self.backgroundColor.v
		return conf.bgColor.v

	def getDayParams(self, allCalTypes: bool = False) -> list[DayCalTypeDayParamsDict]:
		if not self.dayParams:
			return []
		params = self.dayParams.v
		if allCalTypes:
			n = len(calTypes.active)
			while len(params) < n:
				params.append(
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
		return params

	def getMonthParams(
		self,
		allCalTypes: bool = False,
	) -> list[DayCalTypeWMParamsDict]:
		if not self.monthParams:
			return []
		params = self.monthParams.v
		if allCalTypes:
			n = len(calTypes.active)
			while len(params) < n:
				params.append(
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
		return params

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
		if rtl and geo["auto_rtl"]:
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
		print(gevent)
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
		win.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
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

	def updateTypeParamsWidget(self) -> list[StackPage]:
		from scal3.ui_gtk.cal_type_params import DayNumListParamsWidget

		monthParams = self.getMonthParams(allCalTypes=True)
		vbox = self.dayMonthParamsVbox
		for child in vbox.get_children():
			child.destroy()
		# ---
		subPages = []
		# ---
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		assert self.dayParams
		assert self.monthParams
		for index, calType in enumerate(calTypes.active):
			module = calTypes[calType]
			if module is None:
				raise RuntimeError(f"cal type '{calType}' not found")
			calTypeDesc = _("{calType} Calendar").format(
				calType=_(module.desc, ctx="calendar"),
			)
			# --
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			# ---
			dayWidget = DayNumListParamsWidget(
				params=self.dayParams,
				index=index,
				calType=calType,
				cal=self,
				sgroupLabel=sgroupLabel,
				hasEnable=True,
				enableTitleLabel=_("Day of Month"),
				useFrame=True,
			)
			pack(pageWidget, dayWidget)
			# ---
			monthWidget = MonthNameListParamsWidget(
				params=self.monthParams,
				index=index,
				calType=calType,
				cal=self,
				sgroupLabel=sgroupLabel,
				hasEnable=True,
				enableTitleLabel=_("Month Name"),
				useFrame=True,
			)
			monthWidget.show_all()
			page = StackPage()
			page.pageWidget = monthWidget
			page.pageName = module.name + "." + "month"
			page.pageParent = module.name
			page.pageTitle = _("Month Name") + " - " + calTypeDesc
			page.pageLabel = _("Month Name")
			page.pageExpand = False
			subPages.append(page)
			pack(pageWidget, newSubPageButton(self, page), padding=4)
			# ---
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			page.pageTitle = calTypeDesc
			page.pageLabel = calTypeDesc
			page.pageExpand = False
			subPages.append(page)
			self.buttons1.append(newSubPageButton(self, page))
			# ---
			c = self.getCell()
			dayWidget.setFontPreviewText(
				_(c.dates[calType][2], calType=calTypes.primary),
			)
			monthWidget.setFontPreviewText(
				self.getMonthName(c, calType, monthParams[index]),
			)
		# ---
		vbox.show_all()
		return subPages

	def getWindow(self) -> gtk.Window:
		assert self._window is not None
		return self._window

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.pref_utils import (
			CheckPrefItem,
			ColorPrefItem,
		)

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		subPages = []
		prefItem: PrefItem
		# ---
		buttons1: list[gtk.Button] = []
		buttons2: list[gtk.Button] = []
		self.buttons1 = buttons1
		# ----
		if self.backgroundColor:
			prefItem = ColorPrefItem(
				prop=self.backgroundColor,
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			pack(hbox, gtk.Label(label=_("Background") + ": "))
			pack(hbox, prefItem.getWidget())
			pack(hbox, gtk.Label(), 1, 1)
			pack(optionsWidget, hbox)
		# --------
		self.dayMonthParamsVbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		pack(optionsWidget, self.dayMonthParamsVbox)
		subPages += self.updateTypeParamsWidget()
		# ----
		pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
		page = StackPage()
		page.pageWidget = pageWidget
		page.pageName = "buttons"
		page.pageTitle = _("Buttons")
		page.pageLabel = _("Buttons")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(self, page))
		# ---
		if self.widgetButtonsEnable:
			prefItem = CheckPrefItem(
				prop=self.widgetButtonsEnable,
				label=_("Widget Buttons"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		if self.widgetButtonsSize:
			prefItem = IntSpinPrefItem(
				prop=self.widgetButtonsSize,
				bounds=(0, 99),
				step=1,
				label=_("Widget Buttons Size"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		if self.widgetButtonsOpacity:
			prefItem = FloatSpinPrefItem(
				prop=self.widgetButtonsOpacity,
				bounds=(0, 1),
				digits=2,
				step=0.1,
				label=_("Widget Buttons Opacity"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		if self.navButtonsEnable:
			prefItem = CheckPrefItem(
				prop=self.navButtonsEnable,
				label=_("Navigation buttons"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
		pageWidget.show_all()
		# -----
		if self.weekdayParams:
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			# ---
			weekdayWidget = WeekDayNameParamsWidget(
				params=self.weekdayParams,
				cal=self,
				# sgroupLabel=None,
				desc=_("Week Day"),
				hasEnable=True,
			)
			pack(pageWidget, weekdayWidget)
			# ---
			if self.weekdayLocalize and langSh != "en":
				prefItem = CheckPrefItem(
					prop=self.weekdayLocalize,
					label=_("Localize"),
					live=True,
					onChangeFunc=self.w.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			if self.weekdayAbbreviate:
				prefItem = CheckPrefItem(
					prop=self.weekdayAbbreviate,
					label=_("Abbreviate"),
					live=True,
					onChangeFunc=self.w.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			if langHasUppercase and self.weekdayUppercase:
				prefItem = CheckPrefItem(
					prop=self.weekdayUppercase,
					label=_("Uppercase"),
					live=True,
					onChangeFunc=self.w.queue_draw,
				)
				pack(pageWidget, prefItem.getWidget())
			# ---
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "weekday"
			page.pageTitle = _("Week Day")
			page.pageLabel = _("Week Day")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(self, page))
			# ---
			c = self.getCell()
			text = core.getWeekDayAuto(
				c.weekDay,
				localize=self.getWeekdayLocalize(),
				abbreviate=self.getWeekdayAbbreviate(),
				relative=False,
			)
			weekdayWidget.setFontPreviewText(text)
		# --------
		vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		page = StackPage()
		page.pageWidget = vbox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events")
		page.pageExpand = False
		subPages.append(page)
		buttons2.append(newSubPageButton(self, page))
		# ---
		if self.eventIconSize:
			prefItem = IntSpinPrefItem(
				prop=self.eventIconSize,
				bounds=(5, 999),
				step=1,
				label=_("Icon Size"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(vbox, prefItem.getWidget())
		# ---
		if self.eventTotalSizeRatio:
			prefItem = FloatSpinPrefItem(
				prop=self.eventTotalSizeRatio,
				bounds=(0, 1),
				digits=3,
				step=0.01,
				label=_("Total Size Ratio"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(vbox, prefItem.getWidget())
		# ----
		if self.seasonPieEnable:
			pageWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = "seasonPie"
			page.pageTitle = _("Season Pie")
			page.pageLabel = _("Season Pie")
			page.pageExpand = False
			subPages.append(page)
			buttons2.append(newSubPageButton(self, page))
			# ---
			prefItem = CheckPrefItem(
				prop=self.seasonPieEnable,
				label=_("Season Pie"),
				live=True,
				onChangeFunc=self.w.queue_draw,
			)
			pack(pageWidget, prefItem.getWidget())
			# ---
			frame = gtk.Frame()
			frame.set_border_width(5)
			frame.set_label(_("Colors"))
			grid = gtk.Grid()
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			grid.set_row_spacing(3)
			grid.set_border_width(5)
			frame.add(grid)
			pack(pageWidget, frame)
			assert self.seasonPieColors is not None
			for index, season in enumerate(("Spring", "Summer", "Autumn", "Winter")):
				hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
				label = gtk.Label(label=_(season))
				label.set_xalign(0)
				prefItem = ColorPrefItem(
					prop=self.seasonPieColors[season],
					useAlpha=True,
					live=True,
					onChangeFunc=self.w.queue_draw,
				)
				row_index = int(index / 2)
				column_index = index % 2 * 3
				grid.attach(
					label,
					column_index,
					row_index,
					1,
					1,
				)
				grid.attach(
					prefItem.getWidget(),
					column_index + 1,
					row_index,
					1,
					1,
				)
				dummyLabel = gtk.Label()
				dummyLabel.set_hexpand(True)
				grid.attach(
					dummyLabel,
					column_index + 2,
					row_index,
					1,
					1,
				)
			pageWidget.show_all()
		# ----
		for buttons in (buttons1, buttons2):
			grid = gtk.Grid()
			grid.set_row_homogeneous(True)
			grid.set_column_homogeneous(True)
			grid.set_row_spacing(5)
			grid.set_column_spacing(5)
			for index, button in enumerate(buttons):
				grid.attach(
					button,
					index % 2,
					index // 2,
					1,
					1,
				)
			grid.show_all()
			pack(optionsWidget, grid, padding=5)
		# ---
		vbox.show_all()
		# --------
		self.subPages = subPages
		self.optionsWidget = optionsWidget
		# ---
		optionsWidget.show_all()
		return optionsWidget

	def getSubPages(self) -> list[StackPage]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		assert self.subPages is not None
		return self.subPages

	@staticmethod
	def getRenderPos(
		params: DayCalTypeBaseParamsDict,
		x0: float,
		y0: float,
		w: float,
		h: float,
		fontw: float,
		fonth: float,
	) -> tuple[float, float]:
		xalign = params.get("xalign")
		yalign = params.get("yalign")

		if not xalign or xalign == "center":
			x = x0 + w / 2 - fontw / 2 + params["pos"][0]
		elif xalign == "left":
			x = x0 + params["pos"][0]
		elif xalign == "right":
			x = x0 + w - fontw - params["pos"][0]
		else:
			x = x0 + w / 2 - fontw / 2 + params["pos"][0]
			log.error(f"invalid {xalign=}")

		if not yalign or yalign == "center":
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
		elif yalign == "top":
			y = y0 + params["pos"][1]
		elif yalign == "buttom":
			y = y0 + h - fonth - params["pos"][1]
		else:
			y = y0 + h / 2 - fonth / 2 + params["pos"][1]
			log.error(f"invalid {yalign=}")

		return (x, y)

	@classmethod
	def getCell(cls) -> CellType:
		return ui.cells.current

	def drawAll(
		self,
		_widget: gtk.Widget | None = None,
		cr: ImageContext | None = None,
		cursor: bool = True,
	) -> None:
		win = self.w.get_window()
		assert win is not None
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		if cr is None:
			cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr, cursor)
		finally:
			win.end_draw_frame(dctx)

	def drawEventIcons(
		self,
		cr: ImageContext,
		c: CellType,
		w: int,
		h: int,
		x0: int,
		y0: int,
	) -> None:
		if not self.eventTotalSizeRatio:
			return
		assert self.eventIconSize
		iconList = c.getDayEventIcons()
		if not iconList:
			return
		iconsN = len(iconList)

		maxTotalSize = self.eventTotalSizeRatio.v * min(w, h)
		sideCount = isqrt(iconsN - 1) + 1
		iconSize = min(
			self.eventIconSize.v,
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

	@staticmethod
	def getMonthName(
		c: CellType,
		calType: int,
		params: DayCalTypeWMParamsDict,
	) -> str:
		month: int = c.dates[calType][1]
		abbreviate: bool = params.get("abbreviate", False)
		uppercase: bool = params.get("uppercase", False)
		text = getMonthName(calType, month, abbreviate=abbreviate)
		if uppercase:
			text = text.upper()
		return text

	def iterMonthParams(self) -> Iterable[tuple[int, DayCalTypeWMParamsDict]]:
		return (
			(calType, params)
			for calType, params in zip(
				calTypes.active,
				self.getMonthParams(),
				strict=False,
			)
			if params.get("enable", True)
		)

	def getWeekdayLocalize(self) -> bool:
		if self.weekdayLocalize:
			return self.weekdayLocalize.v
		return True

	def getWeekdayAbbreviate(self) -> bool:
		if self.weekdayAbbreviate:
			return self.weekdayAbbreviate.v
		return False

	def drawSeasonPie(self, cr: ImageContext, w: float, h: float) -> None:
		if not self.seasonPieEnable:
			return

		if not self.seasonPieEnable.v:
			return

		assert self.seasonPieGeo is not None
		assert self.seasonPieColors is not None
		assert self.seasonPieTextColor is not None

		seasonName, seasonFrac = getSeasonNamePercentFromJd(
			self.getCell().jd,
			conf.seasonPBar_southernHemisphere.v,
		)

		geo = self.seasonPieGeo.v
		color = self.seasonPieColors[seasonName].v
		textColor = self.seasonPieTextColor.v
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
			self.w,
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

	def drawWithContext(self, cr: ImageContext, _cursor: bool) -> None:
		# gevent = gtk.get_current_event()
		w = self.w.get_allocation().width
		h = self.w.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, self.getBackgroundColor())
		# -----
		c = self.getCell()
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
		for calType, dparams in zip(
			calTypes.active,
			self.getDayParams(),
			strict=False,
		):
			if not dparams.get("enable", True):
				continue
			dayNum = c.dates[calType][2]
			if dparams.get("localize", False):
				dayStr = _(dayNum)
			else:
				dayStr = str(dayNum)
			layout = newTextLayout(
				self.w,
				dayStr,
				getParamsFont(dparams),
			)
			assert layout is not None
			fontw, fonth = layout.get_pixel_size()
			if calType == calTypes.primary and c.holiday:
				setColor(cr, conf.holidayColor.v)
			else:
				setColor(cr, dparams["color"])
			font_x, font_y = self.getRenderPos(dparams, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		for calType, mparams in self.iterMonthParams():
			text = self.getMonthName(c, calType, mparams)
			layout = newTextLayout(
				self.w,
				text,
				getParamsFont(mparams),
			)
			assert layout is not None
			fontw, fonth = layout.get_pixel_size()
			setColor(cr, mparams["color"])
			font_x, font_y = self.getRenderPos(mparams, x0, y0, w, h, fontw, fonth)
			cr.move_to(font_x, font_y)
			show_layout(cr, layout)

		if self.weekdayParams:
			wparams = self.weekdayParams.v
			if wparams.get("enable", True):
				text = core.getWeekDayAuto(
					c.weekDay,
					localize=self.getWeekdayLocalize(),
					abbreviate=self.getWeekdayAbbreviate(),
					relative=False,
				)
				if (
					langHasUppercase
					and self.weekdayUppercase
					and self.weekdayUppercase.v
				):
					text = text.upper()
				daynum = newTextLayout(
					self.w,
					text,
					getParamsFont(wparams),
				)
				assert daynum is not None
				fontw, fonth = daynum.get_pixel_size()
				setColor(cr, wparams["color"])
				font_x, font_y = self.getRenderPos(wparams, x0, y0, w, h, fontw, fonth)
				cr.move_to(font_x, font_y)
				show_layout(cr, daynum)

		self.drawSeasonPie(cr, w, h)

		self._allButtons = self.getAllButtons()
		for button in self._allButtons:
			button.draw(cr, w, h)

	def onButtonPress(self, _obj: gtk.Widget, gevent: gdk.EventButton) -> bool:
		b = gevent.button
		x, y = gevent.x, gevent.y

		double = gevent.type == TWO_BUTTON_PRESS

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
