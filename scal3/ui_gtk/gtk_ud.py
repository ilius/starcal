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

# The low-level module for gtk ui dependent stuff (classes/functions/settings)
# ud = ui dependent
# upper the "ui" module

from __future__ import annotations

from gi.overrides import GObject

from scal3 import logger
from scal3.property import Property

log = logger.get()

import os
import sys
from os.path import join
from typing import TYPE_CHECKING, Any, Final

from gi.overrides.GObject import Object

from scal3 import locale_man, ui
from scal3.config_utils import loadModuleConfig, saveSingleConfig
from scal3.format_time import compileTmFormat
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.path import confDir, sourceDir, sysConfDir
from scal3.ui import conf
from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.drawing import calcTextPixelSize
from scal3.ui_gtk.font_utils import gfontDecode, pfontEncode

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.cell_type import CompiledTimeFormat
	from scal3.event_update_queue import EventUpdateRecord
	from scal3.ui.pytypes import CustomizableToolBoxDict
	from scal3.ui_gtk.customize import CustomizableCalObj

__all__ = [
	"BaseCalObj",
	"CalObjType",
	"adjustTimeCmd",
	"clockFormatBin",
	"cssFunc",
	"dateFormatBin",
	"hasLightTheme",
	"justificationList",
	"mainToolbarData",
	"saveConf",
	"screenH",
	"updateFormatsBin",
	"wcalToolbarData",
	"windowList",
	"workAreaH",
	"workAreaW",
]

# ------------------------------------------------------------

sysConfPath = join(sysConfDir, "ui-gtk.json")

confPath = join(confDir, "ui-gtk.json")

dateFormat: Final[Property[str]] = Property("%Y/%m/%d")
# clockFormat: "%T", "%X" (local), "<b>%T</b>", "%m:%d"
clockFormat: Final[Property[str]] = Property("%X")
confParams = {
	"dateFormat": dateFormat,
	"clockFormat": clockFormat,
	# "adjustTimeCmd": adjustTimeCmd,
}


def loadConf() -> None:
	loadModuleConfig(
		confPath=confPath,
		sysConfPath=sysConfPath,
		params=confParams,
		decoders={},
	)
	updateFormatsBin()


def saveConf() -> None:
	saveSingleConfig(confPath, confParams, {})


# ------------------------------------------------------------


class CalObjType(GObject.Object):
	pass


