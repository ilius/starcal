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

from datetime import datetime, timedelta
from time import time as now
from typing import TYPE_CHECKING

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.event_lib import ev
from scal3.event_lib.lifetime import LifetimeEvent
from scal3.event_lib.task import TaskEvent
from scal3.locale_man import tr as _
from scal3.time_utils import getEpochFromJd
from scal3.timeline import conf
from scal3.timeline.funcs import calcTimeLineData
from scal3.timeline.utils import dayLen
from scal3.ui_gtk import (
	CursorType,
	Menu,
	WindowEdge,
	begin_resize_drag,
	connect_draw,
	gdk,
	getScrollValue,
	gtk,
	new_cursor,
	set_widget_cursor,
	source_remove,
	timeout_add,
)
from scal3.ui_gtk.button_drawing import SVGButton
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.timeline.drawing import TimeLineDrawing
from scal3.ui_gtk.timeline.movement import MovementHelper
from scal3.ui_gtk.utils import openWindow, widgetActionCallback
from scal3.utils import iceil

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.timeline.box import Box
	from scal3.timeline.funcs import TimeLineData
	from scal3.ui_gtk.drawing import ImageContext
	from scal3.ui_gtk.timeline.prefs import TimeLinePreferencesWindow

__all__ = ["TimeLine"]


