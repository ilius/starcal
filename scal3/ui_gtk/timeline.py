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

from scal3 import logger
from scal3.event_lib.events import LifetimeEvent, TaskEvent
from scal3.ui_gtk.customize import CustomizableCalObj

log = logger.get()

from datetime import datetime, timedelta
from time import perf_counter
from time import time as now
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import ui
from scal3.cal_types import calTypes
from scal3.event_lib import ev
from scal3.locale_man import localTz
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
	getUtcOffsetByEpoch,
	getUtcOffsetByJd,
)
from scal3.timeline import conf
from scal3.timeline.funcs import TimeLineData, calcTimeLineData
from scal3.timeline.utils import dayLen, fontFamily
from scal3.ui_gtk import (
	Menu,
	gdk,
	getScrollValue,
	gtk,
	main_context_default,
	source_remove,
	timeout_add,
)
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.button_drawing import SVGButton
from scal3.ui_gtk.drawing import (
	ImageContext,
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.gtk_ud import CalObjWidget
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
from scal3.ui_gtk.timeline_box import (
	drawBoxBG,
	drawBoxBorder,
	drawBoxText,
)
from scal3.ui_gtk.utils import openWindow
from scal3.utils import iceil

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository.GLib import Source

	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.timeline.box import Box
	from scal3.timeline.tick import Tick
	from scal3.ui_gtk.timeline_prefs import TimeLinePreferencesWindow

__all__ = ["TimeLineWindow"]


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
		self.w.connect("draw", self.onExposeEvent)
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
		self.movingLastPress = 0.0
		self.movingV = 0.0
		self.movingF = 0.0
		# -------
		self.boxEditing: tuple[int, EventType, Box, float, float] | None = None
		# boxEditing: None or tuple of (editType, event, box, x0, t0)
		# editType=0   moving
		# editType=-1  resizing to left
		# editType=+1  resizing to right

		self.pressingButton: SVGButton | None = None

		self._lastScrollDir = ""
		self._lastScrollTime: datetime | None = None

		self.timeUpdateSourceId: int | None = None
		self.animTimerSource: Source | None = None

	def centerToNow(self) -> None:
		self.stopMovingAnim()
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
		self.startAnimConstantAccel(-1, conf.movingHandForceButton.v)
		# FIXME: what if animation is disabled?

	def onMoveRightClick(self, _button: gdk.EventButton) -> None:
		self.startAnimConstantAccel(1, conf.movingHandForceButton.v)
		# FIXME: what if animation is disabled?

	def onMoveStopClick(self, _button: gdk.EventButton) -> None:
		self.stopMovingAnim()

	def arrowButtonReleased(self, _gevent: gdk.EventButton) -> None:
		self.movingF = 0
		# ^ this will only make it stop slowly (by friction force)
		# if you want it to stop movement, set: self.movingV = 0
		# just like self.stopMovingAnim

	def onZoomMenuItemClick(self, _w: gtk.Widget, timeWidth: int) -> None:
		timeCenter = self.timeStart + self.timeWidth / 2
		self.timeStart = timeCenter - timeWidth / 2
		self.timeWidth = timeWidth
		self.w.queue_draw()

	def zoomMenuOpen(self, _button: gdk.EventButton) -> None:
		avgYearLen = dayLen * calTypes.primaryModule().avgYearLen
		etime = gtk.get_current_event_time()
		menu = Menu()

		def selectZoomLevel(timeWidth: int) -> Callable[[gtk.Widget], None]:
			def func(w: gtk.Widget) -> None:
				self.onZoomMenuItemClick(w, timeWidth)

			return func

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
					func=selectZoomLevel(timeWidth),
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
		from scal3.ui_gtk.timeline_prefs import TimeLinePreferencesWindow

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

	def drawTick(self, cr: ImageContext, tick: Tick, maxTickHeight: float) -> None:
		tickH = tick.height
		tickW = tick.width
		tickH = min(tickH, maxTickHeight)
		# ---
		tickX = tick.pos - tickW / 2.0
		tickY = 1
		cr.rectangle(tickX, tickY, tickW, tickH)
		color = tick.color or conf.fgColor.v
		assert color is not None
		fillColor(cr, color)
		# fillColor never seems to raise exception anymore (in Gtk3)
		# ---
		font = ui.Font(family=fontFamily, size=tick.fontSize)
		# layout = newLimitedWidthTextLayout(
		# 	self,
		# 	tick.label,
		# 	tick.maxLabelWidth,
		# 	font=font,
		# 	truncate=truncateTickLabel,
		# )  # FIXME
		layout = newTextLayout(
			self.w,
			text=tick.label,
			font=font,
			maxSize=(tick.maxLabelWidth, 0),
			maximizeScale=1.0,
			truncate=conf.truncateTickLabel.v,
		)  # FIXME
		if layout:
			# layout.set_auto_dir(0)  # FIXME
			# log.debug(f"{layout.get_auto_dir() = }")
			layoutW, _layoutH = layout.get_pixel_size()
			layoutX = tick.pos - layoutW / 2.0
			layoutY = tickH * conf.labelYRatio.v
			cr.move_to(layoutX, layoutY)
			# cr.move_to never seems to raise exception anymore
			show_layout(cr, layout)  # with the same tick.color

	def drawBox(self, cr: ImageContext, box: Box) -> None:
		x = box.x
		w = box.w
		y = box.y
		h = box.h
		# ---
		drawBoxBG(cr, box, x, y, w, h)
		drawBoxBorder(cr, box, x, y, w, h)
		drawBoxText(cr, box, x, y, w, h, self.w)

	def drawBoxEditingHelperLines(self, cr: ImageContext) -> None:
		if not self.boxEditing:
			return
		assert conf.fgColor.v is not None
		_editType, _event, box, _x0, _t0 = self.boxEditing
		setColor(cr, conf.fgColor.v)
		d = conf.boxEditHelperLineWidth.v
		cr.rectangle(
			box.x,
			0,
			d,
			box.y,
		)
		cr.fill()
		cr.rectangle(
			box.x + box.w - d,
			0,
			d,
			box.y,
		)
		cr.fill()

	def drawAll(self, cr: ImageContext) -> None:
		assert conf.bgColor.v is not None
		assert self.data is not None
		timeStart = self.timeStart
		timeWidth = self.timeWidth
		timeEnd = timeStart + timeWidth
		# ----
		alloc = self.w.get_allocation()
		width = alloc.width
		height = alloc.height
		pixelPerSec = self.pixelPerSec
		dayPixel = dayLen * pixelPerSec  # pixel
		maxTickHeight = conf.maxTickHeightRatio.v * height
		# -----
		cr.rectangle(0, 0, width, height)
		fillColor(cr, conf.bgColor.v)
		# -----
		setColor(cr, conf.holidayBgBolor.v)
		for x in self.data.holidays:
			cr.rectangle(x, 0, dayPixel, height)
			cr.fill()
		# -----
		for tick in self.data.ticks:
			self.drawTick(cr, tick, maxTickHeight)
		# ------
		beforeBoxH = maxTickHeight  # FIXME
		maxBoxH = height - beforeBoxH
		for box in self.data.boxes:
			box.setPixelValues(timeStart, pixelPerSec, beforeBoxH, maxBoxH)
			self.drawBox(cr, box)
		self.drawBoxEditingHelperLines(cr)
		# Show (possible) Daylight Saving change
		if (
			timeStart > 0
			and 2 * 3600 < timeWidth < 30 * dayLen
			and getUtcOffsetByEpoch(timeStart) != getUtcOffsetByEpoch(timeEnd)
		):
			startJd = getJdFromEpoch(timeStart)
			endJd = getJdFromEpoch(timeEnd)
			lastOffset = getUtcOffsetByJd(startJd, localTz)
			dstChangeJd = None
			deltaSec = 0
			for jd in range(startJd + 1, endJd + 1):
				offset = getUtcOffsetByJd(jd, localTz)
				deltaSec = offset - lastOffset
				if deltaSec != 0:
					dstChangeJd = jd
					break
			if dstChangeJd is not None:
				pass
				# deltaHour = deltaSec / 3600.0
				# dstChangeEpoch = getEpochFromJd(dstChangeJd)
				# log.debug(f"{dstChangeEpoch = }")
			else:
				log.info("dstChangeEpoch not found")

		# Draw Current Time Marker
		dt = self.currentTime - timeStart
		if 0 <= dt <= timeWidth:
			setColor(cr, conf.currentTimeMarkerColor.v)
			cr.rectangle(
				dt * pixelPerSec - conf.currentTimeMarkerWidth.v / 2.0,
				0,
				conf.currentTimeMarkerWidth.v,
				conf.currentTimeMarkerHeightRatio.v * height,
			)
			cr.fill()
		# ------
		for button in self.getButtons():
			button.draw(cr, width, height)

	def onExposeEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		win = self.w.get_window()
		assert win is not None
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr)
		finally:
			win.end_draw_frame(dctx)

	def drawWithContext(self, cr: ImageContext) -> None:
		# t0 = perf_counter()
		if not self.boxEditing:
			self.updateData()
			self.currentTimeUpdate(restart=True, draw=False)
		# t1 = perf_counter()
		self.drawAll(cr)
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

	def onScroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool | None:
		smallForce = False
		if gevent.is_scroll_stop_event():  # or gevent.is_stop == 1
			smallForce = True
			# self._lastScrollDir = ""
			# self.stopMovingAnim()
			# return
		dirStr = getScrollValue(gevent, last=self.getLastScrollDir())
		if not dirStr:
			return None
		self._lastScrollDir = dirStr
		self._lastScrollTime = datetime.now()
		if gevent.get_state() & gdk.ModifierType.CONTROL_MASK:
			self.zoom(
				dirStr == "up",
				conf.scrollZoomStep.v,
				gevent.x / self.w.get_allocation().width,
			)
		else:
			self.movingUserEvent(
				direction=(-1 if dirStr == "up" else 1),
				source="scroll",
				smallForce=smallForce,
			)
		self.w.queue_draw()
		return True

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		assert self.data is not None
		if self.pressingButton is not None:
			self.pressingButton.onRelease(gevent)  # type: ignore[misc]
			self.pressingButton = None
		win = self.w.get_window()
		assert win is not None
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
					win.set_cursor(gdk.Cursor.new(gdk.CursorType.FLEUR))
				elif right == minA:
					editType = 1
					t0 = event.getEndEpoch()
					win.set_cursor(
						gdk.Cursor.new(gdk.CursorType.RIGHT_SIDE),
					)
				elif left == minA:
					editType = -1
					t0 = event.getStartEpoch()
					win.set_cursor(
						gdk.Cursor.new(gdk.CursorType.LEFT_SIDE),
					)
				if editType is not None:
					self.boxEditing = (editType, event, box, x, t0)
					self.w.queue_draw()
					return True
		elif gevent.button == 3:

			def editEvent(event: EventType, gid: int) -> Callable[[gtk.Widget], None]:
				def func(w: gtk.Widget) -> None:
					self.onEditEventClick(w, winTitle, event, gid)

				return func

			def editGroup(group: EventGroupType) -> Callable[[gtk.Widget], None]:
				def func(w: gtk.Widget) -> None:
					self.onEditGroupClick(w, winTitle, group)

				return func

			def moveToTrash(
				group: EventGroupType, event: EventType
			) -> Callable[[gtk.Widget], None]:
				def func(w: gtk.Widget) -> None:
					self.moveEventToTrash(w, group, event)

				return func

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
							func=editEvent(event, gid),
						),
					)
				# --
				winTitle = _("Edit") + " " + group.desc
				menu.add(
					ImageMenuItem(
						winTitle,
						imageName="document-edit.svg",
						func=editGroup(group),
					),
				)
				# --
				menu.add(gtk.SeparatorMenuItem())
				# --
				menu.add(
					ImageMenuItem(
						_("Move to {title}").format(title=ev.trash.title),
						imageName=ev.trash.getIconRel(),
						func=moveToTrash(group, event),
					),
				)
				# --
				menu.show_all()
				self.tmpMenu = menu
				menu.popup(None, None, None, None, 3, gevent.time)
		return False

	def motionNotify(self, _w: gtk.Widget, gevent: gdk.EventMotion) -> None:
		if not self.boxEditing:
			return
		editType, event, box, x0, t0 = self.boxEditing
		# print(f"motionNotify: {self.event=}")
		assert isinstance(event, TaskEvent | LifetimeEvent)
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
		if self.pressingButton is not None:
			self.pressingButton.onRelease(gevent)  # type: ignore[misc]
			self.pressingButton = None
		win = self.w.get_window()
		assert win is not None
		win.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		self.w.queue_draw()

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.w.queue_draw()

	def onEditEventClick(
		self,
		_menu: gtk.Widget,
		winTitle: str,
		event: EventType,
		_gid: int,
	) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		window = self.w.get_toplevel()
		assert isinstance(window, gtk.Window)

		eventNew = EventEditorDialog(
			event,
			title=winTitle,
			transient_for=window,
		).run2()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.onConfigChange()

	def onEditGroupClick(
		self,
		_menu: gtk.Widget,
		_winTitle: str,
		group: EventGroupType,
	) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		window = self.w.get_toplevel()
		assert isinstance(window, gtk.Window)

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

	def moveEventToTrash(
		self,
		_menu: gtk.Widget,
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
		assert isinstance(win, gtk.Window)
		win.begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
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
		self.movingUserEvent(
			direction=1,
			source="keyboard",
			smallForce=bool(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveLeft(self, gevent: gdk.EventKey) -> None:
		self.movingUserEvent(
			direction=-1,
			source="keyboard",
			smallForce=bool(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveStop(self, _ge: gdk.EventKey) -> None:
		self.stopMovingAnim()

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

	def movingUserEvent(
		self,
		direction: int = 1,
		smallForce: bool = False,
		source: str = "keyboard",
	) -> None:
		"""Source in ("keyboard", "scroll", "button")."""
		if conf.enableAnimation.v:
			tm = perf_counter()
			# dtEvent = tm - self.movingLastPress
			self.movingLastPress = tm
			"""
				We should call a new updateMovingAnim if:
					last key press has bin timeout, OR
					force direction has been change, OR
					its currently still (no speed and no force)
			"""
			if (
				self.movingF * direction < 0 or self.movingF * self.movingV == 0
				# or dtEvent > conf.movingKeyTimeout.v
			):
				if source == "scroll":
					force = conf.movingHandForceMouse.v
					if smallForce:
						force = (force + conf.movingFrictionForce.v) / 2.0
				elif source == "keyboard":
					if smallForce:
						force = conf.movingHandForceKeyboardSmall.v
					else:
						force = conf.movingHandForceKeyboard.v
				elif source == "button":
					force = conf.movingHandForceButton.v
				else:
					raise ValueError(f"invalid {source=}")
				self.movingF = direction * force
				self.movingV += conf.movingInitialVelocity.v * direction
				self.stopAnimTimers()
				self.updateMovingAnim(
					self.movingF,
					tm,
					tm,
					self.movingV,
					self.movingF,
				)
		else:
			self.timeStart += (
				direction
				* (
					conf.movingStaticStepMouse.v
					if source == "mouse"
					else conf.movingStaticStepKeyboard.v
				)
				* self.timeWidth
				/ self.w.get_allocation().width
			)

	def stopAnimTimers(self) -> None:
		if self.animTimerSource is None:
			return
		if not self.animTimerSource.is_destroyed():
			source_remove(self.animTimerSource.get_id())
		self.animTimerSource = None
		# .is_destroyed() is checked to get rid of this warning:
		# Warning: Source ID {id} was not found when attempting to remove it

	def startAnimConstantAccel(self, direction: int, force: float) -> None:
		if self.movingV != 0:
			self.stopAnimTimers()
		self.movingF = direction * force
		if self.movingV == 0:
			self.movingV = conf.movingInitialVelocity.v * direction
		tm = perf_counter()
		self.updateMovingAnim(
			self.movingF,  # f1
			tm,  # t0
			tm,  # t1
			self.movingV,  # v0
			force - conf.movingFrictionForce.v,  # a1
			holdForce=True,
		)

	def updateMovingAnim(
		self,
		f1: float,  # force
		t0: float,  # perf_counter time
		t1: float,  # perf_counter time
		v0: float,  # speed
		a1: float,  # acceleration
		holdForce: bool = False,
	) -> None:
		# log.debug(f"updateMovingAnim: {f1=:.1f}, {v0=:.1f}, {a1=:.1f}")
		t2 = perf_counter()
		f = self.movingF
		if not holdForce and f != f1:
			# log.debug("Stopping movement: f != f1")
			return
		v1 = self.movingV
		if f == v1 == 0:
			return
		timeout = (
			conf.movingKeyTimeoutFirst.v
			if t2 - t0 < conf.movingKeyTimeoutFirst.v
			else conf.movingKeyTimeout.v
		)
		if not holdForce and f != 0 and t2 - self.movingLastPress >= timeout:
			# Stopping
			# log.debug("Stopping force")
			f = self.movingF = 0
		if v1 > 0:
			a2 = f - conf.movingFrictionForce.v
		elif v1 < 0:
			a2 = f + conf.movingFrictionForce.v
		else:
			a2 = f
		if a2 != a1:
			return self.updateMovingAnim(
				f,
				t2,
				t2,
				v1,
				a2,
				holdForce=holdForce,
			)
		v2 = v0 + a2 * (t2 - t0)
		if v2 > conf.movingMaxVelocity.v:
			v2 = conf.movingMaxVelocity.v
		elif v2 < -conf.movingMaxVelocity.v:
			v2 = -conf.movingMaxVelocity.v
		if f == 0 and v1 * v2 <= 0:
			# log.debug("Stopping movement: f == 0 and v1 * v2 <= 0")
			self.movingV = 0
			return
		source_id = timeout_add(
			conf.movingUpdateTime.v,
			self.updateMovingAnim,
			f,
			t0,
			t2,
			v0,
			a2,
			holdForce,
		)
		self.animTimerSource = main_context_default().find_source_by_id(source_id)
		self.movingV = v2
		self.timeStart += (
			v2 * (t2 - t1) * self.timeWidth / self.w.get_allocation().width
		)
		self.w.queue_draw()
		return

	def stopMovingAnim(self) -> None:
		# stop moving immudiatly
		self.movingF = 0
		self.movingV = 0


class TimeLineWindow(CalObjWidget):
	objName = "timeLineWin"
	desc = _("Time Line")

	def __init__(self) -> None:
		win = gtk.Window()
		self.w: gtk.Window = win
		self.initVars()
		ud.windowList.appendItem(self)
		# ---
		win.resize(ud.workAreaW, 150)
		win.move(0, 0)
		win.set_title(_("Time Line"))
		win.set_decorated(False)
		win.connect("delete-event", self.onDeleteEvent)
		win.connect("button-press-event", self.onButtonPress)
		self.tline = TimeLine(self.onCloseClick)
		win.connect("key-press-event", self.tline.onKeyPress)
		win.add(self.tline.w)
		self.tline.show()
		self.appendItem(self.tline)

	def showDayInWeek(self, jd: int) -> None:
		self.tline.showDayInWeek(jd)

	def onDeleteEvent(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> bool:
		if ui.mainWin:
			self.hide()
		else:
			gtk.main_quit()  # FIXME
		return True

	def onCloseClick(self) -> None:
		if ui.mainWin:
			self.hide()
		else:
			gtk.main_quit()  # FIXME

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button == 1:
			self.w.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
			return True
		return False


if __name__ == "__main__":
	win = TimeLineWindow()
	# win.tline.timeWidth = 100 * minYearLenSec  # 2 * 10**17
	# win.tline.timeStart = now() - win.tline.timeWidth  # -10**17
	win.show()
	gtk.main()
