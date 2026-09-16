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

from os.path import join
from time import perf_counter
from typing import TYPE_CHECKING, ClassVar

from scal3 import logger

log = logger.get()

from gi.repository import Gio as gio

from scal3 import cal_types, core, ui
from scal3.app_info import APP_DESC, homePage
from scal3.cal_types import calTypes
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.path import sourceDir
from scal3.ui import conf
from scal3.ui_gtk import (
	GdkPixbuf,
	connect_dialog_response,
	gdk,
	gtk,
	listener,
	pixcache,
	quit_application,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.mainwin_menu import MainWinMenu
from scal3.ui_gtk.mainwin_status_icon import MainWinStatusIcon
from scal3.ui_gtk.starcal_classes import MainWinEventMan, MainWinVbox, SignalHandler
from scal3.ui_gtk.starcal_funcs import (
	childButtonPress,
	liveConfChanged,
	onMainButtonPress,
	onScreenSizeChange,
	onToggleRightPanel,
)
from scal3.ui_gtk.starcal_layout import makeMainWinLayout
from scal3.ui_gtk.utils import openWindow, showError

if TYPE_CHECKING:
	from types import FrameType
	from typing import Any

	from scal3.ui_gtk.about import AboutDialog
	from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
	from scal3.ui_gtk.customize_dialog import CustomizeWindow
	from scal3.ui_gtk.day_info import DayInfoDialog
	from scal3.ui_gtk.export import ExportDialog
	from scal3.ui_gtk.layout import WinLayoutBox
	from scal3.ui_gtk.pytypes import CustomizableCalObjType
	from scal3.ui_gtk.right_panel import MainWinRightPanel
	from scal3.ui_gtk.selectdate import SelectDateDialog
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_types import OptEvent, OptWidget
	from scal3.ui_gtk.statusBar import CalObj as StatusBar
	from scal3.ui_gtk.winContronller import CalObj as WinContronllersObj

__all__ = ["MainWin"]


class MainWin(CalObjWidget):
	objName = "mainWin"
	desc = _("Main Window")
	Sig: ClassVar[type[SignalHandlerType]] = SignalHandler
	timeout = 1  # second
	statusIconMode: int

	def autoResize(self) -> None:
		self.win.resize(conf.winWidth.v, conf.winHeight.v)

	# def maximize(self):
	# 	pass

	def __init__(self, statusIconMode: int = 2) -> None:
		super().__init__()
		appId = "apps.starcal"
		# if this application_id is already running, Gtk will crash
		# with Segmentation fault
		if ev.allReadOnly:
			appId += str(int(perf_counter() * 10**9))
		self.app = gtk.Application(application_id=appId)
		self.app.register(gio.Cancellable.new())
		self.win = win = gtk.ApplicationWindow(application=self.app)
		self.w: gtk.Widget = self.win
		# ---
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		ud.windowList.appendItem(self)
		ui.mainWin = self
		# ------------------
		self.eventManInternal = MainWinEventMan(self.win)
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
		#   3: xfce panel applet
		self.statusIconMode = statusIconMode
		# ---
		# ui.eventManDialog = None
		# ui.timeLineWin = None
		# ui.yearWheelWin = None
		# ---
		# ---
		self.dayInfoDialog: DayInfoDialog | None = None
		# log.debug("windowList.items", [item.objName for item in ud.windowList.items])
		# -----------
		# self.connect("window-state-event", selfStateEvent)
		win.set_title(f"{APP_DESC} {core.VERSION}")
		# self.connect("main-show", lambda arg: self.present())
		# self.connect("main-hide", lambda arg: self.hide())
		win.set_decorated(False)
		win.set_skip_taskbar_hint(not conf.winTaskbar.v)
		win.set_role("starcal")
		# self.w.set_focus_on_map(True)#????????
		# self.w.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# self.w.connect("realize", self.onRealize)
		win.set_default_size(conf.winWidth.v, 1)
		win.move(conf.winX.v, conf.winY.v)
		# -------------------------------------------------------------
		win.connect("focus-in-event", self.onFocusIn)
		win.connect("focus-out-event", self.onFocusOut)
		win.connect("key-press-event", self.onKeyPress)
		win.connect("configure-event", self.onConfigureEvent)
		self.s.connect("toggle-right-panel", self.onToggleRightPanel)
		# -------------------------------------------------------------
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
		self.layout = self.makeLayout()
		self.appendItem(self.layout)
		self.vbox = self.layout.getWidget()
		self.vbox.show()
		win.add(self.vbox)
		# --------------------
		if conf.winMaximized.v:
			win.maximize()
		# --------------------
		# ui.prefWindow = None
		self.exportDialog: ExportDialog | None = None
		self.selectDateDialog: SelectDateDialog | None = None
		# ------------- Building About Dialog
		self.aboutDialog: AboutDialog | None = None
		# ---------------
		self.menu = MainWinMenu(
			self,
			win=self.win,
			w=self.w,
			eventMan=self.eventManInternal,
		)
		# -----
		win.set_keep_above(conf.winKeepAbove.v)
		if conf.winSticky.v:
			win.stick()
		# ------------------------------------------------------------
		self.statusIcon = MainWinStatusIcon(
			self,
			win=self.win,
			w=self.w,
			statusIconMode=self.statusIconMode,
		)
		listener.dateChange.add(self)
		# ---------
		self.w.connect("delete-event", self.onDeleteEvent)
		# -----------------------------------------
		self.onConfigChange()

	def makeLayout(self) -> WinLayoutBox:
		return makeMainWinLayout(
			createEventDayView=self.createEventDayView,
			createWindowControllers=self.createWindowControllers,
			createStatusBar=self.createStatusBar,
			createMainVBox=self.createMainVBox,
			createRightPanel=self.createRightPanel,
		)

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
		self.rightPanel = MainWinRightPanel(self.win)
		self.rightPanel.onConfigChange()
		return self.rightPanel

	def onToggleRightPanel(self, _sig: SignalHandlerType) -> None:
		assert self.rightPanel is not None
		self.ignoreConfigureEvent = True
		ui.disableRedraw = True
		try:
			onToggleRightPanel(self.rightPanel, self.win)
		finally:
			self.ignoreConfigureEvent = False
			ui.disableRedraw = False
			ui.saveConfCustomize()

	def createStatusBar(self) -> CustomizableCalObj:
		from scal3.ui_gtk.statusBar import CalObj as StatusBar

		if self.statusBar is not None:
			return self.statusBar
		self.statusBar = StatusBar(self.win)
		return self.statusBar

	def createEventDayView(self) -> CustomizableCalObj:
		from scal3.ui_gtk.event.occurrence_view import LimitedHeightDayOccurrenceView

		return LimitedHeightDayOccurrenceView(
			self,
			eventSepParam=conf.eventDayViewEventSep,
		)

	def selectDateResponse(self, _w: gtk.Widget, y: int, m: int, d: int) -> None:
		ui.cells.changeDate(y, m, d)
		self.broadcastDateChange()

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

	def focusIn(self) -> None:
		self.focus = True
		if self.winCon and self.winCon.enable:
			self.winCon.windowFocusIn()

	def focusOutDo(self) -> bool:
		if not self.focus:  # and t-self.focusOutTime>0.002:
			self.win.set_keep_above(conf.winKeepAbove.v)
			if self.winCon and self.winCon.enable:
				self.winCon.windowFocusOut()
		return False

	def onFocusIn(self, _w: gtk.Widget, _ge: gdk.EventFocus) -> None:
		# log.debug("focusIn")
		self.focusIn()

	def onFocusOut(self, _w: gtk.Widget, _ge: gdk.EventFocus) -> None:
		# called 0.0004 sec (max) after focusIn
		# (if switched between two windows)
		dt = perf_counter() - ui.focusTime
		# log.debug(f"MainWin: focusOut: {ui.focusTime=}, {dt=}")
		if dt > 0.05:  # FIXME
			self.focus = False
			timeout_add(2, self.focusOutDo)

	def toggleMinimized(self, _ge: gdk.EventButton) -> None:
		if conf.winTaskbar.v:
			self.win.iconify()
			return
		self.win.close()

	def toggleMaximized(self, _ge: gdk.EventButton) -> None:
		if conf.winMaximized.v:
			self.win.unmaximize()
		else:
			self.unmaxWinWidth = conf.winWidth.v
			self.win.maximize()
		conf.winMaximized.v = not conf.winMaximized.v
		ui.saveLiveConf()

	def toggleWidthMaximized(self, _ge: gdk.EventButton) -> None:
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
		self.win.resize(ww, conf.winHeight.v)

	def screenSizeChanged(self, rect: gdk.Rectangle) -> None:
		onScreenSizeChange(self.win, rect)

	def onConfigureEvent(self, _w: gtk.Widget, _ge: gdk.EventConfigure) -> bool:
		if self.ignoreConfigureEvent:
			return False
		wx, wy = self.win.get_position()
		# maxPosDelta = max(
		# 	abs(conf.winX.v - wx),
		# 	abs(conf.winY.v - wy),
		# )
		# log.debug(wx, wy)
		ww, wh = self.win.get_size()
		if self.win.get_property("visible"):
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

	def onMainButtonPress(self, w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		return onMainButtonPress(self.win, self.menuMainCreate, w, gevent)

	def childButtonPress(
		self,
		widget: gtk.Widget,  # noqa: ARG002
		gevent: gdk.EventButton,
	) -> bool:
		return childButtonPress(self.win, self.menuMainCreate, widget, gevent)

	def changeDate(self, year: int, month: int, day: int) -> None:
		ui.cells.changeDate(year, month, day)
		self.broadcastDateChange()

	def goToday(self, _w: OptWidget = None) -> None:
		self.changeDate(*cal_types.getSysDate(calTypes.primary))

	def onDateChange(self) -> None:
		super().onDateChange()
		plugIndex = core.plugIndex.v
		allPlugList = core.allPlugList.v
		for idx in plugIndex:
			plug = allPlugList[idx]
			if plug is None:
				continue
			if hasattr(plug, "date_change_after"):
				plug.date_change_after(*ui.cells.current.date)

	def menuCellPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		self.menu.cellPopup(_sig, x, y, item)

	# TODO: customize list of main menu items (disable/enable/re-order)
	def menuMainCreate(self) -> gtk.Menu:
		return self.menu.mainCreate()

	# handler for "popup-main-menu" signal
	def menuMainPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		self.menu.mainPopup(_sig, x, y, item)

	def getMainWinMenuItem(self) -> gtk.MenuItem:
		return self.statusIcon.getMainWinMenuItem()

	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]:
		return self.statusIcon.popupItems()

	def statusIconPopup(self, sicon: gtk.StatusIcon, button: int, etime: int) -> None:
		self.statusIcon.popup(sicon, button, etime)

	def statusIconPopupAtPointer(self, button: int = 3) -> None:
		self.statusIcon.popupAtPointer(button)

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:
		self.broadcastDateChange()
		self.statusIcon.update(gdate=gdate)

	def statusIconUpdateTooltip(self) -> None:
		self.statusIcon.updateTooltip()

	def statusIconUpdate(
		self,
		gdate: tuple[int, int, int] | None = None,
		checkStatusIconMode: bool = True,
	) -> None:
		self.statusIcon.update(gdate, checkStatusIconMode)

	def onStatusIconClick(self, _w: OptWidget = None) -> None:
		self.statusIcon.onClick(_w)

	def hasStatusIcon(self) -> bool:
		return self.statusIcon.sicon is not None

	def onDeleteEvent(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> bool:
		# conf.winX.v, conf.winY.v = self.w.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(conf.winX.v, conf.winY.v)
		sicon = self.statusIcon.sicon
		if ui.dayCalWin and ui.dayCalWin.is_visible():
			self.hide()
		elif self.statusIconMode == 0 or not sicon:
			self.quit()
		elif self.statusIconMode > 1:
			if sicon.is_embedded() or (ui.dayCalWin and ui.dayCalWin.is_visible()):
				self.hide()
			else:
				self.quit()
		return True

	def onEscape(self) -> None:
		# conf.winX.v, conf.winY.v = self.w.get_position()
		# FIXME: ^ gives bad position sometimes
		# liveConfChanged()
		# log.debug(conf.winX.v, conf.winY.v)
		sicon = self.statusIcon.sicon
		if self.statusIconMode == 0:
			self.quit()
		elif self.statusIconMode > 1:  # noqa: SIM102
			assert sicon is not None
			if sicon.is_embedded():
				self.hide()

	# Callable[[int, FrameType | None], Any] | int | Handlers | None
	def quitOnSignal(self, _sig: int, _frame: FrameType | None) -> None:
		self.quit()

	def onQuitClick(
		self,
		_w: OptWidget = None,
		_event: OptEvent = None,
	) -> None:
		self.quit()

	def quit(self) -> None:
		try:
			ui.saveLiveConf()
		except Exception:
			log.exception("")
		sicon = self.statusIcon.sicon
		if self.statusIconMode > 1 and sicon:
			sicon.set_visible(False)
			# ^ needed for windows. before or after main_quit ?
		xfceApplet = self.statusIcon.xfceApplet
		if xfceApplet is not None and xfceApplet is not sicon:
			xfceApplet.set_visible(False)
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
		quit_application(self.app)

	def quitFromMenu(self, _w: gtk.Widget) -> None:
		self.quit()

	def adjustTime(
		self,
		_w: OptWidget = None,
		_event: OptEvent = None,
	) -> None:
		from subprocess import Popen

		if not ud.adjustTimeCmd:
			showError(
				"Failed to find gksudo, kdesudo, gksu, gnomesu, kdesu"
				" or any askpass program to use with sudo",
				transient_for=self.win,
			)
			return
		Popen(ud.adjustTimeCmd, env=ud.adjustTimeEnv)

	def aboutShow(self, _w: OptWidget = None, _data: Any = None) -> None:
		if not self.aboutDialog:
			from scal3.ui_gtk.about import AboutDialog

			logoSize = int(ud.screenH * 0.15)
			with open(
				join(sourceDir, "authors-dialog"),
				encoding="utf-8",
			) as authorsFile:
				authors = authorsFile.read().splitlines()
			dialog = AboutDialog(
				name=APP_DESC,
				version=core.VERSION,
				title=_("About ") + APP_DESC,
				authors=[_(author) for author in authors],
				comments=core.aboutText,
				license=core.licenseText,
				website=homePage,
				logo=GdkPixbuf.Pixbuf.new_from_file_at_size(
					ui.appLogo,
					logoSize,
					logoSize,
				),
				transient_for=self.win,
			)
			# add Donate button, FIXME
			dialog.connect("delete-event", self.aboutHide)
			connect_dialog_response(dialog, self.aboutHide)
			# dialog.set_skip_taskbar_hint(True)
			self.aboutDialog = dialog
		openWindow(self.aboutDialog)

	def aboutHide(self, _w: gtk.Widget, _ge: OptEvent = None) -> bool:
		# arg maybe an event, or response id
		assert self.aboutDialog is not None
		self.aboutDialog.hide()
		return True

	def prefShow(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		if not ui.prefWindow:
			from scal3.ui_gtk.preferences import PreferencesWindow

			ui.prefWindow = PreferencesWindow(transient_for=self.win)
			ui.prefWindow.updatePrefGui()
		if self.customizeWindow and self.customizeWindow.is_visible():
			log.warning("customize window is open")
		openWindow(ui.prefWindow)

	def eventManCreate(self) -> None:
		checkEventsReadOnly()  # FIXME
		if ui.eventManDialog is None:
			from scal3.ui_gtk.event.manager import EventManagerDialog

			ui.eventManDialog = EventManagerDialog(self)

	def eventManShow(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		self.eventManCreate()
		openWindow(ui.eventManDialog.w)

	def addCustomEvent(self, _w: OptWidget = None) -> None:
		self.eventManCreate()
		ui.eventManDialog.addCustomEvent()

	def dayCalWinShow(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		if not ui.dayCalWin:
			from scal3.ui_gtk.day_cal_window import DayCalWindow

			ui.dayCalWin = DayCalWindow(self)
		ui.dayCalWin.w.present()

	def timeLineShow(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		if not ui.timeLineWin:
			from scal3.ui_gtk.timeline import TimeLineWindow

			ui.timeLineWin = TimeLineWindow(self.win)
		openWindow(ui.timeLineWin.w)

	def timeLineShowSelectedDay(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		if not ui.timeLineWin:
			from scal3.ui_gtk.timeline import TimeLineWindow

			ui.timeLineWin = TimeLineWindow(self.win)
		ui.timeLineWin.showDayInWeek(ui.cells.current.jd)
		openWindow(ui.timeLineWin.w)

	def selectDateShow(self, _w: OptWidget = None) -> None:
		if not self.selectDateDialog:
			from scal3.ui_gtk.selectdate import SelectDateDialog

			self.selectDateDialog = SelectDateDialog(transient_for=self.win)
			self.selectDateDialog.connect(
				"response-date",
				self.selectDateResponse,
			)
		self.selectDateDialog.show()

	def dayInfoShow(self, _sig: SignalHandlerType | None = None) -> None:
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog

			self.dayInfoDialog = DayInfoDialog(transient_for=self.win)
			self.s.emit("date-change")
		openWindow(self.dayInfoDialog.dialog)

	def dayInfoShowFromMenu(self, _w: gtk.Widget) -> None:
		if not self.dayInfoDialog:
			from scal3.ui_gtk.day_info import DayInfoDialog

			self.dayInfoDialog = DayInfoDialog(transient_for=self.win)
			self.s.emit("date-change")
		openWindow(self.dayInfoDialog.dialog)

	def customizeWindowCreate(self) -> CustomizeWindow:
		if not self.customizeWindow:
			from scal3.ui_gtk.customize_dialog import CustomizeWindow

			self.customizeWindow = customizeWindow = CustomizeWindow(
				self.layout,
				transient_for=self.win,
			)
			return customizeWindow

		return self.customizeWindow

	# def switchWcalMcal(self, _w: OptWidget = None) -> None:
	# 	assert self.mainVBox is not None
	# 	customizeWindow = self.customizeWindowCreate()
	# 	self.mainVBox.switchWcalMcal(customizeWindow)
	# 	customizeWindow.updateMainPanelTreeEnableChecks()
	# 	customizeWindow.save()

	def customizeShow(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
	) -> None:
		customizeWindow = self.customizeWindowCreate()
		openWindow(customizeWindow)

	def exportShow(self, year: int, month: int) -> None:
		if not self.exportDialog:
			from scal3.ui_gtk.export import ExportDialog

			self.exportDialog = ExportDialog(transient_for=self.win)
		self.exportDialog.showDialog(year, month)

	def onExportClick(self, _w: OptWidget = None) -> None:
		self.exportShow(ui.cells.current.year, ui.cells.current.month)

	def onExportClickStatusIcon(
		self,
		_w: OptWidget = None,
		_event: OptEvent = None,
	) -> None:
		year, month, _day = cal_types.getSysDate(calTypes.primary)
		self.exportShow(year, month)

	def onConfigChange(self) -> None:
		self.menu.destroyMenus()
		super().onConfigChange()
		self.autoResize()
		# self.w.set_property("skip-taskbar-hint", not conf.winTaskbar.v)
		# self.w.set_skip_taskbar_hint  # FIXME
		# skip-taskbar-hint need to restart ro be applied
		# self.updateToolbarClock()  # FIXME
		# self.updateStatusIconClock()
		self.statusIcon.update()
