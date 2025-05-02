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
from scal3 import logger
from scal3.ui import conf

log = logger.get()

from scal3 import logger

log = logger.get()


from scal3 import core, ui
from scal3.ui_gtk import gdk, gtk, listener
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.drawing import newDndDatePixbuf

__all__ = ["CalBase"]


class CalBase(CustomizableCalObj):
	dragAndDropEnable = True
	doubleClickEnable = True
	signals = CustomizableCalObj.signals + [
		("popup-cell-menu", [int, int]),
		("popup-main-menu", [int, int]),
		("double-button-press", []),
		("pref-update-bg-color", []),
		("day-info", []),
	]
	myKeys = (
		"space",
		"home",
		"t",
		"menu",
		"i",
	)

	def connect(self, sigName, *a, **ka):
		try:
			CustomizableCalObj.connect(self, sigName, *a, **ka)
		except Exception:
			log.exception(f"{sigName=}")

	def initCal(self):
		self.initVars()
		listener.dateChange.add(self)
		# ----
		if self.dragAndDropEnable:
			self.defineDragAndDrop()
		if self.doubleClickEnable:
			self.connect("double-button-press", ui.cells.current.dayOpenEvolution)
		if self.win:
			self.connect("popup-cell-menu", self.win.menuCellPopup)
			self.connect("popup-main-menu", self.win.menuMainPopup)
			self.connect("pref-update-bg-color", self.win.prefUpdateBgColor)
			self.connect("day-info", self.win.dayInfoShow)
		# ---
		self.subPages = None

	def gotoJd(self, jd):
		ui.cells.gotoJd(jd)
		self.onDateChange()

	def goToday(self, _obj=None):
		return self.gotoJd(core.getCurrentJd())

	def jdPlus(self, p):
		ui.cells.jdPlus(p)
		self.onDateChange()

	def changeDate(self, year, month, day, calType=None):
		ui.cells.changeDate(year, month, day, calType)
		self.onDateChange()

	def onCurrentDateChange(self, gdate):  # noqa: ARG002
		self.queue_draw()

	def getCellPagePlus(self, jd, plus):  # use for sliding
		raise NotImplementedError

	def defineDragAndDrop(self):
		self.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			[],
			gdk.DragAction.COPY,  # FIXME
		)
		self.drag_source_add_text_targets()
		# ---
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag-begin", self.dragBegin)
		self.connect("drag-data-received", self.dragDataRec)
		# ---
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
		# self.drag_source_add_uri_targets()#???????
		# self.connect("drag-end", self.dragCalEnd)
		# self.connect("drag-drop", self.dragCalDrop)
		# self.connect("drag-failed", self.dragCalFailed)
		# self.connect("drag-leave", self.dragLeave)

	def dragDataGet(  # noqa: PLR6301
		self,
		_obj,
		_context,
		selection,
		_target_id,
		_etime,
	):
		# context is instance of gi.repository.Gdk.DragContext
		y, m, d = ui.cells.current.dates[ui.dragGetCalType]
		text = f"{y:04d}/{m:02d}/{d:02d}"
		selection.set_text(text, len(text))
		# pbuf = newDndDatePixbuf(ui.cells.current.dates[ui.dragGetCalType])
		# selection.set_pixbuf(pbuf)
		return True

	def dragLeave(self, _obj, context, etime):  # noqa: PLR6301
		context.drop_reply(False, etime)
		return True

	def dragDataRec(self, _obj, _context, _x, _y, selection, _target_id, _etime):
		from scal3.ui_gtk.dnd import processDroppedDate

		dtypeAtom = selection.get_data_type()
		dtype = dtypeAtom.name()

		text = selection.get_text()
		dateM = processDroppedDate(text, dtype)
		if dateM:
			self.changeDate(*dateM)
			return False

		if dtype == "application/x-color":
			# selection.get_text() is None
			text = selection.data
			conf.bgColor.v = (
				ord(text[1]),
				ord(text[3]),
				ord(text[5]),
				ord(text[7]),
			)
			self.emit("pref-update-bg-color")
			self.queue_draw()
			return False

		log.warning(f"Unknown dropped data type {dtype!r}, {text=}, {selection=}")
		return True

	def dragBegin(self, _obj, context):  # noqa: PLR6301
		# context is instance of gi.repository.Gdk.DragContext
		# win = context.get_source_window()
		# log.debug("dragBegin", id(win), win.get_geometry())
		pbuf = newDndDatePixbuf(ui.cells.current.dates[ui.dragGetCalType])
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
		if kname in {"space", "home", "t"}:
			self.goToday()
		elif kname == "menu":
			self.emit("popup-cell-menu", *self.getCellPos())
		elif kname == "i":
			self.emit("day-info")
		else:
			return False
		return True
