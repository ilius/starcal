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

from contextlib import suppress

from scal3 import event_lib
from scal3.cal_types import calTypes
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.time_utils import durationUnitsAbs, durationUnitValues
from scal3.ui import conf
from scal3.ui_gtk import GdkPixbuf, gtk, pack
from scal3.ui_gtk.drawing import newColorCheckPixbuf
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.utils import set_tooltip

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.ui_gtk.event import EventWidgetType

try:
	from scal3.ui_gtk.mywidgets.source_editor import SourceEditorWithFrame
except (ImportError, ValueError):
	log.exception("")
	from scal3.ui_gtk.mywidgets import (  # type: ignore[assignment]
		TextFrame as SourceEditorWithFrame,
	)

__all__ = [
	"DurationInputBox",
	"GroupsTreeCheckList",
	"NotificationBox",
	"Scale10PowerComboBox",
	"SingleGroupComboBox",
	"WidgetClass",
	"getGroupRow",
	"getTreeGroupPixbuf",
]


def getTreeGroupPixbuf(group: EventGroupType) -> GdkPixbuf.Pixbuf:
	return newColorCheckPixbuf(
		group.color.rgb(),
		conf.eventTreeGroupIconSize.v,
		group.enable,
	)


def getGroupRow(group: EventGroupType) -> tuple[int, GdkPixbuf.Pixbuf, str]:
	assert group.id is not None
	return (
		group.id,
		getTreeGroupPixbuf(group),
		group.title,
	)


class WidgetClass(gtk.Box):
	expandDescription = True

	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self, event: EventType) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry

		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.w = self
		self._event = event
		# -----------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		# ---
		pack(hbox, gtk.Label(label=_("Calendar Type")))
		combo = CalTypeCombo()
		combo.setActive(calTypes.primary)  # overwritten in updateWidget()
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = combo
		# ---
		pack(self, hbox)
		# -----------
		if event.isAllDay:
			self.tzCheck = None
		else:
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			self.tzCheck = gtk.CheckButton(label=_("Time Zone"))
			set_tooltip(self.tzCheck, _("For input times of event"))
			pack(hbox, self.tzCheck)
			tzCombo = TimeZoneComboBoxEntry()
			pack(hbox, tzCombo)
			pack(hbox, gtk.Label(), 1, 1)
			self.tzCombo = tzCombo
			pack(self, hbox)
			self.tzCheck.connect(
				"clicked",
				lambda check: self.tzCombo.set_sensitive(
					check.get_active(),
				),
			)
		# -----------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Summary")))
		self.summaryEntry = gtk.Entry()
		pack(hbox, self.summaryEntry, 1, 1)
		pack(self, hbox)
		# -----------
		self.descriptionInput = SourceEditorWithFrame()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.add(self.descriptionInput)
		# ---
		frame = gtk.Frame()
		frame.set_label(_("Description"))
		frame.add(swin)
		pack(self, frame, self.expandDescription, self.expandDescription)
		# -----------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Icon") + ":"))
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		# ----------
		self.calTypeCombo.connect(
			"changed",
			self.calTypeComboChanged,
		)  # right place? before updateWidget? FIXME

	def focusSummary(self) -> None:
		self.summaryEntry.select_region(0, -1)
		self.summaryEntry.grab_focus()

	def updateWidget(self) -> None:
		# log.debug("updateWidget", self._event.files)
		self.calTypeCombo.setActive(self._event.calType)
		if self.tzCheck:
			if self._event.timeZone:
				self.tzCheck.set_active(self._event.timeZoneEnable)
				self.tzCombo.set_sensitive(self._event.timeZoneEnable)
				self.tzCombo.set_text(self._event.timeZone)
			else:
				self.tzCheck.set_active(False)
				self.tzCombo.set_sensitive(False)
		# ---
		self.summaryEntry.set_text(self._event.summary)
		self.descriptionInput.set_text(self._event.description)
		self.iconSelect.set_filename(self._event.icon)
		# -----
		for attr in ("notificationBox", "filesBox"):
			box = getattr(self, attr, None)
			if box is not None:
				box.updateWidget()
		# -----
		self.calTypeComboChanged()

	def updateVars(self) -> None:
		calType = self.calTypeCombo.getActive()
		assert calType is not None
		self._event.calType = calType
		if self.tzCheck:
			self._event.timeZoneEnable = self.tzCheck.get_active()
			self._event.timeZone = self.tzCombo.get_text()
		else:
			self._event.timeZoneEnable = False  # FIXME
		self._event.summary = self.summaryEntry.get_text()
		self._event.description = self.descriptionInput.get_text()
		self._event.icon = self.iconSelect.get_filename()
		# -----
		for attr in ("notificationBox", "filesBox"):
			box = getattr(self, attr, None)
			if box is not None:
				box.updateVars()
		# -----

	def calTypeComboChanged(self, obj: Any = None) -> None:  # FIXME
		pass


