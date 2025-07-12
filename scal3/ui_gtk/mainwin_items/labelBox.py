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
from scal3.ui import conf

log = logger.get()

from time import time as now
from typing import TYPE_CHECKING

from scal3 import locale_man, ui
from scal3.cal_types import calTypes
from scal3.color_utils import colorizeSpan
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.ui_gtk import (
	Menu,
	MenuItem,
	gdk,
	getScrollValue,
	gtk,
	pack,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.drawing import calcTextPixelSize
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk.gtk_ud import CalObjWidget, commonSignals
from scal3.ui_gtk.mywidgets.button import ConButton
from scal3.ui_gtk.signals import SignalHandlerBase, SignalHandlerType, registerSignals
from scal3.ui_gtk.utils import (
	get_menu_width,
	imageFromIconName,
	pixbufFromFile,
	set_tooltip,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk.option_ui import OptionUI
	from scal3.ui_gtk.starcal_types import MainWinType

__all__ = ["CalObj"]

primaryCalStyleClass = "primarycal"


class BaseLabel(CustomizableCalObj):
	vertical = False

	def __init__(self, calType: int) -> None:
		super().__init__()
		self.w: gtk.EventBox = gtk.EventBox()
		self.calType = calType


class MonthLabel(BaseLabel):
	styleClass = "monthlabel"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		if conf.labelBoxMonthColorEnable.v:
			return (
				"."
				+ MonthLabel.styleClass
				+ " "
				+ cssTextStyle(
					fgColor=conf.labelBoxMonthColor.v,
				)
			)
		return ""

	@staticmethod
	def getItemStr(i: int) -> str:
		return _(i + 1, fillZero=2)

	@classmethod
	def getActiveStr(cls, s: str) -> str:
		return colorizeSpan(s, conf.labelBoxMenuActiveColor.v)
		# return f"<b>{s}</b>"

	def __init__(self, calType: int, active: int = 0) -> None:
		BaseLabel.__init__(self, calType)
		self.w.get_style_context().add_class(self.styleClass)
		# ---
		self.objName = f"monthLabel({calType})"
		# self.set_border_width(1)#???????????
		self.initVars()
		# ---
		if calType == calTypes.primary:
			self.w.get_style_context().add_class(primaryCalStyleClass)
		# ---
		self.label = gtk.Label()
		self.label.set_use_markup(True)
		self.w.add(self.label)
		self.menu = Menu()
		self.menu.set_border_width(0)
		self.menuLabels: list[gtk.Label] = []
		self.w.connect("button-press-event", self.onButtonPress)
		self.active = active
		self.setActive(active)

	def createMenuLabels(self) -> None:
		if self.menuLabels:
			return
		for i in range(12):
			if ui.monthRMenuNum:
				text = self.getItemStr(i) + ": " + _(getMonthName(self.calType, i + 1))
			else:
				text = _(getMonthName(self.calType, i + 1))
			if i == self.active:
				text = self.getActiveStr(text)
			item = MenuItem()
			label = item.get_child()
			assert isinstance(label, gtk.Label), f"{label=}"
			label.set_label(text)
			# label.set_justify(gtk.Justification.LEFT)
			label.set_xalign(0)
			label.set_use_markup(True)
			item.set_right_justified(True)  # ?????????
			item.connect("activate", self.itemActivate, i)
			self.menu.append(item)
			self.menuLabels.append(label)
		self.menu.show_all()

	def setActive(self, active: int) -> None:
		# (Performance) update menu here, or make menu entirly
		# before popup?
		newStr = getMonthName(self.calType, active + 1)
		oldStr = getMonthName(self.calType, self.active + 1)
		if self.menuLabels:
			if ui.monthRMenuNum:
				self.menuLabels[self.active].set_label(
					self.getItemStr(self.active) + ": " + oldStr,
				)
				self.menuLabels[active].set_label(
					self.getActiveStr(
						self.getItemStr(active) + ": " + newStr,
					),
				)
			else:
				self.menuLabels[self.active].set_label(oldStr)
				self.menuLabels[active].set_label(self.getActiveStr(newStr))
		self.label.set_label(newStr)
		self.active = active

	def changeCalType(self, calType: int) -> None:
		self.calType = calType
		self.label.set_label(getMonthName(self.calType, self.active + 1))
		for i in range(12):
			if ui.monthRMenuNum:
				s = self.getItemStr(i) + ": " + getMonthName(self.calType, i + 1)
			else:
				s = getMonthName(self.calType, i + 1)
			if i == self.active:
				s = self.getActiveStr(s)
			self.menuLabels[i].set_label(s)

	def itemActivate(self, _item: MenuItem, index: int) -> None:
		y, m, d = ui.cells.current.dates[self.calType]
		m = index + 1
		ui.cells.changeDate(y, m, d, self.calType)
		self.broadcastDateChange()

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 3:
			self.createMenuLabels()
			win = self.w.get_window()
			assert win is not None
			_foo, x, y = win.get_origin()
			# foo == 1, doc says "not meaningful, ignore"
			y += self.w.get_allocation().height
			# align menu to center:
			x -= int(
				(get_menu_width(self.menu) - self.w.get_allocation().width) // 2,
			)
			self.menu.popup(
				None,
				None,
				lambda *_args: (x, y, True),
				None,
				gevent.button,
				gevent.time,
			)
			ui.updateFocusTime()
			return True

		return False

	def onDateChange(self) -> None:
		super().onDateChange()
		self.setActive(ui.cells.current.dates[self.calType][1] - 1)


@registerSignals
class IntLabelSignalHandler(SignalHandlerBase):
	signals = commonSignals + [
		("changed", [int]),
	]


class IntLabel(BaseLabel):
	Sig = IntLabelSignalHandler

	@classmethod
	def getActiveStr(cls, s: str) -> str:
		return colorizeSpan(s, conf.labelBoxMenuActiveColor.v)

	def __init__(self, calType: int, height: int = 9, active: int = 0) -> None:
		BaseLabel.__init__(self, calType)
		# self.set_border_width(1)#???????????
		self.height = height
		# self.delay = delay
		self.label = gtk.Label()
		self.label.set_use_markup(True)
		self.w.add(self.label)
		self.menu: Menu | None = None
		self.w.connect("button-press-event", self.onButtonPress)
		self.active = active
		self.setActive(active)
		self.start = 0
		self.remain = 0
		self.ymPressTime = 0
		self.etime = 0.0
		self.step = 0

	def setActive(self, active: int) -> None:
		text = _(active)
		self.label.set_label(text)
		self.active = active

	def createMenu(self) -> None:
		if self.menu:
			return
		self.menu = Menu()
		self.menu.set_direction(gtk.TextDirection.LTR)
		self.menuLabels = []
		self.menu.connect("scroll-event", self.menuScroll)
		# ----------
		item = gtk.MenuItem()
		item.add(
			imageFromIconName(
				"pan-up-symbolic",
				gtk.IconSize.MENU,
			),
		)
		# item.set_border_width(0)
		# log.debug(item.style_get_property("horizontal-padding") # OK)
		# ???????????????????????????????????
		# item.config("horizontal-padding"=0)
		# style = item.get_style()
		# style.set_property("horizontal-padding", 0)
		# item.set_style(style)
		self.menu.append(item)
		item.connect("select", self.arrowSelect, -1)
		item.connect("deselect", self.arrowDeselect)
		item.connect("activate", lambda _w: False)
		# ----------
		for i in range(self.height):
			item = MenuItem()
			label = item.get_child()
			assert isinstance(label, gtk.Label), f"{label=}"
			label.set_use_markup(True)
			label.set_direction(gtk.TextDirection.LTR)
			item.connect("activate", self.itemActivate, i)
			self.menu.append(item)
			self.menuLabels.append(label)
		# ----------
		item = gtk.MenuItem()
		item.add(
			imageFromIconName(
				"pan-down-symbolic",
				gtk.IconSize.MENU,
			),
		)
		self.menu.append(item)
		item.connect("select", self.arrowSelect, 1)
		item.connect("deselect", self.arrowDeselect)
		# ----------
		self.menu.show_all()

	def updateMenu(self, start: int | None = None) -> None:
		self.createMenu()
		if start is None:
			start = self.active - self.height // 2
		self.start = start
		for i in range(self.height):
			if start + i == self.active:
				self.menuLabels[i].set_label(
					self.getActiveStr(_(start + i)),
				)
			else:
				self.menuLabels[i].set_label(_(start + i))

	def itemActivate(self, _item: MenuItem, index: int) -> None:
		self.setActive(self.start + index)
		self.s.emit("changed", self.start + index)

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 3:
			self.updateMenu()
			assert self.menu is not None
			win = self.w.get_window()
			assert win is not None
			_foo, x, y = win.get_origin()
			y += self.w.get_allocation().height
			x -= 6  # FIXME: because of menu padding
			self.menu.popup(
				None,
				None,
				lambda *_args: (x, y, True),
				None,
				gevent.button,
				gevent.time,
			)
			ui.updateFocusTime()
			return True

		return False

	def arrowSelect(self, _item: MenuItem, plus: int) -> None:
		self.remain = plus
		timeout_add(
			int(ui.labelMenuDelay * 1000),
			self.arrowRemain,
			plus,
		)

	def arrowDeselect(self, _item: gtk.Widget) -> None:
		self.remain = 0

	def arrowRemain(self, plus: int) -> bool:
		t = now()
		# log.debug(t - self.etime)
		if self.remain == plus:
			if t - self.etime < ui.labelMenuDelay - 0.02:
				if self.step > 1:
					self.step = 0
					return False
				self.step += 1
				self.etime = t  # FIXME
				return True

			self.updateMenu(self.start + plus)
			self.etime = t
			return True

		return False

	def menuScroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool | None:
		d = getScrollValue(gevent)
		if d == "up":
			self.updateMenu(self.start - 1)
			return None

		if d == "down":
			self.updateMenu(self.start + 1)
			return None

		return False


class YearLabel(IntLabel):
	styleClass = "yearlabel"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		if conf.labelBoxYearColorEnable.v:
			return (
				"."
				+ YearLabel.styleClass
				+ " "
				+ cssTextStyle(
					fgColor=conf.labelBoxYearColor.v,
				)
			)
		return ""

	def __init__(self, calType: int) -> None:
		IntLabel.__init__(self, calType=calType)
		self.objName = f"yearLabel({calType})"
		self.initVars()
		# ---
		self.w.get_style_context().add_class(self.styleClass)
		if calType == calTypes.primary:
			self.w.get_style_context().add_class(primaryCalStyleClass)
		# ---
		self.s.connect("changed", self.onChanged)

	def onChanged(self, _sig: SignalHandlerType, year: int) -> None:
		calType = self.calType
		_y, m, d = ui.cells.current.dates[calType]
		ui.cells.changeDate(year, m, d, calType)
		self.broadcastDateChange()

	def changeCalType(self, calType: int) -> None:
		self.calType = calType
		# self.broadcastDateChange()

	def onDateChange(self) -> None:
		super().onDateChange()
		self.setActive(ui.cells.current.dates[self.calType][0])

	def setActive(self, active: int) -> None:
		text = _(active)
		self.label.set_label(text)
		self.active = active


class SmallNoFocusButton(ConButton):
	def __init__(
		self,
		imageName: str,
		func: Callable[[gtk.Widget], None],
		tooltip: str = "",
	) -> None:
		ConButton.__init__(self, continuousClick=True)
		self.set_relief(gtk.ReliefStyle.NONE)
		self.set_can_focus(False)
		self._imageName = imageName
		self._image = gtk.Image()
		self.updateIcon()
		self.add(self._image)
		self.connect("con-clicked", func)
		if tooltip:
			set_tooltip(self, tooltip)

	def updateIcon(self) -> None:
		self._image.set_from_pixbuf(
			pixbufFromFile(
				self._imageName,
				size=conf.labelBoxIconSize.v,
			),
		)


class YearLabelButtonBox(CalObjWidget):
	def __init__(self, calType: int) -> None:
		self.w: gtk.Box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		# ---
		self.removeButton = SmallNoFocusButton(
			"list-remove.svg",
			self.onPrevClick,
			_("Previous Year"),
		)
		self.addButton = SmallNoFocusButton(
			"list-add.svg",
			self.onNextClick,
			_("Next Year"),
		)
		pack(self.w, self.removeButton)
		# ---
		self.label = YearLabel(calType)
		pack(self.w, self.label.w)
		self.appendItem(self.label)
		# ---
		pack(self.w, self.addButton)

	def onPrevClick(self, _b: gtk.Widget) -> None:
		ui.cells.yearPlus(-1)
		self.label.broadcastDateChange()
		# self.label.s.emit("date-change")

	def onNextClick(self, _b: gtk.Widget) -> None:
		ui.cells.yearPlus(1)
		self.label.broadcastDateChange()
		# self.label.s.emit("date-change")

	def changeCalType(self, calType: int) -> None:
		self.label.changeCalType(calType)

	def onFontConfigChange(self) -> None:
		self.removeButton.updateIcon()
		self.addButton.updateIcon()


class MonthLabelButtonBox(CalObjWidget):
	def __init__(self, calType: int) -> None:
		self.w = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		self.removeButton = SmallNoFocusButton(
			"list-remove.svg",
			self.onPrevClick,
			_("Previous Month"),
		)
		self.addButton = SmallNoFocusButton(
			"list-add.svg",
			self.onNextClick,
			_("Next Month"),
		)
		# ---
		pack(self.w, self.removeButton)
		# ---
		self.label = MonthLabel(calType)
		pack(self.w, self.label.w)
		self.appendItem(self.label)
		# ---
		pack(self.w, self.addButton)

	def onPrevClick(self, _b: gtk.Widget) -> None:
		ui.cells.monthPlus(-1)
		self.label.broadcastDateChange()

	def onNextClick(self, _b: gtk.Widget) -> None:
		ui.cells.monthPlus(1)
		self.label.broadcastDateChange()

	def changeCalType(self, calType: int) -> None:
		self.label.changeCalType(calType)

	def onFontConfigChange(self) -> None:
		self.removeButton.updateIcon()
		self.addButton.updateIcon()


class CalObj(CustomizableCalObj):
	objName = "labelBox"
	desc = _("Year & Month Bar")
	itemListCustomizable = False
	hasOptions = True
	styleClass = "labelbox"

	@staticmethod
	def getFont() -> ui.Font:
		if conf.labelBoxFontEnable.v and conf.labelBoxFont.v:
			font = conf.labelBoxFont.v.copy()  # make a copy to be safe to modify
		else:
			font = ui.getFont()
		if conf.boldYmLabel.v:
			font.bold = True
		return font

	def __init__(self, win: MainWinType) -> None:
		super().__init__()
		self.win = win
		self.w: gtk.Box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		self.w.get_style_context().add_class(self.styleClass)
		# self.set_border_width(2)
		self.ybox: YearLabelButtonBox | None = None
		self.mbox: MonthLabelButtonBox | None = None
		self.monthLabels: list[MonthLabel] = []
		self.onBorderWidthChange()
		# self.onConfigChange()

	@staticmethod
	def newSeparator() -> gtk.Widget:
		# return gtk.VSeparator()
		return gtk.Label()

	def updateIconSize(self) -> None:
		alphabet = locale_man.getAlphabet()
		height = calcTextPixelSize(self.win.w, alphabet, font=self.getFont())[1]
		conf.labelBoxIconSize.v = int(height * 0.6)

	def updateTextWidth(self) -> None:
		font = self.getFont()
		pfont = pfontEncode(font)
		lay = self.w.create_pango_layout("")
		lay.set_font_description(pfont)
		for label in self.monthLabels:
			wm = 0
			for m in range(12):
				name = getMonthName(label.calType, m)
				lay.set_text(
					text=name,
					length=-1,
				)
				# OR lay.set_markup
				w = lay.get_pixel_size()[0]
				wm = max(w, wm)
			label.w.set_property("width-request", wm)

	@staticmethod
	def getFontPreviewText(calType: int) -> str:
		date = ui.cells.current.dates[calType]
		year = _(date[0])
		month = getMonthName(calType, date[1])
		return f"{year} {month}"

	def getFontPreviewTextFull(self) -> str:
		return " ".join(
			[self.getFontPreviewText(calType) for calType in calTypes.active],
		)

	def onConfigChange(self) -> None:
		super().onConfigChange()
		# -----
		self.updateIconSize()
		# ----
		self.items = []
		for child in self.w.get_children():
			child.destroy()
		# ---
		monthLabels = []
		calType = calTypes.primary
		# --
		ybox = YearLabelButtonBox(calType)
		pack(self.w, ybox.w)
		# FIXME: self.appendItem(ybox)  and self.appendItem(mbox)
		self.appendItem(ybox.label)
		self.ybox = ybox
		# --
		pack(self.w, self.newSeparator(), 1, 1)
		# --
		mbox = MonthLabelButtonBox(calType)
		pack(self.w, mbox.w)
		self.appendItem(mbox.label)
		monthLabels.append(mbox.label)
		self.mbox = mbox
		# ----
		label: CustomizableCalObj
		for _i, calType in list(enumerate(calTypes.active))[1:]:
			pack(self.w, self.newSeparator(), 1, 1)
			label = YearLabel(calType)
			pack(self.w, label.w)
			self.appendItem(label)
			# ---------------
			label = MonthLabel(calType)
			pack(self.w, label.w, padding=5)
			monthLabels.append(label)
			self.appendItem(label)
		# ----
		self.monthLabels = monthLabels
		self.updateTextWidth()
		# -----
		self.w.show_all()
		# -----
		self.broadcastDateChange()

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		font = CalObj.getFont()
		css = (
			"."
			+ CalObj.styleClass
			+ " "
			+ cssTextStyle(
				font=font,
			)
		)
		if conf.labelBoxPrimaryFontEnable.v and conf.labelBoxPrimaryFont.v:
			font = conf.labelBoxPrimaryFont.v
			if conf.boldYmLabel.v:
				font = font.copy()
				font.bold = True
			css += (
				"\n."
				+ CalObj.styleClass
				+ " ."
				+ primaryCalStyleClass
				+ " "
				+ cssTextStyle(
					font=font,
				)
			)
		return css

	def onFontConfigChange(self) -> None:
		ud.windowList.updateCSS()
		self.updateIconSize()
		if self.ybox:
			self.ybox.onFontConfigChange()
		if self.mbox:
			self.mbox.onFontConfigChange()
		self.updateTextWidth()

	def onBorderWidthChange(self) -> None:
		self.w.set_border_width(conf.labelBoxBorderWidth.v)

	def onMenuColorChange(self) -> None:
		self.onDateChange()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui import (
			CheckColorOptionUI,
			CheckFontOptionUI,
			CheckOptionUI,
			ColorOptionUI,
			FontOptionUI,
			IntSpinOptionUI,
		)

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
		option: OptionUI
		# ----
		option = IntSpinOptionUI(
			option=conf.labelBoxBorderWidth,
			bounds=(0, 99),
			step=1,
			unitLabel=_("pixels"),
			label=_("Border Width"),
			live=True,
			onChangeFunc=self.onBorderWidthChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		pack(hbox, gtk.Label(label=_("Active menu item color")))
		option = ColorOptionUI(
			option=conf.labelBoxMenuActiveColor,
			live=True,
			onChangeFunc=self.onMenuColorChange,
		)
		pack(hbox, option.getWidget())
		pack(optionsWidget, hbox)
		# ---
		checkSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		option = CheckColorOptionUI(
			CheckOptionUI(option=conf.labelBoxYearColorEnable, label=_("Year Color")),
			ColorOptionUI(option=conf.labelBoxYearColor, useAlpha=True),
			checkSizeGroup=checkSizeGroup,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		option = CheckColorOptionUI(
			CheckOptionUI(option=conf.labelBoxMonthColorEnable, label=_("Month Color")),
			ColorOptionUI(option=conf.labelBoxMonthColor, useAlpha=True),
			checkSizeGroup=checkSizeGroup,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		previewText = self.getFontPreviewTextFull()
		option = CheckFontOptionUI(
			CheckOptionUI(option=conf.labelBoxFontEnable, label=_("Font")),
			FontOptionUI(option=conf.labelBoxFont, previewText=previewText),
			live=True,
			onChangeFunc=self.onFontConfigChange,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		previewText = self.getFontPreviewText(calTypes.primary)
		option = CheckFontOptionUI(
			CheckOptionUI(
				option=conf.labelBoxPrimaryFontEnable,
				label=_("Primary Calendar Font"),
			),
			FontOptionUI(option=conf.labelBoxPrimaryFont, previewText=previewText),
			vertical=True,
			spacing=0,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		option = CheckOptionUI(
			option=conf.boldYmLabel,
			label=_("Bold Font"),
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return self.optionsWidget