class TimeLine(CustomizableCalObj):
	objName = "timeLine"
	desc = _("Time Line")

	def __init__(self, closeFunc: Callable[[], None]) -> None:
		super().__init__()
		self.w = gtk.DrawingArea()
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		self.prefWindow: TimeLinePreferencesWindow | None = None
		# ---
		self.closeFunc = closeFunc
		# ---
		self.keysActionDict = {
			"moveToNow": self.onKeyMoveToNow,
			"moveRight": self.onKeyMoveRight,
			"moveLeft": self.onKeyMoveLeft,
			"moveStop": self.onKeyMoveStop,
			"close": self.onKeyClose,
			"zoomIn": self.onKeyZoomIn,
			"zoomOut": self.onKeyZoomOut,
		}
		# ---
		connect_draw(self.w, self.onExposeEvent)
		self.w.connect("scroll-event", self.onScroll)
		self.w.connect("button-press-event", self.onButtonPress)
		self.w.connect("motion-notify-event", self.motionNotify)
		self.w.connect("button-release-event", self.buttonRelease)
		self.w.connect("key-press-event", self.onKeyPress)
		# self.connect("event", show_event)
		self.currentTime = now()
		self.timeWidth: float = dayLen
		self.timeStart: float = self.currentTime - self.timeWidth / 2.0
		self.updateBasicButtons()
		self.updateMovementButtons()
		# zoom in and zoom out buttons FIXME
		self.data: TimeLineData | None = None
		# --------
		self.boxEditing: tuple[int, EventType, Box, float, float] | None = None
		# boxEditing: None or tuple of (editType, event, box, x0, t0)
		# editType=0   moving
		# editType=-1  resizing to left
		# editType=+1  resizing to right

		self.pressingButton: SVGButton | None = None

		self._lastScrollDir = ""
		self._lastScrollTime: datetime | None = None

		self.timeUpdateSourceId: int | None = None
		# --------
		self.movement = MovementHelper(self)
		self.drawing = TimeLineDrawing(self)

	# --- accessors for the movement/drawing composition helpers ------------
	def getWidget(self) -> gtk.Widget:
		return self.w

	def getTimeStart(self) -> float:
		return self.timeStart

	def setTimeStart(self, value: float) -> None:
		self.timeStart = value

	def getTimeWidth(self) -> float:
		return self.timeWidth

	def getWidgetWidth(self) -> float:
		return self.w.get_allocation().width

	def getPixelPerSec(self) -> float:
		return self.pixelPerSec

	def getData(self) -> TimeLineData | None:
		return self.data

	def getCurrentTime(self) -> float:
		return self.currentTime

	def getBoxEditing(self) -> tuple[int, EventType, Box, float, float] | None:
		return self.boxEditing

	def queueDraw(self) -> None:
		self.w.queue_draw()

	# ----------------------------------------------------------------------

	def centerToNow(self) -> None:
		self.movement.stopMovingAnim()
		self.timeStart = now() - self.timeWidth / 2.0

	def showDayInWeek(self, jd: int) -> None:
		timeCenter = getEpochFromJd(jd) + dayLen / 2
		timeWidth = 7 * dayLen
		self.timeStart = timeCenter - timeWidth / 2
		self.timeWidth = timeWidth
		self.w.queue_draw()

	def onCenterToNowClick(self, _e: gdk.EventButton) -> None:
		self.centerToNow()
		self.w.queue_draw()

	def onDateChange(self) -> None:
		super().onDateChange()
		self.w.queue_draw()

	def updateBasicButtons(self) -> None:
		size = conf.basicButtonsSize.v
		space = size + conf.basicButtonsSpacing.v

		def close(_ge: gdk.EventButton) -> None:
			self.closeFunc()

		self.basicButtons = [
			SVGButton(
				onPress=self.onCenterToNowClick,
				imageName="go-home.svg",
				x=1,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=conf.basicButtonsOpacity.v,
			),
			SVGButton(
				onPress=self.zoomMenuOpen,
				imageName="zoom-question.svg",
				x=1 + space,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=conf.basicButtonsOpacity.v,
			),
			SVGButton(
				onPress=self.openPreferences,
				imageName="preferences-system.svg",
				x=1 + space * 2,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=conf.basicButtonsOpacity.v,
			),
			SVGButton(
				onPress=close,
				imageName="application-exit.svg",
				x=1 + space * 3,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=conf.basicButtonsOpacity.v,
			),
			SVGButton(
				onPress=self.startResize,
				imageName="resize-small.svg",
				# equivalent of "sw-resize"
				x=1,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="right",
				yalign="buttom",
				opacity=conf.basicButtonsOpacity.v,
			),
		]

	def updateMovementButtons(self) -> None:
		if not conf.movementButtonsEnable.v:
			self.movementButtons = []
			return

		size = conf.movementButtonsSize.v
		self.movementButtons = [
			SVGButton(
				onPress=self.onMoveLeftClick,
				imageName="go-previous.svg",
				x=-size * 1.5,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=conf.movementButtonsOpacity.v,
				onRelease=self.arrowButtonReleased,
			),
			SVGButton(
				onPress=self.onMoveStopClick,
				imageName="process-stop.svg",
				x=0,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=conf.movementButtonsOpacity.v,
			),
			SVGButton(
				onPress=self.onMoveRightClick,
				imageName="go-next.svg",
				x=size * 1.5,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=conf.movementButtonsOpacity.v,
				onRelease=self.arrowButtonReleased,
			),
		]

	def getButtons(self) -> list[SVGButton]:
		return self.basicButtons + self.movementButtons

	def onMoveLeftClick(self, _button: gdk.EventButton) -> None:
		self.movement.startAnimConstantAccel(-1, conf.movingHandForceButton.v)
		# FIXME: what if animation is disabled?

	def onMoveRightClick(self, _button: gdk.EventButton) -> None:
		self.movement.startAnimConstantAccel(1, conf.movingHandForceButton.v)
		# FIXME: what if animation is disabled?

	def onMoveStopClick(self, _button: gdk.EventButton) -> None:
		self.movement.stopMovingAnim()

	def arrowButtonReleased(self, _gevent: gdk.EventButton) -> None:
		self.movement.arrowButtonReleased()

	@widgetActionCallback
	def onZoomMenuItemClick(self, timeWidth: int) -> None:
		timeCenter = self.timeStart + self.timeWidth / 2
		self.timeStart = timeCenter - timeWidth / 2
		self.timeWidth = timeWidth
		self.w.queue_draw()

	def zoomMenuOpen(self, _button: gdk.EventButton) -> None:
		avgYearLen = dayLen * calTypes.primaryModule().avgYearLen
		etime = gtk.get_current_event_time()
		menu = Menu()

		for title, timeWidth in [
			(_("1 day"), dayLen),
			(_("1 week"), dayLen * 7),
			(_("{count} weeks").format(count=_(4)), dayLen * 28),
			(_("1 year"), int(avgYearLen)),
		] + [
			(_("{count} years").format(count=_(num)), int(avgYearLen * num))
			for num in (2, 4, 8, 16, 32, 64, 100)
		]:
			menu.add(
				ImageMenuItem(
					title,
					onActivate=self.onZoomMenuItemClick(timeWidth),
				),
			)
		menu.show_all()
		menu.popup(
			None,
			None,
			None,  # lambda *args: (x, y, True),
			None,
			3,
			etime,
		)

	def openPreferences(self, _ge: gdk.EventButton) -> None:
		from scal3.ui_gtk.timeline.prefs import TimeLinePreferencesWindow

		if self.prefWindow is None:
			# _tl: TimeLineType = self
			self.prefWindow = TimeLinePreferencesWindow(self)
		openWindow(self.prefWindow)

	def currentTimeUpdate(self, restart: bool = False, draw: bool = True) -> None:
		if restart and self.timeUpdateSourceId is not None:
			source_remove(self.timeUpdateSourceId)
			self.timeUpdateSourceId = None
		try:
			pixelPerSec = self.pixelPerSec
		except AttributeError:
			pixelPerSec = 1
		seconds = iceil(0.4 / pixelPerSec)
		tm = now()
		miliSeconds = int(1000 * (seconds + 0.01 - tm % 1))
		miliSeconds = min(miliSeconds, 4294967295)
		# to avoid: OverflowError: %d not in range 0 to 4294967295
		self.timeUpdateSourceId = timeout_add(
			miliSeconds,
			self.currentTimeUpdate,
		)
		self.currentTime = int(tm)
		parent = self.w.get_parent()
		if (
			draw
			and parent
			and parent.get_visible()
			and self.timeStart <= tm <= self.timeStart + self.timeWidth + 1
		):
			# log.debug(f"{tm%100:.2f} currentTimeUpdate: DRAW")
			self.w.queue_draw()

	def updateData(self) -> None:
		width = self.w.get_allocation().width
		self.pixelPerSec = width / self.timeWidth  # pixel/second
		self.borderTm = conf.boxEditBorderWidth.v / self.pixelPerSec  # second
		self.data = calcTimeLineData(
			self.timeStart,
			self.timeWidth,
			self.pixelPerSec,
			self.borderTm,
		)

	def onExposeEvent(
		self,
		_widget: gtk.Widget,
		cr: ImageContext,
	) -> None:
		self.drawWithContext(cr)

	def drawWithContext(self, cr: ImageContext) -> None:
		# t0 = perf_counter()
		if not self.boxEditing:
			self.updateData()
			self.currentTimeUpdate(restart=True, draw=False)
		# t1 = perf_counter()
		self.drawing.drawAll(cr)
		# t2 = perf_counter()
		# log.debug(f"drawing time / data calc time: {(t2-t1)/(t1-t0):.2f}")

	def getLastScrollDir(self) -> str:
		"""Returns "up", "down" or ""."""
		if not self._lastScrollDir:
			return ""

		if self._lastScrollTime is None:
			return ""

		if datetime.now() - self._lastScrollTime > timedelta(seconds=2):
			return ""

		return self._lastScrollDir

	def onScroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool:
		smallForce = False
		if gevent.is_scroll_stop_event():  # or gevent.is_stop == 1
			smallForce = True
			# self._lastScrollDir = ""
			# self.stopMovingAnim()
			# return
		dirStr = getScrollValue(gevent, last=self.getLastScrollDir())
		if not dirStr:
			return False
		self._lastScrollDir = dirStr
		self._lastScrollTime = datetime.now()
		if gevent.get_state() & gdk.ModifierType.CONTROL_MASK:
			self.zoom(
				dirStr == "up",
				conf.scrollZoomStep.v,
				gevent.x / self.w.get_allocation().width,
			)
		else:
			self.movement.movingUserEvent(
				direction=(-1 if dirStr == "up" else 1),
				source="scroll",
				smallForce=smallForce,
			)
		self.w.queue_draw()
		return True

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		assert self.data is not None
		button = self.pressingButton
		if button is not None:
			assert button.onRelease is not None
			button.onRelease(gevent)
			self.pressingButton = None
		x = gevent.x
		y = gevent.y
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		if gevent.button == 1:
			for button in self.getButtons():
				if button.contains(x, y, w, h):
					button.onPress(gevent)
					if button.onRelease is not None:
						self.pressingButton = button
					return True
			# ----
			for box in self.data.boxes:
				if not box.hasBorder:
					continue
				if not box.ids:
					continue
				if not box.contains(x, y):
					continue
				gid, eid = box.ids
				group = ev.groups[gid]
				event = group[eid]
				# ----
				top = y - box.y
				left = x - box.x
				right = box.x + box.w - x
				minA = min(conf.boxEditBorderWidth.v, top, left, right)
				editType = None
				if top == minA:
					editType = 0
					t0 = event.getStartEpoch()
					set_widget_cursor(self.w, new_cursor(CursorType.FLEUR))
				elif right == minA:
					editType = 1
					t0 = event.getEndEpoch()
					set_widget_cursor(self.w, new_cursor(CursorType.RIGHT_SIDE))
				elif left == minA:
					editType = -1
					t0 = event.getStartEpoch()
					set_widget_cursor(self.w, new_cursor(CursorType.LEFT_SIDE))
				if editType is not None:
					self.boxEditing = (editType, event, box, x, t0)
					self.w.queue_draw()
					return True
		elif gevent.button == 3:
			for box in self.data.boxes:
				if not box.ids:
					continue
				if not box.contains(x, y):
					continue
				gid, eid = box.ids
				group = ev.groups[gid]
				event = group[eid]
				# ----
				menu = Menu()
				# --
				if not event.readOnly:
					winTitle = _("Edit") + " " + event.desc
					menu.add(
						ImageMenuItem(
							winTitle,
							imageName="document-edit.svg",
							onActivate=self.onEditEventClick(winTitle, event, gid),
						),
					)
				# --
				winTitle = _("Edit") + " " + group.desc
				menu.add(
					ImageMenuItem(
						winTitle,
						imageName="document-edit.svg",
						onActivate=self.onEditGroupClick(winTitle, group),
					),
				)
				# --
				menu.add(gtk.SeparatorMenuItem())
				# --
				menu.add(
					ImageMenuItem(
						_("Move to {title}").format(title=ev.trash.title),
						imageName=ev.trash.getIconRel(),
						onActivate=self.moveEventToTrash(group, event),
					),
				)
				# --
				menu.show_all()
				menu.popup(None, None, None, None, 3, gevent.time)
		return False

	def motionNotify(self, _w: gtk.Widget, gevent: gdk.EventMotion) -> None:
		if not self.boxEditing:
			return
		editType, event, box, x0, t0 = self.boxEditing
		# log.debug(f"motionNotify: {self.event=}")
		assert isinstance(event, TaskEvent | LifetimeEvent), f"{event=}"
		t1 = int(t0 + (gevent.x - x0) / self.pixelPerSec)
		if editType == 0:
			event.modifyPos(t1)
		elif editType == 1:
			if t1 - box.t0 > 2 * conf.boxEditBorderWidth.v / self.pixelPerSec:
				event.modifyEnd(t1)
		elif editType == -1:  # noqa: SIM102
			if box.t1 - t1 > 2 * conf.boxEditBorderWidth.v / self.pixelPerSec:
				event.modifyStart(t1)
		box.t0 = max(
			event.getStartEpoch(),
			self.timeStart - self.borderTm,
		)
		box.t1 = min(
			event.getEndEpoch(),
			self.timeStart + self.timeWidth + self.borderTm,
		)
		self.w.queue_draw()

	def buttonRelease(self, _w: gtk.Widget, gevent: gdk.EventButton) -> None:
		if self.boxEditing:
			_editType, event, _box, _x0, _t0 = self.boxEditing
			event.afterModify()
			event.save()
			self.boxEditing = None
		button = self.pressingButton
		if button is not None:
			assert button.onRelease is not None
			button.onRelease(gevent)
			self.pressingButton = None
		set_widget_cursor(self.w, new_cursor(CursorType.LEFT_PTR))
		self.w.queue_draw()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.w.queue_draw()

	@widgetActionCallback
	def onEditEventClick(
		self,
		winTitle: str,
		event: EventType,
		_gid: int,
	) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		window = self.w.get_toplevel()
		assert isinstance(window, gtk.Window), f"{window=}"

		eventNew = EventEditorDialog(
			event,
			title=winTitle,
			transient_for=window,
		).run2()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.onConfigChange()

	@widgetActionCallback
	def onEditGroupClick(
		self,
		_winTitle: str,
		group: EventGroupType,
	) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		window = self.w.get_toplevel()
		assert isinstance(window, gtk.Window), f"{window=}"

		groupNew = GroupEditorDialog(
			group,
			transient_for=window,
		).run2()
		if groupNew is None:
			return
		groupNew.afterModify()
		groupNew.save()  # FIXME
		ui.eventUpdateQueue.put("eg", groupNew, self)
		self.onConfigChange()
		self.w.queue_draw()

	@widgetActionCallback
	def moveEventToTrash(
		self,
		group: EventGroupType,
		event: EventType,
	) -> None:
		from scal3.ui_gtk.event.utils import confirmEventTrash

		if not confirmEventTrash(event):
			return
		ui.moveEventToTrash(group, event, self)
		self.onConfigChange()

	def startResize(self, gevent: gdk.EventButton) -> None:
		win = self.w.get_parent()
		assert isinstance(win, gtk.Window), f"{win=}"
		begin_resize_drag(
			win,
			WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def zoom(self, zoomIn: bool, stepFact: float, posFact: float) -> None:
		zoomValue = 1.0 / stepFact if zoomIn else stepFact
		self.timeStart += self.timeWidth * (1 - zoomValue) * posFact
		self.timeWidth *= zoomValue

	def keyboardZoom(self, zoomIn: bool) -> None:
		self.zoom(zoomIn, conf.keyboardZoomStep.v, 0.5)

	def onKeyMoveToNow(self, _ge: gdk.EventKey) -> None:
		self.centerToNow()

	def onKeyMoveRight(self, gevent: gdk.EventKey) -> None:
		self.movement.movingUserEvent(
			direction=1,
			source="keyboard",
			smallForce=bool(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveLeft(self, gevent: gdk.EventKey) -> None:
		self.movement.movingUserEvent(
			direction=-1,
			source="keyboard",
			smallForce=bool(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveStop(self, _ge: gdk.EventKey) -> None:
		self.movement.stopMovingAnim()

	def onKeyClose(self, _ge: gdk.EventKey) -> None:
		self.closeFunc()

	def onKeyZoomIn(self, _ge: gdk.EventKey) -> None:
		self.keyboardZoom(True)

	def onKeyZoomOut(self, _ge: gdk.EventKey) -> None:
		self.keyboardZoom(False)

	def onKeyPress(self, _arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		keyName = gdk.keyval_name(gevent.keyval)
		if not keyName:
			return False
		keyName = keyName.lower()
		# log.debug(f"{now():.3f}")
		action = conf.keys.v.get(keyName)
		if action:
			func = self.keysActionDict.get(action)
			if func is not None:
				func(gevent)
				self.w.queue_draw()
				return True
		# if k=="end":
		# 	pass
		# elif k=="page_up":
		# 	pass
		# elif k=="page_down":
		# 	pass
		# elif k=="menu":# Simulate right click (key beside Right-Ctrl)
		# 	#self.emit("popup-cell-menu", *self.getCellPos())
		# elif k in ("f10","m"): # F10 or m or M
		# 	if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
		# 		# Simulate right click (key beside Right-Ctrl)
		# 		self.emit("popup-cell-menu", *self.getCellPos())
		# 	else:
		# 		self.emit("popup-main-menu", *self.getMainMenuPos())
		return False
