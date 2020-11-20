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

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3.path import *
from scal3 import logger
from scal3.utils import myRaise

log = logger.get()

if not isfile(join(confDir, "core.json")) and not isdir(join(confDir, "event")):
	from scal3.utils import restartLow
	try:
		__import__("scal3.ui_gtk.import_config_2to3")
	except Exception as e:
		myRaise()
		log.error(str(e)) # TODO: log the full traceback
		if not isdir(confDir):
			os.mkdir(confDir, 0o755)
	else:
		if isfile(join(confDir, "core.json")):
			restartLow()

from scal3.utils import versionLessThan
from scal3.cal_types import calTypes
from scal3 import core

from scal3 import locale_man
from scal3.locale_man import rtl, lang ## import scal3.locale_man after core
#_ = locale_man.loadTranslator(False)## FIXME
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.utils import *
#from scal3.ui_gtk.color_utils import rgbToGdkColor
from scal3.ui_gtk import listener
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import DummyCalObj, CustomizableCalBox
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk import hijri as hijri_gtk


ui.uiName = "gtk"


mainWinItemsDesc = {
	"dayCal": _("Day Calendar"),
	"eventDayView": _("Events of Day"),
	"labelBox": _("Year & Month Labels"),
	"monthCal": _("Month Calendar"),
	"pluginsText": _("Plugins Text"),
	"seasonPBar": _("Season Progress Bar"),
	"yearPBar": _("Year Progress Bar"),
	"statusBar": _("Status Bar"),
	"toolbar": _("Toolbar"),
	"weekCal": _("Week Calendar"),
	"winContronller": _("Window Controller"),
}


#def show_event(widget, gevent):
#	print(type(widget), gevent.type.value_name, gevent.get_value())
#	# gevent.send_event


def liveConfChanged():
	tm = now()
	if tm - ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			ui.saveLiveConfLoop,
		)
		ui.lastLiveConfChangeTime = tm


# How to define icon of custom stock????????????
#gtk.stock_add((
#("gtk-evolution", "E_volution", gdk.ModifierType.BUTTON1_MASK, 0, "gtk20")


@registerSignals
class MainWinVbox(gtk.VBox, CustomizableCalBox):
	_name = "mainWin"
	desc = _("Main Window")
	params = (
		"ui.mainWinItems",
		"ui.winControllerButtons",
		"ui.mcalHeight",
		"ui.mcalLeftMargin",
		"ui.mcalTopMargin",
		"ui.mcalTypeParams",
		"ui.mcalGrid",
		"ui.mcalGridColor",
		"ui.wcalHeight",
		"ui.wcalTextSizeScale",
		"ui.wcalItems",
		"ui.wcalGrid",
		"ui.wcalGridColor",
		"ud.wcalToolbarData",
		"ui.wcal_toolbar_mainMenu_icon",
		"ui.wcal_weekDays_width",
		"ui.wcalFont_weekDays",
		"ui.wcalFont_pluginsText",
		"ui.wcal_eventsIcon_width",
		"ui.wcal_eventsText_showDesc",
		"ui.wcal_eventsText_colorize",
		"ui.wcalFont_eventsText",
		"ui.wcal_daysOfMonth_dir",
		"ui.wcalTypeParams",
		"ui.wcal_daysOfMonth_width",
		"ui.wcal_eventsCount_expand",
		"ui.wcal_eventsCount_width",
		"ui.wcalFont_eventsBox",
		"ui.dcalHeight",
		"ui.dcalTypeParams",
		"ui.pluginsTextInsideExpander",
		"ud.mainToolbarData",
	)

	def __init__(self):
		gtk.VBox.__init__(self)
		self.initVars()

	def updateVars(self):
		CustomizableCalBox.updateVars(self)
		ui.mainWinItems = self.getItemsData()

	def keyPress(self, arg, gevent):
		CustomizableCalBox.keyPress(self, arg, gevent)
		return True ## FIXME

	def switchWcalMcal(self, customizeDialog):
		wi = None
		mi = None
		for i, item in enumerate(self.items):
			if item._name == "weekCal":
				wi = i
			elif item._name == "monthCal":
				mi = i
		for itemIndex in (wi, mi):
			customizeDialog.loadItem(
				self,
				itemIndex,
				(itemIndex,),
			)
		wcal, mcal = self.items[wi], self.items[mi]
		wcal.enable, mcal.enable = mcal.enable, wcal.enable
		## FIXME
		#self.reorder_child(wcal, mi)
		#self.reorder_child(mcal, wi)
		#self.items[wi], self.items[mi] = mcal, wcal
		self.showHide()
		self.onDateChange()


