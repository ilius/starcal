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

import sys

if sys.version_info[0] != 3:
	sys.stderr.write("Run this script with Python 3.x\n")
	sys.exit(1)

import signal
from time import time as now
from time import localtime
import os
import os.path
from os.path import join, dirname, isfile, isdir
from typing import Tuple

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3.path import *
from scal3 import logger

log = logger.get()

if not (isfile(join(confDir, "core.json")) or isdir(join(confDir, "event"))):
	from scal3.utils import restartLow
	try:
		__import__("scal3.ui_gtk.import_config_2to3")
	except Exception as e:
		log.exception("")
		log.error(str(e))  # TODO: log the full traceback
		if not isdir(confDir):
			os.mkdir(confDir, 0o755)
	else:
		if isfile(join(confDir, "core.json")):
			restartLow()

from scal3.utils import versionLessThan
from scal3 import cal_types
from scal3.cal_types import calTypes
from scal3 import core

from scal3 import locale_man
from scal3.locale_man import rtl, lang  # import scal3.locale_man after core
# _ = locale_man.loadTranslator(False)  # FIXME
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui
from scal3.color_utils import rgbToHtmlColor

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.utils import *
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
	CheckMenuItem,
	CustomCheckMenuItem,
)
from scal3.ui_gtk import listener
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import (
	DummyCalObj,
	CustomizableCalBox,
	CustomizableCalObj,
	newSubPageButton
)
from scal3.ui_gtk.layout import WinLayoutBox, WinLayoutObj
from scal3.ui_gtk.layout_utils import moduleObjectInitializer
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk import hijri as hijri_gtk
from scal3.ui_gtk.mainwin_items import mainWinItemsDesc

from gi.repository import Gio as gio


ui.uiName = "gtk"


def liveConfChanged():
	tm = now()
	if tm - ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			ui.saveLiveConfLoop,
		)
		ui.lastLiveConfChangeTime = tm


@registerSignals
class MainWinVbox(gtk.Box, CustomizableCalBox):
	_name = "mainPanel"
	desc = _("Main Panel")
	itemListCustomizable = True
	myKeys = (
		'down',
		'end',
		'f10',
		'home',
		'i',
		'j',
		'k',
		'left',
		'm',
		'menu',
		'n',
		'p',
		'page_down',
		'page_up',
		'right',
		'space',
		't',
		'up',
	)

	def __init__(self, win):
		self.win = win
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.initVars()
		itemsPkg = "scal3.ui_gtk.mainwin_items"
		for (name, enable) in ui.mainWinItems:
			if name in ("winContronller", "statusBar"):
				log.warning(f"Skipping main win item {name!r}")
				continue
			# log.debug(name, enable)
			if enable:
				try:
					module = __import__(
						".".join([
							itemsPkg,
							name,
						]),
						fromlist=["CalObj"],
					)
					CalObj = module.CalObj
				except RuntimeError as e:
					raise e
				except Exception as e:
					log.error(f"error importing mainWinItem {name}")
					log.exception("")
					# raise e
					continue
				try:
					item = CalObj(win)
				except Exception as e:
					log.error(f"name={name}, module={module}")
					raise e
				item.enable = enable
				# modify_bg_all(
				# 	item,
				# 	gtk.StateType.NORMAL,
				# 	rgbToGdkColor(*ui.bgColor),
				# )
			else:
				desc = mainWinItemsDesc[name]
				item = DummyCalObj(name, desc, itemsPkg, True)
			self.appendItem(item)

	def updateVars(self):
		CustomizableCalBox.updateVars(self)
		ui.mainWinItems = self.getItemsData()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		CustomizableCalBox.onKeyPress(self, arg, gevent)
		return True  # FIXME

	def switchWcalMcal(self, customizeDialog):
		wi = None
		mi = None
		for i, item in enumerate(self.items):
			if item._name == "weekCal":
				wi = i
			elif item._name == "monthCal":
				mi = i
		for itemIndex in (wi, mi):
			customizeDialog.loadItem(self, itemIndex)
		wcal, mcal = self.items[wi], self.items[mi]
		wcal.enable, mcal.enable = mcal.enable, wcal.enable
		# FIXME
		# self.reorder_child(wcal, mi)
		# self.reorder_child(mcal, wi)
		# self.items[wi], self.items[mi] = mcal, wcal
		self.showHide()
		self.onDateChange()

	def getOptionsWidget(self):
		if self.optionsWidget is not None:
			return self.optionsWidget
		self.optionsWidget = VBox(spacing=self.optionsPageSpacing)
		return self.optionsWidget


