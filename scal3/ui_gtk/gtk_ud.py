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

## The low-level module for gtk ui dependent stuff (classes/functions/settings)
## ud = ui dependent
## upper the "ui" module

import time
from os.path import join

from scal3.path import *
from scal3.utils import myRaise
from scal3.json_utils import *
from scal3.locale_man import rtl
from scal3 import core
from scal3 import ui
from scal3.format_time import compileTmFormat

from gi.overrides.GObject import Object

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.font_utils import gfontDecode, pfontEncode


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


@registerSignals
class BaseCalObj(Object):
	_name = ""
	desc = ""
	loaded = True
	customizable = False
	signals = [
		("config-change", []),
		("date-change", []),
	]

	def initVars(self):
		self.items = []
		self.enable = True

	def onConfigChange(self, sender=None, emit=True):
		if emit:
			self.emit("config-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onConfigChange(emit=False)

	def onDateChange(self, sender=None, emit=True):
		if emit:
			self.emit("date-change")
		for item in self.items:
			if item.enable and item is not sender:
				item.onDateChange(emit=False)

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

	def moveItemUp(self, i):
		self.items.insert(i - 1, self.items.pop(i))

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

	def onConfigChange(self, *a, **ka):
		ui.cellCache.clear()
		settings.set_property(
			"gtk-font-name",
			pfontEncode(ui.getFont()).to_string(),
		)
		####
		BaseCalObj.onConfigChange(self, *a, **ka)
		self.onDateChange()


def getGtkDefaultFont():
	fontName = settings.get_property("gtk-font-name")
	font = gfontDecode(fontName)
	font[3] = max(5, font[3])
	return font

####################################################

windowList = IntegatedWindowList()

###########

if rtl:
	gtk.Widget.set_default_direction(gtk.TextDirection.RTL)

gtk.Window.set_default_icon_from_file(ui.logo)

settings = gtk.Settings.get_default()

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
	("Menu", gtk.IconSize.MENU),
	("Small Toolbar", gtk.IconSize.SMALL_TOOLBAR),
	("Button", gtk.IconSize.BUTTON),
	("Large Toolbar", gtk.IconSize.LARGE_TOOLBAR),
	("DND", gtk.IconSize.DND),
	("Dialog", gtk.IconSize.DIALOG),
] ## in size order
iconSizeDict = dict(iconSizeList)

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


def setDefault_adjustTimeCmd():
	global adjustTimeCmd
	for cmd in ("gksudo", "kdesudo", "gksu", "gnomesu", "kdesu"):
		if os.path.isfile("/usr/bin/%s" % cmd):
			adjustTimeCmd = [
				cmd,
				join(rootDir, "scripts", "run"),
				"scal3/ui_gtk/adjust_dtime.py"
			]
			break

# user should be able to configure this in Preferences
adjustTimeCmd = ""
setDefault_adjustTimeCmd()

##############################

mainToolbarData = {
	"items": [],
	"iconSize": "Large Toolbar",
	"style": "Icon",
	"buttonsBorder": 0,
}

wcalToolbarData = {
	"items": [
		("mainMenu", True),
		("backward4", False),
		("backward", True),
		("today", True),
		("forward", True),
		("forward4", False),
	],
	"iconSize": "Button",
	"style": "Icon",
	"buttonsBorder": 0,
}

###########################################################

try:
	wcalToolbarData = ui.ud__wcalToolbarData ## loaded from jsom
except AttributeError:
	pass

try:
	mainToolbarData = ui.ud__mainToolbarData ## loaded from jsom
except AttributeError:
	pass


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
