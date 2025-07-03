#!/usr/bin/env python3
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

import os
import os.path
import signal
import sys
from os.path import dirname, join
from time import localtime, perf_counter
from typing import TYPE_CHECKING

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger

log = logger.get()

from gi.repository import Gio as gio

import scal3.account.starcal  # noqa: F401
from scal3.event_lib import ev

try:
	import scal3.account.google  # noqa: F401
except Exception as e:
	log.error(f"error loading google account module: {e}")


from scal3 import cal_types, core, event_lib, locale_man, ui
from scal3.cal_types import calTypes, convert
from scal3.cell import init as initCell
from scal3.color_utils import rgbToHtmlColor
from scal3.locale_man import rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.path import pixDir, sourceDir
from scal3.ui import conf
from scal3.ui.msgs import menuMainItemDefs
from scal3.ui_gtk import (
	GdkPixbuf,
	Menu,
	VBox,
	gdk,
	gtk,
	listener,
	menuitems,
	pixcache,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk import hijri as hijri_gtk
from scal3.ui_gtk.customize import CustomizableCalBox, CustomizableCalObj, DummyCalObj
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.layout import WinLayoutBox, WinLayoutObj
from scal3.ui_gtk.mainwin_items import mainWinItemsDesc
from scal3.ui_gtk.menuitems import (
	CheckMenuItem,
	ImageMenuItem,
)
from scal3.ui_gtk.signals import registerSignals
from scal3.ui_gtk.starcal_import_all import doFullImport
from scal3.ui_gtk.utils import (
	get_menu_height,
	get_menu_width,
	openWindow,
	setClipboard,
	showError,
)

if TYPE_CHECKING:
	from collections.abc import Callable
	from types import FrameType
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType
	from scal3.ui_gtk.about import AboutDialog
	from scal3.ui_gtk.customize_dialog import CustomizeWindow
	from scal3.ui_gtk.day_info import DayInfoDialog
	from scal3.ui_gtk.export import ExportDialog
	from scal3.ui_gtk.gtk_ud import CalObjType
	from scal3.ui_gtk.right_panel import MainWinRightPanel
	from scal3.ui_gtk.selectdate import SelectDateDialog
	from scal3.ui_gtk.statusBar import CalObj as StatusBar
	from scal3.ui_gtk.winContronller import CalObj as WinContronllersObj

__all__ = ["MainWin", "checkEventsReadOnly", "listener", "main"]


# _ = locale_man.loadTranslator()  # FIXME

ui.uiName = "gtk"


def liveConfChanged() -> None:
	tm = perf_counter()
	if tm - ui.lastLiveConfChangeTime > ui.saveLiveConfDelay:
		timeout_add(
			int(ui.saveLiveConfDelay * 1000),
			ui.saveLiveConfLoop,
		)
		ui.lastLiveConfChangeTime = tm


@registerSignals
class MainWinVbox(gtk.Box, CustomizableCalBox):  # type: ignore[misc]
	vertical = True
	objName = "mainPanel"
	desc = _("Main Panel")
	itemListCustomizable = True
	myKeys: set[str] = {
		"down",
		"end",
		"f10",
		"home",
		"i",
		"j",
		"k",
		"left",
		"m",
		"menu",
		"n",
		"p",
		"page_down",
		"page_up",
		"right",
		"space",
		"t",
		"up",
	}

	def __init__(self, win: MainWin) -> None:
		self.win = win
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w: gtk.Box = self
		self.initVars()

	def createItems(self) -> None:
		win = self.win
		itemsPkg = "scal3.ui_gtk.mainwin_items"

		for name, enable in conf.mainWinItems.v:
			if name in {"winContronller", "statusBar"}:
				log.warning(f"Skipping main win item {name!r}")
				continue
			# log.debug(name, enable)
			if not enable:
				self.appendItem(
					DummyCalObj(name, mainWinItemsDesc[name], itemsPkg, True),  # type: ignore[arg-type]
				)
				continue

			try:
				module = __import__(
					f"{itemsPkg}.{name}",
					fromlist=["CalObj"],
				)
				CalObj = module.CalObj
			except RuntimeError:
				raise
			except Exception as e:
				log.error(f"error importing mainWinItem {name}")
				log.exception("")
				if os.getenv("STARCAL_DEV") == "1":
					raise e from None
				continue
			# try:
			item = CalObj(win)
			# except Exception as e:
			# 	log.error(f"creating {CalObj} instance at {module}: {e}")
			# 	raise
			item.enable = enable
			self.appendItem(item)
			signalNames = {sigTup[0] for sigTup in item.signals}
			if "popup-cell-menu" in signalNames:
				item.connect("popup-cell-menu", win.menuCellPopup)
			if "popup-main-menu" in signalNames:
				item.connect("popup-main-menu", win.menuMainPopup)
			if "pref-update-bg-color" in signalNames:
				item.connect("pref-update-bg-color", win.prefUpdateBgColor)
			if "day-info" in signalNames:
				item.connect("day-info", win.dayInfoShow)

	def updateVars(self) -> None:
		CustomizableCalBox.updateVars(self)
		conf.mainWinItems.v = self.getItemsData()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		CustomizableCalBox.onKeyPress(self, arg, gevent)
		return True  # FIXME

	def switchWcalMcal(self, customizeWindow: CustomizeWindow) -> None:
		wi = None
		mi = None
		for i, item in enumerate(self.items):
			if item.objName == "weekCal":
				wi = i
			elif item.objName == "monthCal":
				mi = i
		if wi is None or mi is None:
			log.error(f"weekCal index: {wi}, monthCal index: {mi}")
			return
		for itemIndex in (wi, mi):
			customizeWindow.loadItem(self, itemIndex)
		wcal, mcal = self.items[wi], self.items[mi]
		wcal.enable, mcal.enable = mcal.enable, wcal.enable
		# FIXME
		# self.reorder_child(wcal, mi)
		# self.reorder_child(mcal, wi)
		# self.items[wi], self.items[mi] = mcal, wcal
		self.showHide()
		self.onDateChange()

	def getOptionsWidget(self) -> gtk.Widget | None:
		if self.optionsWidget is not None:
			return self.optionsWidget
		self.optionsWidget = VBox(spacing=self.optionsPageSpacing)
		return self.optionsWidget


@registerSignals
class MainWin(gtk.ApplicationWindow, ud.BaseCalObj):  # type: ignore[misc]
	objName = "mainWin"
	desc = _("Main Window")
	timeout = 1  # second
	signals = ud.BaseCalObj.signals + [
		("toggle-right-panel", []),
	]

	def autoResize(self) -> None:
		self.w.resize(conf.winWidth.v, conf.winHeight.v)

	# def maximize(self):
	# 	pass

	def __init__(self, statusIconMode: int = 2) -> None:
		super().__init__()
		appId = "apps.starcal"
		# if this application_id is already running, Gtk will crash
		# with Segmentation fault
		if ev.allReadOnly:
			appId += "2"
		self.app = gtk.Application(application_id=appId)
		self.app.register(gio.Cancellable.new())
		gtk.ApplicationWindow.__init__(self, application=self.app)
		self.w: gtk.Window = self
		# ---
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		ud.windowList.appendItem(self)
		ui.mainWin = self
		# ------------------
		self.unmaxWinWidth = 0
		self.ignoreConfigureEvent = False
		# ------------------
		# statusIconMode:
		#   ("none", "none")
		#   ("statusIcon", "normal")
		#   ("applet", "gnome")
		#   ("applet", "kde")
		# --
		#   0: none (simple window)
		#   1: (dropped) applet
		#   2: standard status icon
		self.statusIconMode = statusIconMode
		# ---
		# ui.eventManDialog = None
		# ui.timeLineWin = None
		# ui.yearWheelWin = None
		# ---
		# ui.weekCalWin = WeekCalWindow()
		# ud.windowList.appendItem(ui.weekCalWin)
		# ---
		self.dayInfoDialog: DayInfoDialog | None = None
		# log.debug("windowList.items", [item.objName for item in ud.windowList.items])
		# -----------
		# self.connect("window-state-event", selfStateEvent)
		self.w.set_title(f"{core.APP_DESC} {core.VERSION}")
		# self.connect("main-show", lambda arg: self.present())
		# self.connect("main-hide", lambda arg: self.hide())
		self.w.set_decorated(False)
		self.w.set_property("skip-taskbar-hint", not conf.winTaskbar.v)
		# self.w.set_skip_taskbar_hint  # FIXME
		self.w.set_role("starcal")
		# self.w.set_focus_on_map(True)#????????
		# self.w.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# self.w.connect("realize", self.onRealize)
		self.w.set_default_size(conf.winWidth.v, 1)
		self.w.move(conf.winX.v, conf.winY.v)
		# -------------------------------------------------------------
		self.w.connect("focus-in-event", self.focusIn, "Main")
		self.w.connect("focus-out-event", self.focusOut, "Main")
		self.w.connect("key-press-event", self.onKeyPress)
		self.w.connect("configure-event", self.onConfigureEvent)
		self.connect("toggle-right-panel", self.onToggleRightPanel)
		# -------------------------------------------------------------
		"""
		#self.w.add_events(gdk.EventMask.VISIBILITY_NOTIFY_MASK)
		#self.connect("frame-event", show_event)
		# Compiz does not send configure-event(or any event) when MOVING
		# window(sends in last point,
		# when moving completed)
		#self.connect("drag-motion", show_event)
		ud.rootWindow.set_events(...
		ud.rootWindow.add_filter(self.onRootWinEvent)
		#self.realize()
		#gdk.flush()
		#self.onConfigureEvent(None, None)
		#self.connect("drag-motion", show_event)
		# ----------------------
		# ????????????????????????????????????????????????
		# when button is down(before button-release-event),
		# motion-notify-event does not recived!
		"""
		# ------------------------------------------------------------------
		self.focus = False
		# self.focusOutTime = 0
		# self.clockTr = None
		# ------------------------------------------------------------------
		self.winCon: WinContronllersObj | None = None
		self.mainVBox: MainWinVbox | None = None
		self.rightPanel: MainWinRightPanel | None = None
		self.statusBar: StatusBar | None = None
		# ----
		self.customizeWindow: CustomizeWindow | None = None
		# ------------
		layoutFooter = WinLayoutBox(
			name="footer",
			desc="Footer",  # should not be seen in GUI
			vertical=True,
			expand=False,
			itemsMovable=True,
			itemsParam=conf.mainWinFooterItems,
			buttonSpacing=2,
			items=[
				WinLayoutObj(
					name="statusBar",
					desc=_("Status Bar"),
					enableParam=conf.statusBarEnable,
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=self.createStatusBar,
				),
				WinLayoutObj(
					name="pluginsText",
					desc=_("Plugins Text"),
					enableParam=conf.pluginsTextEnable,
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=self.createPluginsText,
				),
				WinLayoutObj(
					name="eventDayView",
					desc=_("Events of Day"),
					enableParam=conf.eventDayViewEnable,
					vertical=False,
					expand=False,
					movable=True,
					buttonBorder=0,
					initializer=self.createEventDayView,
				),
			],
		)
		layoutFooter.setItemsOrder(conf.mainWinFooterItems)

		def x_large(text: str) -> str:
			return "<span size='x-large'>" + text + "</span>"

		self.layout = WinLayoutBox(
			name="layout",
			desc=_("Main Window"),
			vertical=True,
			expand=True,
			items=[
				WinLayoutObj(
					name="layout_winContronller",
					desc=_("Window Controller"),
					enableParam=conf.winControllerEnable,
					vertical=False,
					expand=False,
					initializer=self.createWindowControllers,
				),
				WinLayoutBox(
					name="middleBox",
					desc="Middle Box",  # should not be seen in GUI
					vertical=False,
					expand=True,
					items=[
						WinLayoutObj(
							name="mainPanel",
							desc=x_large(_("Main Panel")),
							vertical=True,
							expand=True,
							initializer=self.createMainVBox,
						),
						WinLayoutObj(
							name="rightPanel",
							desc=_("Right Panel"),
							enableParam=conf.mainWinRightPanelEnable,
							vertical=True,
							expand=False,
							labelAngle=90 if rtl else -90,
							initializer=self.createRightPanel,
							buttonBorder=int(ui.getFont().size),
						),
					],
				),
				layoutFooter,
			],
		)

		self.appendItem(self.layout)
		self.vbox = self.layout.getWidget()
		self.vbox.show()
		self.w.add(self.vbox)
		# --------------------
		if conf.winMaximized.v:
			self.w.maximize()
		# --------------------
		# ui.prefWindow = None
		self.exportDialog: ExportDialog | None = None
		self.selectDateDialog: SelectDateDialog | None = None
		# ------------- Building About Dialog
		self.aboutDialog: AboutDialog | None = None
		# ---------------
		self.menuMain: gtk.Menu | None = None
		self.menuCell: gtk.Menu | None = None
		# -----
		self.w.set_keep_above(conf.winKeepAbove.v)
		if conf.winSticky.v:
			self.w.stick()
		# ------------------------------------------------------------
		self.statusIconInit()
		listener.dateChange.add(self)
		# ---------
		self.w.connect("delete-event", self.onDeleteEvent)
		# -----------------------------------------
		for plug in core.allPlugList.v:
			if plug is None:
				continue
			if plug.external and hasattr(plug, "set_dialog"):
				plug.set_dialog(self)
		# ---------------------------
		self.onConfigChange()
		# ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))

	# def mainWinStateEvent(self, obj, gevent):
	# log.debug(dir(event))
	# log.debug(gevent.new_window_state)
	# self._event = event

	def createWindowControllers(self) -> CustomizableCalObj:
		from scal3.ui_gtk.winContronller import CalObj as WinContronllersObj

		if self.winCon is not None:
			return self.winCon
		ui.checkWinControllerButtons()
		self.winCon = WinContronllersObj(self)
		return self.winCon

	def createMainVBox(self) -> MainWinVbox:
		if self.mainVBox is not None:
			return self.mainVBox
		ui.checkMainWinItems()
		self.mainVBox = MainWinVbox(self)
		self.mainVBox.createItems()
		self.mainVBox.w.connect("button-press-event", self.onMainButtonPress)
		return self.mainVBox

	def createRightPanel(self) -> CustomizableCalObj:
		from scal3.ui_gtk.right_panel import MainWinRightPanel

		if self.rightPanel is not None:
			return self.rightPanel
		self.rightPanel = MainWinRightPanel()
		self.rightPanel.onConfigChange()
		return self.rightPanel

	def _onToggleRightPanel(self) -> None:
		assert self.rightPanel is not None
		enable = not conf.mainWinRightPanelEnable.v
		conf.mainWinRightPanelEnable.v = enable
		self.rightPanel.enable = enable
		self.rightPanel.showHide()
		self.rightPanel.onDateChange()

		# update Enable checkbutton in Customize dialog
		self.rightPanel.onToggleFromMainWin()

		if conf.mainWinRightPanelResizeOnToggle.v:
			ww, wh = self.w.get_size()
			mw = conf.mainWinRightPanelWidth.v
			if enable:
				ww += mw
			else:
				ww -= mw
			if rtl:
				wx, wy = self.w.get_position()
				wx += mw * (-1 if enable else 1)
				self.w.move(wx, wy)
			self.w.resize(ww, wh)

	def onToggleRightPanel(self, _sig: Any) -> None:
		self.ignoreConfigureEvent = True
		ui.disableRedraw = True
		try:
			self._onToggleRightPanel()
		finally:
			self.ignoreConfigureEvent = False
			ui.disableRedraw = False
			ui.saveConfCustomize()

	def createStatusBar(self) -> CustomizableCalObj:
		from scal3.ui_gtk.statusBar import CalObj as StatusBar

		if self.statusBar is not None:
			return self.statusBar
		self.statusBar = StatusBar(self.w)
		return self.statusBar

	@staticmethod
	def createPluginsText() -> CustomizableCalObj:
		from scal3.ui_gtk.pluginsText import PluginsTextBox

		return PluginsTextBox(insideExpanderParam=conf.pluginsTextInsideExpander)

	@staticmethod
	def createEventDayView() -> CustomizableCalObj:
		from scal3.ui_gtk.event.occurrence_view import LimitedHeightDayOccurrenceView

		return LimitedHeightDayOccurrenceView(eventSepParam=conf.eventDayViewEventSep)

	def selectDateResponse(self, _w: gtk.Widget, y: int, m: int, d: int) -> None:
		ui.cells.changeDate(y, m, d)
		self.onDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		# log.debug(f"{now()}: MainWin.onKeyPress: {kname}")
		if kname == "escape":
			self.onEscape()
		elif kname == "f1":
			self.aboutShow()
		elif kname in {"insert", "plus", "kp_add"}:
			self.eventManShow()
		elif kname in {"q", "arabic_dad"}:  # FIXME
			self.quit()
		elif kname == "r":
			if gevent.state & gdk.ModifierType.CONTROL_MASK:
				log.info("Ctrl + R -> onConfigChange")
				self.onConfigChange()
		else:
			self.layout.onKeyPress(arg, gevent)
		return True  # FIXME

	def focusIn(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
		_data: Any = None,
	) -> None:
		# log.debug("focusIn")
		self.focus = True
		if self.winCon and self.winCon.enable:
			self.winCon.windowFocusIn()

	def focusOut(
		self,
		_widget: gtk.Widget,
		_gevent: gdk.Event,
		_data: Any = None,
	) -> None:
		# called 0.0004 sec (max) after focusIn
		# (if switched between two windows)
		dt = perf_counter() - ui.focusTime
		# log.debug(f"MainWin: focusOut: {ui.focusTime=}, {dt=}")
		if dt > 0.05:  # FIXME
			self.focus = False
			timeout_add(2, self.focusOutDo)

	def focusOutDo(self) -> bool:
		if not self.focus:  # and t-self.focusOutTime>0.002:
			self.w.set_keep_above(conf.winKeepAbove.v)
			if self.winCon and self.winCon.enable:
				self.winCon.windowFocusOut()
		return False

	def toggleMinimized(self, _gevent: gdk.EventButton) -> None:
		if conf.winTaskbar.v:
			self.w.iconify()
			return
		self.w.emit("delete-event", gdk.Event.new(gdk.EventType.DELETE))

	def toggleMaximized(self, _gevent: gdk.EventButton) -> None:
		if conf.winMaximized.v:
			self.w.unmaximize()
		else:
			self.unmaxWinWidth = conf.winWidth.v
			self.w.maximize()
		conf.winMaximized.v = not conf.winMaximized.v
		ui.saveLiveConf()

	def toggleWidthMaximized(self, _gevent: gdk.EventButton) -> None:
		ww = conf.winWidth.v
		workAreaW = ud.workAreaW
		if ww < workAreaW:
			self.unmaxWinWidth = ww
			ww = workAreaW
		elif self.unmaxWinWidth > 0:
			ww = self.unmaxWinWidth
		else:
			return
		conf.winWidth.v = ww
		self.w.resize(ww, conf.winHeight.v)

	def screenSizeChanged(self, rect: gdk.Rectangle) -> None:
		if conf.winMaximized.v:
			return
		winWidth = min(conf.winWidth.v, rect.width)
		winHeight = min(conf.winHeight.v, rect.height)
		winX = min(conf.winX.v, rect.width - conf.winWidth.v)
		winY = min(conf.winY.v, rect.height - conf.winHeight.v)

		if (winWidth, winHeight) != (conf.winWidth.v, conf.winHeight.v):
			self.w.resize(winWidth, winHeight)

		if (winX, winY) != (conf.winX.v, conf.winY.v):
			self.w.move(winX, winY)

	def onConfigureEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> bool | None:
		if self.ignoreConfigureEvent:
			return None
		wx, wy = self.w.get_position()
		# maxPosDelta = max(
		# 	abs(conf.winX.v - wx),
		# 	abs(conf.winY.v - wy),
		# )
		# log.debug(wx, wy)
		ww, wh = self.w.get_size()
		if self.w.get_property("visible"):
			conf.winX.v, conf.winY.v = (wx, wy)
		if not conf.winMaximized.v:
			conf.winWidth.v = ww
			conf.winHeight.v = wh
		self.onWindowSizeChange()
		liveConfChanged()
		return False

	def onWindowSizeChange(self) -> None:
		if self.rightPanel:
			self.rightPanel.onWindowSizeChange()

	def onMainButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		# only for mainVBox for now, not rightPanel
		# does not work for statusBar, don't know why
		# log.debug(f"MainWin: onMainButtonPress, {gevent.button=}")
		b = gevent.button
		if b == 3:
			menuMain = self.menuMainCreate()
			menuMain.popup(None, None, None, None, 3, gevent.time)
		elif b == 1:
			# FIXME: used to cause problems with `ConButton`
			# when using 'pressed' and 'released' signals
			self.w.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
		ui.updateFocusTime()
		return False

	def childButtonPress(
		self,
		widget: gtk.Widget,  # noqa: ARG002
		gevent: gdk.EventButton,
	) -> bool:
		b = gevent.button
		# log.debug(dir(gevent))
		# foo, x, y, mask = gevent.get_window().get_pointer()
		# x, y = self.w.get_pointer()
		x, y = int(gevent.x_root), int(gevent.y_root)
		result = False
		if b == 1:
			self.w.begin_move_drag(gevent.button, x, y, gevent.time)
			result = True
		elif b == 3:
			menuMain = self.menuMainCreate()
			if rtl:
				x -= get_menu_width(menuMain)
			menuMain.popup(
				None,
				None,
				lambda *_args: (x, y, True),
				None,
				3,
				gevent.time,
			)
			result = True
		ui.updateFocusTime()
		return result

	def begin_resize_drag(self, *args) -> None:
		conf.winMaximized.v = False
		ui.updateFocusTime()
		self.w.begin_resize_drag(*args)

	def onResizeFromMenu(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
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

	def changeDate(self, year: int, month: int, day: int) -> None:
		ui.cells.changeDate(year, month, day)
		self.onDateChange()

	def goToday(self, _w: gtk.Widget | None = None) -> None:
		self.changeDate(*cal_types.getSysDate(calTypes.primary))

	def onDateChange(self, *a, **kw) -> None:
		plugIndex = core.plugIndex.v
		allPlugList = core.allPlugList.v
		# log.debug("MainWin.onDateChange")
		super().onDateChange(*a, **kw)
		for idx in plugIndex:
			plug = allPlugList[idx]
			if plug is None:
				continue
			if hasattr(plug, "date_change_after"):
				plug.date_change_after(*ui.cells.current.date)
		# log.debug(
		# 	f"Occurrence Time: max={ui.Cell.ocTimeMax:e}, " +
		# 	f"avg={ui.Cell.ocTimeSum/ui.Cell.ocTimeCount:e}"
		# )

	def _getEventAddToMenuItem(self, menu2: gtk.Menu, group: EventGroupType) -> None:
		from scal3.ui_gtk.drawing import newColorCheckPixbuf

		if not group.enable:
			return
		if not group.showInCal():  # FIXME
			return
		eventTypes = group.acceptsEventTypes
		if not eventTypes:
			return
		item2_kwargs: dict[str, Any] = {}
		if group.icon:
			item2_kwargs["imageName"] = group.icon
		else:
			item2_kwargs["pixbuf"] = newColorCheckPixbuf(
				group.color.rgb(),
				20,
				True,
			)

		def addToGroupFromMenu(eventType: str) -> Callable[[gtk.Widget], None]:
			def func(w: gtk.Widget) -> None:
				self.addToGroupFromMenu(w, group, eventType)

			return func

		# --
		if len(eventTypes) == 1:
			menu2.add(
				ImageMenuItem(
					group.title,
					func=addToGroupFromMenu(eventTypes[0]),
					**item2_kwargs,
				),
			)
		else:
			menu3 = Menu()
			for eventType in eventTypes:
				eventClass = event_lib.classes.event.byName[eventType]
				menu3.add(
					ImageMenuItem(
						eventClass.desc,
						imageName=eventClass.getDefaultIcon(),
						func=addToGroupFromMenu(eventType),
					),
				)
			menu3.show_all()
			item2 = ImageMenuItem(
				group.title,
				**item2_kwargs,  # type: ignore[arg-type]
			)
			item2.set_submenu(menu3)
			menu2.add(item2)

	def getEventAddToMenuItem(self) -> gtk.MenuItem | None:
		if ev.allReadOnly:
			return None
		menu2 = Menu()
		# --
		for group in ev.groups:
			self._getEventAddToMenuItem(menu2, group)
		# --
		if not menu2.get_children():
			return None
		menu2.show_all()
		addToItem = ImageMenuItem(
			label=_("_Add Event to"),
			imageName="list-add.svg",
		)
		addToItem.set_submenu(menu2)
		return addToItem

	def editEventFromMenu(self, _item: gtk.Widget, groupId: int, eventId: int) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		event = ui.getEvent(groupId, eventId)
		eventNew = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self.w,
		).run()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.onConfigChange()

	@staticmethod
	def trimMenuItemLabel(s: str, maxLen: int) -> str:
		if len(s) > maxLen - 3:
			s = s[: maxLen - 3].rstrip(" ") + "..."
		return s

	def addEditEventCellMenuItems(self, menu: gtk.Menu) -> None:
		if ev.allReadOnly:
			return
		eventsData = ui.cells.current.getEventsData()
		if not eventsData:
			return

		def editEvent(groupId: int, eventId: int) -> Callable[[gtk.Widget], None]:
			def func(w: gtk.Widget) -> None:
				self.editEventFromMenu(w, groupId, eventId)

			return func

		if len(eventsData) < 4:  # TODO: make it customizable
			for eData in eventsData:
				groupId, eventId = eData.ids
				menu.add(
					ImageMenuItem(
						label=_("Edit")
						+ ": "
						+ self.trimMenuItemLabel(eData.text[0], 25),
						imageName=eData.icon,
						func=editEvent(groupId, eventId),
					),
				)
			return

		subMenu = Menu()
		subMenuItem = ImageMenuItem(
			label=_("_Edit Event"),
			imageName="list-add.svg",
		)
		for eData in eventsData:
			groupId, eventId = eData.ids
			subMenu.add(
				ImageMenuItem(
					eData.text[0],
					imageName=eData.icon,
					func=editEvent(groupId, eventId),
				),
			)
		subMenu.show_all()
		subMenuItem.set_submenu(subMenu)
		menu.add(subMenuItem)

	def menuCellPopup(
		self,
		widget: gtk.Widget,
		x: int,
		y: int,
		calObjName: str,
	) -> None:
		# calObjName is in ("weekCal", "monthCal", ...)
		menu = Menu()
		# ----
		for calType in calTypes.active:
			calTypeDesc = calTypes.getDesc(calType)
			assert calTypeDesc
			menu.add(
				ImageMenuItem(
					label=_("Copy {calType} Date").format(
						calType=_(calTypeDesc, ctx="calendar"),
					),
					imageName="edit-copy.svg",
					func=self.copyDateGetCallback(calType),
				),
			)
		menu.add(
			ImageMenuItem(
				label=_("Day Info"),
				imageName="info.svg",
				func=self.dayInfoShowFromMenu,
			),
		)
		addToItem = self.getEventAddToMenuItem()
		if addToItem is not None:
			menu.add(addToItem)
		self.addEditEventCellMenuItems(menu)
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			ImageMenuItem(
				label=_("Select _Today"),
				imageName="go-home.svg",
				func=self.goToday,
			),
		)
		menu.add(
			ImageMenuItem(
				label=_("Select _Date..."),
				imageName="select-date.svg",
				func=self.selectDateShow,
			),
		)
		if calObjName in {"weekCal", "monthCal"}:
			isWeek = calObjName == "weekCal"
			calDesc = "Month Calendar" if isWeek else "Week Calendar"
			menu.add(
				ImageMenuItem(
					label=_("Switch to " + calDesc),
					imageName="" if isWeek else "week-calendar.svg",
					func=self.switchWcalMcal,
				),
			)
		menu.add(
			ImageMenuItem(
				label=_("In Time Line"),
				imageName="timeline.svg",
				func=self.timeLineShowSelectedDay,
			),
		)
		if os.path.isfile("/usr/bin/evolution"):  # FIXME
			menu.add(
				ImageMenuItem(
					label=_("In E_volution"),
					imageName="evolution.png",
					func=ui.cells.current.dayOpenEvolution,
				),
			)
		# ----
		moreMenu = Menu()
		moreMenu.add(
			ImageMenuItem(
				label=_("_Customize"),
				imageName="document-edit.svg",
				func=self.customizeShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				func=self.prefShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				func=self.eventManShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				func=self.yearWheelShow,
			),
		)  # icon? FIXME
		moreMenu.add(
			ImageMenuItem(
				label=_("Day Calendar (Desktop Widget)"),
				imageName="starcal.svg",
				func=self.dayCalWinShow,
			),
		)
		# moreMenu.add(ImageMenuItem(
		# 	"Week Calendar",
		# 	imageName="week-calendar.svg",
		# 	func=self.weekCalShow,
		# ))
		moreMenu.add(
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				func=self.onExportClick,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				func=self.aboutShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				func=self.quit,
			),
		)
		# --
		moreMenu.show_all()
		moreItem = ImageMenuItem(label=_("More"))
		moreItem.set_submenu(moreMenu)
		# moreItem.show_all()
		menu.add(moreItem)
		# ----
		menu.show_all()
		coord = widget.translate_coordinates(self.w, x, y)
		if coord is None:
			raise RuntimeError(
				f"failed to translate coordinates ({x}, {y}) from widget {widget}",
			)
		dx, dy = coord
		win = self.w.get_window()
		assert win is not None
		_foo, wx, wy = win.get_origin()
		x = wx + dx
		y = wy + dy
		if rtl:
			x -= get_menu_width(menu)
		# ----
		etime = gtk.get_current_event_time()
		# log.debug("menuCellPopup", x, y, etime)
		self.menuCell = menu
		# without the above line, the menu is not showing up
		# some GC-related pygi bug probably
		menu.popup(
			None,
			None,
			lambda *_args: (x, y, True),
			None,
			3,
			etime,
		)
		ui.updateFocusTime()

	# TODO: customize list of main menu items (disable/enable/re-order)
	def menuMainCreate(self) -> gtk.Menu:
		if self.menuMain:
			return self.menuMain
		menu = gtk.Menu(reserve_toggle_size=False)
		# ----
		for propsTmp in menuMainItemDefs.values():
			props = dict(propsTmp)  # make a copy before modify
			cls = getattr(menuitems, props.pop("cls"))
			props["func"] = getattr(self, props["func"])
			if "active" in props:
				props["active"] = getattr(conf, props["active"])
			menu.add(cls(**props))
		# -------
		menu.show_all()
		self.menuMain = menu
		return menu

	# handler for "popup-main-menu" signal
	def menuMainPopup(
		self,
		widget: gtk.Widget,
		x: int,
		y: int,
	) -> None:
		menu = self.menuMainCreate()
		dcoord = widget.translate_coordinates(self.w, x, y)
		assert dcoord is not None
		dx, dy = dcoord
		win = self.w.get_window()
		assert win is not None
		_foo, wx, wy = win.get_origin()
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
		etime = gtk.get_current_event_time()
		# log.debug("menuMainPopup", x, y, etime)
		menu.popup(
			None,
			None,
			lambda *_args: (x, y, True),
			None,
			3,
			etime,
		)
		ui.updateFocusTime()

	def addToGroupFromMenu(
		self,
		_menu: gtk.Widget,
		group: EventGroupType,
		eventType: str,
	) -> None:
		from scal3.ui_gtk.event.editor import addNewEvent

		# log.debug("addToGroupFromMenu", group.title, eventType)
		eventTypeDesc = event_lib.classes.event.byName[eventType].desc
		title = _("Add {eventType}").format(eventType=eventTypeDesc)
		event = addNewEvent(
			group,
			eventType,
			useSelectedDate=True,
			title=title,
			transient_for=self.w,
		)
		if event is None:
			return
		if event.parent is None:
			raise RuntimeError("event.parent is None")
		ui.eventUpdateQueue.put("+", event, self)
		self.onConfigChange()

	@staticmethod
	def prefUpdateBgColor(_cal: CustomizableCalObj) -> None:
		if ui.prefWindow:
			ui.prefWindow.colorbBg.setRGBA(conf.bgColor.v)
		# else:  # FIXME
		ui.saveLiveConf()

	def onKeepAboveClick(self, check: CheckMenuItem) -> None:
		print(check)
		act = check.get_active()
		self.w.set_keep_above(act)
		conf.winKeepAbove.v = act
		ui.saveLiveConf()

	def onStickyClick(self, check: CheckMenuItem) -> None:
		if check.get_active():
			self.w.stick()
			conf.winSticky.v = True
		else:
			self.w.unstick()
			conf.winSticky.v = False
		ui.saveLiveConf()

	@staticmethod
	def copyDate(calType: int) -> None:
		assert ud.dateFormatBin is not None
		setClipboard(ui.cells.current.format(ud.dateFormatBin, calType=calType))

	@staticmethod
	def copyDateGetCallback(
		calType: int,
	) -> Callable[[gtk.Widget], None]:
		def callback(
			_widget: gtk.Widget,
		) -> None:
			assert ud.dateFormatBin is not None
			setClipboard(
				ui.cells.current.format(
					ud.dateFormatBin,
					calType=calType,
				),
			)

		return callback

	@staticmethod
	def copyCurrentDate(
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		assert ud.dateFormatBin is not None
		setClipboard(ui.cells.today.format(ud.dateFormatBin))

	@staticmethod
	def copyCurrentDateTime(
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		assert ud.dateFormatBin is not None
		assert ud.clockFormatBin is not None
		dateStr = ui.cells.today.format(ud.dateFormatBin)
		timeStr = ui.cells.today.format(
			ud.clockFormatBin,
			tm=localtime()[3:6],
		)
		setClipboard(f"{dateStr}, {timeStr}")

	"""
	def updateToolbarClock(self):
		if conf.showDigClockTb.v:
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
		if conf.showDigClockTr.v:
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

	# def weekCalShow(self, _w: gtk.Widget | None = None, data: Any = None):
	# 	openWindow(ui.weekCalWin.w)

	@staticmethod
	def useAppIndicator() -> bool:
		if not conf.useAppIndicator.v:
			return False
		try:
			import scal3.ui_gtk.starcal_appindicator  # noqa: F401
		except (ImportError, ValueError):
			return False
		return True

	def statusIconInit(self) -> None:
		self.sicon: gtk.StatusIcon | IndicatorStatusIconWrapper | None
		if self.statusIconMode != 2:
			self.sicon = None
			return

		if self.useAppIndicator():
			from scal3.ui_gtk.starcal_appindicator import (
				IndicatorStatusIconWrapper,
			)

			self.sicon = IndicatorStatusIconWrapper(self)
			return

		sicon = gtk.StatusIcon()
		self.sicon = sicon
		sicon.set_title(core.APP_DESC)
		sicon.set_visible(True)  # is needed?
		sicon.connect(
			"button-press-event",
			self.onStatusIconPress,
		)
		sicon.connect("activate", self.onStatusIconClick)
		sicon.connect("popup-menu", self.statusIconPopup)

	def getMainWinMenuItem(self) -> gtk.MenuItem:
		item = gtk.MenuItem(label=_("Main Window"))
		item.connect("activate", self.onStatusIconClick)
		return item

	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]:
		return [
			ImageMenuItem(
				label=_("Copy Date and _Time"),
				imageName="edit-copy.svg",
				func=self.copyCurrentDateTime,
			),
			ImageMenuItem(
				label=_("Copy _Date"),
				imageName="edit-copy.svg",
				func=self.copyCurrentDate,
			),
			ImageMenuItem(
				label=_("Ad_just System Time"),
				imageName="preferences-system.svg",
				func=self.adjustTime,
			),
			# ImageMenuItem(
			# 	label=_("_Add Event"),
			# 	imageName="list-add.svg",
			# 	func=ui.addCustomEvent,
			# ),  # FIXME
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				func=self.onExportClickStatusIcon,
			),
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				func=self.prefShow,
			),
			ImageMenuItem(
				label=_("_Customize"),
				imageName="document-edit.svg",
				func=self.customizeShow,
			),
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				func=self.eventManShow,
			),
			ImageMenuItem(
				label=_("Time Line"),
				imageName="timeline.svg",
				func=self.timeLineShow,
			),
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				func=self.yearWheelShow,
			),
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				func=self.aboutShow,
			),
			gtk.SeparatorMenuItem(),
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				func=self.quit,
			),
		]

	def statusIconPopup(self, sicon: gtk.StatusIcon, button: int, etime: int) -> None:
		assert isinstance(self.sicon, gtk.StatusIcon)
		menu = Menu()
		if os.sep == "\\":
			from scal3.ui_gtk.windows import setupMenuHideOnLeave

			setupMenuHideOnLeave(menu)
		items = self.getStatusIconPopupItems()
		# items.insert(0, self.getMainWinMenuItem())-- FIXME
		get_pos_func = None
		y1 = 0
		geo = sicon.get_geometry()
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
		try:  # new gi versions
			y = gtk.StatusIcon.position_menu(menu, 0, 0, self.sicon)[1]  # type: ignore
		except TypeError:  # old gi versions
			y = gtk.StatusIcon.position_menu(menu, self.sicon)[1]
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

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:
		self.statusIconUpdate(gdate=gdate)

	@staticmethod
	def getStatusIconTooltip() -> str:
		# tt = core.weekDayName[core.getWeekDay(*ddate)]
		tt = core.weekDayName[core.jwday(ui.cells.today.jd)]
		# if conf.pluginsTextStatusIcon.v:--?????????
		# 	sep = _(",")+" "
		# else:
		sep = "\n"
		for calType in calTypes.active:
			y, m, d = ui.cells.today.dates[calType]
			tt += sep + _(d) + " " + locale_man.getMonthName(calType, m, y) + " " + _(y)
		if conf.pluginsTextStatusIcon.v:
			text = ui.cells.today.getPluginsText()
			if text:
				tt += "\n\n" + text  # .replace("\t", "\n") # FIXME
		for item in ui.cells.today.getEventsData():
			if not item.showInStatusIcon:
				continue
			itemS = ""
			if item.time:
				itemS += item.time + " - "
			itemS += item.text[0]
			tt += "\n\n" + itemS
		return tt

	def statusIconUpdateIcon(self, ddate: tuple[int, int, int]) -> None:  # FIXME
		from scal3.utils import toBytes

		assert self.sicon is not None

		imagePath = (
			conf.statusIconImageHoli.v
			if ui.cells.today.holiday
			else conf.statusIconImage.v
		)
		ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
		with open(imagePath, "rb") as fp:
			data = fp.read()
		if ext == "svg":
			if conf.statusIconLocalizeNumber.v:
				dayNum = locale_man.numEncode(
					ddate[2],
					localeMode="calendar",
				)
			else:
				dayNum = str(ddate[2])
			style: list[tuple[str, Any]] = []
			if conf.statusIconFontFamilyEnable.v:
				family = conf.statusIconFontFamily.v or ui.getFont().family
				style.append(("font-family", family))
			if (
				conf.statusIconHolidayFontColorEnable.v
				and conf.statusIconHolidayFontColor.v
				and ui.cells.today.holiday
			):
				style.append(
					("fill", rgbToHtmlColor(conf.statusIconHolidayFontColor.v)),
				)
			if style:
				styleStr = "".join([f"{key}:{value};" for key, value in style])
				dayNum = f'<tspan style="{styleStr}">{dayNum}</tspan>'
			data = data.replace(
				b"TX",
				toBytes(dayNum),
			)
		loader = GdkPixbuf.PixbufLoader.new_with_type(ext)
		if conf.statusIconFixedSizeEnable.v:
			try:
				width, height = conf.statusIconFixedSizeWH.v
				loader.set_size(width, height)
			except Exception:
				log.exception("")
		try:
			loader.write(data)
		finally:
			loader.close()
		pixbuf = loader.get_pixbuf()
		assert pixbuf is not None

		# alternative way:
		# stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
		# pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)

		self.sicon.set_from_pixbuf(pixbuf)

	def statusIconUpdateTooltip(self) -> None:
		try:
			sicon = self.sicon
		except AttributeError:
			return
		if sicon is None:
			return
		# assert isinstance(sicon, gtk.StatusIcon)
		sicon.set_tooltip_text(self.getStatusIconTooltip())

	def statusIconUpdate(
		self,
		gdate: tuple[int, int, int] | None = None,
		checkStatusIconMode: bool = True,
	) -> None:
		if checkStatusIconMode and self.statusIconMode < 1:
			return
		if gdate is None:
			gdate = localtime()[:3]
		if calTypes.primary == core.GREGORIAN:
			ddate = gdate
		else:
			ddate = convert(
				gdate[0],
				gdate[1],
				gdate[2],
				core.GREGORIAN,
				calTypes.primary,
			)
		# -------
		assert self.sicon is not None
		self.sicon.set_from_file(join(pixDir, "starcal-24.png"))
		self.statusIconUpdateIcon(ddate)
		# -------
		self.statusIconUpdateTooltip()

	def onStatusIconPress(self, _obj: gtk.Widget, gevent: gdk.Event) -> bool | None:
		if gevent.button == 2:
			# middle button press
			self.copyDate(calTypes.primary)
			return True
		return None

	def onStatusIconClick(self, _w: gtk.Widget | None = None) -> None:
		if self.w.get_property("visible"):
			# conf.winX.v, conf.winY.v = self.w.get_position()
			# FIXME: ^ gives bad position sometimes
			# liveConfChanged()
			# log.debug(conf.winX.v, conf.winY.v)
			self.hide()
		else:
			self.w.move(conf.winX.v, conf.winY.v)
			# every calling of .hide() and .present(), makes dialog not on top
			# (forgets being on top)
			self.w.set_keep_above(conf.winKeepAbove.v)
			if conf.winSticky.v:
				self.w.stick()
			self.w.deiconify()
			self.w.present()
			self.focusIn()
			# in LXDE, the window was not focused without self.focusIn()
			# while worked in Xfce and GNOME.

	def onDeleteEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		# conf.winX.v, conf.winY.v = self.w.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(conf.winX.v, conf.winY.v)
		if self.statusIconMode == 0 or not self.sicon:
			self.quit()
		elif self.statusIconMode > 1:
			if self.sicon.is_embedded() or (ui.dayCalWin and ui.dayCalWin.is_visible()):
				self.hide()
			else:
				self.quit()
		return True

	def onEscape(self) -> None:
		# conf.winX.v, conf.winY.v = self.w.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(conf.winX.v, conf.winY.v)
		if self.statusIconMode == 0:
			self.quit()
		elif self.statusIconMode > 1:  # noqa: SIM102
			assert self.sicon is not None
			if self.sicon.is_embedded():
				self.hide()

	# Callable[[int, FrameType | None], Any] | int | Handlers | None
	def quitOnSignal(self, _sig: int, _frame: FrameType | None) -> None:
		self.quit()

	def quit(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		try:
			ui.saveLiveConf()
		except Exception:
			log.exception("")
		if self.statusIconMode > 1 and self.sicon:
			self.sicon.set_visible(False)
			# ^ needed for windows. before or after main_quit ?
		# ------
		t0 = perf_counter()
		core.stopRunningThreads()
		t1 = perf_counter()
		pixcache.cacheSaveStop()
		t2 = perf_counter()
		ui.eventUpdateQueue.stopLoop()
		t3 = perf_counter()
		log.info(f"stopRunningThreads took {t1 - t0:.6f} seconds")
		log.info(f"cacheSaveStop took {t2 - t1:.6f} seconds")
		log.info(f"eventUpdateQueue.stopLoop took {t3 - t2:.6f} seconds")
		# ------
		try:
			self.w.destroy()
		except Exception:
			log.exception("error in destroy")
		# ------
		return gtk.main_quit()

	def adjustTime(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		from subprocess import Popen

		if not ud.adjustTimeCmd:
			showError(
				"Failed to find gksudo, kdesudo, gksu, gnomesu, kdesu"
				" or any askpass program to use with sudo",
				transient_for=self.w,
			)
			return
		Popen(ud.adjustTimeCmd, env=ud.adjustTimeEnv)

	def aboutShow(self, _w: gtk.Widget | None = None, _data: Any = None) -> None:
		if not self.aboutDialog:
			from scal3.ui_gtk.about import AboutDialog

			logoSize = int(ud.screenH * 0.15)
			with open(
				join(sourceDir, "authors-dialog"),
				encoding="utf-8",
			) as authorsFile:
				authors = authorsFile.read().splitlines()
			dialog = AboutDialog(
				name=core.APP_DESC,
				version=core.VERSION,
				title=_("About ") + core.APP_DESC,
				authors=[_(author) for author in authors],
				comments=core.aboutText,
				license=core.licenseText,
				website=core.homePage,
				logo=GdkPixbuf.Pixbuf.new_from_file_at_size(
					ui.appLogo,
					logoSize,
					logoSize,
				),
				transient_for=self.w,
			)
			# add Donate button, FIXME
			dialog.connect("delete-event", self.aboutHide)
			dialog.connect("response", self.aboutHide)
			# dialog.set_skip_taskbar_hint(True)
			self.aboutDialog = dialog
		openWindow(self.aboutDialog)

	def aboutHide(self, _w: gtk.Widget, _gevent: gdk.Event | None = None) -> bool:
		# arg maybe an event, or response id
		assert self.aboutDialog is not None
		self.aboutDialog.hide()
		return True

	def prefShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		if not ui.prefWindow:
			from scal3.ui_gtk.preferences import PreferencesWindow

			ui.prefWindow = PreferencesWindow(transient_for=self.w)
			ui.prefWindow.updatePrefGui()
		if self.customizeWindow and self.customizeWindow.is_visible():
			log.warning("customize window is open")
		openWindow(ui.prefWindow)

	def eventManCreate(self) -> None:
		checkEventsReadOnly()  # FIXME
		if ui.eventManDialog is None:
			from scal3.ui_gtk.event.manager import EventManagerDialog

			ui.eventManDialog = EventManagerDialog(transient_for=self.w)

	def eventManShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		self.eventManCreate()
		openWindow(ui.eventManDialog.w)

	@staticmethod
	def eventSearchCreate() -> None:
		if ui.eventSearchWin is None:
			from scal3.ui_gtk.event.search_events import EventSearchWindow

			ui.eventSearchWin = EventSearchWindow()

	def eventSearchShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		self.eventSearchCreate()
		openWindow(ui.eventSearchWin)

	def addCustomEvent(self, _w: gtk.Widget | None = None) -> None:
		self.eventManCreate()
		ui.eventManDialog.addCustomEvent()

	@staticmethod
	def dayCalWinShow(
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		if not ui.dayCalWin:
			from scal3.ui_gtk.day_cal_window import DayCalWindow

			ui.dayCalWin = DayCalWindow()
		ui.dayCalWin.w.present()

	@staticmethod
	def timeLineShow(
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		if not ui.timeLineWin:
			from scal3.ui_gtk.timeline import TimeLineWindow

			ui.timeLineWin = TimeLineWindow()
		openWindow(ui.timeLineWin.w)

	@staticmethod
	def timeLineShowSelectedDay(
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		if not ui.timeLineWin:
			from scal3.ui_gtk.timeline import TimeLineWindow

			ui.timeLineWin = TimeLineWindow()
		ui.timeLineWin.showDayInWeek(ui.cells.current.jd)
		openWindow(ui.timeLineWin.w)

	@staticmethod
	def yearWheelShow(
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		if not ui.yearWheelWin:
			from scal3.ui_gtk.year_wheel import YearWheelWindow

			ui.yearWheelWin = YearWheelWindow()
		openWindow(ui.yearWheelWin.w)

	def selectDateShow(self, _w: gtk.Widget | None = None) -> None:
		if not self.selectDateDialog:
			from scal3.ui_gtk.selectdate import SelectDateDialog

			self.selectDateDialog = SelectDateDialog(transient_for=self.w)
			self.selectDateDialog.connect(
				"response-date",
				self.selectDateResponse,
			)
		self.selectDateDialog.show()

	def dayInfoShow(self, _w: gtk.Widget | None = None) -> None:
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog

			self.dayInfoDialog = DayInfoDialog(transient_for=self.w)
			self.emit("date-change")
		openWindow(self.dayInfoDialog.w)

	def dayInfoShowFromMenu(self, _w: gtk.Widget) -> None:
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog

			self.dayInfoDialog = DayInfoDialog(transient_for=self.w)
			self.emit("date-change")
		openWindow(self.dayInfoDialog.w)

	def customizeWindowCreate(self) -> CustomizeWindow:
		if not self.customizeWindow:
			from scal3.ui_gtk.customize_dialog import CustomizeWindow

			self.customizeWindow = customizeWindow = CustomizeWindow(
				self.layout,
				transient_for=self.w,
			)
			return customizeWindow

		return self.customizeWindow

	def switchWcalMcal(self, _w: gtk.Widget | None = None) -> None:
		assert self.mainVBox is not None
		customizeWindow = self.customizeWindowCreate()
		self.mainVBox.switchWcalMcal(customizeWindow)
		customizeWindow.updateMainPanelTreeEnableChecks()
		customizeWindow.save()

	def customizeShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		customizeWindow = self.customizeWindowCreate()
		openWindow(customizeWindow)

	def exportShow(self, year: int, month: int) -> None:
		if not self.exportDialog:
			from scal3.ui_gtk.export import ExportDialog

			self.exportDialog = ExportDialog(transient_for=self.w)
		self.exportDialog.showDialog(year, month)

	def onExportClick(self, _w: gtk.Widget | None = None) -> None:
		self.exportShow(ui.cells.current.year, ui.cells.current.month)

	def onExportClickStatusIcon(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		year, month, _day = cal_types.getSysDate(calTypes.primary)
		self.exportShow(year, month)

	def onConfigChange(self, *a, **kw) -> None:
		if self.menuMain:
			self.menuMain.destroy()
			self.menuMain = None
		if self.menuCell:
			self.menuCell.destroy()
			self.menuCell = None
		super().onConfigChange(*a, **kw)
		self.autoResize()
		# self.w.set_property("skip-taskbar-hint", not conf.winTaskbar.v)
		# self.w.set_skip_taskbar_hint  # FIXME
		# skip-taskbar-hint need to restart ro be applied
		# self.updateToolbarClock()  # FIXME
		# self.updateStatusIconClock()
		self.statusIconUpdate()


# -------------------------------------------------------------------------3


# core.COMMAND = sys.argv[0] # OR __file__ # ????????


gtk.init_check(sys.argv)  # type: ignore[call-arg]

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


for plug in core.allPlugList.v:
	if plug is None:
		continue
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


def main() -> None:
	statusIconMode = 2
	action = ""
	if conf.showMain.v:
		action = "show"
	if len(sys.argv) > 1:
		if sys.argv[1] in {"--no-tray-icon", "--no-status-icon"}:
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
	# -------------------------------
	ui.init()
	initCell()
	# -------------------------------
	pixcache.cacheSaveStart()
	ui.eventUpdateQueue.startLoop()
	# -------------------------------
	listener.dateChange.add(hijri_gtk.HijriMonthsExpirationListener())
	hijri_gtk.checkHijriMonthsExpiration()
	# -------------------------------
	checkEventsReadOnly(False)
	# FIXME: right place?
	ev.info.updateAndSave()
	# -------------------------------
	mainWin = MainWin(statusIconMode=statusIconMode)
	if TYPE_CHECKING:
		_mainWin: CalObjType = mainWin
	if os.getenv("STARCAL_FULL_IMPORT"):
		doFullImport(mainWin)
	# -------------------------------
	# if action == "html":
	# 	mainWin.exportHtml("calendar.html") # exportHtml(path, months, title)
	# 	sys.exit(0)
	# elif action == "svg":
	# 	mainWin.export.exportSvg(f"{core.deskDir}/2010-01.svg", [(2010, 1)])
	# 	sys.exit(0)
	if action == "show" or not mainWin.sicon:
		mainWin.w.present()
	if conf.showDesktopWidget.v:
		mainWin.dayCalWinShow()
	# ud.rootWindow.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
	# FIXME: ^
	# mainWin.app.run(None)
	signal.signal(signal.SIGINT, mainWin.quitOnSignal)
	gtk.main()


if __name__ == "__main__":
	main()