@registerSignals
#class MainWin(gtk.ApplicationWindow, ud.IntegratedCalObj):
class MainWin(gtk.Window, ud.BaseCalObj):
	_name = "mainWin"
	desc = _("Main Window")
	timeout = 1 ## second
	setMinHeight = lambda self: self.resize(ui.winWidth, 2)
	#def maximize(self):
	#	pass

	def __init__(self, statusIconMode=2):
		#from gi.repository import Gio
		#self.app = gtk.Application(application_id="apps.starcal")
		#self.app.register(Gio.Cancellable.new())
		#gtk.ApplicationWindow.__init__(self, application=self.app)
		gtk.Window.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		ud.windowList.appendItem(self)
		ui.mainWin = self
		##################
		# statusIconMode:
		#	("none", "none")
		#	("statusIcon", "normal")
		#	("applet", "gnome")
		#	("applet", "kde")
		##
		#	0: none (simple window)
		#	1: applet
		#	2: standard status icon
		self.statusIconMode = statusIconMode
		###
		#ui.eventManDialog = None
		#ui.timeLineWin = None
		#ui.yearWheelWin = None
		###
		#ui.weekCalWin = WeekCalWindow()
		#ud.windowList.appendItem(ui.weekCalWin)
		###
		self.dayInfoDialog = None
		#print("windowList.items", [item._name for item in ud.windowList.items])
		###########
		##self.connect("window-state-event", selfStateEvent)
		self.set_title("%s %s" % (core.APP_DESC, core.VERSION))
		#self.connect("main-show", lambda arg: self.present())
		#self.connect("main-hide", lambda arg: self.hide())
		self.set_decorated(False)
		self.set_property("skip-taskbar-hint", not ui.winTaskbar)
		# self.set_skip_taskbar_hint  # FIXME
		self.set_role("starcal")
		#self.set_focus_on_map(True)#????????
		#self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		#self.connect("realize", self.onRealize)
		self.set_default_size(ui.winWidth, 1)
		try:
			self.move(ui.winX, ui.winY)
		except:
			pass
		#############################################################
		self.connect("focus-in-event", self.focusIn, "Main")
		self.connect("focus-out-event", self.focusOut, "Main")
		self.connect("button-press-event", self.buttonPress)
		self.connect("key-press-event", self.keyPress)
		self.connect("configure-event", self.configureEvent)
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
		#self.configureEvent(None, None)
		#self.connect("drag-motion", show_event)
		######################
		## ????????????????????????????????????????????????
		# when button is down(before button-release-event),
		# motion-notify-event does not recived!
		"""
		##################################################################
		self.focus = False
		#self.focusOutTime = 0
		#self.clockTr = None
		##################################################################
		self.winCon = None
		############
		self.vbox = MainWinVbox()
		ui.checkMainWinItems()
		itemsPkg = "scal3.ui_gtk.mainwin_items"
		for (name, enable) in ui.mainWinItems:
			#print(name, enable)
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
				except:
					myRaise()
					continue
				item = CalObj()
				item.enable = enable
				item.connect("size-allocate", self.childSizeAllocate)
				#modify_bg_all(
				#	item,
				#	gtk.StateType.NORMAL,
				#	rgbToGdkColor(*ui.bgColor),
				#)
			else:
				desc = mainWinItemsDesc[name]
				item = DummyCalObj(name, desc, itemsPkg, True)
			self.vbox.appendItem(item)
		self.appendItem(self.vbox)
		self.vbox.show()
		self.customizeDialog = None
		#######
		self.add(self.vbox)
		####################
		self.isMaximized = False
		####################
		#ui.prefDialog = None
		self.exportDialog = None
		self.selectDateDialog = None
		############### Building About Dialog
		self.aboutDialog = None
		###############
		self.menuMain = None
		#####
		check = gtk.CheckMenuItem(label=_("_On Top"))
		check.set_use_underline(True)
		check.connect("activate", self.keepAboveClicked)
		check.set_active(ui.winKeepAbove)
		self.set_keep_above(ui.winKeepAbove)
		self.checkAbove = check
		#####
		check = gtk.CheckMenuItem(label=_("_Sticky"))
		check.set_use_underline(True)
		check.connect("activate", self.stickyClicked)
		check.set_active(ui.winSticky)
		if ui.winSticky:
			self.stick()
		self.checkSticky = check
		############################################################
		self.statusIconInit()
		listener.dateChange.add(self)
		#if self.statusIconMode!=1:
		#	timeout_add_seconds(self.timeout, self.statusIconUpdate)
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
		#ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))

	#def mainWinStateEvent(self, obj, gevent):
		#print(dir(event))
		#print(gevent.new_window_state)
		#self.event = event

	def childSizeAllocate(self, cal, req):
		self.setMinHeight()

	def selectDateResponse(self, widget, y, m, d):
		ui.changeDate(y, m, d)
		self.onDateChange()

	def keyPress(self, arg, gevent):
		kname = gdk.keyval_name(gevent.keyval).lower()
		#print(now(), "MainWin.keyPress", kname)
		if kname == "escape":
			self.onEscape()
		elif kname == "f1":
			self.aboutShow()
		elif kname in ("insert", "plus", "kp_add"):
			self.eventManShow()
		elif kname in ("q", "arabic_dad"):## FIXME
			self.quit()
		else:
			self.vbox.keyPress(arg, gevent)
		return True ## FIXME

	def focusIn(self, widegt, event, data=None):
		self.focus = True
		if self.winCon and self.winCon.enable:
			self.winCon.windowFocusIn()

	def focusOut(self, widegt, event, data=None):
		# called 0.0004 sec (max) after focusIn
		# (if switched between two windows)
		dt = now() - ui.focusTime
		#print("focusOut", dt)
		if dt > 0.05:  # FIXME
			self.focus = False
			timeout_add(2, self.focusOutDo)

	def focusOutDo(self):
		if not self.focus:# and t-self.focusOutTime>0.002:
			ab = self.checkAbove.get_active()
			self.set_keep_above(ab)
			if self.winCon and self.winCon.enable:
				self.winCon.windowFocusOut()
		return False

	"""
	def checkResize(self, widget, req):
		if ui.mcalHeight != req.height:# and ui.winWidth == req.width:
			if req.height == 0:
				req.height = 1
			ui.mcalHeight = req.height
	"""

	def configureEvent(self, widget, gevent):
		wx, wy = self.get_position()
		maxPosDelta = max(
			abs(ui.winX - wx),
			abs(ui.winY - wy),
		)
		#print(wx, wy)
		ww, wh = self.get_size()
		#if ui.bgUseDesk and maxPosDelta > 1:## FIXME
		#	self.queue_draw()
		if self.get_property("visible"):
			ui.winX, ui.winY = (wx, wy)
		ui.winWidth = ww
		liveConfChanged()
		return False

	def buttonPress(self, obj, gevent):
		print("MainWin.buttonPress")
		b = gevent.button
		#print("buttonPress", b)
		if b == 3:
			self.menuMainCreate()
			self.menuMain.popup(None, None, None, None, 3, gevent.time)
			ui.updateFocusTime()
		elif b == 1:
			# FIXME: used to cause problems with `ConButton` when using 'pressed' and 'released' signals
			self.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
		return False

	def childButtonPress(self, widget, gevent):
		b = gevent.button
		#print(dir(gevent))
		#foo, x, y, mask = gevent.get_window().get_pointer()
		#x, y = self.get_pointer()
		x, y = gevent.x_root, gevent.y_root
		if b == 1:
			self.begin_move_drag(gevent.button, x, y, gevent.time)
			return True
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
			ui.updateFocusTime()
			return True
		return False

	def startResize(self, widget, gevent):
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
		return self.changeDate(*core.getSysDate(calTypes.primary))

	def onDateChange(self, *a, **kw):
		#print("MainWin.onDateChange")
		ud.BaseCalObj.onDateChange(self, *a, **kw)
		#for j in range(len(core.plugIndex)):##????????????????????
		#	try:
		#		core.allPlugList[core.plugIndex[j]].date_change(*date)
		#	except AttributeError:
		#		pass
		self.setMinHeight()
		for j in range(len(core.plugIndex)):
			try:
				core.allPlugList[core.plugIndex[j]].date_change_after(*date)
			except AttributeError:
				pass
		#print("Occurence Time: max=%e, avg=%e" % (
		#	ui.Cell.ocTimeMax,
		#	ui.Cell.ocTimeSum/ui.Cell.ocTimeCount
		#))

	def getEventAddToMenuItem(self):
		from scal3.ui_gtk.drawing import newColorCheckPixbuf
		addToItem = labelStockMenuItem("_Add to", gtk.STOCK_ADD)
		if event_lib.allReadOnly:
			addToItem.set_sensitive(False)
			return addToItem
		menu2 = gtk.Menu()
		##
		for group in ui.eventGroups:
			if not group.enable:
				continue
			if not group.showInCal():## FIXME
				continue
			eventTypes = group.acceptsEventTypes
			if not eventTypes:
				continue
			item2 = ImageMenuItem()
			item2.set_label(group.title)
			##
			image = gtk.Image()
			if group.icon:
				image.set_from_file(group.icon)
			else:
				image.set_from_pixbuf(newColorCheckPixbuf(group.color, 20, True))
			item2.set_image(image)
			##
			if len(eventTypes) == 1:
				item2.connect("activate", self.addToGroupFromMenu, group, eventTypes[0])
			else:
				menu3 = gtk.Menu()
				for eventType in eventTypes:
					eventClass = event_lib.classes.event.byName[eventType]
					item3 = ImageMenuItem()
					item3.set_label(eventClass.desc)
					icon = eventClass.getDefaultIcon()
					if icon:
						item3.set_image(imageFromFile(icon))
					item3.connect("activate", self.addToGroupFromMenu, group, eventType)
					menu3.add(item3)
				menu3.show_all()
				item2.set_submenu(menu3)
			menu2.add(item2)
		##
		menu2.show_all()
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
			parent=parent,
		).run()
		if event is None:
			return
		ui.eventDiff.add("e", event)
		self.onConfigChange()

	def trimMenuItemLabel(self, s: str, maxLen: int):
		if len(s) > maxLen-3:
			s = s[:maxLen-3].rstrip(" ") + "..."
		return s

	def addEditEventCellMenuItems(self, menu):
		if event_lib.allReadOnly:
			return
		eventsData = ui.cell.eventsData
		if not eventsData:
			return
		if len(eventsData) < 4: # make it customizable TODO
			for eData in eventsData:
				groupId, eventId = eData["ids"]
				menu.add(labelImageMenuItem(
					_("Edit") + ": " + self.trimMenuItemLabel(eData["text"][0], 25),
					eData["icon"],
					self.editEventFromMenu, groupId, eventId,
				))
		else:
			subMenu = gtk.Menu()
			subMenuItem = labelStockMenuItem("_Edit Event", gtk.STOCK_ADD)
			for eData in eventsData:
				groupId, eventId = eData["ids"]
				subMenu.add(labelImageMenuItem(
					eData["text"][0],
					eData["icon"],
					self.editEventFromMenu, groupId, eventId,
				))
			subMenu.show_all()
			subMenuItem.set_submenu(subMenu)
			menu.add(subMenuItem)

	def menuCellPopup(self, widget, etime, x, y):
		calObjName = widget._name  # why private? FIXME
		# calObjName is in ("weekCal", "monthCal", ...)
		menu = gtk.Menu()
		####
		for calType in calTypes.active:
			menu.add(labelStockMenuItem(
				_("Copy %s Date") % _(calTypes.getDesc(calType)),
				gtk.STOCK_COPY,
				self.copyDateGetCallback(calType),
				calType,
			))
		menu.add(labelStockMenuItem(
			"Day Info",
			gtk.STOCK_INFO,
			self.dayInfoShow,
		))
		menu.add(self.getEventAddToMenuItem())
		self.addEditEventCellMenuItems(menu)
		menu.add(gtk.SeparatorMenuItem())
		menu.add(labelStockMenuItem(
			"Select _Today",
			gtk.STOCK_HOME,
			self.goToday,
		))
		menu.add(labelStockMenuItem(
			"Select _Date...",
			gtk.STOCK_INDEX,
			self.selectDateShow,
		))
		if calObjName in ("weekCal", "monthCal"):
			menu.add(labelStockMenuItem(
				"Switch to " + (
					"Month Calendar" if calObjName == "weekCal"
					else "Week Calendar"
				),
				gtk.STOCK_REDO,
				self.switchWcalMcal,
			))
		if os.path.isfile("/usr/bin/evolution"):  # FIXME
			menu.add(labelImageMenuItem(
				"In E_volution",
				"evolution-18.png",
				ui.dayOpenEvolution,
			))
		#if os.path.isfile("/usr/bin/sunbird"):  # FIXME
		#	menu.add(labelImageMenuItem(
		#	"In _Sunbird",
		#	"sunbird-18.png",
		#	ui.dayOpenSunbird,
		#))
		####
		moreMenu = gtk.Menu()
		moreMenu.add(labelStockMenuItem(
			"_Customize",
			gtk.STOCK_EDIT,
			self.customizeShow,
		))
		moreMenu.add(labelStockMenuItem(
			"_Preferences",
			gtk.STOCK_PREFERENCES,
			self.prefShow,
		))
		moreMenu.add(labelStockMenuItem(
			"_Event Manager",
			gtk.STOCK_ADD,
			self.eventManShow,
		))
		moreMenu.add(labelImageMenuItem(
			"Time Line",
			"timeline-18.png",
			self.timeLineShow,
		))
		moreMenu.add(labelImageMenuItem(
			"Year Wheel",
			"year-wheel-18.png",
			self.yearWheelShow,
		))  # icon? FIXME
		#moreMenu.add(labelImageMenuItem(
		#	"Week Calendar",
		#	"weekcal-18.png",
		#	self.weekCalShow,
		#))
		moreMenu.add(labelStockMenuItem(
			_("Export to %s") % "HTML",
			gtk.STOCK_CONVERT,
			self.exportClicked,
		))
		moreMenu.add(labelStockMenuItem(
			"_About",
			gtk.STOCK_ABOUT,
			self.aboutShow,
		))
		if self.statusIconMode != 1:
			moreMenu.add(labelStockMenuItem(
				"_Quit",
				gtk.STOCK_QUIT,
				self.quit,
			))
		##
		moreMenu.show_all()
		moreItem = MenuItem(_("More"))
		moreItem.set_submenu(moreMenu)
		#moreItem.show_all()
		menu.add(moreItem)
		####
		menu.show_all()
		dx, dy = widget.translate_coordinates(self, x, y)
		foo, wx, wy = self.get_window().get_origin()
		x = wx + dx
		y = wy + dy
		if rtl:
			x -= get_menu_width(menu)
		####
		etime = gtk.get_current_event_time()
		#print("menuCellPopup", x, y, etime)
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
		menu = gtk.Menu()
		####
		item = ImageMenuItem(_("Resize"))
		item.set_image(imageFromFile("resize.png"))
		item.connect("button-press-event", self.startResize)
		menu.add(item)
		#######
		menu.add(self.checkAbove)
		menu.add(self.checkSticky)
		#######
		menu.add(labelStockMenuItem(
			"Select _Today",
			gtk.STOCK_HOME,
			self.goToday,
		))
		menu.add(labelStockMenuItem(
			"Select _Date...",
			gtk.STOCK_INDEX,
			self.selectDateShow,
		))
		menu.add(labelStockMenuItem(
			"Day Info",
			gtk.STOCK_INFO,
			self.dayInfoShow,
		))
		menu.add(labelStockMenuItem(
			"_Customize",
			gtk.STOCK_EDIT,
			self.customizeShow,
		))
		menu.add(labelStockMenuItem(
			"_Preferences",
			gtk.STOCK_PREFERENCES,
			self.prefShow,
		))
		#menu.add(labelStockMenuItem(
		#	"_Add Event",
		#	gtk.STOCK_ADD,
		#	ui.addCustomEvent,
		#))
		#menu.add(labelStockMenuItem(
		#	"_Event Manager",
		#	gtk.STOCK_ADD,
		#	self.eventManShow,
		#))
		menu.add(labelImageMenuItem(
			"Time Line",
			"timeline-18.png",
			self.timeLineShow,
		))
		menu.add(labelImageMenuItem(
			"Year Wheel",
			"year-wheel-18.png",
			self.yearWheelShow,
		))  # icon? FIXME
		#menu.add(labelImageMenuItem(
		#	"Week Calendar",
		#	"weekcal-18.png",
		#	self.weekCalShow,
		#))
		menu.add(labelStockMenuItem(
			_("Export to %s") % "HTML",
			gtk.STOCK_CONVERT,
			self.exportClicked,
		))
		menu.add(labelStockMenuItem(
			"Ad_just System Time",
			gtk.STOCK_PREFERENCES,
			self.adjustTime,
		))
		menu.add(labelStockMenuItem(
			"_About",
			gtk.STOCK_ABOUT,
			self.aboutShow,
		))
		if self.statusIconMode != 1:
			menu.add(labelStockMenuItem(
				"_Quit",
				gtk.STOCK_QUIT,
				self.quit,
			))
		menu.show_all()
		self.menuMain = menu

	def menuMainPopup(self, widget, etime, x, y):
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
		#print("menuMainPopup", x, y, etime)
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
		#print("addToGroupFromMenu", group.title, eventType)
		title = _("Add ") + event_lib.classes.event.byName[eventType].desc
		event = addNewEvent(
			group,
			eventType,
			useSelectedDate=True,
			title=title,
			parent=self,
		)
		if event is None:
			return
		ui.eventDiff.add("+", event)
		self.onConfigChange()

	def prefUpdateBgColor(self, cal):
		if ui.prefDialog:
			ui.prefDialog.colorbBg.set_color(ui.bgColor)
		#else:## FIXME
		ui.saveLiveConf()

	def keepAboveClicked(self, check):
		act = check.get_active()
		self.set_keep_above(act)
		ui.winKeepAbove = act
		ui.saveLiveConf()

	def stickyClicked(self, check):
		if check.get_active():
			self.stick()
			ui.winSticky = True
		else:
			self.unstick()
			ui.winSticky = False
		ui.saveLiveConf()

	def copyDate(self, calType: int):
		setClipboard(ui.cell.format(ud.dateFormatBin, mode=calType))

	def copyDateGetCallback(self, calType: int):
		return lambda obj=None, event=None: setClipboard(ui.cell.format(ud.dateFormatBin, mode=calType))

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

	#def weekCalShow(self, obj=None, data=None):
	#	openWindow(ui.weekCalWin)

	def statusIconInit(self):
		if self.statusIconMode == 2:
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
				##self.sicon.set_blinking(True)
				## ^ for Alarms ## some problem with gnome-shell
				#self.sicon.set_name("starcal")
				# Warning: g_object_notify: object class `GtkStatusIcon"
				# has no property named `name"
				self.sicon.set_title(core.APP_DESC)
				self.sicon.set_visible(True)  # is needed?
				self.sicon.connect(
					"button-press-event",
					self.statusIconButtonPress,
				)
				self.sicon.connect("activate", self.statusIconClicked)
				self.sicon.connect("popup-menu", self.statusIconPopup)
				#self.sicon.set_from_stock(gtk.STOCK_HOME)
		else:
			self.sicon = None

	def getMainWinMenuItem(self):
		return labelMenuItem("Main Window", self.statusIconClicked)

	def getStatusIconPopupItems(self):
		return [
			labelStockMenuItem(
				"Copy _Time",
				gtk.STOCK_COPY,
				self.copyTime,
			),
			labelStockMenuItem(
				"Copy _Date",
				gtk.STOCK_COPY,
				self.copyDateToday,
			),
			labelStockMenuItem(
				"Ad_just System Time",
				gtk.STOCK_PREFERENCES,
				self.adjustTime,
			),
			#labelStockMenuItem(
			#	"_Add Event",
			#	gtk.STOCK_ADD,
			#	ui.addCustomEvent,
			#),  # FIXME
			labelStockMenuItem(
				_("Export to %s") % "HTML",
				gtk.STOCK_CONVERT,
				self.exportClickedStatusIcon,
			),
			labelStockMenuItem(
				"_Preferences",
				gtk.STOCK_PREFERENCES,
				self.prefShow,
			),
			labelStockMenuItem(
				"_Customize",
				gtk.STOCK_EDIT,
				self.customizeShow,
			),
			labelStockMenuItem(
				"_Event Manager",
				gtk.STOCK_ADD,
				self.eventManShow,
			),
			labelImageMenuItem(
				"Time Line",
				"timeline-18.png",
				self.timeLineShow,
			),
			labelImageMenuItem(
				"Year Wheel",
				"year-wheel-18.png",
				self.yearWheelShow,
			),  # icon? FIXME
			labelStockMenuItem(
				"_About",
				gtk.STOCK_ABOUT,
				self.aboutShow,
			),
			gtk.SeparatorMenuItem(),
			labelStockMenuItem(
				"_Quit",
				gtk.STOCK_QUIT,
				self.quit,
			),
		]

	def statusIconPopup(self, sicon, button, etime):
		menu = gtk.Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave
			setupMenuHideOnLeave(menu)
		items = self.getStatusIconPopupItems()
		# items.insert(0, self.getMainWinMenuItem())## FIXME
		get_pos_func = None
		y1 = 0
		geo = self.sicon.get_geometry()
		## Previously geo was None on windows, and on Linux it had `geo.index(1)` (not sure about the type)
		## Now it's tuple on both Linux and windows
		if geo is None:
			items.reverse()
		elif isinstance(geo, tuple):
			# geo == (True, screen, area, orientation)
			y1 = geo[2].y
		else:
			y1 = geo.index(1)
		try:
			y = gtk.StatusIcon.position_menu(menu, self.sicon)[1]
		except TypeError: ## new gi versions
			y = gtk.StatusIcon.position_menu(menu, 0, 0, self.sicon)[1]
		if y1 > 0 and y < y1:  # taskbar is on bottom
			items.reverse()
		get_pos_func = gtk.StatusIcon.position_menu
		for item in items:
			menu.add(item)
		menu.show_all()
		#print("statusIconPopup", button, etime)
		menu.popup(None, None, get_pos_func, self.sicon, button, etime)
		#self.sicon.do_popup_menu(self.sicon, button, etime)
		ui.updateFocusTime()
		self.sicon.menu = menu ## to prevent gurbage collected

	def onCurrentDateChange(self, gdate):
		self.statusIconUpdate(gdate=gdate)

	def getStatusIconTooltip(self):
		##tt = core.weekDayName[core.getWeekDay(*ddate)]
		tt = core.weekDayName[core.jwday(ui.todayCell.jd)]
		#if ui.pluginsTextStatusIcon:##?????????
		#	sep = _(",")+" "
		#else:
		sep = "\n"
		for mode in calTypes.active:
			y, m, d = ui.todayCell.dates[mode]
			tt += "%s%s %s %s" % (
				sep,
				_(d),
				locale_man.getMonthName(mode, m, y),
				_(y),
			)
		if ui.pluginsTextStatusIcon:
			text = ui.todayCell.pluginsText
			if text != "":
				tt += "\n\n%s" % text  # .replace("\t", "\n") ## FIXME
		for item in ui.todayCell.eventsData:
			if not item["showInStatusIcon"]:
				continue
			itemS = ""
			if item["time"]:
				itemS += item["time"] + " - "
			itemS += item["text"][0]
			tt += "\n\n%s" % itemS
		return tt

	def statusIconUpdateIcon(self, ddate):  # FIXME
		from scal3.utils import toBytes
		imagePath = (
			ui.statusIconImageHoli if ui.todayCell.holiday
			else ui.statusIconImage
		)
		ext = os.path.splitext(imagePath)[1][1:].lower()
		loader = GdkPixbuf.PixbufLoader.new_with_type(ext)
		if ui.statusIconFixedSizeEnable:
			try:
				width, height = ui.statusIconFixedSizeWH
				loader.set_size(width, height)
			except:
				myRaise()
		data = open(imagePath, "rb").read()
		if ext == "svg":
			dayNum = locale_man.numEncode(
				ddate[2],
				mode=calTypes.primary,  # FIXME
			)
			if ui.statusIconFontFamilyEnable:
				if ui.statusIconFontFamily:
					family = ui.statusIconFontFamily
				else:
					family = ui.getFont()[0]
				dayNum = "<tspan style=\"font-family:%s\">%s</tspan>" % (
					family,
					dayNum,
				)
			data = data.replace(
				b"TX",
				toBytes(dayNum),
			)
		loader.write(data)
		loader.close()
		pixbuf = loader.get_pixbuf()
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
		if calTypes.primary == core.DATE_GREG:
			ddate = gdate
		else:
			ddate = core.convert(
				gdate[0],
				gdate[1],
				gdate[2],
				core.DATE_GREG,
				calTypes.primary,
			)
		#######
		self.sicon.set_from_file(join(pixDir, "starcal-24.png"))
		self.statusIconUpdateIcon(ddate)
		#######
		self.statusIconUpdateTooltip()
		return True

	def statusIconButtonPress(self, obj, gevent):
		if gevent.button == 2:
			## middle button press
			self.copyDate(calTypes.primary)
			return True

	def statusIconClicked(self, obj=None):
		if self.get_property("visible"):
			#ui.winX, ui.winY = self.get_position()
			# ^ FIXME gives bad position sometimes
			#liveConfChanged()
			#print(ui.winX, ui.winY)
			self.hide()
		else:
			self.move(ui.winX, ui.winY)
			# every calling of .hide() and .present(), makes dialog not on top
			# (forgets being on top)
			act = self.checkAbove.get_active()
			self.set_keep_above(act)
			if self.checkSticky.get_active():
				self.stick()
			self.deiconify()
			self.present()

	def onDeleteEvent(self, widget=None, event=None):
		#ui.winX, ui.winY = self.get_position()
		# ^ FIXME gives bad position sometimes
		#liveConfChanged()
		#print(ui.winX, ui.winY)
		if self.statusIconMode == 0 or not self.sicon:
			self.quit()
		elif self.statusIconMode > 1:
			if self.sicon.is_embedded():
				self.hide()
			else:
				self.quit()
		return True

	def onEscape(self):
		#ui.winX, ui.winY = self.get_position()
		# ^ FIXME gives bad position sometimes
		#liveConfChanged()
		#print(ui.winX, ui.winY)
		if self.statusIconMode == 0:
			self.quit()
		elif self.statusIconMode > 1:
			if self.sicon.is_embedded():
				self.hide()

	def quit(self, widget=None, event=None):
		try:
			ui.saveLiveConf()
		except:
			myRaise()
		if self.statusIconMode > 1 and self.sicon:
			self.sicon.set_visible(False)
			# ^ needed for windows. before or after main_quit ?
		self.destroy()
		######
		core.stopRunningThreads()
		######
		return gtk.main_quit()

	def adjustTime(self, widget=None, event=None):
		from subprocess import Popen
		if not ud.adjustTimeCmd:
			showError("Failed to find gksudo, kdesudo, gksu, gnomesu, kdesu or any askpass program to use with sudo")
			return
		Popen(ud.adjustTimeCmd, env=ud.adjustTimeEnv)

	def aboutShow(self, obj=None, data=None):
		if not self.aboutDialog:
			from scal3.ui_gtk.about import AboutDialog
			with open(
				join(rootDir, "authors-dialog"),
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
				parent=self,
			)
			# add Donate button, FIXME
			dialog.connect("delete-event", self.aboutHide)
			dialog.connect("response", self.aboutHide)
			#dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file(ui.logo))
			#dialog.set_skip_taskbar_hint(True)
			self.aboutDialog = dialog
		openWindow(self.aboutDialog)

	def aboutHide(self, widget, arg=None):
		# arg maybe an event, or response id
		self.aboutDialog.hide()
		return True

	def prefShow(self, obj=None, data=None):
		if not ui.prefDialog:
			from scal3.ui_gtk.preferences import PrefDialog
			ui.prefDialog = PrefDialog(self.statusIconMode, parent=self)
			ui.prefDialog.updatePrefGui()
		openWindow(ui.prefDialog)

	def eventManCreate(self):
		checkEventsReadOnly() ## FIXME
		if not ui.eventManDialog:
			from scal3.ui_gtk.event.manager import EventManagerDialog
			ui.eventManDialog = EventManagerDialog(parent=self)

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
			self.selectDateDialog = SelectDateDialog(parent=self)
			self.selectDateDialog.connect(
				"response-date",
				self.selectDateResponse,
			)
		self.selectDateDialog.show()

	def dayInfoShow(self, widget=None):
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog
			self.dayInfoDialog = DayInfoDialog(parent=self)
			self.dayInfoDialog.onDateChange()
		openWindow(self.dayInfoDialog)

	def customizeDialogCreate(self):
		if not self.customizeDialog:
			from scal3.ui_gtk.customize_dialog import CustomizeDialog
			self.customizeDialog = CustomizeDialog(self.vbox, parent=self)

	def switchWcalMcal(self, widget=None):
		self.customizeDialogCreate()
		self.vbox.switchWcalMcal(self.customizeDialog)
		self.customizeDialog.updateTreeEnableChecks()
		self.customizeDialog.save()

	def customizeShow(self, obj=None, data=None):
		self.customizeDialogCreate()
		openWindow(self.customizeDialog)

	def exportShow(self, year, month):
		if not self.exportDialog:
			from scal3.ui_gtk.export import ExportDialog
			self.exportDialog = ExportDialog(parent=self)
		self.exportDialog.showDialog(year, month)

	def exportClicked(self, widget=None):
		self.exportShow(ui.cell.year, ui.cell.month)

	def exportClickedStatusIcon(self, widget=None, event=None):
		year, month, day = core.getSysDate(calTypes.primary)
		self.exportShow(year, month)

	def onConfigChange(self, *a, **kw):
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		#self.set_property("skip-taskbar-hint", not ui.winTaskbar)
		# self.set_skip_taskbar_hint ## FIXME
		# skip-taskbar-hint need to restart ro be applied
		#self.updateToolbarClock()## FIXME
		#self.updateStatusIconClock()
		self.statusIconUpdate()


###########################################################################3


#core.COMMAND = sys.argv[0] ## OR __file__ ## ????????


gtk.init_check(sys.argv)

# clickWebsite = lambda widget, url: core.openUrl(url)
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
themeDir = join(rootDir, "themes")
theme = "Dark" # "Default
if theme is not None:
	gtkrc = join(themeDir, theme, "gtkrc")
	try:
		#gtk.rc_set_default_files([gtkrc])
		gtk.rc_parse(gtkrc)
		#gtk.rc_reparse_all()
		#exec(open(join(themeDir, theme, "starcalrc")).read())
	except:
		myRaise(__file__)
"""


