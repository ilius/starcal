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
	signals = CustomizableCalObj.signals + [
		('popup-cell-menu', [int, int, int]),
		('popup-main-menu', [int, int, int]),
		('2button-press', []),
		('pref-update-bg-color', []),
		('day-info', []),
	]
	myKeys = (
		'space', 'home', 't',
		'menu',
		'i',
	)

	def initCal(self):
		self.initVars()
		listener.dateChange.add(self)
		####
		self.defineDragAndDrop()
		self.connect('2button-press', ui.dayOpenEvolution)
		if ui.mainWin:
			self.connect('popup-cell-menu', ui.mainWin.menuCellPopup)
			self.connect('popup-main-menu', ui.mainWin.menuMainPopup)
			self.connect('pref-update-bg-color', ui.mainWin.prefUpdateBgColor)
			self.connect('day-info', ui.mainWin.dayInfoShow)

	def gotoJd(self, jd):
		ui.gotoJd(jd)
		self.onDateChange()

	def goToday(self, obj=None):
		return self.gotoJd(core.getCurrentJd())

	def jdPlus(self, p):
		ui.jdPlus(p)
		self.onDateChange()

	def changeDate(self, year, month, day, mode=None):
		ui.changeDate(year, month, day, mode)
		self.onDateChange()

	def onCurrentDateChange(self, gdate):
		self.queue_draw()

	def getCellPagePlus(self, jd, plus):## use for sliding
		raise NotImplementedError

	def gridCheckClicked(self, checkb):
		checkb.colorb.set_sensitive(checkb.get_active())
		checkb.item.updateVar()
		self.queue_draw()

	def gridColorChanged(self, colorb):
		colorb.item.updateVar()
		self.queue_draw()

	def defineDragAndDrop(self):
		self.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			[],
			gdk.DragAction.MOVE,  # FIXME
		)
		self.drag_source_add_text_targets()
		###
		self.connect('drag-data-get', self.dragDataGet)
		self.connect('drag-begin', self.dragBegin)
		self.connect('drag-data-received', self.dragDataRec)
		###
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			[],
			gdk.DragAction.COPY,  # FIXME
		)
		self.drag_dest_add_text_targets()
		self.drag_dest_add_uri_targets()
		## ACTION_MOVE, FIXME
		## if source ACTION was ACTION_COPY, calendar recieves its own dragged day
		## just like gnome-calendar-applet (but it seems not a logical behaviar)
		#self.drag_source_add_uri_targets()#???????
		##self.connect('drag-end', self.dragCalEnd)
		##self.connect('drag-drop', self.dragCalDrop)
		##self.connect('drag-failed', self.dragCalFailed)
		#self.connect('drag-leave', self.dragLeave)

	def dragDataGet(self, obj, context, selection, target_id, etime):
		## context is instance of gi.repository.Gdk.DragContext
		text = '%.2d/%.2d/%.2d' % ui.cell.dates[ui.dragGetMode]
		selection.set_text(text, len(text))
		#pbuf = newDndDatePixbuf(ui.cell.dates[ui.dragGetMode])
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
		elif dtype == 'application/x-color':
			## selection.get_text() == None
			text = selection.data
			ui.bgColor = (
				ord(text[1]),
				ord(text[3]),
				ord(text[5]),
				ord(text[7]),
			)
			self.emit('pref-update-bg-color')
			self.queue_draw()
		else:
			print(
				'Unknown dropped data type "%s", text="%s", data="%s"' % (
					dtype,
					text,
					selection.data,
				),
			)
			return True
		return False

	def dragBegin(self, obj, context):
		## context is instance of gi.repository.Gdk.DragContext
		#win = context.get_source_window()
		#print('dragBegin', id(win), win.get_geometry())
		pbuf = newDndDatePixbuf(ui.cell.dates[ui.dragGetMode])
		w = pbuf.get_width()
		#print(dir(context))
		gtk.drag_set_icon_pixbuf(
			context,
			pbuf,
			w / 2,  # y offset
			-10,  # x offset FIXME - not to be hidden behind mouse cursor
		)
		return True

	def getCellPos(self):
		raise NotImplementedError

	def keyPress(self, arg, gevent):
		CustomizableCalObj.keyPress(self, arg, gevent)
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname in ('space', 'home', 't'):
			self.goToday()
		elif kname == 'menu':
			self.emit('popup-cell-menu', gevent.time, *self.getCellPos())
		elif kname == 'i':
			self.emit('day-info')
		else:
			return False
		return True