@registerSignals
class BaseCalObj(CalObjType):
	objName = ""
	desc = ""
	loaded = True
	customizable = False
	itemHaveOptions = True
	signals: list[tuple[str, list[Any]]] = [
		("config-change", []),
		("date-change", []),
		("goto-page", [str]),
	]

	def initVars(self) -> None:
		self.items: list[CustomizableCalObj] = []
		self.enable = True

	def onConfigChange(
		self,
		sender: CustomizableCalObj | None = None,
		toParent: bool = True,
	) -> None:
		if sender is self:
			return
		if sender is None:
			sender = self
		log.debug(
			f"onConfigChange: name={self.objName}, toParent={toParent}, "
			f"sender={sender.objName if sender else sender}",
		)
		if toParent:
			self.emit("config-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onConfigChange(sender=sender, toParent=False)

	def onDateChange(
		self,
		sender: CustomizableCalObj | None = None,
		toParent: bool = True,
	) -> None:
		if sender is self:
			return
		if sender is None:
			sender = self
		log.debug(
			f"onDateChange: name={self.objName}, toParent={toParent}, "
			f"sender={sender.objName if sender else sender}",
		)
		if toParent:
			self.emit("date-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onDateChange(sender=sender, toParent=False)

	def onEnableCheckClick(self) -> None:
		enable = self.enableParam.v
		self.enable = enable
		self.onConfigChange()
		self.showHide()

	def __getitem__(self, key: str) -> CustomizableCalObj | None:
		for item in self.items:
			if item.objName == key:
				return item
		return None

	def connectItem(self, item: CustomizableCalObj) -> None:
		item.connect("config-change", self.onConfigChange)
		item.connect("date-change", self.onDateChange)

	# def insertItem(self, index, item):
	# 	self.items.insert(index, item)
	# 	self.connectItem(item)

	def appendItem(self, item: CustomizableCalObj) -> None:
		self.items.append(item)
		self.connectItem(item)

	def replaceItem(self, itemIndex: int, item: CustomizableCalObj) -> None:
		self.items[itemIndex] = item
		self.connectItem(item)

	def moveItem(self, i: int, j: int) -> None:
		self.items.insert(j, self.items.pop(i))

	def addItemWidget(self, i: int) -> None:
		pass

	def showHide(self) -> None:
		if hasattr(self, "set_visible"):
			self.set_visible(self.enable)
		else:
			log.warning(f"{self} has no set_visible method")
			if self.enable:
				self.show()
			else:
				self.hide()
		for item in self.items:
			item.showHide()


class IntegatedWindowList(BaseCalObj):
	objName = "windowList"
	desc = "Window List"

	def __init__(self) -> None:
		Object.__init__(self)
		self.initVars()
		ui.eventUpdateQueue.registerConsumer(self)
		# ---
		self.styleProvider = gtk.CssProvider()
		screen = gdk.Screen.get_default()
		assert screen is not None
		gtk.StyleContext.add_provider_for_screen(
			screen,
			self.styleProvider,
			gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		# ---
		self.cssFuncList: list[Callable[[], str]] = []
		# ---
		self.lastAlphabetHeight = 0.0

	def addCSSFunc(self, func: Callable[[], str]) -> None:
		self.cssFuncList.append(func)

	def updateIconSizes(self) -> None:
		from scal3.ui_gtk import pixcache

		alphabet = locale_man.getAlphabet()
		height = calcTextPixelSize(
			ui.mainWin,
			alphabet,
			font=ui.getFont(),
		)[1]
		log.debug(f"{height=}, {alphabet=}")

		if height == self.lastAlphabetHeight:
			return

		conf.menuIconSize.v = int(height * 0.7)
		conf.menuCheckSize.v = int(height * 0.8)
		conf.menuEventCheckIconSize.v = int(height * 0.8)
		conf.buttonIconSize.v = int(height * 0.65)
		conf.stackIconSize.v = int(height * 0.8)
		conf.eventTreeIconSize.v = int(height * 0.7)
		conf.eventTreeGroupIconSize.v = int(height * 0.85)
		conf.imageInputIconSize.v = int(height * 1.2)
		conf.treeIconSize.v = int(height * 0.7)
		conf.comboBoxIconSize.v = int(height * 0.8)
		conf.toolbarIconSize.v = int(height * 0.9)
		conf.messageDialogIconSize.v = int(height * 2.0)
		conf.rightPanelEventIconSize.v = int(height * 0.8)

		pixcache.clear()
		self.lastAlphabetHeight = height

	def onEventUpdate(self, _record: EventUpdateRecord) -> None:
		# ui.cells.clear()  # causes crash, no idea why!
		ui.cells.clearEventsData()
		self.onDateChange()

	def onConfigChange(self, *a, **ka) -> None:
		ui.cells.clear()
		settings.set_property(
			"gtk-font-name",
			pfontEncode(ui.getFont()).to_string(),
		)
		# ----
		self.updateIconSizes()
		# ----
		self.updateCSS()
		# ----
		BaseCalObj.onConfigChange(self, *a, **ka)
		self.onDateChange()

	# override_color and override_font are deprecated since version 3.16
	# override_color:
	#   doc says: Use a custom style provider and style classes instead
	# override_font:
	#   This function is not useful in the context of CSS-based rendering
	# If you wish to change the font a widget uses to render its text you
	# should use a custom CSS style, through an application-specific
	# Gtk.StyleProvider and a CSS style class.

	def updateCSS(self) -> None:
		from scal3.ui_gtk.color_utils import gdkColorToRgb
		from scal3.ui_gtk.utils import cssTextStyle

		assert ui.mainWin is not None
		font = ui.getFont()
		fgColor = gdkColorToRgb(
			ui.mainWin.get_style_context().get_color(gtk.StateFlags.NORMAL),
		)
		log.debug(f"{fgColor=}")

		css = ""

		if conf.oldStyleProgressBar.v:
			css += "progressbar progress, trough {min-height: 1.3em;}\n"
		else:
			textStyle = cssTextStyle(
				font=font,
				fgColor=fgColor,
				# extra={"text-align": "justify"},  # not supported
			)
			css += "progressbar progress, trough {min-height: 0.5em;}\n"
			css += f"progressbar text {textStyle}\n"

		smallerFont = ui.getFont(0.8)
		css += f".smaller {cssTextStyle(font=smallerFont)}\n"

		biggerFont = ui.getFont(1.25)
		css += f".bigger {cssTextStyle(font=biggerFont)}\n"

		css += "check {min-width: 1.42em; min-height: 1.42em;}\n"

		mcs = conf.menuCheckSize.v
		css += f"menuitem check {{min-width: {mcs}px; min-height: {mcs}px;}}\n"

		for func in self.cssFuncList:
			cssPart = func()
			if not cssPart:
				continue
			css += cssPart + "\n"

		log.debug(css + "\n_______________________")
		self.styleProvider.load_from_data(css.encode("utf-8"))


def getGtkDefaultFont() -> ui.Font:
	fontName = settings.get_property("gtk-font-name")
	font = gfontDecode(fontName)
	font.size = max(font.size, 5)
	return font


def _getLightness(c: gdk.RGBA) -> float:
	maxValue = max(c.red, c.green, c.blue)
	if maxValue > 255:
		log.warning(f"_getLightness: bad color {c}")
		maxValue = 0
	return (maxValue + min(c.red, c.green, c.blue)) / 2.0


def hasLightTheme(widget: gtk.Widget) -> bool:
	styleCtx = widget.get_style_context()
	fg = styleCtx.get_color(gtk.StateFlags.NORMAL)
	bg = styleCtx.get_property("background-color", gtk.StateFlags.NORMAL)
	# from scal3.ui_gtk.color_utils import gdkColorToRgb
	# from scal3.color_utils import rgbToHsl
	# print("fg_rgb:", gdkColorToRgb(fg))
	# print("bg_rgb:", gdkColorToRgb(bg))
	# print("fg_hsl:", rgbToHsl(*gdkColorToRgb(fg)))
	# print("bg_hsl:", rgbToHsl(*gdkColorToRgb(bg)))
	# print(
	# 	f"fg lightness: {_getLightness(fg):.2f}, "
	# 	f"bg lightness: {_getLightness(bg):.2f}"
	# )
	return _getLightness(fg) < _getLightness(bg)


def getSettings() -> gtk.Settings:
	settings = gtk.Settings.get_default()
	if settings is None:
		# if gdk.Screen.get_default() is None:
		# 	raise RuntimeError("There is not default screen")
		# raise RuntimeError("settings is None")
		settings = gtk.Settings.get_for_screen(gdk.Screen())
		assert settings is not None
	return settings


def getDisplay() -> gdk.Display:
	display = gdk.Display.get_default()
	assert display is not None
	return display


# ----------------------------------------------------


windowList = IntegatedWindowList()


def cssFunc(func: Callable) -> Callable:
	"""Decorator for global functions or static methods."""
	windowList.addCSSFunc(func)
	return func


# -----------

if sys.getdefaultencoding() != "utf-8":
	log.warning(f"System encoding is not utf-8, it's {sys.getdefaultencoding()!r}")

if rtl:
	gtk.Widget.set_default_direction(gtk.TextDirection.RTL)

gtk.Window.set_default_icon_from_file(ui.appIcon)

display = getDisplay()

settings = getSettings()

# ui.timeout_initial = settings.get_property("gtk-timeout-initial") # == 200
# ui.timeout_repeat = settings.get_property("gtk-timeout-repeat") # == 20
# timeout_repeat=20 is too small! FIXME


ui.initFonts(getGtkDefaultFont())
ui.fontDefaultInit = ui.fontDefault

# -----------
textDirDict = {
	"ltr": gtk.TextDirection.LTR,
	"rtl": gtk.TextDirection.RTL,
	"auto": gtk.TextDirection.NONE,
}

iconSizeList = [
	# in size order
	("Menu", gtk.IconSize.MENU),  # 16x16
	("Small Toolbar", gtk.IconSize.SMALL_TOOLBAR),  # 16x16
	("Button", gtk.IconSize.BUTTON),  # 16x16
	("Large Toolbar", gtk.IconSize.LARGE_TOOLBAR),  # 24x24
	("DND", gtk.IconSize.DND),  # 32x32
	("Dialog", gtk.IconSize.DIALOG),  # 48x48
]
iconSizeDict = dict(iconSizeList)
iconSizeNames = [x[0] for x in iconSizeList]

# ---------------

justificationList = [
	(
		"left",
		_("Right" if rtl else "Left"),
		gtk.Justification.LEFT,
	),
	(
		"right",
		_("Left" if rtl else "Right"),
		gtk.Justification.RIGHT,
	),
	("center", _("Center"), gtk.Justification.CENTER),
	("fill", _("Fill"), gtk.Justification.FILL),
]
justificationByName = {name: value for name, desc, value in justificationList}

# ------------------------------

# if conf.fontCustomEnable.v:-- FIXME
# 	settings.set_property("gtk-font-name", fontCustom)


dateFormatBin: CompiledTimeFormat | None = None
clockFormatBin: CompiledTimeFormat | None = None


def updateFormatsBin() -> None:
	global dateFormatBin, clockFormatBin
	dateFormatBin = compileTmFormat(dateFormat.v)
	clockFormatBin = compileTmFormat(clockFormat.v)


# ------------------------------


def findAskpass() -> str | None:
	from os.path import isfile

	for askpass in (
		# Debian (not in PATH)
		"/usr/lib/openssh/gnome-ssh-askpass",
		# Debian (in PATH)
		"/usr/bin/ksshaskpass",
		# Debian (in PATH)
		"/usr/bin/lxqt-openssh-askpass",
		# Red Hat
		"/usr/libexec/openssh/lxqt-openssh-askpass",
		# Debian (in PATH)
		"/usr/bin/ssh-askpass-fullscreen",
		# Debian (not in PATH), ArchLinux
		"/usr/lib/ssh/x11-ssh-askpass",
		# FreeBSD (package openssh-askpass)
		"/usr/local/bin/ssh-askpass",  # link to x11-ssh-askpass
	):
		if isfile(askpass):
			return askpass
	return None


def setDefault_adjustTimeCmd() -> None:
	global adjustTimeCmd
	from os.path import isfile

	for sudo in ("/usr/bin/sudo", "/usr/local/bin/sudo"):
		if isfile(sudo):
			log.debug(f"Found sudo: {sudo}")
			askpass = findAskpass()
			if askpass:
				adjustTimeCmd = [
					sudo,
					"-A",  # --askpass
					join(sourceDir, "scripts", "run"),
					"scal3/ui_gtk/adjust_dtime.py",
				]
				adjustTimeEnv["SUDO_ASKPASS"] = askpass
				return

	for cmd in ("gksudo", "kdesudo", "gksu", "gnomesu", "kdesu"):
		if isfile(f"/usr/bin/{cmd}"):
			adjustTimeCmd = [
				cmd,
				join(sourceDir, "scripts", "run"),
				"scal3/ui_gtk/adjust_dtime.py",
			]
			return


# user should be able to configure this in Preferences
adjustTimeCmd: list[str] = []
adjustTimeEnv = os.environ
setDefault_adjustTimeCmd()

# ------------------------------

mainToolbarData: CustomizableToolBoxDict = {
	"items": [],
	"iconSizePixel": 24,
	"buttonBorder": 0,
	"buttonPadding": 0,
	"preferIconName": False,
}

wcalToolbarData: CustomizableToolBoxDict = {
	"items": [
		("mainMenu", True),
		("weekNum", False),
		("backward4", False),
		("backward", True),
		("today", True),
		("forward", True),
		("forward4", False),
	],
	"iconSizePixel": 16,
	"buttonBorder": 0,
	"buttonPadding": 0,
	"preferIconName": False,
}

# -----------------------------------------------------------

# loaded from jsom
if conf.ud__wcalToolbarData.v is not None:
	wcalToolbarData = conf.ud__wcalToolbarData.v

# loaded from jsom
if conf.ud__mainToolbarData.v is not None:
	mainToolbarData = conf.ud__mainToolbarData.v

loadConf()

# ------------------------------------------------------------


def getMonitor() -> gdk.Monitor:
	display = gdk.Display.get_default()
	assert display is not None

	monitor = display.get_monitor_at_point(1, 1)
	if monitor is not None:
		log.debug("getMonitor: using get_monitor_at_point")
		return monitor

	monitor = display.get_primary_monitor()
	if monitor is not None:
		log.debug("getMonitor: using get_primary_monitor")
		return monitor

	monitor = display.get_monitor_at_window(gdk.get_default_root_window())
	if monitor is not None:
		log.debug("getMonitor: using get_monitor_at_window")
		return monitor

	return None


def getScreenSize() -> tuple[int, int] | None:
	# includes panels/docks
	monitor = getMonitor()
	if monitor is None:
		return None
	rect = monitor.get_geometry()
	return rect.width, rect.height


def getWorkAreaSize() -> tuple[int, int] | None:
	monitor = getMonitor()
	if monitor is None:
		return None
	rect = monitor.get_workarea()
	return rect.width, rect.height


# ------------------------------

rootWindow = gdk.get_default_root_window()

_screenSize = getScreenSize()
_workAreaSize = getWorkAreaSize()
if _screenSize is None:
	screenW, screenH = rootWindow.get_width(), rootWindow.get_height()
else:
	screenW, screenH = _screenSize
if _workAreaSize is None:
	workAreaW, workAreaH = screenW, screenH
else:
	workAreaW, workAreaH = _workAreaSize


# print(f"screen: {screenW}x{screenH}, work area: {workAreaW}x{workAreaH}")
# for normal windows, we should use workAreaW and workAreaH
# for menus, we should use screenW and screenH, because they can go over panels

# ------------------------------

# FIXME
# import atexit
# atexit.register(
# 	rootWindow.set_cursor,
# 	gdk.Cursor.new(gdk.CursorType.LEFT_PTR),
# )
# rootWindow.set_cursor(cursor=gdk.Cursor.new(gdk.CursorType.WATCH))  # FIXME


def screenSizeChanged(_screen: gdk.Screen) -> None:
	global screenW, screenH, workAreaW, workAreaH
	if ui.mainWin is None:
		return
	display = gdk.Display.get_default()
	assert display is not None
	monitor = display.get_monitor_at_window(
		ui.mainWin.get_window(),
	)
	screenSize = monitor.get_geometry()
	workAreaSize = monitor.get_workarea()
	screenW, screenH = screenSize.width, screenSize.height
	workAreaW, workAreaH = workAreaSize.width, workAreaSize.height
	log.info(f"screen: {screenW}x{screenH}, work area: {workAreaW}x{workAreaH}")
	ui.mainWin.screenSizeChanged(screenSize)


screen = gdk.Screen.get_default()
assert screen is not None
screen.connect("size-changed", screenSizeChanged)