@registerSignals
class MainWin(gtk.ApplicationWindow, ud.BaseCalObj):
	_name = "mainWin"
	desc = _("Main Window")
	timeout = 1  # second
	signals = ud.BaseCalObj.signals + [
		("toggle-right-panel", []),
	]

	def autoResize(self):
		self.resize(ui.winWidth, ui.winHeight)

	# def maximize(self):
	# 	pass

	def __init__(self, statusIconMode=2):
		appId = "apps.starcal"
		# if this application_id is already running, Gtk will crash
		# with Segmentation fault
		if event_lib.allReadOnly:
			appId += "2"
		self.app = gtk.Application(application_id=appId)
		self.app.register(gio.Cancellable.new())
		gtk.ApplicationWindow.__init__(self, application=self.app)
		###
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		ud.windowList.appendItem(self)
		ui.mainWin = self
		##################
		self.ignoreConfigureEvent = False
		##################
		# statusIconMode:
		#   ("none", "none")
		#   ("statusIcon", "normal")
		#   ("applet", "gnome")
		#   ("applet", "kde")
		##
		#   0: none (simple window)
		#   1: (dropped) applet
		#   2: standard status icon
		self.statusIconMode = statusIconMode
		###
		# ui.eventManDialog = None
		# ui.timeLineWin = None
		# ui.yearWheelWin = None
		###
		# ui.weekCalWin = WeekCalWindow()
		# ud.windowList.appendItem(ui.weekCalWin)
		###
		self.dayInfoDialog = None
		# log.debug("windowList.items", [item._name for item in ud.windowList.items])
		###########
		# self.connect("window-state-event", selfStateEvent)
		self.set_title(f"{core.APP_DESC} {core.VERSION}")
		# self.connect("main-show", lambda arg: self.present())
		# self.connect("main-hide", lambda arg: self.hide())
		self.set_decorated(False)
		self.set_property("skip-taskbar-hint", not ui.winTaskbar)
		# self.set_skip_taskbar_hint  # FIXME
		self.set_role("starcal")
		# self.set_focus_on_map(True)#????????
		# self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# self.connect("realize", self.onRealize)
		self.set_default_size(ui.winWidth, 1)
		self.move(ui.winX, ui.winY)
		#############################################################
		self.connect("focus-in-event", self.focusIn, "Main")
		self.connect("focus-out-event", self.focusOut, "Main")
		self.connect("key-press-event", self.onKeyPress)
		self.connect("configure-event", self.onConfigureEvent)
		self.connect("toggle-right-panel", self.onToggleRightPanel)
		#############################################################
		"""
		#self.add_events(gdk.EventMask.VISIBILITY_NOTIFY_MASK)
		#self.connect("frame-event", show_event)
		# Compiz does not send configure-event(or any event) when MOVING
		# window(sends in last point,
		## when moving completed)
		#self.connect("drag-motion", show_event)
		ud.rootWindow.set_events(...
		ud.rootWindow.add_filter(self.onRootWinEvent)
		#self.realize()
		#gdk.flush()
		#self.onConfigureEvent(None, None)
		#self.connect("drag-motion", show_event)
		######################
		## ????????????????????????????????????????????????
		# when button is down(before button-release-event),
		# motion-notify-event does not recived!
		"""
		##################################################################
		self.focus = False
		# self.focusOutTime = 0
		# self.clockTr = None
		##################################################################
		self.winCon = None
		self.mainVBox = None
		self.rightPanel = None
		self.statusBar = None
		####
		self.customizeDialog = None
		############
		layoutFooter = WinLayoutBox(
			name="footer",
			desc="Footer",  # should not be seen in GUI
			enableParam="",
			vertical=True,
			expand=False,
			itemsMovable=True,
			itemsParam="mainWinFooterItems",
			buttonSpacing=2,
			items=[
				WinLayoutObj(
					name="statusBar",
					desc=_("Status Bar"),
					enableParam="statusBarEnable",
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=self.createStatusBar,
				),
				WinLayoutObj(
					name="pluginsText",
					desc=_("Plugins Text"),
					enableParam="pluginsTextEnable",
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=moduleObjectInitializer(
						"scal3.ui_gtk.pluginsText",
						"PluginsTextBox",
						insideExpanderParam="pluginsTextInsideExpander",
					),
				),
				WinLayoutObj(
					name="eventDayView",
					desc=_("Events of Day"),
					enableParam="eventDayViewEnable",
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=moduleObjectInitializer(
						"scal3.ui_gtk.event.occurrence_view",
						"LimitedHeightDayOccurrenceView",
						eventSepParam="eventDayViewEventSep",
					),
				),
			],
		)
		layoutFooter.setItemsOrder(ui.mainWinFooterItems)
		self.layout = WinLayoutBox(
			name="layout",
			desc=_("Main Window"),
			enableParam="",
			vertical=True,
			expand=True,
			items=[
				WinLayoutObj(
					name="layout_winContronller",
					desc=_("Window Controller"),
					enableParam="winControllerEnable",
					vertical=False,
					expand=False,
					initializer=self.createWindowControllers,
				),
				WinLayoutBox(
					name="middleBox",
					desc="Middle Box",  # should not be seen in GUI
					enableParam="",
					vertical=False,
					expand=True,
					items=[
						WinLayoutObj(
							name="mainPanel",
							desc=_("Main Panel"),
							enableParam="",
							vertical=True,
							expand=True,
							initializer=self.createMainVBox,
						),
						WinLayoutObj(
							name="rightPanel",
							desc=_("Right Panel"),
							enableParam="mainWinRightPanelEnable",
							vertical=True,
							expand=False,
							labelAngle=90 if rtl else -90,
							initializer=self.createRightPanel,
						),
					],
				),
				layoutFooter,
			],
		)

		self.appendItem(self.layout)
		self.vbox = self.layout.getWidget()
		self.vbox.show()
		self.add(self.vbox)
		####################
		if ui.winMaximized:
			self.maximize()
		####################
		# ui.prefWindow = None
		self.exportDialog = None
		self.selectDateDialog = None
		# ############# Building About Dialog
		self.aboutDialog = None
		###############
		self.menuMain = None
		self.menuCell = None
		#####
		self.set_keep_above(ui.winKeepAbove)
		if ui.winSticky:
			self.stick()
		############################################################
		self.statusIconInit()
		listener.dateChange.add(self)
		#########
		self.connect("delete-event", self.onDeleteEvent)
		#########################################
		for plug in core.allPlugList:
			if plug.external:
				try:
					plug.set_dialog(self)
				except AttributeError:
					pass
		###########################
		self.onConfigChange()
		# ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))

	# def mainWinStateEvent(self, obj, gevent):
		# log.debug(dir(event))
		# log.debug(gevent.new_window_state)
		# self.event = event

	def createWindowControllers(self):
		from scal3.ui_gtk.winContronller import CalObj as WinContronllersObj
		if self.winCon is not None:
			return self.winCon
		ui.checkWinControllerButtons()
		self.winCon = WinContronllersObj(self)
		return self.winCon

	def createMainVBox(self):
		if self.mainVBox is not None:
			return self.mainVBox
		ui.checkMainWinItems()
		mainVBox = MainWinVbox(self)
		mainVBox.connect("button-press-event", self.onMainButtonPress)
		self.mainVBox = mainVBox
		return mainVBox

	def createRightPanel(self):
		from scal3.ui_gtk.right_panel import MainWinRightPanel
		if self.rightPanel is not None:
			return self.rightPanel
		self.rightPanel = MainWinRightPanel()
		self.rightPanel.onConfigChange()
		return self.rightPanel

	def _onToggleRightPanel(self):
		enable = not ui.mainWinRightPanelEnable
		ui.mainWinRightPanelEnable = enable
		self.rightPanel.enable = enable
		self.rightPanel.showHide()
		self.rightPanel.onDateChange()
		if ui.mainWinRightPanelResizeOnToggle:
			ww, wh = self.get_size()
			mw = ui.mainWinRightPanelWidth
			if enable:
				ww += mw
			else:
				ww -= mw
			if rtl:
				wx, wy = self.get_position()
				wx += mw * (-1 if enable else 1)
				self.move(wx, wy)
			self.resize(ww, wh)

	def onToggleRightPanel(self, widget):
		self.ignoreConfigureEvent = True
		ui.disableRedraw = True
		try:
			self._onToggleRightPanel()
		finally:
			self.ignoreConfigureEvent = False
			ui.disableRedraw = False
			ui.saveConfCustomize()

	def createStatusBar(self):
		from scal3.ui_gtk.statusBar import CalObj as StatusBar
		if self.statusBar is not None:
			return self.statusBar
		self.statusBar = StatusBar(self)
		return self.statusBar

	def selectDateResponse(self, widget, y, m, d):
		ui.changeDate(y, m, d)
		self.onDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		kname = gdk.keyval_name(gevent.keyval).lower()
		# log.debug(f"{now()}: MainWin.onKeyPress: {kname}")
		if kname == "escape":
			self.onEscape()
		elif kname == "f1":
			self.aboutShow()
		elif kname in ("insert", "plus", "kp_add"):
			self.eventManShow()
		elif kname in ("q", "arabic_dad"):  # FIXME
			self.quit()
		elif kname == "r":
			if gevent.state & gdk.ModifierType.CONTROL_MASK:
				log.info(f"Ctrl + R -> onConfigChange")
				self.onConfigChange()
		else:
			self.layout.onKeyPress(arg, gevent)
		return True  # FIXME

	def focusIn(self, widget=None, gevent=None, data=None):
		log.debug("focusIn")
		self.focus = True
		if self.winCon and self.winCon.enable:
			self.winCon.windowFocusIn()

	def focusOut(self, widegt, event, data=None):
		# called 0.0004 sec (max) after focusIn
		# (if switched between two windows)
		dt = now() - ui.focusTime
		log.debug(f"MainWin: focusOut: focusTime={ui.focusTime}, dt={dt}")
		if dt > 0.05:  # FIXME
			self.focus = False
			timeout_add(2, self.focusOutDo)

	def focusOutDo(self):
		if not self.focus:  # and t-self.focusOutTime>0.002:
			self.set_keep_above(ui.winKeepAbove)
			if self.winCon and self.winCon.enable:
				self.winCon.windowFocusOut()
		return False

	def onConfigureEvent(self, widget, gevent):
		if self.ignoreConfigureEvent:
			return
		wx, wy = self.get_position()
		# maxPosDelta = max(
		# 	abs(ui.winX - wx),
		# 	abs(ui.winY - wy),
		# )
		# log.debug(wx, wy)
		ww, wh = self.get_size()
		if self.get_property("visible"):
			ui.winX, ui.winY = (wx, wy)
		if not ui.winMaximized:
			ui.winWidth = ww
			ui.winHeight = wh
		self.onWindowSizeChange()
		liveConfChanged()
		return False

	def onWindowSizeChange(self):
		if self.rightPanel:
			self.rightPanel.onWindowSizeChange()

	def onMainButtonPress(self, obj, gevent):
		# only for mainVBox for now, not rightPanel
		# does not work for statusBar, don't know why
		# log.debug("MainWin: onMainButtonPress, button={gevent.button}")
		b = gevent.button
		if b == 3:
			self.menuMainCreate()
			self.menuMain.popup(None, None, None, None, 3, gevent.time)
		elif b == 1:
			# FIXME: used to cause problems with `ConButton`
			# when using 'pressed' and 'released' signals
			self.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
		ui.updateFocusTime()
		return False

	def childButtonPress(self, widget, gevent):
		b = gevent.button
		# log.debug(dir(gevent))
		# foo, x, y, mask = gevent.get_window().get_pointer()
		# x, y = self.get_pointer()
		x, y = gevent.x_root, gevent.y_root
		result = False
		if b == 1:
			self.begin_move_drag(gevent.button, x, y, gevent.time)
			result = True
		elif b == 3:
			self.menuMainCreate()
			if rtl:
				x -= get_menu_width(self.menuMain)
			self.menuMain.popup(
				None,
				None,
				lambda *args: (x, y, True),
				None,
				3,
				gevent.time,
			)
			result = True
		ui.updateFocusTime()
		return result

	def begin_resize_drag(self, *args):
		ui.updateFocusTime()
		return gtk.Window.begin_resize_drag(self, *args)

	def onResizeFromMenu(self, widget, gevent):
		if self.menuMain:
			self.menuMain.hide()
		self.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
		return True

	def changeDate(self, year, month, day):
		ui.changeDate(year, month, day)
		self.onDateChange()

	def goToday(self, obj=None):
		return self.changeDate(*cal_types.getSysDate(calTypes.primary))

	def onDateChange(self, *a, **kw):
		# log.debug("MainWin.onDateChange")
		ud.BaseCalObj.onDateChange(self, *a, **kw)
		# for j in range(len(core.plugIndex)):##????????????????????
		# 	try:
		# 		core.allPlugList[core.plugIndex[j]].date_change(*date)
		# 	except AttributeError:
		# 		pass
		for j in range(len(core.plugIndex)):
			try:
				core.allPlugList[core.plugIndex[j]].date_change_after(*date)
			except AttributeError:
				pass
		# log.debug(
		# 	f"Occurence Time: max={ui.Cell.ocTimeMax:e}, " +
		# 	f"avg={ui.Cell.ocTimeSum/ui.Cell.ocTimeCount:e}"
		# )

	def getEventAddToMenuItem(self) -> Optional[gtk.MenuItem]:
		from scal3.ui_gtk.drawing import newColorCheckPixbuf
		if event_lib.allReadOnly:
			return None
		menu2 = Menu()
		##
		for group in ui.eventGroups:
			if not group.enable:
				continue
			if not group.showInCal():  # FIXME
				continue
			eventTypes = group.acceptsEventTypes
			if not eventTypes:
				continue
			item2_kwargs = {}
			if group.icon:
				item2_kwargs["imageName"] = group.icon
			else:
				item2_kwargs["pixbuf"] = newColorCheckPixbuf(group.color, 20, True)
			##
			if len(eventTypes) == 1:
				menu2.add(ImageMenuItem(
					group.title,
					func=self.addToGroupFromMenu,
					args=(group, eventTypes[0]),
					**item2_kwargs
				))
			else:
				menu3 = Menu()
				for eventType in eventTypes:
					eventClass = event_lib.classes.event.byName[eventType]
					menu3.add(ImageMenuItem(
						eventClass.desc,
						imageName=eventClass.getDefaultIcon(),
						func=self.addToGroupFromMenu,
						args=(group, eventType),
					))
				menu3.show_all()
				item2 = ImageMenuItem(
					group.title,
					**item2_kwargs
				)
				item2.set_submenu(menu3)
				menu2.add(item2)
		##
		if not menu2.get_children():
			return None
		menu2.show_all()
		addToItem = ImageMenuItem(
			_("_Add Event to"),
			imageName="list-add.svg",
		)
		addToItem.set_submenu(menu2)
		return addToItem

	def editEventFromMenu(self, item, groupId, eventId):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		event = ui.getEvent(groupId, eventId)
		group = ui.eventGroups[groupId]
		parent = self
		event = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=parent,
		).run()
		if event is None:
			return
		ui.eventUpdateQueue.put("e", event, self)
		self.onConfigChange()

	def trimMenuItemLabel(self, s: str, maxLen: int):
		if len(s) > maxLen - 3:
			s = s[:maxLen - 3].rstrip(" ") + "..."
		return s

	def addEditEventCellMenuItems(self, menu):
		if event_lib.allReadOnly:
			return
		eventsData = ui.cell.getEventsData()
		if not eventsData:
			return
		if len(eventsData) < 4:  # TODO: make it customizable
			for eData in eventsData:
				groupId, eventId = eData["ids"]
				menu.add(ImageMenuItem(
					_("Edit") + ": " + self.trimMenuItemLabel(eData["text"][0], 25),
					imageName=eData["icon"],
					func=self.editEventFromMenu,
					args=(groupId, eventId,),
				))
		else:
			subMenu = Menu()
			subMenuItem = ImageMenuItem(
				_("_Edit Event"),
				imageName="list-add.svg",
			)
			for eData in eventsData:
				groupId, eventId = eData["ids"]
				subMenu.add(ImageMenuItem(
					eData["text"][0],
					imageName=eData["icon"],
					func=self.editEventFromMenu,
					args=(groupId, eventId,),
				))
			subMenu.show_all()
			subMenuItem.set_submenu(subMenu)
			menu.add(subMenuItem)

	def menuCellPopup(self, widget, etime, x, y):
		calObjName = widget._name  # why private? FIXME
		# calObjName is in ("weekCal", "monthCal", ...)
		menu = Menu()
		####
		for calType in calTypes.active:
			menu.add(ImageMenuItem(
				_("Copy {calType} Date").format(calType=_(calTypes.getDesc(calType))),
				imageName="edit-copy.svg",
				func=self.copyDateGetCallback(calType),
				args=(calType,)
			))
		menu.add(ImageMenuItem(
			_("Day Info"),
			imageName="info.svg",
			func=self.dayInfoShow,
		))
		addToItem = self.getEventAddToMenuItem()
		if addToItem is not None:
			menu.add(addToItem)
		self.addEditEventCellMenuItems(menu)
		menu.add(gtk.SeparatorMenuItem())
		menu.add(ImageMenuItem(
			_("Select _Today"),
			imageName="go-home.svg",
			func=self.goToday,
		))
		menu.add(ImageMenuItem(
			_("Select _Date..."),
			imageName="select-date.svg",
			func=self.selectDateShow,
		))
		if calObjName in ("weekCal", "monthCal"):
			isWeek = calObjName == "weekCal"
			menu.add(ImageMenuItem(
				_("Switch to " + (
					"Month Calendar" if isWeek else "Week Calendar"
				)),
				imageName="" if isWeek else "week-calendar.svg",
				func=self.switchWcalMcal,
			))
		if os.path.isfile("/usr/bin/evolution"):  # FIXME
			menu.add(ImageMenuItem(
				_("In E_volution"),
				imageName="evolution.png",
				func=ui.dayOpenEvolution,
			))
		####
		moreMenu = Menu()
		moreMenu.add(ImageMenuItem(
			_("_Customize"),
			imageName="document-edit.svg",
			func=self.customizeShow,
		))
		moreMenu.add(ImageMenuItem(
			_("_Preferences"),
			imageName="preferences-system.svg",
			func=self.prefShow,
		))
		moreMenu.add(ImageMenuItem(
			_("_Event Manager"),
			imageName="list-add.svg",
			func=self.eventManShow,
		))
		moreMenu.add(ImageMenuItem(
			_("Time Line"),
			imageName="timeline.svg",
			func=self.timeLineShow,
		))
		moreMenu.add(ImageMenuItem(
			_("Year Wheel"),
			imageName="year-wheel.svg",
			func=self.yearWheelShow,
		))  # icon? FIXME
		moreMenu.add(ImageMenuItem(
			_("Day Calendar (Desktop Widget)"),
			imageName="starcal.svg",
			func=self.dayCalWinShow,
		))
		# moreMenu.add(ImageMenuItem(
		# 	"Week Calendar",
		# 	imageName="week-calendar.svg",
		# 	func=self.weekCalShow,
		# ))
		moreMenu.add(ImageMenuItem(
			_("Export to {format}").format(format="HTML"),
			imageName="export-to-html.svg",
			func=self.onExportClick,
		))
		moreMenu.add(ImageMenuItem(
			_("_About"),
			imageName="dialog-information.svg",
			func=self.aboutShow,
		))
		moreMenu.add(ImageMenuItem(
			_("_Quit"),
			imageName="application-exit.svg",
			func=self.quit,
		))
		##
		moreMenu.show_all()
		moreItem = ImageMenuItem(label=_("More"))
		moreItem.set_submenu(moreMenu)
		# moreItem.show_all()
		menu.add(moreItem)
		####
		menu.show_all()
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
		self.menuCell = menu
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

	def menuMainCreate(self):
		if self.menuMain:
			return
		menu = gtk.Menu(reserve_toggle_size=0)
		####
		item = ImageMenuItem(_("Resize"), "resize.svg")
		item.connect("button-press-event", self.onResizeFromMenu)
		menu.add(item)
		#######
		menu.add(CheckMenuItem(
			label=_("_On Top"),
			func=self.onKeepAboveClick,
			active=ui.winKeepAbove,
		))
		menu.add(CheckMenuItem(
			label=_("On All De_sktops"),
			func=self.onStickyClick,
			active=ui.winSticky,
		))
		#######
		menu.add(ImageMenuItem(
			_("Select _Today"),
			imageName="go-home.svg",
			func=self.goToday,
		))
		menu.add(ImageMenuItem(
			_("Select _Date..."),
			imageName="select-date.svg",
			func=self.selectDateShow,
		))
		menu.add(ImageMenuItem(
			_("Day Info"),
			imageName="info.svg",
			func=self.dayInfoShow,
		))
		menu.add(ImageMenuItem(
			_("_Customize"),
			imageName="document-edit.svg",
			func=self.customizeShow,
		))
		menu.add(ImageMenuItem(
			_("_Preferences"),
			imageName="preferences-system.svg",
			func=self.prefShow,
		))
		# menu.add(ImageMenuItem(
		# 	_("_Add Event"),
		# 	imageName="list-add.svg",
		# 	func=ui.addCustomEvent,
		# ))
		# menu.add(ImageMenuItem(
		# 	_("_Event Manager"),
		# 	imageName="list-add.svg",
		# 	func=self.eventManShow,
		# ))
		menu.add(ImageMenuItem(
			_("Day Calendar (Desktop Widget)"),
			imageName="starcal.svg",
			func=self.dayCalWinShow,
		))
		menu.add(ImageMenuItem(
			_("Time Line"),
			imageName="timeline.svg",
			func=self.timeLineShow,
		))
		menu.add(ImageMenuItem(
			_("Year Wheel"),
			imageName="year-wheel.svg",
			func=self.yearWheelShow,
		))  # icon? FIXME
		# menu.add(ImageMenuItem(
		# 	_("Week Calendar"),
		# 	imageName="week-calendar.svg",
		# 	func=self.weekCalShow,
		# ))
		menu.add(ImageMenuItem(
			_("Export to {format}").format(format="HTML"),
			imageName="export-to-html.svg",
			func=self.onExportClick,
		))
		menu.add(ImageMenuItem(
			_("Ad_just System Time"),
			imageName="preferences-system.svg",
			func=self.adjustTime,
		))
		menu.add(ImageMenuItem(
			_("_About"),
			imageName="dialog-information.svg",
			func=self.aboutShow,
		))
		menu.add(ImageMenuItem(
			_("_Quit"),
			imageName="application-exit.svg",
			func=self.quit,
		))
		menu.show_all()
		self.menuMain = menu

	# handler for "popup-main-menu" signal
	def menuMainPopup(
		self,
		widget: gtk.Widget,
		etime: int,
		x: int,
		y: int,
	):
		self.menuMainCreate()
		if etime == 0:
			etime = gtk.get_current_event_time()
		menu = self.menuMain
		dx, dy = widget.translate_coordinates(self, x, y)
		foo, wx, wy = self.get_window().get_origin()
		x = wx + dx
		y = wy + dy
		if rtl:
			x -= get_menu_width(menu)
		menuH = get_menu_height(menu)
		if menuH > 0 and y + menuH > ud.screenH:
			if y - menuH >= 0:
				y -= menuH
			else:
				y -= menuH // 2
		# log.debug("menuMainPopup", x, y, etime)
		menu.popup(
			None,
			None,
			lambda *args: (x, y, True),
			None,
			3,
			etime,
		)
		ui.updateFocusTime()

	def addToGroupFromMenu(self, menu, group, eventType):
		from scal3.ui_gtk.event.editor import addNewEvent
		# log.debug("addToGroupFromMenu", group.title, eventType)
		title = _("Add ") + event_lib.classes.event.byName[eventType].desc
		event = addNewEvent(
			group,
			eventType,
			useSelectedDate=True,
			title=title,
			transient_for=self,
		)
		if event is None:
			return
		if event.parent is None:
			raise RuntimeError("event.parent is None")
		ui.eventUpdateQueue.put("+", event, self)
		self.onConfigChange()

	def prefUpdateBgColor(self, cal):
		if ui.prefWindow:
			ui.prefWindow.colorbBg.set_rgba(ui.bgColor)
		# else:  # FIXME
		ui.saveLiveConf()

	def onKeepAboveClick(self, check):
		act = check.get_active()
		self.set_keep_above(act)
		ui.winKeepAbove = act
		ui.saveLiveConf()

	def onStickyClick(self, check):
		if check.get_active():
			self.stick()
			ui.winSticky = True
		else:
			self.unstick()
			ui.winSticky = False
		ui.saveLiveConf()

	def copyDate(self, calType: int):
		setClipboard(ui.cell.format(ud.dateFormatBin, calType=calType))

	def copyDateGetCallback(self, calType: int):
		return lambda obj=None, event=None: setClipboard(ui.cell.format(
			ud.dateFormatBin,
			calType=calType,
		))

	def copyDateToday(self, obj=None, event=None):
		setClipboard(ui.todayCell.format(ud.dateFormatBin))

	def copyTime(self, obj=None, event=None):
		setClipboard(ui.todayCell.format(
			ud.clockFormatBin,
			tm=localtime()[3:6],
		))

	"""
	def updateToolbarClock(self):
		if ui.showDigClockTb:
			if self.clock is None:
				from scal3.ui_gtk.mywidgets.clock import FClockLabel
				self.clock = FClockLabel(ud.clockFormat)
				pack(self.toolbBox, self.clock)
				self.clock.show()
			else:
				self.clock.format = ud.clockFormat
		else:
			if self.clock is not None:
				self.clock.destroy()
				self.clock = None

	def updateStatusIconClock(self, checkStatusIconMode=True):
		if checkStatusIconMode and self.statusIconMode!=2:
			return
		if ui.showDigClockTr:
			if self.clockTr is None:
				from scal3.ui_gtk.mywidgets.clock import FClockLabel
				self.clockTr = FClockLabel(ud.clockFormat)
				try:
					pack(self.statusIconHbox, self.clockTr)
				except AttributeError:
					self.clockTr.destroy()
					self.clockTr = None
				else:
					self.clockTr.show()
			else:
				self.clockTr.format = ud.clockFormat
		else:
			if self.clockTr is not None:
				self.clockTr.destroy()
				self.clockTr = None
	"""

	# def weekCalShow(self, obj=None, data=None):
	# 	openWindow(ui.weekCalWin)

	def statusIconInit(self):
		if self.statusIconMode != 2:
			self.sicon = None
			return

		useAppIndicator = ui.useAppIndicator
		if useAppIndicator:
			try:
				import scal3.ui_gtk.starcal_appindicator
			except (ImportError, ValueError):
				useAppIndicator = False
		if useAppIndicator:
			from scal3.ui_gtk.starcal_appindicator import (
				IndicatorStatusIconWrapper,
			)
			self.sicon = IndicatorStatusIconWrapper(self)
		else:
			self.sicon = gtk.StatusIcon()
			self.sicon.set_title(core.APP_DESC)
			self.sicon.set_visible(True)  # is needed?
			self.sicon.connect(
				"button-press-event",
				self.onStatusIconPress,
			)
			self.sicon.connect("activate", self.onStatusIconClick)
			self.sicon.connect("popup-menu", self.statusIconPopup)

	def getMainWinMenuItem(self):
		item = gtk.MenuItem(label=_("Main Window"))
		item.connect("activate", self.onStatusIconClick)
		return item

	def getStatusIconPopupItems(self):
		return [
			ImageMenuItem(
				_("Copy _Time"),
				imageName="edit-copy.svg",
				func=self.copyTime,
			),
			ImageMenuItem(
				_("Copy _Date"),
				imageName="edit-copy.svg",
				func=self.copyDateToday,
			),
			ImageMenuItem(
				_("Ad_just System Time"),
				imageName="preferences-system.svg",
				func=self.adjustTime,
			),
			# ImageMenuItem(
			# 	_("_Add Event"),
			# 	imageName="list-add.svg",
			# 	func=ui.addCustomEvent,
			# ),  # FIXME
			ImageMenuItem(
				_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				func=self.onExportClickStatusIcon,
			),
			ImageMenuItem(
				_("_Preferences"),
				imageName="preferences-system.svg",
				func=self.prefShow,
			),
			ImageMenuItem(
				_("_Customize"),
				imageName="document-edit.svg",
				func=self.customizeShow,
			),
			ImageMenuItem(
				_("_Event Manager"),
				imageName="list-add.svg",
				func=self.eventManShow,
			),
			ImageMenuItem(
				_("Time Line"),
				imageName="timeline.svg",
				func=self.timeLineShow,
			),
			ImageMenuItem(
				_("Year Wheel"),
				imageName="year-wheel.svg",
				func=self.yearWheelShow,
			),
			ImageMenuItem(
				_("_About"),
				imageName="dialog-information.svg",
				func=self.aboutShow,
			),
			gtk.SeparatorMenuItem(),
			ImageMenuItem(
				_("_Quit"),
				imageName="application-exit.svg",
				func=self.quit,
			),
		]

	def statusIconPopup(self, sicon, button, etime):
		menu = Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave
			setupMenuHideOnLeave(menu)
		items = self.getStatusIconPopupItems()
		# items.insert(0, self.getMainWinMenuItem())## FIXME
		get_pos_func = None
		y1 = 0
		geo = self.sicon.get_geometry()
		# Previously geo was None on windows
		# and on Linux it had `geo.index(1)` (not sure about the type)
		# Now it's tuple on both Linux and windows
		if geo is None:
			items.reverse()
		elif isinstance(geo, tuple):
			# geo == (True, screen, area, orientation)
			y1 = geo[2].y
		else:
			y1 = geo.index(1)
		try:
			y = gtk.StatusIcon.position_menu(menu, self.sicon)[1]
		except TypeError:  # new gi versions
			y = gtk.StatusIcon.position_menu(menu, 0, 0, self.sicon)[1]
		if y1 > 0 and y < y1:  # taskbar is on bottom
			items.reverse()
		get_pos_func = gtk.StatusIcon.position_menu
		for item in items:
			menu.add(item)
		menu.show_all()
		# log.debug("statusIconPopup", button, etime)
		menu.popup(None, None, get_pos_func, self.sicon, button, etime)
		# self.sicon.do_popup_menu(self.sicon, button, etime)
		ui.updateFocusTime()
		self.sicon.menu = menu  # to prevent gurbage collected

	def onCurrentDateChange(self, gdate):
		self.statusIconUpdate(gdate=gdate)

	def getStatusIconTooltip(self):
		# tt = core.weekDayName[core.getWeekDay(*ddate)]
		tt = core.weekDayName[core.jwday(ui.todayCell.jd)]
		# if ui.pluginsTextStatusIcon:##?????????
		# 	sep = _(",")+" "
		# else:
		sep = "\n"
		for calType in calTypes.active:
			y, m, d = ui.todayCell.dates[calType]
			tt += (
				sep +
				_(d) +
				" " +
				locale_man.getMonthName(calType, m, y) +
				" " +
				_(y)
			)
		if ui.pluginsTextStatusIcon:
			text = ui.todayCell.getPluginsText()
			if text != "":
				tt += "\n\n" + text  # .replace("\t", "\n") ## FIXME
		for item in ui.todayCell.getEventsData():
			if not item["showInStatusIcon"]:
				continue
			itemS = ""
			if item["time"]:
				itemS += item["time"] + " - "
			itemS += item["text"][0]
			tt += "\n\n" + itemS
		return tt

	def statusIconUpdateIcon(self, ddate):  # FIXME
		from scal3.utils import toBytes
		imagePath = (
			ui.statusIconImageHoli if ui.todayCell.holiday
			else ui.statusIconImage
		)
		ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
		with open(imagePath, "rb") as fp:
			data = fp.read()
		if ext == "svg":
			dayNum = locale_man.numEncode(
				ddate[2],
				localeMode=calTypes.primary,  # FIXME
			)
			style = []  # type: List[Tuple[str, Any]]
			if ui.statusIconFontFamilyEnable:
				if ui.statusIconFontFamily:
					family = ui.statusIconFontFamily
				else:
					family = ui.getFont()[0]
				style.append(("font-family", family))
			if ui.statusIconHolidayFontColorEnable and ui.statusIconHolidayFontColor:
				if ui.todayCell.holiday:
					style.append(("fill", rgbToHtmlColor(ui.statusIconHolidayFontColor)))
			if style:
				styleStr = "".join([f"{key}:{value};" for key, value in style])
				dayNum = f"<tspan style=\"{styleStr}\">{dayNum}</tspan>"
			data = data.replace(
				b"TX",
				toBytes(dayNum),
			)
		loader = GdkPixbuf.PixbufLoader.new_with_type(ext)
		if ui.statusIconFixedSizeEnable:
			try:
				width, height = ui.statusIconFixedSizeWH
				loader.set_size(width, height)
			except Exception:
				log.exception("")
		try:
			loader.write(data)
		finally:
			loader.close()
		pixbuf = loader.get_pixbuf()

		# alternative way:
		# stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
		# pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)

		self.sicon.set_from_pixbuf(pixbuf)

	def statusIconUpdateTooltip(self):
		try:
			sicon = self.sicon
		except AttributeError:
			return
		set_tooltip(sicon, self.getStatusIconTooltip())

	def statusIconUpdate(self, gdate=None, checkStatusIconMode=True):
		if checkStatusIconMode and self.statusIconMode < 1:
			return
		if gdate is None:
			gdate = localtime()[:3]
		if calTypes.primary == core.GREGORIAN:
			ddate = gdate
		else:
			ddate = core.convert(
				gdate[0],
				gdate[1],
				gdate[2],
				core.GREGORIAN,
				calTypes.primary,
			)
		#######
		self.sicon.set_from_file(join(pixDir, "starcal-24.png"))
		self.statusIconUpdateIcon(ddate)
		#######
		self.statusIconUpdateTooltip()
		return True

	def onStatusIconPress(self, obj, gevent):
		if gevent.button == 2:
			# middle button press
			self.copyDate(calTypes.primary)
			return True

	def onStatusIconClick(self, obj=None):
		if self.get_property("visible"):
			# ui.winX, ui.winY = self.get_position()
			# FIXME: ^ gives bad position sometimes
			# liveConfChanged()
			# log.debug(ui.winX, ui.winY)
			self.hide()
		else:
			self.move(ui.winX, ui.winY)
			# every calling of .hide() and .present(), makes dialog not on top
			# (forgets being on top)
			self.set_keep_above(ui.winKeepAbove)
			if ui.winSticky:
				self.stick()
			self.deiconify()
			self.present()

	def onDeleteEvent(self, widget=None, event=None):
		# ui.winX, ui.winY = self.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(ui.winX, ui.winY)
		if self.statusIconMode == 0 or not self.sicon:
			self.quit()
		elif self.statusIconMode > 1:
			if self.sicon.is_embedded():
				self.hide()
			else:
				self.quit()
		return True

	def onEscape(self):
		# ui.winX, ui.winY = self.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(ui.winX, ui.winY)
		if self.statusIconMode == 0:
			self.quit()
		elif self.statusIconMode > 1:
			if self.sicon.is_embedded():
				self.hide()

	def quit(self, widget=None, event=None):
		try:
			ui.saveLiveConf()
		except Exception:
			log.exception("")
		if self.statusIconMode > 1 and self.sicon:
			self.sicon.set_visible(False)
			# ^ needed for windows. before or after main_quit ?
		self.destroy()
		######
		t0 = now()
		core.stopRunningThreads()
		t1 = now()
		pixcache.cacheSaveStop()
		t2 = now()
		ui.eventUpdateQueue.stopLoop()
		t3 = now()
		log.info(f"stopRunningThreads took {t1 - t0:.6f} seconds")
		log.info(f"cacheSaveStop took {t2 - t1:.6f} seconds")
		log.info(f"eventUpdateQueue.stopLoop took {t3 - t2:.6f} seconds")
		######
		return gtk.main_quit()

	def adjustTime(self, widget=None, event=None):
		from subprocess import Popen
		if not ud.adjustTimeCmd:
			showError(
				"Failed to find gksudo, kdesudo, gksu, gnomesu, kdesu" +
				" or any askpass program to use with sudo",
				transient_for=self,
			)
			return
		Popen(ud.adjustTimeCmd, env=ud.adjustTimeEnv)

	def aboutShow(self, obj=None, data=None):
		if not self.aboutDialog:
			from scal3.ui_gtk.about import AboutDialog
			with open(
				join(sourceDir, "authors-dialog"),
				encoding="utf-8",
			) as authorsFile:
				authors = authorsFile.read().splitlines()
			dialog = AboutDialog(
				name=core.APP_DESC,
				version=core.VERSION,
				title=_("About ") + core.APP_DESC,
				authors=[
					_(author) for author in authors
				],
				comments=core.aboutText,
				license=core.licenseText,
				website=core.homePage,
				logo=GdkPixbuf.Pixbuf.new_from_file(ui.appLogo),
				transient_for=self,
			)
			# add Donate button, FIXME
			dialog.connect("delete-event", self.aboutHide)
			dialog.connect("response", self.aboutHide)
			# dialog.set_skip_taskbar_hint(True)
			self.aboutDialog = dialog
		openWindow(self.aboutDialog)

	def aboutHide(self, widget, arg=None):
		# arg maybe an event, or response id
		self.aboutDialog.hide()
		return True

	def prefShow(self, obj=None, data=None):
		if not ui.prefWindow:
			from scal3.ui_gtk.preferences import PreferencesWindow
			ui.prefWindow = PreferencesWindow(transient_for=self)
			ui.prefWindow.updatePrefGui()
		openWindow(ui.prefWindow)

	def eventManCreate(self):
		checkEventsReadOnly()  # FIXME
		if ui.eventManDialog is None:
			from scal3.ui_gtk.event.manager import EventManagerDialog
			ui.eventManDialog = EventManagerDialog(transient_for=self)

	def eventManShow(self, obj=None, data=None):
		self.eventManCreate()
		openWindow(ui.eventManDialog)

	def eventSearchCreate(self):
		if ui.eventSearchWin is None:
			from scal3.ui_gtk.event.search_events import EventSearchWindow
			ui.eventSearchWin = EventSearchWindow()

	def eventSearchShow(self, obj=None, data=None):
		self.eventSearchCreate()
		openWindow(ui.eventSearchWin)

	def addCustomEvent(self, obj=None):
		self.eventManCreate()
		ui.eventManDialog.addCustomEvent()

	def dayCalWinShow(self, obj=None, data=None):
		if not ui.dayCalWin:
			from scal3.ui_gtk.day_cal_window import DayCalWindow
			ui.dayCalWin = DayCalWindow()
		ui.dayCalWin.present()

	def timeLineShow(self, obj=None, data=None):
		if not ui.timeLineWin:
			from scal3.ui_gtk.timeline import TimeLineWindow
			ui.timeLineWin = TimeLineWindow()
		openWindow(ui.timeLineWin)

	def yearWheelShow(self, obj=None, data=None):
		if not ui.yearWheelWin:
			from scal3.ui_gtk.year_wheel import YearWheelWindow
			ui.yearWheelWin = YearWheelWindow()
		openWindow(ui.yearWheelWin)

	def selectDateShow(self, widget=None):
		if not self.selectDateDialog:
			from scal3.ui_gtk.selectdate import SelectDateDialog
			self.selectDateDialog = SelectDateDialog(transient_for=self)
			self.selectDateDialog.connect(
				"response-date",
				self.selectDateResponse,
			)
		self.selectDateDialog.show()

	def dayInfoShow(self, widget=None):
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog
			self.dayInfoDialog = DayInfoDialog(transient_for=self)
			self.emit("date-change")
		openWindow(self.dayInfoDialog)

	def customizeDialogCreate(self):
		if not self.customizeDialog:
			from scal3.ui_gtk.customize_dialog import CustomizeDialog
			self.customizeDialog = CustomizeDialog(self.layout, transient_for=self)

	def switchWcalMcal(self, widget=None):
		self.customizeDialogCreate()
		self.mainVBox.switchWcalMcal(self.customizeDialog)
		self.customizeDialog.updateTreeEnableChecks()
		self.customizeDialog.save()

	def customizeShow(self, obj=None, data=None):
		self.customizeDialogCreate()
		openWindow(self.customizeDialog)

	def exportShow(self, year, month):
		if not self.exportDialog:
			from scal3.ui_gtk.export import ExportDialog
			self.exportDialog = ExportDialog(transient_for=self)
		self.exportDialog.showDialog(year, month)

	def onExportClick(self, widget=None):
		self.exportShow(ui.cell.year, ui.cell.month)

	def onExportClickStatusIcon(self, widget=None, event=None):
		year, month, day = cal_types.getSysDate(calTypes.primary)
		self.exportShow(year, month)

	def onConfigChange(self, *a, **kw):
		if self.menuMain:
			self.menuMain.destroy()
			self.menuMain = None
		if self.menuCell:
			self.menuCell.destroy()
			self.menuCell = None
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		self.autoResize()
		# self.set_property("skip-taskbar-hint", not ui.winTaskbar)
		# self.set_skip_taskbar_hint  # FIXME
		# skip-taskbar-hint need to restart ro be applied
		# self.updateToolbarClock()  # FIXME
		# self.updateStatusIconClock()
		self.statusIconUpdate()