# class FilesBox(gtk.Box):
# 	def __init__(self, event: EventType) -> None:
# 		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
# 		self._event = event
# 		self.vbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
# 		pack(self, self.vbox)
# 		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
# 		pack(hbox, gtk.Label(), 1, 1)
# 		addButton = labelImageButton(
# 			label=_("_Add File"),
# 			imageName="list-add.svg",
# 		)
# 		addButton.connect("clicked", self.onAddClick)
# 		pack(hbox, addButton)
# 		pack(self, hbox)
# 		self.show_all()
# 		self.newFiles: list[str] = []

# 	def showFile(self, fname: str) -> None:
# 		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
# 		link = gtk.LinkButton(
# 			self._event.getUrlForFile(fname),
# 			_("File") + ": " + fname,
# 		)
# 		pack(hbox, link)
# 		pack(hbox, gtk.Label(), 1, 1)
# 		delButton = labelImageButton(
# 			label=_("Delete", ctx="button"),
# 			imageName="edit-delete.svg",
# 		)
# 		delButton.fname = fname
# 		delButton.hbox = hbox
# 		delButton.connect("clicked", self.onDelClick)
# 		pack(hbox, delButton)
# 		pack(self.vbox, hbox)
# 		hbox.show_all()

# 	def onAddClick(self, _b: gtk.Button) -> None:
# 		fcd = gtk.FileChooserDialog(
# 			title=_("Add File"),
# 		)
# 		dialog_add_button(
# 			fcd,
# 			res=gtk.ResponseType.OK,
# 			imageName="dialog-ok.svg",
# 			label=_("_Choose"),
# 		)
# 		dialog_add_button(
# 			fcd,
# 			res=gtk.ResponseType.CANCEL,
# 			imageName="dialog-cancel.svg",
# 			label=_("Cancel"),
# 		)
# 		fcd.set_local_only(True)
# 		fcd.connect("response", lambda _w, _e: fcd.hide())
# 		if fcd.run() == gtk.ResponseType.OK:
# 			from shutil import copy

# 			fpath = fcd.get_filename()
# 			fname = split(fpath)[-1]
# 			dstDir = self._event.filesDir
# 			os.makedirs(dstDir, exist_ok=True)
# 			# exist_ok parameter is added in Python 3.2
# 			copy(fpath, join(dstDir, fname))
# 			self._event.files.append(fname)
# 			self.newFiles.append(fname)
# 			self.showFile(fname)

# 	def onDelClick(self, button: gtk.Button) -> None:
# 		os.remove(join(self._event.filesDir, button.fname))
# 		with suppress(ValueError):
# 			self._event.files.remove(button.fname)
# 		button.hbox.destroy()

# 	def removeNewFiles(self) -> None:
# 		for fname in self.newFiles:
# 			os.remove(join(self._event.filesDir, fname))
# 		self.newFiles = []

# 	def updateWidget(self) -> None:
# 		for hbox in self.vbox.get_children():
# 			hbox.destroy()
# 		for fname in self._event.files:
# 			self.showFile(fname)

# 	def updateVars(self) -> None:  # FIXME
# 		pass


