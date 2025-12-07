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
from scal3.ui_gtk.signals import SignalHandlerBase, registerSignals

log = logger.get()

from typing import TYPE_CHECKING, Any

from scal3 import core, ui
from scal3.ui_gtk import gdk, gtk, listener
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj, commonSignals
from scal3.ui_gtk.drawing import newDndDatePixbuf

if TYPE_CHECKING:
	from gi.repository import GObject

	from scal3.ui_gtk.pytypes import StackPageType
	from scal3.ui_gtk.starcal_types import MainWinType

__all__ = ["CalBase"]


@registerSignals
class SignalHandler(SignalHandlerBase):
	signals = commonSignals + [
		("popup-cell-menu", [int, int]),
		("popup-main-menu", [int, int]),
		("double-button-press", []),
		("pref-update-bg-color", []),
		("day-info", []),
	]


class CalBase(CustomizableCalObj):
	Sig = SignalHandler
	dragAndDropEnable = True
	doubleClickEnable = True
	myKeys: set[str] = {
		"space",
		"home",
		"t",
		"menu",
		"i",
	}
	win: MainWinType

	def initCal(self) -> None:
		self.initVars()
		listener.dateChange.add(self)
		# ----
		if self.dragAndDropEnable:
			self.defineDragAndDrop()
		if self.doubleClickEnable:
			self.s.connect("double-button-press", ui.cells.current.dayOpenEvolution)
		# ---
		self.subPages: list[StackPageType] | None = None

	def gotoJd(self, jd: int) -> None:
		ui.cells.gotoJd(jd)
		self.broadcastDateChange()

	def goToday(self, _w: GObject.Object | None = None) -> None:
		self.gotoJd(core.getCurrentJd())

	def jdPlus(self, p: int) -> None:
		ui.cells.jdPlus(p)
		self.broadcastDateChange()

	def changeDate(
		self,
		year: int,
		month: int,
		day: int,
		calType: int | None = None,
	) -> None:
		ui.cells.changeDate(year, month, day, calType)
		self.broadcastDateChange()

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:  # noqa: ARG002
		self.w.queue_draw()

	def defineDragAndDrop(self) -> None:
		self.w.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			[],
			gdk.DragAction.COPY,  # FIXME
		)
		self.w.drag_source_add_text_targets()
		# ---
		self.w.connect("drag-data-get", self.dragDataGet)
		self.w.connect("drag-begin", self.dragBegin)
		self.w.connect("drag-data-received", self.dragDataRec)
		# ---
		self.w.drag_dest_set(
			gtk.DestDefaults.ALL,
			[],
			gdk.DragAction.COPY,  # FIXME
		)
		self.w.drag_dest_add_text_targets()
		self.w.drag_dest_add_uri_targets()
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
		_obj: gtk.Widget,
		_context: gdk.DragContext,
		selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> bool:
		# context is instance of gi.repository.Gdk.DragContext
		y, m, d = ui.cells.current.dates[ui.dragGetCalType]
		text = f"{y:04d}/{m:02d}/{d:02d}"
		selection.set_text(text, len(text))
		# pbuf = newDndDatePixbuf(ui.cells.current.dates[ui.dragGetCalType])
		# selection.set_pixbuf(pbuf)
		return True

	# def dragLeave(  # noqa: PLR6301
	# 	self,
	# 	_obj: gtk.Widget,
	# 	context: gdk.DragContext,
	# 	etime: int,
	# ) -> bool:
	# 	log.debug(f"{context = }")
	# 	context.drop_reply(False, etime)
	# 	return True

	def dragDataRec(
		self,
		_obj: gtk.Widget,
		_context: gdk.DragContext,
		_x: int,
		_y: int,
		selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> bool:
		from scal3.ui_gtk.dnd import processDroppedDate

		dtypeAtom = selection.get_data_type()
		dtype = dtypeAtom.name()

		text = selection.get_text()
		if not text:
			return True
		dateM = processDroppedDate(text, dtype)
		if dateM:
			self.changeDate(*dateM)
			return False

		# TODO: D&D of color does not seem to work
		# if dtype == "application/x-color":
		# 	# selection.get_text() is None
		# 	sdata = selection.data  # type: ignore[attr-defined]
		# 	log.debug(f"{sdata = }")
		# 	conf.bgColor.v = RGBA(
		# 		ord(sdata[1]),
		# 		ord(sdata[3]),
		# 		ord(sdata[5]),
		# 		ord(sdata[7]),
		# 	)
		# 	self.s.emit("pref-update-bg-color")
		# 	self.queue_draw()
		# 	return False

		log.warning(f"Unknown dropped data type {dtype!r}, {text=}, {selection=}")
		return True

	def dragBegin(self, _obj: gtk.Widget, context: gdk.DragContext) -> bool:  # noqa: PLR6301
		# context is instance of gi.repository.Gdk.DragContext
		# win = context.get_source_window()
		# log.debug("dragBegin", id(win), win.get_geometry())
		pbuf = newDndDatePixbuf(ui.cells.current.dates[ui.dragGetCalType])
		w = pbuf.get_width()
		# log.debug(dir(context))
		gtk.drag_set_icon_pixbuf(
			context,
			pbuf,
			int(w / 2),  # y offset
			-10,  # x offset FIXME - not to be hidden behind mouse cursor
		)
		return True

	def getCellPos(self, *_args: Any) -> tuple[int, int]:
		raise NotImplementedError

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		CustomizableCalObj.onKeyPress(self, arg, gevent)
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		if kname in {"space", "home", "t"}:
			self.goToday()
		elif kname == "menu":
			self.s.emit("popup-cell-menu", *self.getCellPos())
		elif kname == "i":
			self.s.emit("day-info")
		else:
			return False
		return True