# #########################################################################3


# core.COMMAND = sys.argv[0] ## OR __file__ ## ????????


gtk.init_check(sys.argv)

# from scal3.os_utils import openUrl
# clickWebsite = lambda widget, url: openUrl(url)
# gtk.link_button_set_uri_hook(clickWebsite)
# gtk.about_dialog_set_url_hook(clickWebsite)

# gtk_link_button_set_uri_hook has been deprecated since version 2.24
# and should not be used in newly-written code.
# Use the “clicked” signal instead
# FIXME

# gtk_about_dialog_set_url_hook has been deprecated since version 2.24
# and should not be used in newly-written code.
# Use the “activate-link” signal
# FIXME


for plug in core.allPlugList:
	if hasattr(plug, "onCurrentDateChange"):
		listener.dateChange.add(plug)


"""
themeDir = join(sourceDir, "themes")
theme = "Dark" # "Default
if theme is not None:
	gtkrc = join(themeDir, theme, "gtkrc")
	try:
		#gtk.rc_set_default_files([gtkrc])
		gtk.rc_parse(gtkrc)
		#gtk.rc_reparse_all()
		#exec(open(join(themeDir, theme, "starcalrc")).read())
	except:
		log.exception("")
"""


def main():
	statusIconMode = 2
	action = ""
	if ui.showMain:
		action = "show"
	if len(sys.argv) > 1:
		if sys.argv[1] in ("--no-tray-icon", "--no-status-icon"):
			statusIconMode = 0
			action = "show"
		elif sys.argv[1] == "--hide":
			action = ""
		elif sys.argv[1] == "--show":
			action = "show"
		# elif sys.argv[1] == "--html":#????????????
		# 	action = "html"
		# elif sys.argv[1] == "--svg":#????????????
		# 	action = "svg"
	###############################
	ui.init()
	###############################
	pixcache.cacheSaveStart()
	ui.eventUpdateQueue.startLoop()
	###############################
	listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
	hijri_gtk.checkHijriMonthsExpiration()
	###############################
	checkEventsReadOnly(False)
	# FIXME: right place?
	event_lib.info.updateAndSave()
	###############################
	mainWin = MainWin(statusIconMode=statusIconMode)
	###############################
	# if action == "html":
	# 	mainWin.exportHtml("calendar.html") ## exportHtml(path, months, title)
	# 	sys.exit(0)
	# elif action == "svg":
	# 	mainWin.export.exportSvg(f"{core.deskDir}/2010-01.svg", [(2010, 1)])
	# 	sys.exit(0)
	if action == "show" or not mainWin.sicon:
		mainWin.present()
	if ui.showDesktopWidget:
		mainWin.dayCalWinShow()
	# ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
	# FIXME: ^
	# mainWin.app.run(None)
	signal.signal(signal.SIGINT, mainWin.quit)
	return gtk.main()


if __name__ == "__main__":
	sys.exit(main())
