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
from scal3 import logger
from scal3.ui import conf

log = logger.get()

from time import time as now

from scal3 import locale_man, ui
from scal3.cal_types import calTypes
from scal3.color_utils import colorizeSpan
from scal3.locale_man import getMonthName
from scal3.locale_man import tr as _
from scal3.ui_gtk import (
	HBox,
	Menu,
	MenuItem,
	VBox,
	gdk,
	getScrollValue,
	gtk,
	pack,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.drawing import (
	calcTextPixelSize,
)
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk.mywidgets.button import ConButton
from scal3.ui_gtk.utils import (
	get_menu_width,
	imageFromIconName,
	pixbufFromFile,
	set_tooltip,
)

__all__ = ["CalObj"]
primaryCalStyleClass = "primarycal"


class BaseLabel(gtk.EventBox):
	def __init__(self):
		gtk.EventBox.__init__(self)


@registerSignals
class MonthLabel(BaseLabel, ud.BaseCalObj):
	styleClass = "monthlabel"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		if conf.labelBoxMonthColorEnable:
			return (
				"."
				+ MonthLabel.styleClass
				+ " "
				+ cssTextStyle(
					fgColor=conf.labelBoxMonthColor,
				)
			)
		return ""

	@staticmethod
	def getItemStr(i):
		return _(i + 1, fillZero=2)

	@classmethod
	def getActiveStr(cls, s):
		return colorizeSpan(s, conf.labelBoxMenuActiveColor)
		# return f"<b>{s}</b>"

	def __init__(self, calType, active=0):
		BaseLabel.__init__(self)
		self.get_style_context().add_class(self.styleClass)
		# ---
		self.objName = f"monthLabel({calType})"
		# self.set_border_width(1)#???????????
		self.initVars()
		self.calType = calType
		# ---
		if calType == calTypes.primary:
			self.get_style_context().add_class(primaryCalStyleClass)
		# ---
		self.label = gtk.Label()
		self.label.set_use_markup(True)
		self.add(self.label)
		self.menu = Menu()
		self.menu.set_border_width(0)
		self.menuLabels = []
		self.connect("button-press-event", self.onButtonPress)
		self.active = active
		self.setActive(active)

	def createMenuLabels(self):
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
			label.set_label(text)
			# label.set_justify(gtk.Justification.LEFT)
			label.set_xalign(0)
			label.set_use_markup(True)
			item.set_right_justified(True)  # ?????????
			item.connect("activate", self.itemActivate, i)
			self.menu.append(item)
			self.menuLabels.append(label)
		self.menu.show_all()

	def setActive(self, active):
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

	def changeCalType(self, calType):
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

	def itemActivate(self, _item, index):
		y, m, d = ui.cells.current.dates[self.calType]
		m = index + 1
		ui.cells.changeDate(y, m, d, self.calType)
		self.onDateChange()

	def onButtonPress(self, _widget, gevent):
		if gevent.button == 3:
			self.createMenuLabels()
			_foo, x, y = self.get_window().get_origin()
			# foo == 1, doc says "not meaningful, ignore"
			y += self.get_allocation().height
			# align menu to center:
			x -= int(
				(get_menu_width(self.menu) - self.get_allocation().width) // 2,
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

	def onDateChange(self, *a, **ka):
		ud.BaseCalObj.onDateChange(self, *a, **ka)
		self.setActive(ui.cells.current.dates[self.calType][1] - 1)


@registerSignals
class IntLabel(BaseLabel):
	signals = [
		("changed", [int]),
	]

	@classmethod
	def getActiveStr(cls, s):
		return colorizeSpan(s, conf.labelBoxMenuActiveColor)

	def __init__(self, height=9, active=0):
		BaseLabel.__init__(self)
		# self.set_border_width(1)#???????????
		self.height = height
		# self.delay = delay
		self.label = gtk.Label()
		self.label.set_use_markup(True)
		self.add(self.label)
		self.menu = None
		self.connect("button-press-event", self.onButtonPress)
		self.active = active
		self.setActive(active)
		self.start = 0
		self.remain = 0
		self.ymPressTime = 0
		self.etime = 0
		self.step = 0

	def setActive(self, active):
		text = _(active)
		self.label.set_label(text)
		self.active = active

	def createMenu(self):
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

	def updateMenu(self, start=None):
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

	def itemActivate(self, _widget, item):
		self.setActive(self.start + item)
		self.emit("changed", self.start + item)

	def onButtonPress(self, _widget, gevent):
		if gevent.button == 3:
			self.updateMenu()
			_foo, x, y = self.get_window().get_origin()
			y += self.get_allocation().height
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

	def arrowSelect(self, _item, plus):
		self.remain = plus
		timeout_add(
			int(ui.labelMenuDelay * 1000),
			self.arrowRemain,
			plus,
		)

	def arrowDeselect(self, _item):
		self.remain = 0

	def arrowRemain(self, plus):
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

	def menuScroll(self, _widget, gevent):
		d = getScrollValue(gevent)
		if d == "up":
			self.updateMenu(self.start - 1)
			return None

		if d == "down":
			self.updateMenu(self.start + 1)
			return None

		return False


@registerSignals
class YearLabel(IntLabel, ud.BaseCalObj):
	signals = ud.BaseCalObj.signals
	styleClass = "yearlabel"

	@staticmethod
	@ud.cssFunc
	def getCSS() -> str:
		from scal3.ui_gtk.utils import cssTextStyle

		if conf.labelBoxYearColorEnable:
			return (
				"."
				+ YearLabel.styleClass
				+ " "
				+ cssTextStyle(
					fgColor=conf.labelBoxYearColor,
				)
			)
		return ""

	def __init__(self, calType, **kwargs):
		IntLabel.__init__(self, **kwargs)
		self.objName = f"yearLabel({calType})"
		self.initVars()
		self.calType = calType
		# ---
		self.get_style_context().add_class(self.styleClass)
		if calType == calTypes.primary:
			self.get_style_context().add_class(primaryCalStyleClass)
		# ---
		self.connect("changed", self.onChanged)

	def onChanged(self, _label, item):
		calType = self.calType
		_y, m, d = ui.cells.current.dates[calType]
		ui.cells.changeDate(item, m, d, calType)
		self.onDateChange()

	def changeCalType(self, calType):
		self.calType = calType
		# self.onDateChange()

	def onDateChange(self, *a, **ka):
		ud.BaseCalObj.onDateChange(self, *a, **ka)
		self.setActive(ui.cells.current.dates[self.calType][0])

	def setActive(self, active):
		text = _(active)
		self.label.set_label(text)
		self.active = active


class SmallNoFocusButton(ConButton):
	def __init__(self, imageName, func, tooltip=""):
		ConButton.__init__(self)
		self.set_relief(2)
		self.set_can_focus(False)
		self._imageName = imageName
		self._image = gtk.Image()
		self.updateIcon()
		self.add(self._image)
		self.connect("con-clicked", func)
		if tooltip:
			set_tooltip(self, tooltip)

	def updateIcon(self):
		self._image.set_from_pixbuf(
			pixbufFromFile(
				self._imageName,
				size=conf.labelBoxIconSize,
			),
		)


class YearLabelButtonBox(gtk.Box, ud.BaseCalObj):
	def __init__(self, calType, **kwargs):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
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
		pack(self, self.removeButton)
		# ---
		self.label = YearLabel(calType, **kwargs)
		pack(self, self.label)
		# ---
		pack(self, self.addButton)

	def onPrevClick(self, _button):
		ui.cells.yearPlus(-1)
		self.label.onDateChange()

	def onNextClick(self, _button):
		ui.cells.yearPlus(1)
		self.label.onDateChange()

	def changeCalType(self, calType):
		return self.label.changeCalType(calType)

	def onFontConfigChange(self):
		self.removeButton.updateIcon()
		self.addButton.updateIcon()


class MonthLabelButtonBox(gtk.Box, ud.BaseCalObj):
	def __init__(self, calType, **kwargs):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
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
		pack(self, self.removeButton)
		# ---
		self.label = MonthLabel(calType, **kwargs)
		pack(self, self.label)
		# ---
		pack(self, self.addButton)

	def onPrevClick(self, _button):
		ui.cells.monthPlus(-1)
		self.label.onDateChange()

	def onNextClick(self, _button):
		ui.cells.monthPlus(1)
		self.label.onDateChange()

	def changeCalType(self, calType):
		return self.label.changeCalType(calType)

	def onFontConfigChange(self):
		self.removeButton.updateIcon()
		self.addButton.updateIcon()


@registerSignals
class CalObj(gtk.Box, CustomizableCalObj):
	objName = "labelBox"
	desc = _("Year & Month Bar")
	itemListCustomizable = False
	hasOptions = True
	styleClass = "labelbox"

	@staticmethod
	def getFont():
		if conf.labelBoxFontEnable and conf.labelBoxFont:
			font = conf.labelBoxFont.copy()  # make a copy to be safe to modify
		else:
			font = ui.getFont()
		if conf.boldYmLabel:
			font.bold = True
		return font

	def __init__(self, win):
		self.win = win
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		self.get_style_context().add_class(self.styleClass)
		# self.set_border_width(2)
		self.ybox = None
		self.mbox = None
		self.monthLabels = []
		self.onBorderWidthChange()

	@staticmethod
	def newSeparator():
		# return gtk.VSeparator()
		return gtk.Label()

	def updateIconSize(self):
		alphabet = locale_man.getAlphabet()
		height = calcTextPixelSize(self.win, alphabet, font=self.getFont())[1]
		conf.labelBoxIconSize = height * 0.6

	def updateTextWidth(self):
		font = self.getFont()
		pfont = pfontEncode(font)
		lay = self.create_pango_layout("")
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
			label.set_property("width-request", wm)

	@staticmethod
	def getFontPreviewText(calType):
		date = ui.cells.current.dates[calType]
		year = _(date[0])
		month = getMonthName(calType, date[1])
		return f"{year} {month}"

	def getFontPreviewTextFull(self):
		return " ".join(
			[self.getFontPreviewText(calType) for calType in calTypes.active],
		)

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		# -----
		self.updateIconSize()
		# ----
		for child in self.get_children():
			child.destroy()
		# ---
		monthLabels = []
		calType = calTypes.primary
		# --
		box = YearLabelButtonBox(calType)
		pack(self, box)
		self.appendItem(box.label)
		self.ybox = box
		# --
		pack(self, self.newSeparator(), 1, 1)
		# --
		box = MonthLabelButtonBox(calType)
		pack(self, box)
		self.appendItem(box.label)
		monthLabels.append(box.label)
		self.mbox = box
		# ----
		for _i, calType in list(enumerate(calTypes.active))[1:]:
			pack(self, self.newSeparator(), 1, 1)
			label = YearLabel(calType)
			pack(self, label)
			self.appendItem(label)
			# ---------------
			label = MonthLabel(calType)
			pack(self, label, padding=5)
			monthLabels.append(label)
			self.appendItem(label)
		# ----
		self.monthLabels = monthLabels
		self.updateTextWidth()
		# -----
		self.show_all()
		# -----
		self.onDateChange()

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
		if conf.labelBoxPrimaryFontEnable and conf.labelBoxPrimaryFont:
			font = conf.labelBoxPrimaryFont
			if conf.boldYmLabel:
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

	def onFontConfigChange(self):
		ud.windowList.updateCSS()
		self.updateIconSize()
		if self.ybox:
			self.ybox.onFontConfigChange()
		if self.mbox:
			self.mbox.onFontConfigChange()
		self.updateTextWidth()

	def onBorderWidthChange(self):
		self.set_border_width(conf.labelBoxBorderWidth)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			CheckColorPrefItem,
			CheckFontPrefItem,
			CheckPrefItem,
			ColorPrefItem,
			FontPrefItem,
			SpinPrefItem,
		)

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = VBox(spacing=5)
		# ----
		prefItem = SpinPrefItem(
			conf,
			"labelBoxBorderWidth",
			0,
			99,
			digits=1,
			step=1,
			unitLabel=_("pixels"),
			label=_("Border Width"),
			live=True,
			onChangeFunc=self.onBorderWidthChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		hbox = HBox(spacing=5)
		pack(hbox, gtk.Label(label=_("Active menu item color")))
		prefItem = ColorPrefItem(
			conf,
			"labelBoxMenuActiveColor",
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(hbox, prefItem.getWidget())
		pack(optionsWidget, hbox)
		# ---
		checkSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ---
		prefItem = CheckColorPrefItem(
			CheckPrefItem(conf, "labelBoxYearColorEnable", _("Year Color")),
			ColorPrefItem(conf, "labelBoxYearColor", True),
			checkSizeGroup=checkSizeGroup,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ---
		prefItem = CheckColorPrefItem(
			CheckPrefItem(conf, "labelBoxMonthColorEnable", _("Month Color")),
			ColorPrefItem(conf, "labelBoxMonthColor", True),
			checkSizeGroup=checkSizeGroup,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ---
		previewText = self.getFontPreviewTextFull()
		prefItem = CheckFontPrefItem(
			CheckPrefItem(conf, "labelBoxFontEnable", label=_("Font")),
			FontPrefItem(conf, "labelBoxFont", previewText=previewText),
			live=True,
			onChangeFunc=self.onFontConfigChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ---
		previewText = self.getFontPreviewText(calTypes.primary)
		prefItem = CheckFontPrefItem(
			CheckPrefItem(
				conf,
				"labelBoxPrimaryFontEnable",
				label=_("Primary Calendar Font"),
			),
			FontPrefItem(conf, "labelBoxPrimaryFont", previewText=previewText),
			vertical=True,
			spacing=0,
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ---
		prefItem = CheckPrefItem(
			conf,
			"boldYmLabel",
			label=_("Bold Font"),
			live=True,
			onChangeFunc=ud.windowList.updateCSS,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return self.optionsWidget


if __name__ == "__main__":
	win = gtk.Dialog()
	box = CalObj()
	win.add_events(
		gdk.EventMask.POINTER_MOTION_MASK
		| gdk.EventMask.FOCUS_CHANGE_MASK
		| gdk.EventMask.BUTTON_MOTION_MASK
		| gdk.EventMask.BUTTON_PRESS_MASK
		| gdk.EventMask.BUTTON_RELEASE_MASK
		| gdk.EventMask.SCROLL_MASK
		| gdk.EventMask.KEY_PRESS_MASK
		| gdk.EventMask.VISIBILITY_NOTIFY_MASK
		| gdk.EventMask.EXPOSURE_MASK,
	)
	pack(win.vbox, box, 1, 1)
	win.vbox.show_all()
	win.resize(600, 50)
	win.set_title(box.desc)
	box.onConfigChange()
	win.run()
