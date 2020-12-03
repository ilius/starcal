#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

# The low-level module for gtk ui dependent stuff (classes/functions/settings)
# ud = ui dependent
# upper the "ui" module

from scal3 import logger
log = logger.get()

import time
from os.path import join

from typing import Callable

from scal3.path import *
from scal3.json_utils import *
from scal3.locale_man import rtl
from scal3 import core
from scal3 import ui
from scal3.format_time import compileTmFormat
from scal3.locale_man import tr as _
from scal3 import locale_man

from gi.overrides.GObject import Object

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.font_utils import gfontDecode, pfontEncode
from scal3.ui_gtk.drawing import calcTextPixelSize


############################################################

sysConfPath = join(sysConfDir, "ui-gtk.json")

confPath = join(confDir, "ui-gtk.json")

confParams = (
	"dateFormat",
	"clockFormat",
	#"adjustTimeCmd",
)


def loadConf():
	loadModuleJsonConf(__name__)
	updateFormatsBin()


def saveConf():
	saveModuleJsonConf(__name__)

############################################################

class CalObjType(Object):
	pass


@registerSignals
class BaseCalObj(CalObjType):
	_name = ""
	desc = ""
	loaded = True
	customizable = False
	signals = [
		("config-change", []),
		("date-change", []),
		("goto-page", [str]),
	]

	def initVars(self):
		self.items = []
		self.enable = True

	def onConfigChange(self, sender=None, toParent=True):
		if sender is self:
			return
		if sender is None:
			sender = self
		log.debug(
			f"onConfigChange: name={self._name}, toParent={toParent}, " +
			f"sender={sender._name if sender else sender}"
		)
		if toParent:
			self.emit("config-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onConfigChange(sender=sender, toParent=False)

	def onDateChange(self, sender=None, toParent=True):
		if sender is self:
			return
		if sender is None:
			sender = self
		log.debug(
			f"onDateChange: name={self._name}, toParent={toParent}, " +
			f"sender={sender._name if sender else sender}"
		)
		if toParent:
			self.emit("date-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onDateChange(sender=sender, toParent=False)

	def onEnableCheckClick(self):
		enable = getattr(ui, self.enableParam)
		self.enable = enable
		self.onConfigChange()
		self.showHide()


	def __getitem__(self, key):
		for item in self.items:
			if item._name == key:
				return item

	def connectItem(self, item):
		item.connect("config-change", self.onConfigChange)
		item.connect("date-change", self.onDateChange)

	#def insertItem(self, index, item):
	#	self.items.insert(index, item)
	#	self.connectItem(item)

	def appendItem(self, item):
		self.items.append(item)
		self.connectItem(item)

	def replaceItem(self, itemIndex, item):
		self.items[itemIndex] = item
		self.connectItem(item)

	def moveItem(self, i, j):
		self.items.insert(j, self.items.pop(i))

	def addItemWidget(self, i):
		pass

	def showHide(self):
		try:
			func = self.show if self.enable else self.hide
		except AttributeError:
			try:
				self.set_visible(self.enable)
			except AttributeError:
				pass
		else:
			func()
		for item in self.items:
			item.showHide()


class IntegatedWindowList(BaseCalObj):
	_name = "windowList"
	desc = "Window List"

	def __init__(self):
		Object.__init__(self)
		self.initVars()
		ui.eventUpdateQueue.registerConsumer(self)
		###
		self.styleProvider = gtk.CssProvider()
		gtk.StyleContext.add_provider_for_screen(
			gdk.Screen.get_default(),
			self.styleProvider,
			gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
		)
		###
		self.cssFuncList = []  # type: List[Callable[[], str]]
		###
		self.lastAlphabetHeight = 0

	def addCSSFunc(self, func: Callable[[], str]) -> None:
		self.cssFuncList.append(func)

	def updateIconSizes(self):
		from scal3.ui_gtk import pixcache

		alphabet = locale_man.getAlphabet()
		height = calcTextPixelSize(
			ui.mainWin,
			alphabet,
			font=ui.getFont(),
		)[1]
		log.debug(f"height={height}, alphabet={alphabet}")

		if height == self.lastAlphabetHeight:
			return

		ui.menuIconSize = int(height * 0.7)
		ui.menuCheckSize = int(height * 0.8)
		ui.menuEventCheckIconSize = height * 0.8
		ui.buttonIconSize = height * 0.65
		ui.stackIconSize = height * 0.8
		ui.eventTreeIconSize = height * 0.7
		ui.eventTreeGroupIconSize = height * 0.85
		ui.imageInputIconSize = height * 1.2
		ui.treeIconSize = height * 0.7
		ui.comboBoxIconSize = height * 0.8
		ui.toolbarIconSize = height * 0.9
		ui.messageDialogIconSize = height * 2.0
		ui.rightPanelEventIconSize = height * 0.8

		pixcache.clear()
		self.lastAlphabetHeight = height

	def onEventUpdate(self, record: "EventUpdateRecord") -> None:
		# ui.cellCache.clear()  # causes crash, no idea why!
		ui.cellCache.clearEventsData()
		self.onDateChange()

	def onConfigChange(self, *a, **ka):
		ui.cellCache.clear()
		settings.set_property(
			"gtk-font-name",
			pfontEncode(ui.getFont()).to_string(),
		)
		####
		self.updateIconSizes()
		####
		self.updateCSS()
		####
		BaseCalObj.onConfigChange(self, *a, **ka)
		self.onDateChange()

	# override_color and override_font are deprecated since version 3.16
	# override_color:
	#	doc says: Use a custom style provider and style classes instead
	# override_font:
	#	This function is not useful in the context of CSS-based rendering
	# If you wish to change the font a widget uses to render its text you
	# should use a custom CSS style, through an application-specific
	# Gtk.StyleProvider and a CSS style class.

	def updateCSS(self):
		from scal3.ui_gtk.utils import cssTextStyle
		from scal3.ui_gtk.color_utils import gdkColorToRgb
		font = ui.getFont()
		fgColor = gdkColorToRgb(
			ui.mainWin.get_style_context().
			get_color(gtk.StateFlags.NORMAL)
		)
		log.debug(f"fgColor={fgColor}")
		css = "progressbar text " + cssTextStyle(
			font=font,
			fgColor=fgColor,
		) + "\n"

		smallerFont = ui.getFont(0.8)
		css += f".smaller {cssTextStyle(font=smallerFont)}\n"

		biggerFont = ui.getFont(1.25)
		css += f".bigger {cssTextStyle(font=biggerFont)}\n"

		css += "check {min-width: 1.42em; min-height: 1.42em;}\n"

		mcs = ui.menuCheckSize
		css += f"menuitem check {{min-width: {mcs}px; min-height: {mcs}px;}}\n"

		for func in self.cssFuncList:
			cssPart = func()
			if not cssPart:
				continue
			css += cssPart + "\n"

		log.debug(css + "\n_______________________")
		self.styleProvider.load_from_data(css.encode("utf-8"))


def getGtkDefaultFont():
	fontName = settings.get_property("gtk-font-name")
	font = gfontDecode(fontName)
	font[3] = max(5, font[3])
	return font


def _getLightness(c: "gdk.Color"):
	return (max(c.red, c.green, c.blue) + min(c.red, c.green, c.blue)) / 2.0

def hasLightTheme(widget):
	styleCtx = widget.get_style_context()
	fg = styleCtx.get_color(gtk.StateFlags.NORMAL)
	bg = styleCtx.get_property('background-color', gtk.StateFlags.NORMAL)
	# from scal3.ui_gtk.color_utils import gdkColorToRgb
	# from scal3.color_utils import rgbToHsl
	# print("fg_rgb:", gdkColorToRgb(fg))
	# print("bg_rgb:", gdkColorToRgb(bg))
	# print("fg_hsl:", rgbToHsl(*gdkColorToRgb(fg)))
	# print("bg_hsl:", rgbToHsl(*gdkColorToRgb(bg)))
	# print(f"fg lightness: {_getLightness(fg):.2f}, bg lightness: {_getLightness(bg):.2f}")
	return _getLightness(fg) < _getLightness(bg)


####################################################

windowList = IntegatedWindowList()

# decorator for global functions or static methods
def cssFunc(func: Callable) -> Callable:
	global windowList
	windowList.addCSSFunc(func)
	return func

###########

if rtl:
	gtk.Widget.set_default_direction(gtk.TextDirection.RTL)

gtk.Window.set_default_icon_from_file(ui.appIcon)

display = gdk.Display.get_default()

settings = gtk.Settings.get_default()

if settings is None:
	# if gdk.Screen.get_default() is None:
	#	raise RuntimeError("There is not default screen")
	# raise RuntimeError("settings == None")
	settings = gtk.Settings.get_for_screen(gdk.Screen())


# ui.timeout_initial = settings.get_property("gtk-timeout-initial") # == 200
# ui.timeout_repeat = settings.get_property("gtk-timeout-repeat") # == 20
# timeout_repeat=20 is too small! FIXME


ui.initFonts(getGtkDefaultFont())
ui.fontDefaultInit = ui.fontDefault

###########
textDirDict = {
	"ltr": gtk.TextDirection.LTR,
	"rtl": gtk.TextDirection.RTL,
	"auto": gtk.TextDirection.NONE,
}

iconSizeList = [
	("Menu", gtk.IconSize.MENU),                    # 16x16
	("Small Toolbar", gtk.IconSize.SMALL_TOOLBAR),  # 16x16
	("Button", gtk.IconSize.BUTTON),                # 16x16
	("Large Toolbar", gtk.IconSize.LARGE_TOOLBAR),  # 24x24
	("DND", gtk.IconSize.DND),                      # 32x32
	("Dialog", gtk.IconSize.DIALOG),                # 48x48
] ## in size order
iconSizeDict = dict(iconSizeList)
iconSizeNames = [x[0] for x in iconSizeList]

###############

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
justificationByName = {
	name: value
	for name, desc, value in justificationList
}

##############################

#if ui.fontCustomEnable:## FIXME
#	settings.set_property("gtk-font-name", fontCustom)


dateFormat = "%Y/%m/%d"
clockFormat = "%X" ## "%T", "%X" (local), "<b>%T</b>", "%m:%d"

dateFormatBin = None
clockFormatBin = None


def updateFormatsBin():
	global dateFormatBin, clockFormatBin
	dateFormatBin = compileTmFormat(dateFormat)
	clockFormatBin = compileTmFormat(clockFormat)

##############################


def findAskpass():
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
		"/bin/x11-ssh-askpass",
	):
		if isfile(askpass):
			return askpass


def setDefault_adjustTimeCmd():
	global adjustTimeCmd
	global adjustTimeEnv
	from os.path import isfile

	sudo = "/usr/bin/sudo"
	if isfile(sudo):
		askpass = findAskpass()
		if askpass:
			adjustTimeCmd = [
				sudo,
				"-A", # --askpass
				join(sourceDir, "scripts", "run"),
				"scal3/ui_gtk/adjust_dtime.py"
			]
			adjustTimeEnv["SUDO_ASKPASS"] = askpass
			return

	for cmd in ("gksudo", "kdesudo", "gksu", "gnomesu", "kdesu"):
		if isfile(f"/usr/bin/{cmd}"):
			adjustTimeCmd = [
				cmd,
				join(sourceDir, "scripts", "run"),
				"scal3/ui_gtk/adjust_dtime.py"
			]
			return


# user should be able to configure this in Preferences
adjustTimeCmd = ""
adjustTimeEnv = os.environ
setDefault_adjustTimeCmd()

##############################

mainToolbarData = {
	"items": [],
	"iconSize": "Large Toolbar",
	"iconSizePixel": 24,
	"style": "Icon",
	"buttonsBorder": 0,
}

wcalToolbarData = {
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
	"style": "Icon",
	"buttonsBorder": 0,
}

###########################################################

# loaded from jsom
tmpValue = getattr(ui, "ud__wcalToolbarData", None)
if tmpValue is not None:
	wcalToolbarData = tmpValue
del tmpValue


# loaded from jsom
tmpValue = getattr(ui, "ud__mainToolbarData", None)
if tmpValue is not None:
	mainToolbarData = tmpValue
del tmpValue


loadConf()

setDefault_adjustTimeCmd()## FIXME

############################################################

rootWindow = gdk.get_default_root_window() ## Good Place?????

#import atexit
#atexit.register(
#	rootWindow.set_cursor,
#	gdk.Cursor.new(gdk.CursorType.LEFT_PTR),
#)  # FIXME
#rootWindow.set_cursor(cursor=gdk.Cursor.new(gdk.CursorType.WATCH))  # FIXME

screenW = rootWindow.get_width()
screenH = rootWindow.get_height()


def screenSizeChanged(screen):
	global screenW, screenH
	if ui.mainWin is None:
		return
	monitor = gdk.Display.get_default().get_monitor_at_window(ui.mainWin.get_window())
	rect = monitor.get_geometry()
	screenW = rect.width
	screenH = rect.height
	ui.mainWin.screenSizeChanged(rect)


gdk.Screen.get_default().connect("size-changed", screenSizeChanged)
