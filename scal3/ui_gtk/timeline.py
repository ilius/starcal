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

import time
from time import time as now

from datetime import datetime, timedelta

import math
from math import pi

from scal3.utils import iceil
from scal3.time_utils import (
	getUtcOffsetByJd,
	getUtcOffsetByEpoch,
	getJdFromEpoch,
	getEpochFromJd,
)
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3.locale_man import localTz
from scal3 import ui

from scal3.timeline import tl
from scal3.timeline.utils import *
from scal3.timeline.funcs import (
	calcTimeLineData,
)

from scal3.ui_gtk import *

from gi.repository.PangoCairo import show_layout

from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
from scal3.ui_gtk.drawing import (
	setColor,
	fillColor,
	newTextLayout,
)
from scal3.ui_gtk.button_drawing import SVGButton
from scal3.ui_gtk.utils import openWindow
from scal3.ui_gtk import gtk_ud as ud

from scal3.ui_gtk.timeline_box import (
	drawBoxBG,
	drawBoxBorder,
	drawBoxText,
)

import scal3.ui_gtk.event.manager

# FIXME: rewove this
from scal3.ui_gtk.timeline_prefs import TimeLinePreferencesWindow


def show_event(widget, gevent):
	log.info(
		type(widget),
		gevent.type.value_name,
		gevent.get_value(),
	)  # gevent.send_event


