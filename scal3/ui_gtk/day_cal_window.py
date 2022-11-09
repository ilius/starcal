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

from scal3 import logger
log = logger.get()

from time import time as now
import os

from scal3.path import *

from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3.json_utils import saveJsonConf, loadJsonConf
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	get_menu_width,
	get_menu_height,
	dialog_add_button,
	openWindow,
)
from scal3.ui_gtk.menuitems import ImageMenuItem

from scal3.ui_gtk.day_cal import DayCal
from scal3.ui_gtk.stack import MyStack, StackPage

confPathLive = join(confDir, "ui-daycal-live.json")

confParamsLive = (
	"dcalWinX",
	"dcalWinY",
	"dcalWinWidth",
	"dcalWinHeight",
)

lastLiveConfChangeTime = 0

loadJsonConf(ui, confPathLive)


def saveLiveConf(): # FIXME: rename to saveConfLive
	saveJsonConf(ui, confPathLive, confParamsLive)


def saveLiveConfLoop(): # FIXME: rename to saveConfLiveLoop
	global lastLiveConfChangeTime
	tm = now()
	if tm - lastLiveConfChangeTime > ui.saveLiveConfDelay:
		saveLiveConf()
		return False # Finish loop
	return True  # Continue loop


def liveConfChanged():
	global lastLiveConfChangeTime
	tm = now()
	if tm - lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			saveLiveConfLoop,
		)
		lastLiveConfChangeTime = tm


