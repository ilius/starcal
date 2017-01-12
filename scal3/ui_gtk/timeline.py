#!/usr/bin/python
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

import time
from time import time as now

import math
from math import pi

from scal3.utils import iceil
from scal3.time_utils import getUtcOffsetByJd
from scal3 import core
from scal3.core import myRaise
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3.locale_man import localTz
from scal3 import ui
from scal3.timeline import *

from gi.repository.GObject import timeout_add
from gi.repository.GLib import source_remove

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.ui_gtk.utils import labelStockMenuItem, labelImageMenuItem
from scal3.ui_gtk.drawing import setColor, fillColor, newTextLayout, Button
from scal3.ui_gtk import gtk_ud as ud
#from scal3.ui_gtk import preferences
from scal3.ui_gtk.timeline_box import *

import scal3.ui_gtk.event.manager


def show_event(widget, gevent):
	print(
		type(widget),
		gevent.type.value_name,
		gevent.get_value(),
	)  # gevent.send_event


@registerSignals
class TimeLine(gtk.DrawingArea, ud.BaseCalObj):
	_name = 'timeLine'
	desc = _('Time Line')

	def centerToNow(self):
		self.stopMovingAnim()
		self.timeStart = now() - self.timeWidth / 2.0

	def centerToNowClicked(self, arg=None):
		self.centerToNow()
		self.queue_draw()

	def __init__(self, closeFunc):
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initVars()
		###
		self.closeFunc = closeFunc
		self.connect('draw', self.onExposeEvent)
		self.connect('scroll-event', self.onScroll)
		self.connect('button-press-event', self.buttonPress)
		self.connect('motion-notify-event', self.motionNotify)
		self.connect('button-release-event', self.buttonRelease)
		self.connect('key-press-event', self.keyPress)
		#self.connect('event', show_event)
		self.currentTime = now()
		self.timeWidth = dayLen
		self.timeStart = self.currentTime - self.timeWidth / 2.0
		self.buttons = [
			Button('home.png', self.centerToNowClicked, 1, -1, False),
			Button('resize-small.png', self.startResize, -1, -1, False),
			Button('exit.png', closeFunc, 35, -1, False)
		]
		# zoom in and zoom out buttons FIXME
		self.data = None
		########
		self.movingLastPress = 0
		self.movingV = 0
		self.movingF = 0
		#######
		self.boxEditing = None
		## or (editType, box, x0, t0)
		## editType=0   moving
		## editType=-1  resizing to left
		## editType=+1  resizing to right

	def currentTimeUpdate(self, restart=False, draw=True):
		if restart:
			try:
				source_remove(self.timeUpdateSourceId)
			except AttributeError:
				pass
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
				#print('%.2f'%(tm%100), 'currentTimeUpdate: DRAW')
				self.queue_draw()

	def updateData(self):
		width = self.get_allocation().width
		self.pixelPerSec = float(width) / self.timeWidth  # pixel/second
		self.borderTm = boxMoveBorder / self.pixelPerSec  # second
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
		try:
			fillColor(cr, tick.color)
		except:
			print(
				'error in fill' +
				', x=%.2f, y=%.2f' % (tickX, tickY) +
				', w=%.2f, h=%.2f' % (tickW, tickH)
			)
		###
		font = [
			fontFamily,
			False,
			False,
			tick.fontSize,
		]
		#layout = newLimitedWidthTextLayout(
		#	self,
		#	tick.label,
		#	tick.maxLabelWidth,
		#	font=font,
		#	truncate=truncateTickLabel,
		#)  # FIXME
		layout = newTextLayout(
			self,
			text=tick.label,
			font=font,
			maxSize=(tick.maxLabelWidth, 0),
			maximizeScale=1.0,
			truncate=truncateTickLabel,
		)  # FIXME
		if layout:
			#layout.set_auto_dir(0)  # FIXME
			#print('layout.get_auto_dir() = %s'%layout.get_auto_dir())
			layoutW, layoutH = layout.get_pixel_size()
			layoutX = tick.pos - layoutW / 2.0
			layoutY = tickH * labelYRatio
			try:
				cr.move_to(layoutX, layoutY)
			except:
				print('error in move_to, x=%.2f, y=%.2f' % (layoutX, layoutY))
			else:
				show_layout(cr, layout)## with the same tick.color

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
		setColor(cr, fgColor)
		d = editingBoxHelperLineWidth
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
		dayPixel = dayLen * pixelPerSec ## pixel
		maxTickHeight = maxTickHeightRatio * height
		#####
		cr.rectangle(0, 0, width, height)
		fillColor(cr, bgColor)
		#####
		setColor(cr, holidayBgBolor)
		for x in self.data['holidays']:
			cr.rectangle(x, 0, dayPixel, height)
			cr.fill()
		#####
		for tick in self.data['ticks']:
			self.drawTick(cr, tick, maxTickHeight)
		######
		beforeBoxH = maxTickHeight ## FIXME
		maxBoxH = height - beforeBoxH
		for box in self.data['boxes']:
			box.setPixelValues(timeStart, pixelPerSec, beforeBoxH, maxBoxH)
			self.drawBox(cr, box)
		self.drawBoxEditingHelperLines(cr)
		###### Show (possible) Daylight Saving change
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
					#print('dstChangeEpoch = %s' % dstChangeEpoch)
				else:
					print('dstChangeEpoch not found')

		###### Draw Current Time Marker
		dt = self.currentTime - timeStart
		if 0 <= dt <= timeWidth:
			setColor(cr, currentTimeMarkerColor)
			cr.rectangle(
				dt * pixelPerSec - currentTimeMarkerWidth / 2.0,
				0,
				currentTimeMarkerWidth,
				currentTimeMarkerHeightRatio * self.get_allocation().height
			)
			cr.fill()
		######
		for button in self.buttons:
			button.draw(cr, width, height)

	def onExposeEvent(self, widget=None, event=None):
		#t0 = now()
		if not self.boxEditing:
			self.updateData()
			self.currentTimeUpdate(restart=True, draw=False)
		#t1 = now()
		self.drawAll(self.get_window().cairo_create())
		#t2 = now()
		#print('drawing time / data calc time: %.2f'%((t2-t1)/(t1-t0)))

	def onScroll(self, widget, gevent):
		d = getScrollValue(gevent)
		#print('onScroll', d)
		if gevent.get_state() & gdk.ModifierType.CONTROL_MASK:
			self.zoom(
				d == 'up',
				scrollZoomStep,
				float(gevent.x) / self.get_allocation().width,
			)
		else:
			self.movingUserEvent(
				direction=(-1 if d == 'up' else 1),
			)  # FIXME
		self.queue_draw()
		return True

	def buttonPress(self, obj, gevent):
		x = gevent.x
		y = gevent.y
		w = self.get_allocation().width
		h = self.get_allocation().height
		if gevent.button == 1:
			for button in self.buttons:
				if button.contains(x, y, w, h):
					button.func(gevent)
					return True
			####
			for box in self.data['boxes']:
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
				minA = min(boxMoveBorder, top, left, right)
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
					return True
		elif gevent.button == 3:
			for box in self.data['boxes']:
				if not box.ids:
					continue
				if not box.contains(x, y):
					continue
				gid, eid = box.ids
				group = ui.eventGroups[gid]
				event = group[eid]
				####
				menu = gtk.Menu()
				##
				if not event.allReadOnly:
					winTitle = _('Edit') + ' ' + event.desc
					menu.add(labelStockMenuItem(
						winTitle,
						gtk.STOCK_EDIT,
						self.editEventClicked,
						winTitle,
						event,
						gid,
					))
				##
				winTitle = _('Edit') + ' ' + group.desc
				menu.add(labelStockMenuItem(
					winTitle,
					gtk.STOCK_EDIT,
					self.editGroupClicked,
					winTitle,
					group,
				))
				##
				menu.add(gtk.SeparatorMenuItem())
				##
				menu.add(labelImageMenuItem(
					_('Move to %s') % ui.eventTrash.title,
					ui.eventTrash.icon,
					self.moveEventToTrash,
					group,
					event,
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
				if t1 - box.t0 > 2 * boxMoveBorder / self.pixelPerSec:
					event.modifyEnd(t1)
			elif editType == -1:
				if box.t1 - t1 > 2 * boxMoveBorder / self.pixelPerSec:
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
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		self.queue_draw()

	def onConfigChange(self, *a, **kw):
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		self.queue_draw()

	def editEventClicked(self, menu, winTitle, event, gid):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		event = EventEditorDialog(
			event,
			title=winTitle,
			#parent=self,## FIXME
		).run()
		if event is None:
			return
		ui.eventDiff.add('e', event)
		self.onConfigChange()

	def editGroupClicked(self, menu, winTitle, group):
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog
		group = GroupEditorDialog(
			group,
			parent=self.get_toplevel(),
		).run()
		if group is not None:
			group.afterModify()
			group.save()## FIXME
			ui.changedGroups.append(group.id)
			ud.windowList.onConfigChange()
			self.queue_draw()

	def moveEventToTrash(self, menu, group, event):
		from scal3.ui_gtk.event.utils import confirmEventTrash
		if not confirmEventTrash(event):
			return
		eventIndex = group.index(event.id)
		ui.moveEventToTrashFromOutside(group, event)
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
		self.zoom(zoomIn, keyboardZoomStep, 0.5)

	def keyPress(self, arg, gevent):
		k = gdk.keyval_name(gevent.keyval).lower()
		#print('%.3f'%now())
		if k in ('space', 'home'):
			self.centerToNow()
		elif k == 'right':
			self.movingUserEvent(
				direction=1,
				smallForce=(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
			)
		elif k == 'left':
			self.movingUserEvent(
				direction=-1,
				smallForce=(gevent.get_state() & gdk.ModifierType.SHIFT_MASK),
			)
		elif k == 'down':
			self.stopMovingAnim()
		elif k in ('q', 'escape'):
			self.closeFunc()
		#elif k=='end':
		#	pass
		#elif k=='page_up':
		#	pass
		#elif k=='page_down':
		#	pass
		#elif k=='menu':# Simulate right click (key beside Right-Ctrl)
		#	#self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
		#elif k in ('f10','m'): # F10 or m or M
		#	if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
		#		# Simulate right click (key beside Right-Ctrl)
		#		self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
		#	else:
		#		self.emit(
		#		'popup-main-menu',
		#		gevent.time,
		#		*self.getMainMenuPos()
		#	)
		elif k in ('plus', 'equal', 'kp_add'):
			self.keyboardZoom(True)
		elif k in ('minus', 'kp_subtract'):
			self.keyboardZoom(False)
		else:
			#print(k)
			return False
		self.queue_draw()
		return True

	def movingUserEvent(self, direction=1, smallForce=False):
		if enableAnimation:
			tm = now()
			#dtEvent = tm - self.movingLastPress
			self.movingLastPress = tm
			'''
				We should call a new updateMovingAnim if:
					last key press has bin timeout, OR
					force direction has been change, OR
					its currently still (no speed and no force)
			'''
			if (
				self.movingF * direction < 0
				or self.movingF * self.movingV == 0
				#or dtEvent > movingKeyTimeout
			):
				self.movingF = direction * (
					movingHandSmallForce if smallForce
					else movingHandForce
				)
				self.movingV += movingV0 * direction
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
				* movingStaticStep
				* self.timeWidth
				/ self.get_allocation().width
			)

	def updateMovingAnim(self, f1, t0, t1, v0, a1):
		t2 = now()
		f = self.movingF
		if f != f1:
			return
		v1 = self.movingV
		if f == 0 and v1 == 0:
			return
		timeout = (
			movingKeyTimeoutFirst
			if t2 - t0 < movingKeyTimeoutFirst
			else movingKeyTimeout
		)
		if f != 0 and t2 - self.movingLastPress >= timeout:  # Stopping
			f = self.movingF = 0
		if v1 > 0:
			a2 = f - movingFrictionForce
		elif v1 < 0:
			a2 = f + movingFrictionForce
		else:
			a2 = f
		if a2 != a1:
			return self.updateMovingAnim(f, t2, t2, v1, a2)
		v2 = v0 + a2 * (t2 - t0)
		if v2 > movingMaxSpeed:
			v2 = movingMaxSpeed
		elif v2 < -movingMaxSpeed:
			v2 = -movingMaxSpeed
		if f == 0 and v1 * v2 <= 0:
			self.movingV = 0
			return
		timeout_add(
			movingUpdateTime,
			self.updateMovingAnim,
			f,
			t0,
			t2,
			v0,
			a2,
		)
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
	_name = 'timeLineWin'
	desc = _('Time Line')

	def __init__(self):
		gtk.Window.__init__(self)
		self.initVars()
		ud.windowList.appendItem(self)
		###
		self.resize(ud.screenW, 150)
		self.move(0, 0)
		self.set_title(_('Time Line'))
		self.set_decorated(False)
		self.connect('delete-event', self.closeClicked)
		self.connect('button-press-event', self.buttonPress)
		###
		self.tline = TimeLine(self.closeClicked)
		self.connect('key-press-event', self.tline.keyPress)
		self.add(self.tline)
		self.tline.show()
		self.appendItem(self.tline)

	def closeClicked(self, arg=None, event=None):
		if ui.mainWin:
			self.hide()
		else:
			gtk.main_quit()## FIXME
		return True

	def buttonPress(self, obj, gevent):
		if gevent.button == 1:
			self.begin_move_drag(
				gevent.button,
				int(gevent.x_root),
				int(gevent.y_root),
				gevent.time,
			)
			return True
		return False


if __name__ == '__main__':
	win = TimeLineWindow()
	#win.tline.timeWidth = 100 * minYearLenSec # 2 * 10**17
	#win.tline.timeStart = now() - win.tline.timeWidth # -10**17
	win.show()
	gtk.main()