@registerSignals
class TimeLine(gtk.DrawingArea, ud.BaseCalObj):
	_name = "timeLine"
	desc = _("Time Line")

	def centerToNow(self):
		self.stopMovingAnim()
		self.timeStart = now() - self.timeWidth / 2.0

	def showDayInWeek(self, jd):
		timeCenter = getEpochFromJd(jd) + dayLen / 2
		timeWidth = 7 * dayLen
		self.timeStart = timeCenter - timeWidth / 2
		self.timeWidth = timeWidth
		self.queue_draw()

	def onCenterToNowClick(self, arg=None):
		self.centerToNow()
		self.queue_draw()

	def onDateChange(self, *a, **kw):
		ud.BaseCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def __init__(self, closeFunc):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		self.prefWindow = None
		###
		self.closeFunc = closeFunc
		###
		self.keysActionDict = {
			"moveToNow": self.onKeyMoveToNow,
			"moveRight": self.onKeyMoveRight,
			"moveLeft": self.onKeyMoveLeft,
			"moveStop": self.onKeyMoveStop,
			"close": self.onKeyClose,
			"zoomIn": self.onKeyZoomIn,
			"zoomOut": self.onKeyZoomOut,
		}
		###
		self.connect("draw", self.onExposeEvent)
		self.connect("scroll-event", self.onScroll)
		self.connect("button-press-event", self.onButtonPress)
		self.connect("motion-notify-event", self.motionNotify)
		self.connect("button-release-event", self.buttonRelease)
		self.connect("key-press-event", self.onKeyPress)
		# self.connect("event", show_event)
		self.currentTime = now()
		self.timeWidth = dayLen
		self.timeStart = self.currentTime - self.timeWidth / 2.0
		self.updateBasicButtons()
		self.updateMovementButtons()
		# zoom in and zoom out buttons FIXME
		self.data = None
		########
		self.movingLastPress = 0
		self.movingV = 0
		self.movingF = 0
		#######
		self.boxEditing = None
		# boxEditing: None or tuple of (editType, box, x0, t0)
		# editType=0   moving
		# editType=-1  resizing to left
		# editType=+1  resizing to right

		self.pressingButton = None

		self._lastScrollDir = ""
		self._lastScrollTime = None

		self.timeUpdateSourceId = None
		self.animTimerSource = None

	def updateBasicButtons(self):
		size = tl.basicButtonsSize
		space = size + tl.basicButtonsSpacing
		self.basicButtons = [
			SVGButton(
				imageName="go-home.svg",
				onPress=self.onCenterToNowClick,
				x=1,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=tl.basicButtonsOpacity,
			),
			SVGButton(
				imageName="zoom-question.svg",
				onPress=self.zoomMenuOpen,
				x=1 + space,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=tl.basicButtonsOpacity,
			),
			SVGButton(
				imageName="preferences-system.svg",
				onPress=self.openPreferences,
				x=1 + space * 2,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=tl.basicButtonsOpacity,
			),
			SVGButton(
				imageName="application-exit.svg",
				onPress=self.closeFunc,
				x=1 + space * 3,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="left",
				yalign="buttom",
				opacity=tl.basicButtonsOpacity,
			),
			SVGButton(
				imageName="resize-small.svg",
				# equivalent of "sw-resize"
				onPress=self.startResize,
				x=1,
				y=1,
				autoDir=False,
				iconSize=size,
				xalign="right",
				yalign="buttom",
				opacity=tl.basicButtonsOpacity,
			),
		]

	def updateMovementButtons(self):
		if not tl.movementButtonsEnable:
			self.movementButtons = []
			return

		size = tl.movementButtonsSize
		self.movementButtons = [
			SVGButton(
				imageName="go-previous.svg",
				onPress=self.onMoveLeftClick,
				x=- size * 1.5,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=tl.movementButtonsOpacity,
				onRelease=self.arrowButtonReleased,
			),
			SVGButton(
				imageName="process-stop.svg",
				onPress=self.onMoveStopClick,
				x=0,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=tl.movementButtonsOpacity,
			),
			SVGButton(
				imageName="go-next.svg",
				onPress=self.onMoveRightClick,
				x=size * 1.5,
				y=0,
				autoDir=False,
				iconSize=size,
				xalign="center",
				yalign="buttom",
				opacity=tl.movementButtonsOpacity,
				onRelease=self.arrowButtonReleased,
			),
		]

	def getButtons(self):
		return self.basicButtons + self.movementButtons

	def onMoveLeftClick(self, button: gdk.EventButton):
		self.startAnimConstantAccel(-1, tl.movingHandForceButton)
		# FIXME: what if animation is disabled?

	def onMoveRightClick(self, button: gdk.EventButton):
		self.startAnimConstantAccel(1, tl.movingHandForceButton)
		# FIXME: what if animation is disabled?

	def onMoveStopClick(self, button: gdk.EventButton):
		self.stopMovingAnim()

	def arrowButtonReleased(self):
		self.movingF = 0
		# ^ this will only make it stop slowly (by friction force)
		# if you want it to stop movement, set: self.movingV = 0
		# just like self.stopMovingAnim

	def onZoomMenuItemClick(self, item, timeWidth):
		timeCenter = self.timeStart + self.timeWidth / 2
		self.timeStart = timeCenter - timeWidth / 2
		self.timeWidth = timeWidth
		self.queue_draw()

	def zoomMenuOpen(self, button: gdk.EventButton):
		avgYearLen = dayLen * calTypes.primaryModule().avgYearLen
		etime = gtk.get_current_event_time()
		menu = Menu()
		for title, timeWidth in [
			(_("1 day"), dayLen),
			(_("1 week"), dayLen * 7),
			(_("{count} weeks").format(count=_(4)), dayLen * 28),
			(_("1 year"), avgYearLen),
		] + [
			(_("{count} years").format(count=_(num)), avgYearLen * num)
			for num in (2, 4, 8, 16, 32, 64, 100)
		]:
			menu.add(ImageMenuItem(
				title,
				func=self.onZoomMenuItemClick,
				args=(timeWidth,),
			))
		menu.show_all()
		menu.popup(
			None,
			None,
			None,  # lambda *args: (x, y, True),
			None,
			3,
			etime,
		)

	def openPreferences(self, arg=None):
		from scal3.ui_gtk.timeline_prefs import TimeLinePreferencesWindow
		if self.prefWindow is None:
			self.prefWindow = TimeLinePreferencesWindow(self)
		openWindow(self.prefWindow)

	def currentTimeUpdate(self, restart=False, draw=True):
		if restart:
			if self.timeUpdateSourceId is not None:
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
		if draw and self.get_parent():
			if (
				self.get_parent().get_visible() and
				self.timeStart <= tm <= self.timeStart + self.timeWidth + 1
			):
				# log.debug(f"{tm%100:.2f} currentTimeUpdate: DRAW")
				self.queue_draw()

	def updateData(self):
		width = self.get_allocation().width
		self.pixelPerSec = width / self.timeWidth  # pixel/second
		self.borderTm = tl.boxEditBorderWidth / self.pixelPerSec  # second
		self.data = calcTimeLineData(
			self.timeStart,
			self.timeWidth,
			self.pixelPerSec,
			self.borderTm,
		)

	def drawTick(self, cr, tick, maxTickHeight):
		tickH = tick.height
		tickW = tick.width
		tickH = min(tickH, maxTickHeight)
		###
		tickX = tick.pos - tickW / 2.0
		tickY = 1
		cr.rectangle(tickX, tickY, tickW, tickH)
		fillColor(cr, tick.color)
		# fillColor never seems to raise exception anymore (in Gtk3)
		###
		font = ui.Font(
			fontFamily,
			False,
			False,
			tick.fontSize,
		)
		# layout = newLimitedWidthTextLayout(
		# 	self,
		# 	tick.label,
		# 	tick.maxLabelWidth,
		# 	font=font,
		# 	truncate=truncateTickLabel,
		# )  # FIXME
		layout = newTextLayout(
			self,
			text=tick.label,
			font=font,
			maxSize=(tick.maxLabelWidth, 0),
			maximizeScale=1.0,
			truncate=tl.truncateTickLabel,
		)  # FIXME
		if layout:
			# layout.set_auto_dir(0)  # FIXME
			# log.debug(f"{layout.get_auto_dir() = }")
			layoutW, layoutH = layout.get_pixel_size()
			layoutX = tick.pos - layoutW / 2.0
			layoutY = tickH * tl.labelYRatio
			cr.move_to(layoutX, layoutY)
			# cr.move_to never seems to raise exception anymore
			show_layout(cr, layout)  # with the same tick.color

	def drawBox(self, cr, box):
		d = box.lineW
		x = box.x
		w = box.w
		y = box.y
		h = box.h
		###
		drawBoxBG(cr, box, x, y, w, h)
		drawBoxBorder(cr, box, x, y, w, h)
		drawBoxText(cr, box, x, y, w, h, self)

	def drawBoxEditingHelperLines(self, cr):
		if not self.boxEditing:
			return
		editType, event, box, x0, t0 = self.boxEditing
		setColor(cr, tl.fgColor)
		d = tl.boxEditHelperLineWidth
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

	def drawAll(self, cr):
		timeStart = self.timeStart
		timeWidth = self.timeWidth
		timeEnd = timeStart + timeWidth
		####
		width = self.get_allocation().width
		height = self.get_allocation().height
		pixelPerSec = self.pixelPerSec
		dayPixel = dayLen * pixelPerSec  # pixel
		maxTickHeight = tl.maxTickHeightRatio * height
		#####
		cr.rectangle(0, 0, width, height)
		fillColor(cr, tl.bgColor)
		#####
		setColor(cr, tl.holidayBgBolor)
		for x in self.data["holidays"]:
			cr.rectangle(x, 0, dayPixel, height)
			cr.fill()
		#####
		for tick in self.data["ticks"]:
			self.drawTick(cr, tick, maxTickHeight)
		######
		beforeBoxH = maxTickHeight  # FIXME
		maxBoxH = height - beforeBoxH
		for box in self.data["boxes"]:
			box.setPixelValues(timeStart, pixelPerSec, beforeBoxH, maxBoxH)
			self.drawBox(cr, box)
		self.drawBoxEditingHelperLines(cr)
		# #### Show (possible) Daylight Saving change
		if timeStart > 0 and 2 * 3600 < timeWidth < 30 * dayLen:
			if getUtcOffsetByEpoch(timeStart) != getUtcOffsetByEpoch(timeEnd):
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
					deltaHour = deltaSec / 3600.0
					dstChangeEpoch = getEpochFromJd(dstChangeJd)
					# log.debug(f"{dstChangeEpoch = }")
				else:
					log.info("dstChangeEpoch not found")

		# #### Draw Current Time Marker
		dt = self.currentTime - timeStart
		if 0 <= dt <= timeWidth:
			setColor(cr, tl.currentTimeMarkerColor)
			cr.rectangle(
				dt * pixelPerSec - tl.currentTimeMarkerWidth / 2.0,
				0,
				tl.currentTimeMarkerWidth,
				tl.currentTimeMarkerHeightRatio * self.get_allocation().height
			)
			cr.fill()
		######
		for button in self.getButtons():
			button.draw(cr, width, height, bgColor=tl.bgColor)

	def onExposeEvent(self, widget=None, event=None):
		win = self.get_window()
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

	def drawWithContext(self, cr: "cairo.Context"):
		# t0 = now()
		if not self.boxEditing:
			self.updateData()
			self.currentTimeUpdate(restart=True, draw=False)
		# t1 = now()
		self.drawAll(cr)
		# t2 = now()
		# log.debug(f"drawing time / data calc time: {(t2-t1)/(t1-t0):.2f}")

	def getLastScrollDir(self) -> "":
		"""
			returns "up", "down" or ""
		"""
		if not self._lastScrollDir:
			return ""

		if self._lastScrollTime is None:
			return ""

		if datetime.now() - self._lastScrollTime > timedelta(seconds=2):
			return ""

	def onScroll(self, widget, gevent):
		smallForce = False
		if gevent.is_scroll_stop_event():  # or gevent.is_stop == 1
			smallForce = True
			# self._lastScrollDir = ""
			# self.stopMovingAnim()
			# return
		dirStr = getScrollValue(gevent, last=self.getLastScrollDir())
		if not dirStr:
			return
		self._lastScrollDir = dirStr
		self._lastScrollTime = datetime.now()
		if gevent.get_state() & gdk.ModifierType.CONTROL_MASK:
			self.zoom(
				dirStr == "up",
				tl.scrollZoomStep,
				gevent.x / self.get_allocation().width,
			)
		else:
			self.movingUserEvent(
				direction=(-1 if dirStr == "up" else 1),
				source="scroll",
				smallForce=smallForce,
			)
		self.queue_draw()
		return True

	def onButtonPress(self, obj, gevent):
		if self.pressingButton is not None:
			self.pressingButton.onRelease()
			self.pressingButton = None
		x = gevent.x
		y = gevent.y
		w = self.get_allocation().width
		h = self.get_allocation().height
		if gevent.button == 1:
			for button in self.getButtons():
				if button.contains(x, y, w, h):
					button.onPress(gevent)
					if button.onRelease is not None:
						self.pressingButton = button
					return True
			####
			for box in self.data["boxes"]:
				if not box.hasBorder:
					continue
				if not box.ids:
					continue
				if not box.contains(x, y):
					continue
				gid, eid = box.ids
				group = ui.eventGroups[gid]
				event = group[eid]
				####
				top = y - box.y
				left = x - box.x
				right = box.x + box.w - x
				minA = min(tl.boxEditBorderWidth, top, left, right)
				editType = None
				if top == minA:
					editType = 0
					t0 = event.getStartEpoch()
					self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.FLEUR))
				elif right == minA:
					editType = 1
					t0 = event.getEndEpoch()
					self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.RIGHT_SIDE))
				elif left == minA:
					editType = -1
					t0 = event.getStartEpoch()
					self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_SIDE))
				if editType is not None:
					self.boxEditing = (editType, event, box, x, t0)
					self.queue_draw()
					return True
		elif gevent.button == 3:
			for box in self.data["boxes"]:
				if not box.ids:
					continue
				if not box.contains(x, y):
					continue
				gid, eid = box.ids
				group = ui.eventGroups[gid]
				event = group[eid]
				####
				menu = Menu()
				##
				if not event.readOnly:
					winTitle = _("Edit") + " " + event.desc
					menu.add(ImageMenuItem(
						winTitle,
						imageName="document-edit.svg",
						func=self.onEditEventClick,
						args=(
							winTitle,
							event,
							gid,
						),
					))
				##
				winTitle = _("Edit") + " " + group.desc
				menu.add(ImageMenuItem(
					winTitle,
					imageName="document-edit.svg",
					func=self.onEditGroupClick,
					args=(
						winTitle,
						group,
					),
				))
				##
				menu.add(gtk.SeparatorMenuItem())
				##
				menu.add(ImageMenuItem(
					_("Move to {title}").format(title=ui.eventTrash.title),
					imageName=ui.eventTrash.getIconRel(),
					func=self.moveEventToTrash,
					args=(
						group,
						event,
					),
				))
				##
				menu.show_all()
				self.tmpMenu = menu
				menu.popup(None, None, None, None, 3, gevent.time)
		return False

	def motionNotify(self, obj, gevent):
		if self.boxEditing:
			editType, event, box, x0, t0 = self.boxEditing
			t1 = t0 + (gevent.x - x0) / self.pixelPerSec
			if editType == 0:
				event.modifyPos(t1)
			elif editType == 1:
				if t1 - box.t0 > 2 * tl.boxEditBorderWidth / self.pixelPerSec:
					event.modifyEnd(t1)
			elif editType == -1:
				if box.t1 - t1 > 2 * tl.boxEditBorderWidth / self.pixelPerSec:
					event.modifyStart(t1)
			box.t0 = max(
				event.getStartEpoch(),
				self.timeStart - self.borderTm,
			)
			box.t1 = min(
				event.getEndEpoch(),
				self.timeStart + self.timeWidth + self.borderTm,
			)
			self.queue_draw()

	def buttonRelease(self, obj, gevent):
		if self.boxEditing:
			editType, event, box, x0, t0 = self.boxEditing
			event.afterModify()
			event.save()
			self.boxEditing = None
		if self.pressingButton is not None:
			self.pressingButton.onRelease()
			self.pressingButton = None
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		self.queue_draw()

	def onEditEventClick(self, menu, winTitle, event, gid):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		event = EventEditorDialog(
			event,
			title=winTitle,
			transient_for=self.get_toplevel(),
		).run()
		if event is None:
			return
		ui.eventUpdateQueue.put("e", event, self)
		self.onConfigChange()

	def onEditGroupClick(self, menu, winTitle, group):
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog
		group = GroupEditorDialog(
			group,
			transient_for=self.get_toplevel(),
		).run()
		if group is not None:
			group.afterModify()
			group.save()  # FIXME
			ui.eventUpdateQueue.put("eg", group, self)
			self.onConfigChange()
			self.queue_draw()

	def moveEventToTrash(self, menu, group, event):
		from scal3.ui_gtk.event.utils import confirmEventTrash
		if not confirmEventTrash(event):
			return
		eventIndex = group.index(event.id)
		ui.moveEventToTrash(group, event, self)
		self.onConfigChange()

	def startResize(self, gevent):
		self.get_parent().begin_resize_drag(
			gdk.WindowEdge.SOUTH_EAST,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)

	def zoom(self, zoomIn, stepFact, posFact):
		zoomValue = 1.0 / stepFact if zoomIn else stepFact
		self.timeStart += self.timeWidth * (1 - zoomValue) * posFact
		self.timeWidth *= zoomValue

	def keyboardZoom(self, zoomIn):
		self.zoom(zoomIn, tl.keyboardZoomStep, 0.5)

	def onKeyMoveToNow(self, gevent: gdk.EventKey):
		self.centerToNow()

	def onKeyMoveRight(self, gevent: gdk.EventKey):
		self.movingUserEvent(
			direction=1,  # noqa: FURB120
			source="keyboard",  # noqa: FURB120
			smallForce=(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveLeft(self, gevent: gdk.EventKey):
		self.movingUserEvent(
			direction=-1,  # noqa: FURB120
			source="keyboard",  # noqa: FURB120
			smallForce=(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
		)

	def onKeyMoveStop(self, gevent: gdk.EventKey):
		self.stopMovingAnim()

	def onKeyClose(self, gevent: gdk.EventKey):
		self.closeFunc()

	def onKeyZoomIn(self, gevent: gdk.EventKey):
		self.keyboardZoom(True)

	def onKeyZoomOut(self, gevent: gdk.EventKey):
		self.keyboardZoom(False)

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		k = gdk.keyval_name(gevent.keyval).lower()
		# log.debug(f"{now():.3f}")
		action = tl.keys.get(k)
		if action:
			func = self.keysActionDict.get(action)
			if func is not None:
				func(gevent)
				self.queue_draw()
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

	def movingUserEvent(self, direction=1, smallForce=False, source="keyboard"):
		"""
			source in ("keyboard", "scroll", "button")
		"""
		if tl.enableAnimation:
			tm = now()
			# dtEvent = tm - self.movingLastPress
			self.movingLastPress = tm
			"""
				We should call a new updateMovingAnim if:
					last key press has bin timeout, OR
					force direction has been change, OR
					its currently still (no speed and no force)
			"""
			if (
				self.movingF * direction < 0
				or self.movingF * self.movingV == 0
				# or dtEvent > tl.movingKeyTimeout
			):
				if source == "scroll":
					force = tl.movingHandForceMouse
					if smallForce:
						force = (force + tl.movingFrictionForce) / 2.0
				elif source == "keyboard":
					if smallForce:
						force = tl.movingHandForceKeyboardSmall
					else:
						force = tl.movingHandForceKeyboard
				elif source == "button":
					force = tl.movingHandForceButton
				else:
					raise ValueError(f"invalid {source=}")
				self.movingF = direction * force
				self.movingV += tl.movingInitialVelocity * direction
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
					tl.movingStaticStepMouse if source == "mouse"
					else tl.movingStaticStepKeyboard
				)
				* self.timeWidth
				/ self.get_allocation().width
			)

	def stopAnimTimers(self):
		if self.animTimerSource is None:
			return
		if not self.animTimerSource.is_destroyed():
			source_remove(self.animTimerSource.get_id())
		self.animTimerSource = None
		# .is_destroyed() is checked to get rid of this warning:
		# Warning: Source ID {id} was not found when attempting to remove it

	def startAnimConstantAccel(self, direction, force):
		if self.movingV != 0:
			self.stopAnimTimers()
		self.movingF = direction * force
		if self.movingV == 0:
			self.movingV = tl.movingInitialVelocity * direction
		tm = now()
		self.updateMovingAnim(
			self.movingF,  # f1
			tm,  # t0
			tm,  # t1
			self.movingV,  # v0
			force - tl.movingFrictionForce,  # a1
			holdForce=True,
		)

	def updateMovingAnim(self, f1, t0, t1, v0, a1, holdForce=False):
		# log.debug(f"updateMovingAnim: {f1=:.1f}, {v0=:.1f}, {a1=:.1f}")
		t2 = now()
		f = self.movingF
		if not holdForce and f != f1:
			# log.debug("Stopping movement: f != f1")
			return
		v1 = self.movingV
		if f == v1 == 0:
			return
		timeout = (
			tl.movingKeyTimeoutFirst
			if t2 - t0 < tl.movingKeyTimeoutFirst
			else tl.movingKeyTimeout
		)
		if not holdForce and f != 0 and t2 - self.movingLastPress >= timeout:
			# Stopping
			# log.debug("Stopping force")
			f = self.movingF = 0
		if v1 > 0:
			a2 = f - tl.movingFrictionForce
		elif v1 < 0:
			a2 = f + tl.movingFrictionForce
		else:
			a2 = f
		if a2 != a1:
			return self.updateMovingAnim(
				f, t2, t2, v1, a2,
				holdForce=holdForce,
			)
		v2 = v0 + a2 * (t2 - t0)
		if v2 > tl.movingMaxVelocity:
			v2 = tl.movingMaxVelocity
		elif v2 < -tl.movingMaxVelocity:
			v2 = -tl.movingMaxVelocity
		if f == 0 and v1 * v2 <= 0:
			# log.debug("Stopping movement: f == 0 and v1 * v2 <= 0")
			self.movingV = 0
			return
		source_id = timeout_add(
			tl.movingUpdateTime,
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
			v2
			* (t2 - t1)
			* self.timeWidth
			/ self.get_allocation().width
		)
		self.queue_draw()

	def stopMovingAnim(self):
		# stop moving immudiatly
		self.movingF = 0
		self.movingV = 0


@registerSignals
class TimeLineWindow(gtk.Window, ud.BaseCalObj):
	_name = "timeLineWin"
	desc = _("Time Line")

	def __init__(self):
		gtk.Window.__init__(self)
		self.initVars()
		ud.windowList.appendItem(self)
		###
		self.resize(ud.workAreaW, 150)
		self.move(0, 0)
		self.set_title(_("Time Line"))
		self.set_decorated(False)
		self.connect("delete-event", self.onCloseClick)
		self.connect("button-press-event", self.onButtonPress)
		self.tline = TimeLine(self.onCloseClick)
		self.connect("key-press-event", self.tline.onKeyPress)
		self.add(self.tline)
		self.tline.show()
		self.appendItem(self.tline)

	def showDayInWeek(self, jd):
		self.tline.showDayInWeek(jd)

	def onCloseClick(self, arg=None, event=None):
		if ui.mainWin:
			self.hide()
		else:
			gtk.main_quit()  # FIXME
		return True

	def onButtonPress(self, obj, gevent):
		if gevent.button == 1:
			self.begin_move_drag(
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
