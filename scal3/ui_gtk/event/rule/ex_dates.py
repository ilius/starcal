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

from typing import TYPE_CHECKING, Any

from scal3 import logger

log = logger.get()

from scal3 import cal_types
from scal3.date_utils import dateDecode, dateEncode
from scal3.locale_man import textNumDecode, textNumEncode
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gdk, gtk, pack
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import dialog_add_button, labelImageButton

if TYPE_CHECKING:
	from gi.repository import GObject

	from scal3.event_lib.rules import ExDatesEventRule

__all__ = ["WidgetClass"]


def encode(d: tuple[int, int, int]) -> str:
	return textNumEncode(dateEncode(d))


def decode(s: str) -> tuple[int, int, int]:
	return dateDecode(textNumDecode(s))


def validate(s: str) -> str:
	return encode(decode(s))


class WidgetClass(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, rule: ExDatesEventRule) -> None:
		self.rule = rule
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.w = self
		# ---
		self.countLabel = gtk.Label()
		pack(self, self.countLabel)
		# ---
		self.listStore = gtk.ListStore(str)
		self.dialog: Dialog | None = None
		# ---
		self.editButton = labelImageButton(
			label=_("Edit"),
			imageName="document-edit.svg",
		)
		self.editButton.connect("clicked", self.showDialog)
		pack(self, self.editButton)

	def updateCountLabel(self) -> None:
		self.countLabel.set_label(
			" " * 2 + _("{count} items").format(count=_(len(self.listStore))) + " " * 2,
		)

	def createDialog(self) -> None:
		if self.dialog:
			return
		# log.debug(f"----- toplevel: {self.get_toplevel()}")
		toplevel = self.get_toplevel()
		assert isinstance(toplevel, gtk.Window), f"{toplevel=}"
		self.dialog = dialog = Dialog(
			title=self.rule.desc,
			transient_for=toplevel,
		)
		# ---
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(True)
		self.treev.set_model(self.listStore)
		# --
		cell = gtk.CellRendererText()
		cell.set_property("editable", True)
		cell.connect("edited", self.dateCellEdited)
		col = gtk.TreeViewColumn(title=_("Date"), cell_renderer=cell, text=0)
		# col.set_title
		self.treev.append_column(col)
		# --
		toolbar = VerticalStaticToolBox(self)
		# --
		toolbar.extend(
			[
				ToolBoxItem(
					name="add",
					imageName="list-add.svg",
					onClick=self.onAddClick,
					desc=_("Add"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="delete",
					imageName="edit-delete.svg",
					onClick=self.onDeleteClick,
					desc=_("Delete", ctx="button"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveUp",
					imageName="go-up.svg",
					onClick=self.onMoveUpClick,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="moveDown",
					imageName="go-down.svg",
					onClick=self.onMoveDownClick,
					desc=_("Move down"),
					continuousClick=False,
				),
			],
		)
		# --
		dialogHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(dialogHbox, self.treev, 1, 1)
		pack(dialogHbox, toolbar.w)
		pack(dialog.vbox, dialogHbox, 1, 1)
		dialog.vbox.show_all()
		dialog.resize(200, 300)
		dialog.connect("response", lambda _w, _e: dialog.hide())
		# --
		_okButton = dialog_add_button(
			dialog,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Save"),
		)

	def showDialog(self, _w: Any = None) -> None:
		self.createDialog()
		assert self.dialog is not None
		self.dialog.run()
		self.updateCountLabel()

	def dateCellEdited(
		self,
		_cell: Any,
		path: str,
		newText: str,
	) -> None:
		index = int(path)
		self.listStore[index][0] = validate(newText)

	def getSelectedIndex(self) -> int | None:
		pathObj = self.treev.get_cursor()[0]
		if pathObj is None:
			return None
		path = pathObj.get_indices()
		if len(path) < 1:
			return None
		return path[0]

	def onAddClick(self, _obj: GObject.Object) -> None:
		index = self.getSelectedIndex()
		calType = self.rule.getCalType()  # FIXME
		row = [encode(cal_types.getSysDate(calType))]
		if index is None:
			newIter = self.listStore.append(row)
		else:
			newIter = self.listStore.insert(index + 1, row)  # type: ignore[no-untyped-call]
		self.treev.set_cursor(self.listStore.get_path(newIter))
		# col = self.treev.get_column(0)
		# cell = col.get_cell_renderers()[0]
		# cell.start_editing(...) # FIXME

	def onDeleteClick(self, _obj: GObject.Object) -> None:
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.listStore[index]

	def onMoveUpClick(self, _obj: GObject.Object) -> None:
		index = self.getSelectedIndex()
		if index is None:
			return
		model = self.listStore
		if index <= 0 or index >= len(model):
			gdk.beep()
			return
		model.swap(
			model.get_iter(str(index - 1)),
			model.get_iter(str(index)),
		)
		self.treev.set_cursor(index - 1)  # type: ignore[arg-type]

	def onMoveDownClick(self, _obj: GObject.Object) -> None:
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.listStore
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(str(index)),
			t.get_iter(str(index + 1)),
		)
		self.treev.set_cursor(index + 1)  # type: ignore[arg-type]

	def updateWidget(self) -> None:
		for date in self.rule.dates:
			self.listStore.append([encode(date)])
		self.updateCountLabel()

	def updateVars(self) -> None:
		self.rule.setDates([decode(row[0]) for row in self.listStore])