class NotificationBox(ExpanderFrame):  # or NotificationBox FIXME
	def __init__(self, event: EventType) -> None:
		ExpanderFrame.__init__(self, label=_("Notification"))
		self._event = event
		self.hboxDict: dict[str, gtk.Box] = {}
		self.checkButtonDict: dict[str, gtk.CheckButton] = {}
		self.inputWidgetDict: dict[str, EventWidgetType] = {}
		totalVbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Notify") + " "))
		self.notifyBeforeInput = DurationInputBox()
		pack(hbox, self.notifyBeforeInput, 0, 0)
		pack(hbox, gtk.Label(label=" " + _("before event")))
		pack(hbox, gtk.Label(), 1, 1)
		pack(totalVbox, hbox)
		# ---
		for cls in event_lib.classes.notifier:
			notifier = cls(self._event)
			inputWidget = makeWidget(notifier)
			if not inputWidget:
				log.error(f"notifier {cls.name}, {inputWidget = }")
				continue
			hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
			cb = gtk.CheckButton(label=notifier.desc)
			cb.connect(
				"clicked",
				self.onCheckClicked,
				inputWidget.w,
			)
			cb.set_active(False)
			pack(hbox, cb)
			self.checkButtonDict[notifier.name] = cb
			# pack(hbox, gtk.Label(), 1, 1)
			pack(hbox, inputWidget.w, 1, 1)
			self.inputWidgetDict[notifier.name] = inputWidget
			self.hboxDict[notifier.name] = hbox
			pack(totalVbox, hbox)
		self.add(totalVbox)

	@staticmethod
	def onCheckClicked(check: gtk.CheckButton, inputWidget: gtk.Widget) -> None:
		inputWidget.set_sensitive(check.get_active())

	def updateWidget(self) -> None:
		self.notifyBeforeInput.setDuration(*self._event.notifyBefore)
		for name, check in self.checkButtonDict.items():
			check.set_active(False)
			inputWidget = self.inputWidgetDict[name]
			inputWidget.w.set_sensitive(False)
		for notifier in self._event.notifiers:
			name = notifier.name
			self.checkButtonDict[name].set_active(True)
			inputWidget = self.inputWidgetDict[name]
			inputWidget.w.set_sensitive(True)
			inputWidget.notifier = notifier  # type: ignore[attr-defined]
			inputWidget.updateWidget()
		self.set_expanded(bool(self._event.notifiers))

	def updateVars(self) -> None:
		self._event.notifyBefore = self.notifyBeforeInput.getDuration()
		# ---
		notifiers = []
		for name, check in self.checkButtonDict.items():
			if check.get_active():
				inputWidget = self.inputWidgetDict[name]
				inputWidget.updateVars()
				notifiers.append(inputWidget.notifier)  # type: ignore[attr-defined]
		self._event.notifiers = notifiers


class DurationInputBox(gtk.Box):
	def show(self) -> None:
		gtk.Box.show_all(self)

	def __init__(self) -> None:
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		# --
		self.valueSpin = FloatSpinButton(0, 999, 1)
		pack(self, self.valueSpin)
		# --
		combo = gtk.ComboBoxText()
		for _unitValue, unitName in durationUnitsAbs:
			combo.append_text(
				_(
					" " + unitName.capitalize() + "s",
				),
			)
		combo.set_active(2)  # hour FIXME
		pack(self, combo)
		self.unitCombo = combo

	def getDuration(self) -> tuple[float, int]:
		return (
			self.valueSpin.get_value(),
			durationUnitValues[self.unitCombo.get_active()],
		)

	def setDuration(self, value: float, unit: int) -> None:
		self.valueSpin.set_value(value)
		self.unitCombo.set_active(durationUnitValues.index(unit))


class Scale10PowerComboBox(gtk.ComboBox):
	def __init__(self) -> None:
		self.listStore = listStore = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(listStore)
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 1)
		# ---
		listStore.append((1, _("Years")))
		listStore.append((100, _("Centuries")))
		listStore.append((1000, _("Thousand Years")))
		listStore.append((1000**2, _("Million Years")))
		listStore.append((1000**3, _("Billion (10^9) Years")))
		# ---
		self.set_active(0)

	def get_value(self) -> int:
		return self.get_model()[self.get_active()][0]  # type: ignore[no-any-return]

	def set_value(self, value: int) -> None:
		model = self.listStore
		row: gtk.TreeModelRow
		for i, row in enumerate(model):  # type: ignore[arg-type]
			if row[0] == value:  # type: ignore[index]
				self.set_active(i)
				return
		model.append(
			(
				value,
				_("{yearCount} Years").format(yearCount=_(value)),
			),
		)
		self.set_active(len(model) - 1)