class DayCalWindowCustomizeWindow(gtk.Dialog):
	def __init__(self, dayCal: DayCal, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self._widget = dayCal
		##
		self.set_title(_("Customize") + ": " + dayCal.desc)
		self.connect("delete-event", self.onSaveClick)
		##
		dialog_add_button(
			self,
			imageName="document-save.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
			onClick=self.onSaveClick,
		)
		##
		self.stack = MyStack(
			headerSpacing=10,
			iconSize=ui.stackIconSize,
		)
		pack(self.vbox, self.stack, 1, 1)
		pageName = "dayCalWin"
		page = StackPage()
		page.pageName = pageName
		page.pagePath = pageName
		page.pageWidget = dayCal.getOptionsWidget()
		page.pageExpand = True
		page.pageExpand = True
		self.stack.addPage(page)
		for page in dayCal.getSubPages():
			page.pageParent = pageName  # FIXME: or pagePath?
			page.pagePath = page.pageName
			self.stack.addPage(page)
		dayCal.connect("goto-page", self.gotoPageCallback)
		##
		# self.vbox.connect("size-allocate", self.vboxSizeRequest)
		self.vbox.show_all()

	def gotoPageCallback(self, item, pagePath):
		self.stack.gotoPage(pagePath)

	# def vboxSizeRequest(self, widget, req):
	# 	self.resize(self.get_size()[0], 1)

	def save(self):
		self._widget.updateVars()
		ui.saveConfCustomize()

	def onSaveClick(self, button=None, event=None):
		self.save()
		self.hide()
		return True


@registerSignals
class DayCalWindowWidget(DayCal):
	dragAndDropEnable = False
	doubleClickEnable = False
	backgroundColorParam = "dcalWinBackgroundColor"
	dayParamsParam = "dcalWinDayParams"
	monthParamsParam = "dcalWinMonthParams"
	weekdayParamsParam = "dcalWinWeekdayParams"
	widgetButtonsEnableParam = "dcalWinWidgetButtonsEnable"
	widgetButtonsParam = "dcalWinWidgetButtons"
	eventIconSizeParam = "dcalWinEventIconSize"
	eventTotalSizeRatioParam = "dcalWinEventTotalSizeRatio"
	weekdayLocalizeParam = "dcalWinWeekdayLocalize"
	weekdayAbbreviateParam = "dcalWinWeekdayAbbreviate"
	weekdayUppercaseParam = "dcalWinWeekdayUppercase"

	seasonPieEnableParam = "dcalWinSeasonPieEnable"
	seasonPieGeoParam = "dcalWinSeasonPieGeo"
	seasonPieColorsParam = {
		"Spring": "dcalWinSeasonPieSpringColor",
		"Summer": "dcalWinSeasonPieSummerColor",
		"Autumn": "dcalWinSeasonPieAutumnColor",
		"Winter": "dcalWinSeasonPieWinterColor",
	}
	seasonPieTextColorParam = "dcalWinSeasonPieTextColor"

	def getCell(self):
		return ui.todayCell

	def __init__(self, win):
		DayCal.__init__(self, win)
		self.set_size_request(50, 50)
		self.menu = None
		self.customizeWindow = None

	def customizeWindowCreate(self):
		if not self.customizeWindow:
			self.customizeWindow = DayCalWindowCustomizeWindow(
				self,
				transient_for=self._window,
			)

	def openCustomize(self, gevent):
		self.customizeWindowCreate()
		x, y = self._window.get_position()
		w, h = self._window.get_size()
		cw, ch = self.customizeWindow.get_size()
		cx = x + w + 5
		cy = y
		if cx + cw > ud.workAreaW:
			cx = x - cw - 5
		if cy + ch > ud.workAreaH:
			cy = y + h - ch
		self.customizeWindow.present()
		self.customizeWindow.move(cx, cy)
		# should move() after present()

	def onButtonPress(self, obj, gevent):
		b = gevent.button
		if b == 1:
			buttons = self._allButtons
			if buttons:
				x, y = gevent.x, gevent.y
				w = self.get_allocation().width
				h = self.get_allocation().height
				for button in buttons:
					if button.contains(x, y, w, h):
						button.onPress(gevent)
						return True
			if ui.mainWin:
				ui.mainWin.onStatusIconClick()
				return True
		elif b == 3:
			self.popupMenuOnButtonPress(obj, gevent)
		elif b == 2:
			self.startMove(gevent, button=b)
		return True

	def getMenuPosFunc(self, menu, gevent, above: bool):
		# looks like gevent.x_root and gevent.y_root are wrong on Wayland
		# (tested on Fedora + Gnome3)
		# we should probably just pass func=None in Wayland for now
		if os.getenv("XDG_SESSION_TYPE") == "wayland":
			return None

		mw = get_menu_width(menu)
		mh = get_menu_height(menu)
		mx = max(0, gevent.x_root - mw) if rtl else gevent.x_root
		my = max(0, gevent.y_root - mh) if above else gevent.y_root

		if mx == my == 0:
			log.info(
				f"{mx=}, {my=}, {mw=}, {mh=}, " +
				f"{gevent.x_root=}, {gevent.y_root=}"
			)
			return None

		return lambda *args: (mx, my, False)

	def getMenu(self, reverse: bool):
		menu = self.menu
		if menu is None:
			menu = Menu()
			if os.sep == "\\":
				from scal3.ui_gtk.windows import setupMenuHideOnLeave
				setupMenuHideOnLeave(menu)
			items = ui.mainWin.getStatusIconPopupItems()
			items.insert(5, ImageMenuItem(
				_("Customize This Window"),
				imageName="document-edit.svg",
				func=self.openCustomize,
			))
			if reverse:
				items.reverse()
			for item in items:
				menu.add(item)
			self.menu = menu
		menu.show_all()
		return menu

	def popupMenuOnButtonPress(self, obj, gevent):
		reverse = gevent.y_root > ud.screenH / 2.0
		menu = self.getMenu(reverse)
		menu.popup(
			None,
			None,
			self.getMenuPosFunc(menu, gevent, reverse),
			self,
			gevent.button,
			gevent.time,
		)
		ui.updateFocusTime()


@registerSignals
class DayCalWindow(gtk.Window, ud.BaseCalObj):
	_name = "dayCalWin"
	desc = _("Day Calendar Window")

	def __init__(self):
		gtk.Window.__init__(self)
		self.initVars()
		ud.windowList.appendItem(self)
		###
		self.resize(ui.dcalWinWidth, ui.dcalWinHeight)
		self.move(ui.dcalWinX, ui.dcalWinY)
		self.set_skip_taskbar_hint(True)
		self.set_decorated(False)
		self.set_keep_below(True)
		self.stick()
		###
		self._widget = DayCalWindowWidget(self)
		self._widget._window = self

		self.connect("key-press-event", self._widget.onKeyPress)
		self.connect("delete-event", self.onDeleteEvent)
		self.connect("configure-event", self.configureEvent)

		self.add(self._widget)
		self._widget.show()
		self.appendItem(self._widget)

	def menuCellPopup(self, widget, etime, x, y):
		reverse = False
		menu = self._widget.getMenu(reverse)
		coord = widget.translate_coordinates(self, x, y)
		if coord is None:
			raise RuntimeError(
				f"failed to translate coordinates ({x}, {y})" +
				f" from widget {widget}"
			)
		dx, dy = coord
		foo, wx, wy = self.get_window().get_origin()
		x = wx + dx
		y = wy + dy
		if rtl:
			x -= get_menu_width(menu)
		####
		etime = gtk.get_current_event_time()
		# log.debug("menuCellPopup", x, y, etime)
		# without the above line, the menu is not showing up
		# some GC-related pygi bug probably
		menu.popup(
			None,
			None,
			lambda *args: (x, y, True),
			None,
			3,
			etime,
		)
		ui.updateFocusTime()


	def menuMainPopup(
		self,
		widget: gtk.Widget,
		etime: int,
		x: int,
		y: int,
	):
		pass

	def prefUpdateBgColor(self, cal):
		pass

	def dayInfoShow(self, widget=None):
		ui.mainWin.dayInfoShow(widget)

	def onDeleteEvent(self, arg=None, event=None):
		if ui.mainWin:
			self.hide()
		else:
			gtk.main_quit()
		return True

	def configureEvent(self, widget, gevent):
		if not self.get_property("visible"):
			return
		wx, wy = self.get_position()
		ww, wh = self.get_size()
		ui.dcalWinX, ui.dcalWinY = (wx, wy)
		ui.dcalWinWidth = ww
		ui.dcalWinHeight = wh
		liveConfChanged()
		return False
