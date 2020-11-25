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

from scal3 import logger
log = logger.get()

from time import time

from scal3 import core
from scal3 import ui

from gi.repository import cairo
from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk import listener
from scal3.ui_gtk.drawing import newDndDatePixbuf
from scal3.ui_gtk.color_utils import rgbToGdkColor
from scal3.ui_gtk.customize import CustomizableCalObj


class CalBase(CustomizableCalObj):
	dragAndDropEnable = True
	doubleClickEnable = True
	signals = CustomizableCalObj.signals + [
		("popup-cell-menu", [int, int, int]),
		("popup-main-menu", [int, int, int]),
		("double-button-press", []),
		("pref-update-bg-color", []),
		("day-info", []),
	]
	myKeys = (
		"space", "home", "t",
		"menu",
		"i",
	)

	def connect(self, sigName, *a, **ka):
		try:
			CustomizableCalObj.connect(self, sigName, *a, **ka)
		except Exception:
			log.exception(f"sigName={sigName}")

	def initCal(self):
		self.initVars()
		listener.dateChange.add(self)
		####
		if self.dragAndDropEnable:
			self.defineDragAndDrop()
		if self.doubleClickEnable:
			self.connect("double-button-press", ui.dayOpenEvolution)
		if self.win:
			self.connect("popup-cell-menu", self.win.menuCellPopup)
			self.connect("popup-main-menu", self.win.menuMainPopup)
			self.connect("pref-update-bg-color", self.win.prefUpdateBgColor)
			self.connect("day-info", self.win.dayInfoShow)
		###
		self.subPages = None

	def gotoJd(self, jd):
		ui.gotoJd(jd)
		self.onDateChange()

	def goToday(self, obj=None):
		return self.gotoJd(core.getCurrentJd())

	def jdPlus(self, p):
		ui.jdPlus(p)
		self.onDateChange()

	def changeDate(self, year, month, day, calType=None):
		ui.changeDate(year, month, day, calType)
		self.onDateChange()

	def onCurrentDateChange(self, gdate):
		self.queue_draw()

	def getCellPagePlus(self, jd, plus):## use for sliding
		raise NotImplementedError

	def defineDragAndDrop(self):
		self.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			[],
			gdk.DragAction.MOVE,  # FIXME
		)
		self.drag_source_add_text_targets()
		###
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag-begin", self.dragBegin)
		self.connect("drag-data-received", self.dragDataRec)
		###
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			[],
			gdk.DragAction.COPY,  # FIXME
		)
		self.drag_dest_add_text_targets()
		self.drag_dest_add_uri_targets()
		# ACTION_MOVE, FIXME
		# if source ACTION was ACTION_COPY, calendar recieves its own
		# dragged day just like gnome-calendar-applet
		# (but it seems not a logical behaviar)
		#self.drag_source_add_uri_targets()#???????
		##self.connect("drag-end", self.dragCalEnd)
		##self.connect("drag-drop", self.dragCalDrop)
		##self.connect("drag-failed", self.dragCalFailed)
		#self.connect("drag-leave", self.dragLeave)

	def dragDataGet(self, obj, context, selection, target_id, etime):
		# context is instance of gi.repository.Gdk.DragContext
		y, m, d = ui.cell.dates[ui.dragGetCalType]
		text = f"{y:04d}/{m:02d}/{d:02d}"
		selection.set_text(text, len(text))
		#pbuf = newDndDatePixbuf(ui.cell.dates[ui.dragGetCalType])
		#selection.set_pixbuf(pbuf)
		return True

	def dragLeave(self, obj, context, etime):
		context.drop_reply(False, etime)
		return True

	def dragDataRec(self, obj, context, x, y, selection, target_id, etime):
		from scal3.ui_gtk.dnd import processDroppedDate
		dtype = selection.get_data_type()
		# dtype = selection.type, REMOVE
		text = selection.get_text()
		dateM = processDroppedDate(text, dtype)
		if dateM:
			self.changeDate(*dateM)
		elif dtype == "application/x-color":
			# selection.get_text() == None
			text = selection.data
			ui.bgColor = (
				ord(text[1]),
				ord(text[3]),
				ord(text[5]),
				ord(text[7]),
			)
			self.emit("pref-update-bg-color")
			self.queue_draw()
		else:
			log.info(
				f"Unknown dropped data type {dtype!r}, text={text!r}, " +
				f"data={selection.data!r}"
			)
			return True
		return False

	def dragBegin(self, obj, context):
		# context is instance of gi.repository.Gdk.DragContext
		#win = context.get_source_window()
		# log.debug("dragBegin", id(win), win.get_geometry())
		pbuf = newDndDatePixbuf(ui.cell.dates[ui.dragGetCalType])
		w = pbuf.get_width()
		# log.debug(dir(context))
		gtk.drag_set_icon_pixbuf(
			context,
			pbuf,
			w / 2,  # y offset
			-10,  # x offset FIXME - not to be hidden behind mouse cursor
		)
		return True

	def getCellPos(self):
		raise NotImplementedError

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		CustomizableCalObj.onKeyPress(self, arg, gevent)
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname in ("space", "home", "t"):
			self.goToday()
		elif kname == "menu":
			self.emit("popup-cell-menu", gevent.time, *self.getCellPos())
		elif kname == "i":
			self.emit("day-info")
		else:
			return False
		return True
