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
from os.path import join
from time import localtime, perf_counter
from typing import TYPE_CHECKING, ClassVar

from scal3 import logger

log = logger.get()

from gi.repository import Gio as gio

from scal3 import cal_types, core, event_lib, locale_man, ui
from scal3.app_info import APP_DESC, homePage
from scal3.cal_types import calTypes, convert
from scal3.color_utils import rgbToHtmlColor
from scal3.event_lib import ev
from scal3.locale_man import rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.path import pixDir, sourceDir
from scal3.ui import conf
from scal3.ui.mainmenuitems import menuMainItemDefs
from scal3.ui_gtk import (
	GdkPixbuf,
	Menu,
	gdk,
	gtk,
	listener,
	pixcache,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.layout import WinLayoutBox, WinLayoutObj
from scal3.ui_gtk.menuitems import (
	CheckMenuItem,
	ImageMenuItem,
	ResizeMenuItem,
)
from scal3.ui_gtk.starcal_classes import MainWinVbox, SignalHandler
from scal3.ui_gtk.starcal_funcs import (
	copyCurrentDate,
	copyCurrentDateTime,
	copyDateGetCallback,
	createPluginsText,
	getStatusIconTooltip,
	liveConfChanged,
	onStatusIconPress,
	shouldUseAppIndicator,
	yearWheelShow,
)
from scal3.ui_gtk.utils import (
	get_menu_height,
	get_menu_width,
	openWindow,
	showError,
	trimMenuItemLabel,
	widgetActionCallback,
	x_large,
)

if TYPE_CHECKING:
	from types import FrameType
	from typing import Any

	from scal3.event_lib.pytypes import EventGroupType
	from scal3.ui_gtk.about import AboutDialog
	from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
	from scal3.ui_gtk.customize_dialog import CustomizeWindow
	from scal3.ui_gtk.day_info import DayInfoDialog
	from scal3.ui_gtk.export import ExportDialog
	from scal3.ui_gtk.menuitems import ItemCallback
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
		# ---
		self.dayInfoDialog: DayInfoDialog | None = None
		# log.debug("windowList.items", [item.objName for item in ud.windowList.items])
		# -----------
		# self.connect("window-state-event", selfStateEvent)
		win.set_title(f"{APP_DESC} {core.VERSION}")
		# self.connect("main-show", lambda arg: self.present())
		# self.connect("main-hide", lambda arg: self.hide())
		win.set_decorated(False)
		win.set_property("skip-taskbar-hint", not conf.winTaskbar.v)
		# self.w.set_skip_taskbar_hint  # FIXME
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
		self.menuMain: gtk.Menu | None = None
		self.menuCell: gtk.Menu | None = None
		# -----
		win.set_keep_above(conf.winKeepAbove.v)
		if conf.winSticky.v:
			win.stick()
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
		self.menuItemsCallback: dict[str, ItemCallback] = {
			"onTop": self.onKeepAboveClick,
			"onAllDesktops": self.onStickyClick,
			"today": self.goToday,
			"selectDate": self.selectDateShow,
			"dayInfo": self.dayInfoShowFromMenu,
			"customize": self.customizeShow,
			"preferences": self.prefShow,
			# "addCustomEvent": self.addCustomEvent,
			"dayCalWin": self.dayCalWinShow,
			"eventManager": self.eventManShow,
			"timeLine": self.timeLineShow,
			"yearWheel": yearWheelShow,
			# "weekCal": self.weekCalShow,
			"exportToHtml": self.onExportClick,
			"adjustTime": self.adjustTime,
			"about": self.aboutShow,
			"quit": self.quitFromMenu,
		}
		assert sorted(self.menuItemsCallback) == sorted(menuMainItemDefs)

	def makeLayout(self) -> WinLayoutBox:
		footer = WinLayoutBox(
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
					initializer=createPluginsText,
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
		footer.setItemsOrder(conf.mainWinFooterItems)
		return WinLayoutBox(
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
				footer,
			],
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

	def _onToggleRightPanel(self) -> None:
		assert self.rightPanel is not None
		enable = not conf.mainWinRightPanelEnable.v
		conf.mainWinRightPanelEnable.v = enable
		self.rightPanel.enable = enable
		self.rightPanel.showHide()
		self.rightPanel.broadcastDateChange()

		# update Enable checkbutton in Customize dialog
		self.rightPanel.onToggleFromMainWin()

		if conf.mainWinRightPanelResizeOnToggle.v:
			ww, wh = self.win.get_size()
			mw = conf.mainWinRightPanelWidth.v
			if enable:
				ww += mw
			else:
				ww -= mw
			if rtl:
				wx, wy = self.win.get_position()
				wx += mw * (-1 if enable else 1)
				self.win.move(wx, wy)
			self.win.resize(ww, wh)

	def onToggleRightPanel(self, _sig: SignalHandlerType) -> None:
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
		self.w.emit("delete-event", gdk.Event.new(gdk.EventType.DELETE))

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
		if conf.winMaximized.v:
			return
		winWidth = min(conf.winWidth.v, rect.width)
		winHeight = min(conf.winHeight.v, rect.height)
		winX = min(conf.winX.v, rect.width - conf.winWidth.v)
		winY = min(conf.winY.v, rect.height - conf.winHeight.v)

		if (winWidth, winHeight) != (conf.winWidth.v, conf.winHeight.v):
			self.win.resize(winWidth, winHeight)

		if (winX, winY) != (conf.winX.v, conf.winY.v):
			self.win.move(winX, winY)

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
			self.win.begin_move_drag(
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
			self.win.begin_move_drag(gevent.button, x, y, gevent.time)
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

	def onResizeFromMenu(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if self.menuMain:
			self.menuMain.hide()
		conf.winMaximized.v = False
		ui.updateFocusTime()
		self.win.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
		return True

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

	def _getEventAddToMenuItem(self, menu2: gtk.Menu, group: EventGroupType) -> None:
		from scal3.ui_gtk.drawing import newColorCheckPixbuf

		if not group.enable:
			return
		if not group.showInCal():  # FIXME
			return
		eventTypes = group.acceptsEventTypes
		if not eventTypes:
			return

		imageName: str | None = None
		pixbuf: GdkPixbuf.Pixbuf | None = None

		if group.icon:
			imageName = group.icon
		else:
			pixbuf = newColorCheckPixbuf(
				group.color.rgb(),
				20,
				True,
			)

		# --
		if len(eventTypes) == 1:
			menu2.add(
				ImageMenuItem(
					group.title,
					onActivate=self.addToGroupFromMenu(group, eventTypes[0]),
					imageName=imageName,
					pixbuf=pixbuf,
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
						onActivate=self.addToGroupFromMenu(group, eventType),
					),
				)
			menu3.show_all()
			item2 = ImageMenuItem(
				group.title,
				imageName=imageName,
				pixbuf=pixbuf,
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

	@widgetActionCallback
	def editEventFromMenu(self, groupId: int, eventId: int) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		event = ui.getEvent(groupId, eventId)
		eventNew = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self.win,
		).run2()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.onConfigChange()

	def addEditEventCellMenuItems(self, menu: gtk.Menu) -> None:
		if ev.allReadOnly:
			return
		eventsData = ui.cells.current.getEventsData()
		if not eventsData:
			return

		if len(eventsData) < 4:  # TODO: make it customizable
			for eData in eventsData:
				groupId, eventId = eData.ids
				menu.add(
					ImageMenuItem(
						label=_("Edit") + ": " + trimMenuItemLabel(eData.text[0], 25),
						imageName=eData.icon,
						onActivate=self.editEventFromMenu(groupId, eventId),
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
					onActivate=self.editEventFromMenu(groupId, eventId),
				),
			)
		subMenu.show_all()
		subMenuItem.set_submenu(subMenu)
		menu.add(subMenuItem)

	def menuCellPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		widget = item.w
		# item.objName is in ("weekCal", "monthCal", ...)
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
					onActivate=copyDateGetCallback(calType),
				),
			)
		menu.add(
			ImageMenuItem(
				label=_("Day Info"),
				imageName="info.svg",
				onActivate=self.dayInfoShowFromMenu,
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
				onActivate=self.goToday,
			),
		)
		menu.add(
			ImageMenuItem(
				label=_("Select _Date..."),
				imageName="select-date.svg",
				onActivate=self.selectDateShow,
			),
		)
		# if item.objName in {"weekCal", "monthCal"}:
		# 	isWeek = item.objName == "weekCal"
		# 	calDesc = "Month Calendar" if isWeek else "Week Calendar"
		# 	menu.add(
		# 		ImageMenuItem(
		# 			label=_("Switch to " + calDesc),
		# 			imageName="" if isWeek else "week-calendar.svg",
		# 			onActivate=self.switchWcalMcal,
		# 		),
		# 	)
		menu.add(
			ImageMenuItem(
				label=_("In Time Line"),
				imageName="timeline.svg",
				onActivate=self.timeLineShowSelectedDay,
			),
		)
		if os.path.isfile("/usr/bin/evolution"):  # FIXME
			menu.add(
				ImageMenuItem(
					label=_("In E_volution"),
					imageName="evolution.png",
					onActivate=ui.cells.current.dayOpenEvolution,
				),
			)
		# ----
		moreMenu = Menu()
		moreMenu.add(
			ImageMenuItem(
				label=_("_Customize"),
				imageName="document-edit.svg",
				onActivate=self.customizeShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				onActivate=self.prefShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				onActivate=self.eventManShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				onActivate=yearWheelShow,
			),
		)  # icon? FIXME
		moreMenu.add(
			ImageMenuItem(
				label=_("Day Calendar (Desktop Widget)"),
				imageName="starcal.svg",
				onActivate=self.dayCalWinShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				onActivate=self.onExportClick,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				onActivate=self.aboutShow,
			),
		)
		moreMenu.add(
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				onActivate=self.onQuitClick,
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
		menu.add(
			ResizeMenuItem(
				label=_("Resize"),
				onButtonPress=self.onResizeFromMenu,
			)
		)
		for name, itemDict in menuMainItemDefs.items():
			menu.add(
				itemDict["cls"](
					label=itemDict["label"],
					onActivate=self.menuItemsCallback[name],
					**itemDict["args"],
				)
			)
		# -------
		menu.show_all()
		self.menuMain = menu
		return menu

	# handler for "popup-main-menu" signal
	def menuMainPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObjType,
	) -> None:
		widget = item.w
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

	@widgetActionCallback
	def addToGroupFromMenu(
		self,
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
			transient_for=self.win,
		)
		if event is None:
			return
		if event.parent is None:
			raise RuntimeError("event.parent is None")
		ui.eventUpdateQueue.put("+", event, self)
		self.onConfigChange()

	def onKeepAboveClick(self, check: gtk.Widget) -> None:
		assert isinstance(check, CheckMenuItem)
		act = check.get_active()
		self.win.set_keep_above(act)
		conf.winKeepAbove.v = act
		ui.saveLiveConf()

	def onStickyClick(self, check: gtk.Widget) -> None:
		assert isinstance(check, CheckMenuItem)
		if check.get_active():
			self.win.stick()
			conf.winSticky.v = True
		else:
			self.win.unstick()
			conf.winSticky.v = False
		ui.saveLiveConf()

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

	def statusIconInit(self) -> None:
		self.sicon: gtk.StatusIcon | IndicatorStatusIconWrapper | None
		if self.statusIconMode != 2:
			self.sicon = None
			return

		if shouldUseAppIndicator():
			from scal3.ui_gtk.starcal_appindicator import (
				IndicatorStatusIconWrapper,
			)

			self.sicon = IndicatorStatusIconWrapper(self)
			return

		sicon = gtk.StatusIcon()
		self.sicon = sicon
		sicon.set_title(APP_DESC)
		sicon.set_visible(True)  # is needed?
		sicon.connect(
			"button-press-event",
			onStatusIconPress,
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
				onActivate=copyCurrentDateTime,
			),
			ImageMenuItem(
				label=_("Copy _Date"),
				imageName="edit-copy.svg",
				onActivate=copyCurrentDate,
			),
			ImageMenuItem(
				label=_("Ad_just System Time"),
				imageName="preferences-system.svg",
				onActivate=self.adjustTime,
			),
			# ImageMenuItem(
			# 	label=_("_Add Event"),
			# 	imageName="list-add.svg",
			# 	onActivate=ui.addCustomEvent,
			# ),  # FIXME
			ImageMenuItem(
				label=_("Export to {format}").format(format="HTML"),
				imageName="export-to-html.svg",
				onActivate=self.onExportClickStatusIcon,
			),
			ImageMenuItem(
				label=_("_Preferences"),
				imageName="preferences-system.svg",
				onActivate=self.prefShow,
			),
			ImageMenuItem(
				label=_("_Customize"),
				imageName="document-edit.svg",
				onActivate=self.customizeShow,
			),
			ImageMenuItem(
				label=_("_Event Manager"),
				imageName="list-add.svg",
				onActivate=self.eventManShow,
			),
			ImageMenuItem(
				label=_("Time Line"),
				imageName="timeline.svg",
				onActivate=self.timeLineShow,
			),
			ImageMenuItem(
				label=_("Year Wheel"),
				imageName="year-wheel.svg",
				onActivate=yearWheelShow,
			),
			ImageMenuItem(
				label=_("_About"),
				imageName="dialog-information.svg",
				onActivate=self.aboutShow,
			),
			gtk.SeparatorMenuItem(),
			ImageMenuItem(
				label=_("_Quit"),
				imageName="application-exit.svg",
				onActivate=self.onQuitClick,
			),
		]

	def statusIconPopup(self, sicon: gtk.StatusIcon, button: int, etime: int) -> None:
		assert isinstance(self.sicon, gtk.StatusIcon), f"{self.sicon=}"
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
			y = gtk.StatusIcon.position_menu(menu, 0, 0, self.sicon)[1]  # type: ignore[call-arg, arg-type]
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
		# assert isinstance(sicon, gtk.StatusIcon), f"{sicon=}"
		sicon.set_tooltip_text(getStatusIconTooltip())

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

	def onStatusIconClick(self, _w: OptWidget = None) -> None:
		if self.w.get_property("visible"):
			# conf.winX.v, conf.winY.v = self.w.get_position()
			# FIXME: ^ gives bad position sometimes
			# liveConfChanged()
			# log.debug(conf.winX.v, conf.winY.v)
			self.hide()
		else:
			self.win.move(conf.winX.v, conf.winY.v)
			# every calling of .hide() and .present(), makes dialog not on top
			# (forgets being on top)
			self.win.set_keep_above(conf.winKeepAbove.v)
			if conf.winSticky.v:
				self.win.stick()
			self.win.deiconify()
			self.win.present()
			self.focusIn()
			# in LXDE, the window was not focused without self.focusIn()
			# while worked in Xfce and GNOME.

	def onDeleteEvent(
		self,
		_w: OptWidget = None,
		_ge: OptEvent = None,
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
			dialog.connect("response", self.aboutHide)
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
		if self.menuMain:
			self.menuMain.destroy()
			self.menuMain = None
		if self.menuCell:
			self.menuCell.destroy()
			self.menuCell = None
		super().onConfigChange()
		self.autoResize()
		# self.w.set_property("skip-taskbar-hint", not conf.winTaskbar.v)
		# self.w.set_skip_taskbar_hint  # FIXME
		# skip-taskbar-hint need to restart ro be applied
		# self.updateToolbarClock()  # FIXME
		# self.updateStatusIconClock()
		self.statusIconUpdate()