class GroupsTreeCheckList(gtk.TreeView):
	def __init__(self) -> None:
		gtk.TreeView.__init__(self)
		self.listStore = gtk.ListStore(
			int,
			bool,
			str,
		)  # groupId(hidden), enable, summary
		self.set_model(self.listStore)
		self.set_headers_visible(False)
		cell: gtk.CellRenderer
		# ---
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		cell.connect("toggled", self.enableCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		# cell.set_active(True)
		col.set_resizable(True)
		self.append_column(col)
		# ---
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=2)
		col.set_resizable(True)
		self.append_column(col)
		# ---
		for group in ev.groups:
			self.listStore.append([group.id, True, group.title])

	def enableCellToggled(self, cell: gtk.CellRendererToggle, path: str) -> None:
		index = int(path)
		active = not cell.get_active()
		self.listStore[index][1] = active
		cell.set_active(active)

	def getValue(self) -> list[int]:
		"""Returns list of group IDs."""
		return [row[0] for row in self.listStore if row[1]]

	def setValue(self, gids: list[int]) -> None:
		for row in self.listStore:
			row[1] = row[0] in gids

	def disableAll(self) -> None:
		model = self.listStore
		for i in range(len(model)):
			model.set_value(model.get_iter(str(i)), 1, False)

	def enableAll(self) -> None:
		model = self.listStore
		for i in range(len(model)):
			model.set_value(model.get_iter(str(i)), 1, True)


class SingleGroupComboBox(gtk.ComboBox):
	def __init__(self) -> None:
		listStore = gtk.ListStore(int, GdkPixbuf.Pixbuf, str)
		gtk.ComboBox.__init__(self)
		self.listStore = listStore
		self.set_model(listStore)
		cell: gtk.CellRenderer
		# -----
		cell = gtk.CellRendererPixbuf()
		self.pack_start(cell, expand=False)
		self.add_attribute(cell, "pixbuf", 1)
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 2)
		# -----
		self.updateItems()

	def updateItems(self) -> None:
		listStore = self.listStore
		activeGid = self.get_active()
		listStore.clear()
		# ---
		for group in ev.groups:
			if not group.enable:  # FIXME
				continue
			listStore.append(getGroupRow(group))
		# ---
		# try:
		gtk.ComboBox.set_active(self, 0)
		# except:
		# 	pass
		if activeGid is not None and activeGid != -1:
			with suppress(ValueError):
				self.set_active(activeGid)

	def getActive(self) -> int | None:
		index = gtk.ComboBox.get_active(self)
		if index in {None, -1}:
			return None
		return self.get_model()[index][0]  # type: ignore[no-any-return]

	def setActive(self, gid: int) -> None:
		listStore = self.listStore
		for i, row in enumerate(listStore):  # type: ignore[var-annotated, arg-type]
			if row[0] == gid:
				gtk.ComboBox.set_active(self, i)
				break
		else:
			raise ValueError(
				f"SingleGroupComboBox.set_active: Group ID {gid} is not in items",
			)

	def getDict(self) -> dict[str, Any]:
		return {"groupId": self.getActive()}


if __name__ == "__main__":
	from pprint import pformat

	from scal3.ui_gtk import Dialog

	dialog = Dialog()
	# widget = ViewEditTagsHbox()
	# widget = EventTagsAndIconSelect()
	# widget = TagsListBox("task")
	widget = SingleGroupComboBox()
	pack(dialog.vbox, widget, 1, 1)
	# dialog.vbox.show_all()
	# dialog.resize(300, 500)
	# dialog.run()
	dialog.show_all()
	gtk.main()
	log.info(pformat(widget.getDict()))