def main():
	"""
	try:
		import psyco
	except ImportError:
		print("Warning: module "psyco" not found. It could speed up execution.")
		psyco_found=False
	else:
		psyco.full()
		print("Using module "psyco" to speed up execution.")
		psyco_found=True"""
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
		#elif sys.argv[1] == "--html":#????????????
		#	action = "html"
		#elif sys.argv[1] == "--svg":#????????????
		#	action = "svg"
	###############################
	ui.init()
	###############################
	listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
	hijri_gtk.checkHijriMonthsExpiration()
	###############################
	checkEventsReadOnly(False)
	## right place? FIXME
	event_lib.info.updateAndSave()
	###############################
	mainWin = MainWin(statusIconMode=statusIconMode)
	#if action == "html":
	#	mainWin.exportHtml("calendar.html") ## exportHtml(path, months, title)
	#	sys.exit(0)
	#elif action == "svg":
	#	mainWin.export.exportSvg("%s/2010-01.svg"%core.deskDir, [(2010, 1)])
	#	sys.exit(0)
	if action == "show" or not mainWin.sicon:
		mainWin.present()
	#ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
	# ^ FIXME
	#mainWin.app.run(None)
	signal.signal(signal.SIGINT, mainWin.quit)
	return gtk.main()


if __name__ == "__main__":
	sys.exit(main())
