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

log = logger.get()
import typing
from contextlib import suppress
from os.path import join
from typing import Any

from scal3 import cal_types, core, locale_man, ui
from scal3 import event_lib as lib
from scal3.config_utils import loadModuleConfig, saveSingleConfig
from scal3.datetime_utils import epochDateTimeEncode
from scal3.event_lib import ev
from scal3.event_lib.event_base import Event
from scal3.event_lib.groups import EventGroup
from scal3.event_lib.trash import EventTrash
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.path import confDir
from scal3.property import Property
from scal3.ui_gtk import GdkPixbuf, HBox, Menu, MenuItem, gdk, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.event import common, setActionFuncs
from scal3.ui_gtk.event.editor import addNewEvent
from scal3.ui_gtk.event.export import (
	MultiGroupExportDialog,
	SingleGroupExportDialog,
)
from scal3.ui_gtk.event.group_op import GroupConvertCalTypeDialog, GroupSortDialog
from scal3.ui_gtk.event.history import EventHistoryDialog
from scal3.ui_gtk.event.import_event import EventsImportWindow
from scal3.ui_gtk.event.trash import TrashEditorDialog
from scal3.ui_gtk.event.utils import (
	checkEventsReadOnly,
	confirmEventsTrash,
	confirmEventTrash,
	eventTreeIconPixbuf,
	eventWriteImageMenuItem,
	eventWriteMenuItem,
	menuItemFromEventGroup,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.mywidgets.resize_button import ResizeButton
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox
from scal3.ui_gtk.utils import (
	confirm,
	dialog_add_button,
	get_menu_width,
	labelImageButton,
	rectangleContainsPoint,
	showError,
)

if typing.TYPE_CHECKING:
	from collections.abc import Callable, Iterable

	from scal3.event_lib.event_container import DummyEventContainer, EventContainer
	from scal3.event_lib.pytypes import (
		AccountType,
		EventContainerType,
		EventGroupType,
		EventType,
	)
	from scal3.event_update_queue import EventUpdateRecord

__all__ = ["EventManagerDialog"]

# log.debug("Testing translator", __file__, _("About"))


type EventOrGroup = lib.Event | lib.EventGroup

confPath = join(confDir, "event", "manager.json")


eventManPos = Property((0, 0))
eventManShowDescription = Property(True)
confParams: dict[str, Property] = {
	"eventManPos": eventManPos,
	"eventManShowDescription": eventManShowDescription,
}

# change date of a dailyNoteEvent when editing it
# dailyNoteChDateOnEdit = True


def loadConf() -> None:
	loadModuleConfig(
		confPath=confPath,
		sysConfPath=None,
		params=confParams,
		decoders={},
	)


def saveConf() -> None:
	saveSingleConfig(confPath, confParams, {})


class EventManagerToolbar(VerticalStaticToolBox):
	def __init__(self, parent: gtk.Window) -> None:
		VerticalStaticToolBox.__init__(self, parent)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		# self.append(ToolBoxItem(
		# 	name="goto-top",
		# 	imageName="go-top.svg",
		# 	onClick="",
		# 	desc=_("Move to top"),
		# 	continuousClick=False,
		# ))
		self.extend(
			[
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick="moveUpByButton",
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick="moveDownByButton",
					desc=_("Move down"),
					continuousClick=False,
				),
				# ToolBoxItem(
				# 	name="goto-bottom",
				# 	imageName="go-bottom.svg",
				# 	onClick="",
				# 	desc=_("Move to bottom"),
				# 	continuousClick=False,
				# ),
				ToolBoxItem(
					name="duplicate",
					imageName="edit-copy.svg",
					onClick="duplicateSelectedObj",
					desc=_("Duplicate"),
					continuousClick=False,
				),
			],
		)


@registerSignals
class EventManagerDialog(MyDialog, ud.BaseCalObj):  # FIXME
	objName = "eventMan"
	desc = _("Event Manager")

	def onShow(self, _w: gtk.Widget) -> None:
		self.move(*eventManPos.v)
		self.onConfigChange()

	@staticmethod
	def onDeleteEvent(_dialog: gtk.Dialog, _ge: gdk.Event) -> bool:
		# onResponse is called before onDeleteEvent
		# just return True, no need to do anything else
		# without this signal handler, the window will be distroyed
		# and can not be opened again
		return True

	def onResponse(self, _dialog: gtk.Dialog, _response_id: int) -> None:
		eventManPos.v = self.get_position()
		saveConf()
		# ---
		self.hide()

	# def findEventByPath(self, eid: int, path: "list[int]""):
	# 	groupIndex, eventIndex = path

	def onConfigChange(self, *a, **kw) -> None:
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		# ---
		if not self.isLoaded:
			if self.get_property("visible"):
				self.waitingDo(self.reloadEvents)  # FIXME
			return

	def onEventUpdate(self, record: EventUpdateRecord) -> None:
		action = record.action

		if action == "r":  # reload group or trash
			if isinstance(record.obj, lib.EventTrash):
				if self.trashIter:
					self.treeModel.remove(self.trashIter)
				self.appendTrash()
				return
			assert record.obj.id is not None
			self.reloadGroupEvents(record.obj.id)

		elif action == "+g":  # new group with events inside it (imported)
			assert isinstance(record.obj, EventGroup)
			self.appendGroupTree(record.obj)

		elif action == "-g":
			log.error(f"Event Manager: onEventUpdate: unexpected {action=}")

		elif action == "eg":  # edit group
			group = record.obj
			assert isinstance(group, EventGroup)
			assert group.id is not None
			groupIter = self.groupIterById[group.id]
			for i, value in enumerate(self.getGroupRow(group)):
				self.treeModel.set_value(groupIter, i, value)

		elif action == "-":
			assert isinstance(record.obj.parent, EventGroup)
			assert isinstance(record.obj, Event)
			assert record.obj.id is not None
			eventIter = self.eventsIter.get(record.obj.id)
			if eventIter is None:
				if record.obj.parent.id in self.loadedGroupIds:
					log.error(
						f"trying to delete non-existing event row, eid={record.obj.id}",
					)
				self.addEventRowToTrash(record.obj)
				return
			path = self.treeModel.get_path(eventIter)
			parentPathObj = gtk.TreePath(path[:1])
			expanded = self.treev.row_expanded(parentPathObj)
			# log.debug(f"{path=}, {parentPathObj=}, {expanded=}")
			self.treeModel.remove(eventIter)
			self.addEventRowToTrash(record.obj)
			if expanded:
				# FIXME: does not work!
				self.treev.expand_row(parentPathObj, False)

		elif action == "+":
			group2 = record.obj.parent
			assert isinstance(group2, EventGroup)
			assert isinstance(record.obj, Event)
			assert group2.id is not None
			if group2.id not in self.loadedGroupIds:
				return
			parentIter = self.groupIterById[group2.id]
			# event is always added to the end of group (at least from
			# outside Event Manager dialog), unless we add a bool global option
			# to add all created events to the beginning of group (prepend)
			self.appendEventRow(parentIter, record.obj)

		elif action == "e":
			assert isinstance(record.obj.parent, EventGroup)
			assert isinstance(record.obj, Event)
			assert record.obj.id is not None
			eventIter = self.eventsIter.get(record.obj.id)
			if eventIter is None:
				if record.obj.parent.id in self.loadedGroupIds:
					log.error(
						f"trying to edit non-existing event row, eid={record.obj.id}",
					)
			else:
				self.updateEventRowByIter(record.obj, eventIter)

	def __init__(self, **kwargs) -> None:
		loadConf()
		checkEventsReadOnly()  # FIXME
		gtk.Dialog.__init__(self, **kwargs)
		self.initVars()
		ud.windowList.appendItem(self)
		ui.eventUpdateQueue.registerConsumer(self)
		# ----
		self.syncing = None  # or a tuple of (groupId, statusText)
		self.groupIterById: dict[int, gtk.TreeIter] = {}
		self.trashIter = None
		self.isLoaded = False
		self.loadedGroupIds: set[int] = set()
		self.eventsIter: dict[int, gtk.TreeIter] = {}
		# ----
		self.multiSelect = False
		self.multiSelectPathDict: dict[int, dict[int, object]] = {}
		self.multiSelectToPaste: tuple[bool, list[gtk.TreeIter]] | None = None
		# ----
		self.set_title(_("Event Manager"))
		self.resize(800, 600)
		self.connect("delete-event", self.onDeleteEvent)
		self.set_transient_for(None)
		self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		# --
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_Apply", ctx="window action"),
			res=gtk.ResponseType.OK,
		)
		# self.connect("response", lambda w, e: self.hide())
		self.connect("response", self.onResponse)
		self.connect("show", self.onShow)
		# -------
		menubar = self.menubar = gtk.MenuBar()
		# ----
		fileItem = self.fileItem = MenuItem(_("_File"))
		fileMenu = Menu()
		fileItem.set_submenu(fileMenu)
		menubar.append(fileItem)
		# --
		addGroupItem = MenuItem(_("Add New Group"))
		addGroupItem.set_sensitive(not ev.allReadOnly)
		addGroupItem.connect("activate", self.addGroupBeforeSelection)
		# FIXME: or before selected group?
		fileMenu.append(addGroupItem)
		# --
		# FIXME right place?
		searchItem = MenuItem(_("_Search Events"))
		searchItem.connect("activate", self.onMenuBarSearchClick)
		fileMenu.append(searchItem)
		# --
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", self.onMenuBarExportClick)
		fileMenu.append(exportItem)
		# --
		importItem = MenuItem(_("_Import", ctx="menu"))
		importItem.set_sensitive(not ev.allReadOnly)
		importItem.connect("activate", self.onMenuBarImportClick)
		fileMenu.append(importItem)
		# --
		orphanItem = MenuItem(_("Check for Orphan Events"))
		orphanItem.set_sensitive(not ev.allReadOnly)
		orphanItem.connect("activate", self.onMenuBarOrphanClick)
		fileMenu.append(orphanItem)
		# ----
		editItem = self.editItem = MenuItem(_("_Edit"))
		if ev.allReadOnly:
			editItem.set_sensitive(False)
		else:
			editMenu = Menu()
			editItem.set_submenu(editMenu)
			menubar.append(editItem)
			# --
			editEditItem = MenuItem(_("Edit"))
			editEditItem.connect("activate", self.onMenuBarEditClick)
			editMenu.append(editEditItem)
			editMenu.connect("show", self.mbarEditMenuPopup)
			self.mbarEditItem = editEditItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			cutItem = MenuItem(_("Cu_t"))
			cutItem.connect("activate", self.onMenuBarCutClick)
			editMenu.append(cutItem)
			self.mbarCutItem = cutItem
			# --
			copyItem = MenuItem(_("_Copy"))
			copyItem.connect("activate", self.onMenuBarCopyClick)
			editMenu.append(copyItem)
			self.mbarCopyItem = copyItem
			# --
			pasteItem = MenuItem(_("_Paste"))
			pasteItem.connect("activate", self.onMenuBarPasteClick)
			editMenu.append(pasteItem)
			self.mbarPasteItem = pasteItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			dupItem = MenuItem(_("_Duplicate"))
			dupItem.connect("activate", self.duplicateSelectedObj)
			editMenu.append(dupItem)
			self.mbarDupItem = dupItem
			# --
			editMenu.append(gtk.SeparatorMenuItem())
			# --
			enableAllItem = MenuItem(_("Enable All Groups"))
			enableAllItem.connect("activate", self.onEnableAllClick)
			editMenu.append(enableAllItem)
			self.mbarEnableAllItem = enableAllItem
			# --
			disableAllItem = MenuItem(_("Disable All Groups"))
			disableAllItem.connect("activate", self.onDisableAllClick)
			editMenu.append(disableAllItem)
			self.mbarDisableAllItem = disableAllItem
		# ----
		viewItem = MenuItem(_("_View"))
		viewMenu = Menu()
		viewItem.set_submenu(viewMenu)
		menubar.append(viewItem)
		# --
		collapseItem = MenuItem(_("Collapse All"))
		collapseItem.connect("activate", self.onCollapseAllClick)
		viewMenu.append(collapseItem)
		# --
		expandItem = MenuItem(_("Expand All"))
		expandItem.connect("activate", self.onExpandAllAllClick)
		viewMenu.append(expandItem)
		# --
		viewMenu.append(gtk.SeparatorMenuItem())
		# --
		self.showDescItem = gtk.CheckMenuItem(label=_("Show _Description"))
		self.showDescItem.set_use_underline(True)
		self.showDescItem.set_active(eventManShowDescription.v)
		self.showDescItem.connect("toggled", self.showDescItemToggled)
		viewMenu.append(self.showDescItem)
		# ----
		# testItem = MenuItem(_("Test"))
		# testMenu = Menu()
		# testItem.set_submenu(testMenu)
		# menubar.append(testItem)
		# ---
		# item = MenuItem("")
		# item.connect("activate", )
		# testMenu.append(item)
		# ----
		multiSelectMenu = Menu()
		multiSelectItemMain = MenuItem(label=_("Multi-select"))
		self.multiSelectItemMain = multiSelectItemMain
		multiSelectItemMain.set_submenu(multiSelectMenu)
		menubar.append(multiSelectItemMain)
		# --
		multiSelectItem = gtk.CheckMenuItem(label=_("Multi-select"))
		multiSelectItem.connect("activate", self.multiSelectToggle)
		multiSelectMenu.append(multiSelectItem)
		self.multiSelectItem = multiSelectItem
		self.multiSelectItemsOther = []
		# ----
		multiSelectMenu.append(gtk.SeparatorMenuItem())
		# ----
		cutItem = MenuItem(_("Cu_t"))
		cutItem.connect("activate", self.multiSelectCut)
		self.multiSelectItemsOther.append(cutItem)
		# --
		copyItem = MenuItem(_("_Copy"))
		copyItem.connect("activate", self.multiSelectCopy)
		self.multiSelectItemsOther.append(copyItem)
		# --
		pasteItem = MenuItem(_("_Paste"))
		pasteItem.connect("activate", self.multiSelectPaste)
		self.multiSelectItemsOther.append(pasteItem)
		# --
		self.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		# --
		deleteItem = MenuItem(_("Delete", ctx="event manager"))
		deleteItem.connect("activate", self.multiSelectDelete)
		self.multiSelectItemsOther.append(deleteItem)
		# --
		self.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		# --
		bulkEditItem = MenuItem(_("Bulk Edit Events"))
		# imageName="document-edit.svg",
		# native CheckMenuItem and ImageMenuItem are not aligned
		bulkEditItem.connect("activate", self.multiSelectBulkEdit)
		self.multiSelectItemsOther.append(bulkEditItem)
		# --
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", self.multiSelectExport)
		self.multiSelectItemsOther.append(exportItem)
		# ---
		for item in self.multiSelectItemsOther:
			item.set_sensitive(False)
			multiSelectMenu.append(item)
		# ----
		menubar.show_all()
		pack(self.vbox, menubar)
		# -------
		# multi-select bar
		self.multiSelectHBox = hbox = HBox(spacing=3)
		self.multiSelectLabel = gtk.Label(label=_("No event selected"))
		self.multiSelectLabel.set_xalign(0)
		self.multiSelectLabel.get_style_context().add_class("smaller")
		pack(hbox, self.multiSelectLabel, 1, 1)

		pack(
			hbox,
			self.smallerButton(
				label=_("Copy"),
				# imageName="edit-copy.svg",
				func=self.multiSelectCopy,
				tooltip=_("Copy"),
			),
		)
		pack(
			hbox,
			self.smallerButton(
				label=_("Cut"),
				# imageName="edit-cut.svg",
				func=self.multiSelectCut,
				tooltip=_("Cut"),
			),
		)
		self.multiSelectPasteButton = self.smallerButton(
			label=_("Paste"),
			# imageName="edit-paste.svg",
			func=self.multiSelectPaste,
			tooltip=_("Paste"),
		)
		pack(hbox, self.multiSelectPasteButton)
		self.multiSelectPasteButton.set_sensitive(False)
		pack(hbox, gtk.Label(), 1, 1)
		pack(
			hbox,
			self.smallerButton(
				label=_("Delete", ctx="event manager"),
				imageName="edit-delete.svg",
				func=self.multiSelectDelete,
				tooltip=_("Move to {title}").format(title=ev.trash.title),
			),
		)
		pack(hbox, gtk.Label(), 1, 1)
		pack(
			hbox,
			self.smallerButton(
				label=_("Cancel"),
				imageName="dialog-cancel.svg",
				func=self.multiSelectCancel,
				tooltip=_("Cancel"),
			),
		)
		# ---
		pack(self.vbox, hbox)
		# -------
		treeBox = HBox()
		# -----
		self.treev = gtk.TreeView()
		self.treev.set_search_column(3)

		# self.treev.set_fixed_height_mode(True)
		# ^ causes multi-select checkbox to be hidden after row-expanded in
		# multi-select mode

		# self.treev.set_headers_visible(False)  # FIXME
		# self.treev.get_selection().set_mode(gtk.SelectionMode.MULTIPLE)  # FIXME
		# self.treev.set_rubber_banding(gtk.SelectionMode.MULTIPLE)  # FIXME
		# self.treev.connect("realize", self.onTreeviewRealize)
		self.treev.get_selection().connect(
			"changed",
			self.treeviewCursorChanged,
		)  # FIXME
		self.treev.connect("button-press-event", self.onTreeviewButtonPress)
		self.treev.connect("row-activated", self.rowActivated)
		self.connect("key-press-event", self.onKeyPress)
		self.treev.connect("key-press-event", self.onTreeviewKeyPress)
		# -----
		swin = gtk.ScrolledWindow()
		swin.add(self.treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(treeBox, swin, 1, 1)
		# ---
		self.toolbar = EventManagerToolbar(self)
		# ---
		pack(treeBox, self.toolbar)
		# -----
		pack(self.vbox, treeBox, 1, 1)
		# -------
		self.treeModel = gtk.TreeStore(
			bool,  # multi-select mode checkbox
			int,  # eventId or groupId, -1 for trash
			GdkPixbuf.Pixbuf,  # eventIcon, groupPixbuf or trashIcon
			str,  # eventSummary, groupTitle or trashTitle
			str,  # eventDescription, empty for group or trash
		)
		self.idColIndex = 1
		self.summaryColIndex = 3
		self.treev.set_model(self.treeModel)
		# ---
		cell = gtk.CellRendererToggle()
		# cell.set_property("activatable", True)
		# cell.set_radio(True)
		cell.connect("toggled", self.multiSelectTreeviewToggle)
		col = gtk.TreeViewColumn(
			title="",
			cell_renderer=cell,
		)
		col.set_cell_data_func(cell, self.multiSelectTreeviewToggleStatus)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.add_attribute(cell, "active", 0)
		col.set_resizable(False)
		col.set_property("expand", False)
		col.set_visible(False)
		self.multiSelectColumn = col
		self.treev.append_column(col)
		# ---
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(
			title="",
			cell_renderer=cell,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.add_attribute(cell, "pixbuf", 2)
		col.set_property("expand", False)
		self.treev.append_column(col)
		self.pixbufCol = col
		# ---
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(
			title=_("Summary"),
			cell_renderer=cell,
			text=3,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.set_resizable(True)
		col.set_property("expand", True)
		self.treev.append_column(col)
		# ---
		cell = gtk.CellRendererText()
		col = self.colDesc = gtk.TreeViewColumn(
			title=_("Description"),
			cell_renderer=cell,
			text=4,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.set_property("expand", True)
		if eventManShowDescription.v:
			self.treev.append_column(col)
		# ---
		# self.treev.set_search_column(2)-- or 3
		# ---
		# (treeIter, move: bool)
		self.toPasteEvent: tuple[gtk.TreeIter, bool] | None = None
		# -----
		hbox = HBox()
		hbox.set_direction(gtk.TextDirection.LTR)
		self.sbar = gtk.Statusbar()
		self.sbar.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.sbar, 1, 1)
		pack(hbox, ResizeButton(self))
		pack(self.vbox, hbox)
		# -----
		self.vbox.show_all()
		self.multiSelectHBox.hide()

	def multiSelectTreeviewToggleStatus(
		self,
		_column: Any,
		cell: gtk.CellRenderer,
		model: gtk.TreeModel,
		gIter: gtk.TreeIter,
		_userData: Any,
	) -> None:
		if not self.multiSelect:
			return

		path = model.get_path(gIter).get_indices()
		value = model.get_value(gIter, 0)
		if len(path) == 2:
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return

		groupIndex = path[0]
		group = self.getGroupByPath(path)
		assert isinstance(group, EventGroup)
		if groupIndex not in self.multiSelectPathDict:
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return

		# we know len(self.multiSelectPathDict[groupIndex]) > 0

		if len(self.multiSelectPathDict[groupIndex]) == len(group):
			cell.set_property("inconsistent", False)
			cell.set_active(True)
			return

		cell.set_property("inconsistent", True)
		cell.set_active(value)

	@staticmethod
	def smallerButton(
		label: str = "",
		imageName: str = "",
		func: Callable[[gtk.Button], None] | None = None,
		tooltip: str = "",
	) -> gtk.Button:
		button = labelImageButton(
			label=label,
			imageName=imageName,
			func=func,
			tooltip=tooltip,
			spacing=4,
		)
		button.get_style_context().add_class("smaller")
		return button

	def multiSelectSetEnable(self, enable: bool) -> None:
		self.multiSelectHBox.set_visible(enable)
		self.multiSelectColumn.set_visible(enable)
		self.editItem.set_sensitive(not enable)
		self.fileItem.set_sensitive(not enable)
		self.toolbar.set_sensitive(not enable)
		for item in self.multiSelectItemsOther:
			item.set_sensitive(enable)
		self.multiSelect = enable

	def multiSelectToggle(self, menuItem: gtk.MenuItem) -> None:
		enable = menuItem.get_active()
		self.multiSelectSetEnable(enable)

	def multiSelectShiftUpDownPress(self, isDown: bool) -> None:
		path = self.getSelectedPath()
		if path is None:
			return
		if len(path) == 1:
			return  # TODO

		if len(path) != 2:
			raise RuntimeError(f"unexpected {path=}")

		model = self.treeModel
		groupIndex, eventIndex = path

		self.multiSelectCBSetEvent(groupIndex, eventIndex, True)

		if eventIndex == 0 and not isDown:
			return

		plus = 1 if isDown else -1
		nextPath = (groupIndex, eventIndex + plus)

		try:
			model.get_iter(nextPath)
		except ValueError:
			# ValueError: invalid tree path '0:4'
			return

		self.multiSelectCBSetEvent(groupIndex, eventIndex + plus, True)
		self.treev.set_cursor(nextPath)
		self.treev.scroll_to_cell(nextPath)

	def multiSelectShiftButtonPress(
		self,
		path: list[int],
	) -> None:
		groupIndex, eventIndex = path
		# s_iter = self.treev.get_selection().get_selected()[1]
		# if s_iter is None
		# s_path = self.treeModel.get_path(s_iter).get_indices()
		if groupIndex not in self.multiSelectPathDict:
			return
		lastEventIndex = next(reversed(self.multiSelectPathDict[groupIndex]))
		# log.debug(f"groupIndex: {groupIndex}")
		# log.debug(f"eventIndex: {lastEventIndex} .. {path[1]}")
		if eventIndex == lastEventIndex:
			return
		if eventIndex > lastEventIndex:
			evIndexRange = range(lastEventIndex + 1, eventIndex + 1)
		else:
			evIndexRange = range(eventIndex, lastEventIndex)
		for evIndex in evIndexRange:
			self.multiSelectCBSetEvent(groupIndex, evIndex, True)

	def multiSelectLabelUpdate(self) -> None:
		self.multiSelectLabel.set_label(
			_("{count} events selected").format(
				count=_(
					sum(
						len(eventIndexes)
						for eventIndexes in self.multiSelectPathDict.values()
					),
				),
			),
		)

	def multiSelectTreeviewToggleSelected(self) -> None:
		path = self.getSelectedPath()
		if path is None:
			return
		self.multiSelectTreeviewTogglePath(path)

	def multiSelectTreeviewToggle(
		self,
		_cell: gtk.CellRendererToggle,
		pathStr: str,
	) -> None:
		path = gtk.TreePath.new_from_string(pathStr).get_indices()
		self.multiSelectTreeviewTogglePath(path)

	def multiSelectCBActivate(self, groupIndex: int, eventIndex: int) -> None:
		if groupIndex not in self.multiSelectPathDict:
			self.multiSelectPathDict[groupIndex] = {}
		self.multiSelectPathDict[groupIndex][eventIndex] = None

	def multiSelectCBSetEvent(
		self,
		groupIndex: int,
		eventIndex: int,
		active: bool,
	) -> None:
		model = self.treeModel
		itr = model.get_iter((groupIndex, eventIndex))
		model.set_value(itr, 0, active)
		if active:
			self.multiSelectCBActivate(groupIndex, eventIndex)
		elif groupIndex in self.multiSelectPathDict:
			if eventIndex in self.multiSelectPathDict[groupIndex]:
				del self.multiSelectPathDict[groupIndex][eventIndex]
			if not self.multiSelectPathDict[groupIndex]:
				del self.multiSelectPathDict[groupIndex]

		parentIter = model.get_iter((groupIndex,))
		try:
			count = len(self.multiSelectPathDict[groupIndex])
		except KeyError:
			model.set_value(parentIter, 0, False)
		else:
			model.set_value(
				parentIter,
				0,
				count == len(ev.groups[self.getRowId(parentIter)]),
			)

		self.multiSelectLabelUpdate()

	def multiSelectCBSetGroup(
		self,
		groupIndex: int,
		eventIndex: int,
		active: bool,
	) -> None:
		if active:
			self.multiSelectCBActivate(groupIndex, eventIndex)
			return

		if groupIndex in self.multiSelectPathDict:
			del self.multiSelectPathDict[groupIndex]

	def multiSelectTreeviewTogglePath(self, path: list[int]) -> None:
		model = self.treeModel
		if len(path) not in {1, 2}:
			raise RuntimeError(f"invalid path depth={len(path)}, {path=}")
		itr = model.get_iter(path)
		pathTuple = tuple(path)

		active = not model.get_value(itr, 0)

		if len(path) == 1:
			model.set_value(itr, 0, active)
			childIter = model.iter_children(itr)
			while childIter is not None:
				isActive = model.get_value(childIter, 0)
				if isActive == active:
					childIter = model.iter_next(childIter)
					continue
				model.set_value(childIter, 0, active)
				groupIndex, eventIndex = tuple(model.get_path(childIter).get_indices())
				self.multiSelectCBSetGroup(groupIndex, eventIndex, active)
				childIter = model.iter_next(childIter)
			self.multiSelectLabelUpdate()
			return

		self.multiSelectCBSetEvent(pathTuple[0], pathTuple[1], active)

	def multiSelectCopy(self, _w: gtk.Widget | None = None) -> None:
		iterList = list(self.multiSelectIters())
		self.multiSelectToPaste = (False, iterList)
		self.multiSelectPasteButton.set_sensitive(True)

	def multiSelectCut(self, _w: gtk.Widget | None = None) -> None:
		iterList = list(self.multiSelectIters())
		self.multiSelectToPaste = (True, iterList)
		self.multiSelectPasteButton.set_sensitive(True)

	def multiSelectPaste(self, _w: gtk.Widget | None = None) -> None:
		toPaste = self.multiSelectToPaste
		if toPaste is None:
			log.error("nothing to paste")
			return

		model = self.treeModel
		move, iterList = toPaste
		if not iterList:
			return

		targetPath = self.getSelectedPath()
		if targetPath is None:
			return
		newEventIter = None

		if len(targetPath) == 2:
			iterList = list(reversed(iterList))
			# so that events are inserted in the same order as they are selected

		for srcIter in iterList:
			iter_ = self._pasteEventToPath(srcIter, move, targetPath)
			if newEventIter is None:
				newEventIter = iter_

		if not move:
			for iter_ in iterList:
				model.set_value(iter_, 0, False)

		if move:
			msg = _("{count} events successfully moved")
		else:
			msg = _("{count} events successfully copied")
		self.sbar.push(
			0,
			msg.format(
				count=_(len(iterList)),
			),
		)

		self.multiSelectOperationFinished()
		self.multiSelectToPaste = None

		if newEventIter:
			self.treev.set_cursor(self.treeModel.get_path(newEventIter))

	def _do_multiSelectDelete(self, iterList: list[gtk.TreeIter]) -> None:
		model = self.treeModel

		saveGroupSet: set[EventContainer] = set()
		ui.eventUpdateQueue.pauseLoop()

		for gIter in iterList:
			path = model.get_path(gIter)
			group, event = self.getEventAndGroupByPath(path)
			assert event.id is not None
			assert isinstance(event, Event)

			if isinstance(group, EventTrash):
				group.delete(event.id)  # group == ev.trash
				saveGroupSet.add(group)
				model.remove(gIter)
				continue

			assert isinstance(group, EventGroup)
			ui.moveEventToTrash(group, event, self, save=False)
			saveGroupSet.add(group)
			saveGroupSet.add(ev.trash)
			model.remove(gIter)
			self.addEventRowToTrash(event)

		for groupTmp in saveGroupSet:
			groupTmp.save()

		ui.eventUpdateQueue.resumeLoop()

	def multiSelectOperationFinished(self) -> None:
		model = self.treeModel
		for groupIndex in self.multiSelectPathDict:
			with suppress(ValueError):
				model.set_value(model.get_iter([groupIndex]), 0, False)

		self.multiSelectPathDict = {}
		self.multiSelectLabelUpdate()
		self.multiSelectPasteButton.set_sensitive(False)

	def multiSelectDelete(self, _w: gtk.Widget | None = None) -> None:
		model = self.treeModel
		if not self.multiSelectPathDict:
			return
		iterList = list(self.multiSelectIters())

		trashIndex = model.get_path(self.trashIter)[0]
		if trashIndex in self.multiSelectPathDict:
			deleteCount = len(self.multiSelectPathDict[trashIndex])
		else:
			deleteCount = 0

		toTrashCount = len(iterList) - deleteCount

		if not confirmEventsTrash(toTrashCount, deleteCount):
			return

		self.waitingDo(self._do_multiSelectDelete, iterList)

		msgs = []
		if toTrashCount:
			msgs.append(
				_("Moved {count} events to {title}").format(
					count=_(toTrashCount),
					title=ev.trash.title,
				),
			)
		if deleteCount:
			msgs.append(
				_("Deleted {count} events from {title}").format(
					count=_(deleteCount),
					title=ev.trash.title,
				),
			)
		self.sbar.push(0, _(", ").join(msgs))

		self.multiSelectOperationFinished()

	def multiSelectIters(self) -> Iterable[gtk.TreeIter]:
		model = self.treeModel
		for groupIndex, eventIndexes in self.multiSelectPathDict.items():
			for eventIndex in eventIndexes:
				yield model.get_iter((groupIndex, eventIndex))

	def multiSelectCancel(self, _w: gtk.Widget | None = None) -> None:
		model = self.treeModel
		self.multiSelectSetEnable(False)
		self.multiSelectItem.set_active(False)
		for gIter in self.multiSelectIters():
			model.set_value(gIter, 0, False)
		self.multiSelectOperationFinished()

	def multiSelectEventIdsDict(self) -> dict[int, list[int]]:
		model = self.treeModel
		idsDict = {}
		for groupIndex, eventIndexes in self.multiSelectPathDict.items():
			groupId = self.getRowId(model.get_iter((groupIndex,)))
			idsDict[groupId] = [
				self.getRowId(model.get_iter((groupIndex, eventIndex)))
				for eventIndex in eventIndexes
			]
		return idsDict

	def multiSelectEventIdsList(self) -> list[tuple[int, int]]:
		model = self.treeModel
		idsList = []
		for groupIndex, eventIndexes in self.multiSelectPathDict.items():
			groupId = self.getRowId(model.get_iter((groupIndex,)))
			idsList += [
				(
					groupId,
					self.getRowId(model.get_iter((groupIndex, eventIndex))),
				)
				for eventIndex in eventIndexes
			]
		return idsList

	def multiSelectBulkEdit(self, _w: gtk.Widget | None = None) -> None:
		from scal3.event_lib.event_container import DummyEventContainer
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog

		idsDict = self.multiSelectEventIdsDict()
		container: EventContainerType = DummyEventContainer(ev.groups, idsDict)  # type: ignore[assignment]
		dialog = EventsBulkEditDialog(container, transient_for=self)

		if dialog.run() == gtk.ResponseType.OK:
			self.waitingDo(self._do_multiSelectBulkEdit, dialog, container)

	def _do_multiSelectBulkEdit(
		self,
		dialog: gtk.Dialog,
		container: DummyEventContainer,
	) -> None:
		dialog.doAction()
		dialog.destroy()
		for event in container:
			self.updateEventRow(event)
			ui.eventUpdateQueue.put("e", event, self)

		self.multiSelectOperationFinished()

	def multiSelectExport(self, _w: gtk.Widget | None = None) -> None:
		from scal3.ui_gtk.event.export import EventListExportDialog

		idsList = self.multiSelectEventIdsList()
		y, m, d = cal_types.getSysDate(core.GREGORIAN)
		dialog = EventListExportDialog(
			idsList,
			defaultFileName=f"selected-events-{y:04d}-{m:02d}-{d:02d}",
			# groupTitle="",
		)
		dialog.run()
		self.sbar.push(
			0,
			_("Exporting {count} events finished").format(
				count=_(len(idsList)),
			),
		)
		self.multiSelectOperationFinished()

	def getRowId(self, gIter: gtk.TreeIter) -> int:
		return self.treeModel.get_value(gIter, self.idColIndex)

	def canPasteToGroup(self, group: EventGroupType) -> bool:
		if self.toPasteEvent is None:
			return False
		if not group.acceptsEventTypes:  # noqa: SIM103
			return False
		# FIXME: check event type here?
		return True

	def checkEventToAdd(
		self,
		group: EventGroupType,
		event: EventType,
	) -> None:
		if not group.checkEventToAdd(event):
			msg = _(
				'Group type "{groupType}" can not contain event type "{eventType}"',
			).format(
				groupType=group.desc,
				eventType=event.desc,
			)
			showError(msg, transient_for=self)
			raise RuntimeError("Invalid event type for this group")

	@staticmethod
	def getGroupRow(
		group: EventGroupType,
	) -> tuple[bool, int, GdkPixbuf.Pixbuf, str, str]:
		ident, pbuf, title = common.getGroupRow(group)
		return (False, ident, pbuf, title, "")

	@staticmethod
	def getEventRow(
		event: EventType,
	) -> tuple[bool, int, GdkPixbuf.Pixbuf | None, str, str]:
		pixbuf = eventTreeIconPixbuf(event.getIconRel())
		if event.icon and pixbuf is None:
			log.error(
				f"getEventRow: invalid {event.icon=} "
				f"for {event.id=} in {event.parent=}",
			)
		assert event.id is not None
		return (
			False,
			event.id,
			pixbuf,
			event.summary,
			event.getShownDescription(),
		)

	def appendEventRow(
		self,
		parentIter: gtk.TreeIter,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter = self.treeModel.append(parentIter, self.getEventRow(event))
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertEventRow(
		self,
		parentIter: gtk.TreeIter,
		position: int,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter = self.treeModel.insert(
			parentIter,
			position,
			self.getEventRow(event),
		)
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertEventRowAfter(
		self,
		parentIter: gtk.TreeIter,
		siblingIter: gtk.TreeIter,
		event: EventType,
	) -> gtk.TreeIter:
		assert event.id is not None
		eventIter = self.treeModel.insert_after(
			parentIter,
			siblingIter,
			self.getEventRow(event),
		)
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertGroup(
		self,
		position: int,
		group: EventGroupType,
	) -> gtk.TreeIter:
		assert group.id is not None
		self.groupIterById[group.id] = groupIter = self.treeModel.insert(
			None,
			position,
			self.getGroupRow(group),
		)
		return groupIter

	def appendGroupEvents(
		self,
		group: EventGroupType,
		groupIter: gtk.TreeIter,
	) -> None:
		assert group.id is not None
		for event in group:
			self.appendEventRow(groupIter, event)
		self.loadedGroupIds.add(group.id)

	def insertGroupTree(self, position: int, group: EventGroupType) -> None:
		groupIter = self.insertGroup(position, group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendGroup(self, group: EventGroupType) -> gtk.TreeIter:
		assert group.id is not None
		self.groupIterById[group.id] = groupIter = self.treeModel.insert_before(
			None,
			self.trashIter,
			self.getGroupRow(group),
		)
		return groupIter

	def appendGroupTree(self, group: EventGroupType) -> None:
		groupIter = self.appendGroup(group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendTrash(self) -> None:
		self.trashIter = self.treeModel.append(
			None,
			(
				False,
				-1,
				eventTreeIconPixbuf(ev.trash.getIconRel()),
				ev.trash.title,
				"",
			),
		)
		for event in ev.trash:
			self.appendEventRow(self.trashIter, event)

	def reloadGroupEvents(self, gid: int) -> None:
		groupIter = self.groupIterById[gid]
		assert self.getRowId(groupIter) == gid
		# --
		self.removeIterChildren(groupIter)
		# --
		group = ev.groups[gid]
		if gid not in self.loadedGroupIds:
			return
		for event in group:
			self.appendEventRow(groupIter, event)

	def reloadEvents(self) -> None:
		self.treeModel.clear()
		self.appendTrash()
		for group in ev.groups:
			self.appendGroupTree(group)
		self.treeviewCursorChanged()
		# ----
		self.isLoaded = True

	def getEventAndGroupByPath(
		self, path: list[int]
	) -> tuple[EventGroupType, EventType]:
		assert len(path) == 2
		groupIndex = path[0]
		eventId = self.getRowId(self.treeModel.get_iter(path))
		groupId = self.getRowId(self.treeModel.get_iter((groupIndex,)))
		group = ev.groups[groupId]
		return group, group[eventId]

	def getEventAndParentByPath(
		self, path: list[int]
	) -> tuple[EventGroupType | EventTrash, EventType]:
		assert len(path) == 2
		groupIndex = path[0]
		eventId = self.getRowId(self.treeModel.get_iter(path))
		groupId = self.getRowId(self.treeModel.get_iter((groupIndex,)))
		parent: EventGroupType | EventTrash
		if groupId == -1:
			parent = ev.trash
		else:
			parent = ev.groups[groupId]
		return parent, parent[eventId]

	def getEventByPath(self, path: list[int]) -> EventType:
		assert len(path) == 2
		groupIndex = path[0]
		eventId = self.getRowId(self.treeModel.get_iter(path))
		groupId = self.getRowId(self.treeModel.get_iter((groupIndex,)))
		group = ev.groups[groupId]
		return group[eventId]

	def getGroupByPath(self, path: list[int]) -> EventGroupType:
		groupIndex = path[0]
		groupId = self.getRowId(self.treeModel.get_iter((groupIndex,)))
		return ev.groups[groupId]

	def getGroupOrTrashByPath(self, path: list[int]) -> EventGroupType | EventTrash:
		groupIndex = path[0]
		groupId = self.getRowId(self.treeModel.get_iter((groupIndex,)))
		if groupId == -1:
			return ev.trash
		return ev.groups[groupId]

	def historyOfEventFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		event = self.getEventByPath(path)
		EventHistoryDialog(event, transient_for=self).run()

	def trashAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		trash: EventTrash,
	) -> None:
		# log.debug("right click on trash", group.title)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.editTrash,
			),
		)

		menu.add(
			eventWriteMenuItem(
				_("Sort Events"),
				imageName="view-sort-ascending.svg",
				func=self.groupSortFromMenu,
				args=(path,),
				sensitive=bool(trash.idList),
			),
		)

		# FIXME: _("Empty {title}").format(title=group.title),
		menu.add(
			eventWriteMenuItem(
				_("Empty Trash"),
				imageName="sweep.svg",
				func=self.emptyTrash,
				sensitive=bool(trash.idList),
			),
		)
		# menu.add(gtk.SeparatorMenuItem())
		# menu.add(eventWriteMenuItem(
		# 	"Add New Group",
		# 	imageName="document-new.svg",
		# 	func=self.addGroupBeforeSelection,
		# ))  # FIXME

	def groupAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		group: EventGroupType,
	) -> None:
		# log.debug("right click on group", group.title)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.editGroupFromMenu,
				args=(path,),
			),
		)
		eventTypes = group.acceptsEventTypes
		if eventTypes is None:
			eventTypes = lib.classes.event.names
		if len(eventTypes) > 3:
			menu.add(
				eventWriteMenuItem(
					_("Add Event"),
					imageName="list-add.svg",
					func=self.addGenericEventToGroupFromMenu,
					args=(path, group),
				),
			)
		else:
			for eventType in eventTypes:
				# if eventType == "custom":  # FIXME
				# 	eventTypeDesc = _("Event")
				# else:
				eventTypeDesc = lib.classes.event.byName[eventType].desc
				label = _("Add {eventType}").format(
					eventType=eventTypeDesc,
				)
				menu.add(
					eventWriteMenuItem(
						label,
						imageName="list-add.svg",
						func=self.addEventToGroupFromMenu,
						args=(
							path,
							group,
							eventType,
							label,
						),
					),
				)
		pasteItem = eventWriteMenuItem(
			_("Paste Event"),
			imageName="edit-paste.svg",
			func=self.pasteEventFromMenu,
			args=(path,),
		)
		menu.add(pasteItem)
		pasteItem.set_sensitive(self.canPasteToGroup(group))
		# --
		if group.remoteIds:
			aid, _remoteGid = group.remoteIds
			try:
				account = ev.accounts[aid]
			except KeyError:
				log.exception("")
			else:
				if account.enable:
					menu.add(gtk.SeparatorMenuItem())
					menu.add(
						eventWriteMenuItem(
							_("Synchronize"),
							imageName="",
							# FIXME: sync-events.svg
							func=self.syncGroupFromMenu,
							args=(
								path,
								account,
							),
						),
					)
				# else:  # FIXME
		# --
		menu.add(gtk.SeparatorMenuItem())
		# menu.add(eventWriteMenuItem(
		# 	_("Add New Group"),
		# 	imageName="document-new.svg",
		# 	func=self.addGroupBeforeGroup,
		# 	args=(path,),
		# ))  # FIXME
		menu.add(
			eventWriteMenuItem(
				_("Duplicate"),
				imageName="edit-copy.svg",
				func=self.duplicateGroupFromMenu,
				args=(path,),
			),
		)
		# ---
		dupAllItem = eventWriteMenuItem(
			_("Duplicate with All Events"),
			imageName="edit-copy.svg",
			func=self.duplicateGroupWithEventsFromMenu,
			args=(path,),
		)
		menu.add(dupAllItem)
		dupAllItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			eventWriteMenuItem(
				_("Delete Group"),
				imageName="edit-delete.svg",
				func=self.deleteGroupFromMenu,
				args=(path,),
			),
		)
		menu.add(gtk.SeparatorMenuItem())
		# --
		# menu.add(eventWriteMenuItem(
		# 	_("Move Up"),
		# 	imageName="go-up.svg",
		# 	func=self.moveUpFromMenu,
		# 	args=(path,),
		# ))
		# menu.add(eventWriteMenuItem(
		# 	_("Move Down"),
		# 	imageName="go-down.svg",
		# 	func=self.moveDownFromMenu,
		# 	args=(path,)
		# ))
		# --
		menu.add(
			ImageMenuItem(
				_("Export", ctx="menu"),
				# imageName="export-events.svg",  # FIXME
				func=self.groupExportFromMenu,
				args=(group,),
			),
		)
		# ---
		menu.add(
			eventWriteMenuItem(
				_("Sort Events"),
				imageName="view-sort-ascending.svg",
				func=self.groupSortFromMenu,
				args=(path,),
				sensitive=not group.isReadOnly() and bool(group.idList),
			),
		)
		# ---
		convertItem = eventWriteMenuItem(
			_("Convert Calendar Type"),
			imageName="convert-calendar.svg",
			func=self.groupConvertCalTypeFromMenu,
			args=(group,),
		)
		menu.add(convertItem)
		convertItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		for newGroupType in group.canConvertTo:
			newGroupTypeDesc = lib.classes.group.byName[newGroupType].desc
			menu.add(
				eventWriteMenuItem(
					_("Convert to {groupType}").format(
						groupType=newGroupTypeDesc,
					),
					func=self.groupConvertToFromMenu,
					args=(
						group,
						newGroupType,
					),
				),
			)
		# ---
		bulkItem = eventWriteMenuItem(
			_("Bulk Edit Events"),
			imageName="document-edit.svg",
			func=self.groupBulkEditFromMenu,
			args=(group, path),
		)
		menu.add(bulkItem)
		bulkItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList),
		)
		# ---
		for actionName, actionFuncName in group.actions:
			menu.add(
				eventWriteMenuItem(
					_(actionName),
					func=self.onGroupActionClick,
					args=(
						group,
						actionFuncName,
					),
				),
			)

	def eventAddRightClickMenuItems(
		self,
		menu: gtk.Menu,
		path: list[int],
		group: EventGroupType | EventTrash,
		event: EventType,
	) -> None:
		# log.debug("right click on event", event.summary)
		menu.add(
			eventWriteMenuItem(
				_("Edit"),
				imageName="document-edit.svg",
				func=self.editEventFromMenu,
				args=(path,),
			),
		)
		# ----
		menu.add(
			eventWriteImageMenuItem(
				_("History"),
				"history.svg",
				func=self.historyOfEventFromMenu,
				args=(path,),
			),
		)
		# ----
		moveToItem = eventWriteMenuItem(
			_("Move to {title}").format(title="..."),
		)
		moveToMenu = Menu()
		for new_group in ev.groups:
			assert new_group.id is not None
			if new_group.id == group.id:
				continue
			# if not new_group.enable:  # FIXME
			# 	continue
			new_groupPath = self.treeModel.get_path(self.groupIterById[new_group.id])
			if event.name in new_group.acceptsEventTypes:
				moveToMenu.add(
					menuItemFromEventGroup(
						new_group,
						func=self.moveEventToPathFromMenu,
						args=(
							path,
							new_groupPath,
						),
					),
				)
		moveToItem.set_submenu(moveToMenu)
		menu.add(moveToItem)
		# ----
		menu.add(gtk.SeparatorMenuItem())
		# ----
		menu.add(
			eventWriteMenuItem(
				_("Cut"),
				imageName="edit-cut.svg",
				func=self.cutEvent,
				args=(path,),
			),
		)
		menu.add(
			eventWriteMenuItem(
				_("Copy"),
				imageName="edit-copy.svg",
				func=self.copyEvent,
				args=(path,),
			),
		)
		# --
		if isinstance(group, EventTrash):
			menu.add(gtk.SeparatorMenuItem())
			menu.add(
				eventWriteMenuItem(
					_("Delete", ctx="event manager"),
					imageName="edit-delete.svg",
					func=self.deleteEventFromTrash,
					args=(path,),
				),
			)
		else:
			pasteItem = eventWriteMenuItem(
				_("Paste"),
				imageName="edit-paste.svg",
				func=self.pasteEventFromMenu,
				args=(path,),
			)
			menu.add(pasteItem)
			pasteItem.set_sensitive(self.canPasteToGroup(group))
			# --
			menu.add(gtk.SeparatorMenuItem())
			menu.add(
				eventWriteMenuItem(
					_("Move to {title}").format(title=ev.trash.title),
					imageName=ev.trash.getIconRel(),
					func=self.moveEventToTrashFromMenu,
					args=(path,),
				),
			)

	def genRightClickMenu(self, path: list[int]) -> gtk.Menu:
		# and Select _All menu item
		# log.debug(len(obj_list))
		menu = Menu()
		if len(path) == 2:
			group, event = self.getEventAndParentByPath(path)
			self.eventAddRightClickMenuItems(menu, path, group, event)
			menu.show_all()
			return menu

		assert len(path) == 1

		groupId = self.getRowId(self.treeModel.get_iter(path))
		if groupId == -1:
			self.trashAddRightClickMenuItems(menu, path, ev.trash)
			menu.show_all()
			return menu

		group = ev.groups[groupId]
		self.groupAddRightClickMenuItems(menu, path, group)
		menu.show_all()
		return menu

	def openRightClickMenu(
		self,
		path: list[int],
		etime: int | None = None,
	) -> None:
		menu = self.genRightClickMenu(path)
		if not menu:
			return
		if etime is None:
			etime = gtk.get_current_event_time()
		self.tmpMenu = menu
		menu.popup(None, None, None, None, 3, etime)

	# def onTreeviewRealize(self, gevent):
	# 	# self.reloadEvents()  # FIXME
	# 	pass

	def rowActivated(
		self,
		treev: gtk.TreeView,
		path: list[int],
		_col: gtk.TreeViewColumn,
	) -> None:
		if self.multiSelect:
			return
		if len(path) == 1:
			pathObj = gtk.TreePath(path)
			if treev.row_expanded(pathObj):
				treev.collapse_row(path)
			else:
				treev.expand_row(pathObj, False)
		elif len(path) == 2:
			self.editEventByPath(path)

	def onKeyPress(self, _dialog: gtk.Widget, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "escape":
			return self.onEscape()
		if kname == "menu":  # noqa: SIM102
			# simulate right click (key beside Right-Ctrl)
			if self.multiSelect:
				self.menubar.select_item(self.multiSelectItemMain)
				return True
		return False
		# return self.onTreeviewKeyPress(self.treev, gevent)

	def menuKeyPressOnPath(self, path: list[int], gevent: gdk.EventKey) -> None:
		treev = self.treev
		menu = self.genRightClickMenu(path)
		if not menu:
			return
		rect = treev.get_cell_area(path, treev.get_column(1))
		x = rect.x
		if rtl:
			x -= get_menu_width(menu) + 40
		else:
			x += 40
		dx, dy = treev.translate_coordinates(self, x, rect.y + 2 * rect.height)
		_foo, wx, wy = self.get_window().get_origin()
		self.tmpMenu = menu
		menu.popup(
			None,
			None,
			lambda *_args: (
				wx + dx,
				wy + dy,
				True,
			),
			None,
			3,
			gevent.time,
		)

	def onTreeviewKeyPress(
		self,
		_treev: gtk.TreeView,
		gevent: gdk.EventKey,
	) -> bool:
		# log.debug(now()-gdk.CURRENT_TIME/1000.0)
		# gdk.CURRENT_TIME == 0
		# gevent.time == gtk.get_current_event_time()	# OK
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "menu":  # simulate right click (key beside Right-Ctrl)
			if self.multiSelect:
				self.menubar.select_item(self.multiSelectItemMain)
				return True
			path = self.getSelectedPath()
			if path:
				self.menuKeyPressOnPath(path, gevent)
				return True

		elif kname == "delete":
			if self.multiSelect:
				self.multiSelectDelete()
			else:
				self.moveSelectionToTrash()
			return True

		elif kname == "space":
			if self.multiSelect:
				self.multiSelectTreeviewToggleSelected()
				return True

		elif kname in {"up", "down"}:
			if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
				isDown = kname == "down"
				self.multiSelectShiftUpDownPress(isDown)
				return True

		return False

	def onEscape(self) -> bool:
		if self.multiSelect:
			self.multiSelectCancel()
			return True
		self.hide()
		return True

	def onMenuBarExportClick(self, _menuItem: gtk.MenuItem) -> None:
		MultiGroupExportDialog(transient_for=self).run()

	def onMenuBarImportClick(self, _menuItem: gtk.MenuItem) -> None:
		EventsImportWindow(self).present()

	@staticmethod
	def onMenuBarSearchClick(_menuItem: gtk.MenuItem) -> None:
		assert ui.mainWin is not None
		ui.mainWin.eventSearchShow()

	def _do_checkForOrphans(self) -> None:
		newGroup = ev.groups.checkForOrphans()
		if newGroup is not None:
			self.appendGroupTree(newGroup)

	def onMenuBarOrphanClick(self, _menuItem: gtk.MenuItem) -> None:
		self.waitingDo(self._do_checkForOrphans)

	def getSelectedPath(self) -> list[int] | None:
		iter_ = self.treev.get_selection().get_selected()[1]
		if iter_ is None:
			return None
		return self.treeModel.get_path(iter_).get_indices()

	def mbarEditMenuPopup(self, _menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if path is None:
			return
		selected = bool(path)
		eventSelected = selected and len(path) == 2
		# ---
		self.mbarEditItem.set_sensitive(selected)
		self.mbarCutItem.set_sensitive(eventSelected)
		self.mbarCopyItem.set_sensitive(eventSelected)
		self.mbarDupItem.set_sensitive(selected)
		# ---
		self.mbarPasteItem.set_sensitive(
			selected and self.canPasteToGroup(self.getGroupByPath(path)),
		)

	def onMenuBarEditClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.editGroupByPath(path)
		elif len(path) == 2:
			self.editEventByPath(path)

	def onMenuBarCutClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.treeModel.get_iter(path), True)

	def onMenuBarCopyClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.treeModel.get_iter(path), False)

	def onMenuBarPasteClick(self, _menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.pasteEventToPath(path)

	def onCollapseAllClick(self, _menuItem: gtk.MenuItem) -> None:
		return self.treev.collapse_all()

	def onExpandAllAllClick(self, _menuItem: gtk.MenuItem) -> None:
		return self.treev.expand_all()

	def _do_showDescItemToggled(self) -> None:
		active = self.showDescItem.get_active()
		eventManShowDescription.v = active
		saveConf()
		if active:
			self.treev.append_column(self.colDesc)
		else:
			self.treev.remove_column(self.colDesc)

	def showDescItemToggled(self, _menuItem: gtk.MenuItem) -> None:
		self.waitingDo(self._do_showDescItemToggled)

	def treeviewCursorChangedPath(self, path: list[int]) -> None:
		text = ""
		modified: float | None = None
		if len(path) == 1:
			group = self.getGroupOrTrashByPath(path)
			assert group.id is not None
			if isinstance(group, EventTrash):
				text = _("contains {eventCount} events").format(
					eventCount=_(len(group)),
				)
			else:
				text = (
					_(
						"contains {eventCount} events and {occurCount} occurrences",
					).format(
						eventCount=_(len(group)),
						occurCount=_(group.occurCount),
					)
					+ _(",")
					+ " "
					+ _("Group ID: {groupId}").format(
						groupId=_(group.id),
					)
				)
			modified = group.modified
			# log.info(f"group, id = {group.id}, uuid = {group.uuid}")
		elif len(path) == 2:
			group, event = self.getEventAndParentByPath(path)
			assert event.id is not None
			text = _("Event ID: {eventId}").format(eventId=_(event.id))
			modified = event.modified
			# log.info(f"event, id = {event.id}, uuid = {event.uuid}")
			for rule in event.rulesDict.values():
				log.debug(f"Rule {rule.name}: '{rule}', info='{rule.getInfo()}'")

		if modified is None:
			raise RuntimeError("modified is None")

		comma = _(",")
		modifiedLabel = _("Last Modified")
		modifiedTime = locale_man.textNumEncode(
			epochDateTimeEncode(modified),
		)
		text += f"{comma} {modifiedLabel}: {modifiedTime}"
		if hasattr(self, "sbar"):
			self.sbar.push(0, text)

	def treeviewCursorChanged(self, _selection: gtk.TreeSelection = None) -> bool:
		path = self.getSelectedPath()

		if not self.syncing:
			if path:
				self.treeviewCursorChangedPath(path)
			elif hasattr(self, "sbar"):
				self.sbar.push(0, "")

		self.toolbar.set_sensitive(bool(path))

		return True

	def _do_onGroupModify(self, group: EventGroupType) -> None:
		group.afterModify()
		group.save()  # FIXME
		assert group.id is not None
		try:
			if group.name == "universityTerm":  # FIXME
				groupIter = self.groupIterById[group.id]
				n = self.treeModel.iter_n_children(groupIter)
				for i in range(n):
					eventIter = self.treeModel.iter_nth_child(groupIter, i)
					eid = self.getRowId(eventIter)
					self.treeModel.set_value(
						eventIter,
						self.summaryColIndex,
						group[eid].getSummary(),
					)
		except Exception:
			log.exception("")

	def onGroupModify(self, group: EventGroupType) -> None:
		self.waitingDo(self._do_onGroupModify, group)

	def setGroupEnable(
		self,
		enable: bool,
		group: EventGroupType,
		path: list[int] | None,
	) -> None:
		assert group.id is not None
		if path is None:
			groupIter = self.groupIterById[group.id]
		else:
			groupIter = self.treeModel.get_iter(path)
		group.enable = enable
		self.treeModel.set_value(
			groupIter,
			2,
			common.getTreeGroupPixbuf(group),
		)
		ev.groups.save()
		if (
			group.enable
			and self.treeModel.iter_n_children(groupIter) == 0
			and len(group) > 0
		):
			for event in group:
				self.appendEventRow(groupIter, event)
			self.loadedGroupIds.add(group.id)
		self.onGroupModify(group)

	def onEnableAllClick(self, _menuItem: gtk.MenuItem) -> None:
		for group in ev.groups:
			self.setGroupEnable(True, group, None)

	def onDisableAllClick(self, _menuItem: gtk.MenuItem) -> None:
		for group in ev.groups:
			self.setGroupEnable(False, group, None)

	def toggleEnableGroup(self, group: EventGroupType, path: list[int]) -> bool:
		col = self.pixbufCol
		cell = col.get_cells()[0]
		try:
			cell.get_property("pixbuf")
		except Exception:
			return False
		enable = not group.enable
		self.setGroupEnable(enable, group, path)
		ui.eventUpdateQueue.put("eg", group, self)
		return True

	def onTreeviewLeftButtonPress(
		self,
		treev: gtk.TreeView,
		gevent: gdk.EventButton,
		path: list[int],
		col: gtk.TreeViewColumn,
	) -> None:
		if len(path) != 1:
			log.error(f"onTreeviewLeftButtonPress: unexpected {path=}")
			return

		groupId = self.getRowId(self.treeModel.get_iter(path))
		if groupId != -1 and col == self.pixbufCol:
			group = ev.groups[groupId]
			self.toggleEnableGroup(group, path)
			treev.set_cursor(path)
			return

		if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
			self.multiSelectShiftButtonPress(path)

	def onTreeviewButtonPress(
		self,
		treev: gtk.TreeView,
		gevent: gdk.EventButton,
	) -> None:
		pos_t = treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return

		pathObj: gtk.TreePath | None
		pathObj, col, _xRel, _yRel = pos_t
		if not pathObj:
			return
		path = pathObj.get_indices()

		if gevent.button == 3:
			if self.multiSelect:
				return
			self.openRightClickMenu(path, gevent.time)
			return

		if gevent.button == 1:
			if not col:
				return
			if not rectangleContainsPoint(
				treev.get_cell_area(path, col),
				gevent.x,
				gevent.y,
			):
				return
			self.onTreeviewLeftButtonPress(treev, gevent, path, col)

	def insertNewGroup(self, groupIndex: int) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		group = GroupEditorDialog(transient_for=self).run()
		if group is None:
			return
		ev.groups.insert(groupIndex, group)
		ev.groups.save()
		assert group.id is not None
		beforeGroupIter = self.treeModel.get_iter((groupIndex,))
		self.groupIterById[group.id] = self.treeModel.insert_before(
			self.treeModel.iter_parent(beforeGroupIter),  # parent
			beforeGroupIter,  # sibling
			self.getGroupRow(group),
		)
		self.onGroupModify(group)
		self.loadedGroupIds.add(group.id)

	def addGroupBeforeGroup(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.insertNewGroup(path[0])

	def addGroupBeforeSelection(self, _w: gtk.Widget | None = None) -> None:
		path = self.getSelectedPath()
		if path is None:
			groupIndex = len(self.treeModel) - 1
		else:
			if not isinstance(path, list):
				raise RuntimeError(f"invalid {path = }")
			groupIndex = path[0]
		self.insertNewGroup(groupIndex)

	def duplicateGroup(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getGroupByPath(path)
		newGroup = group.copy()
		ui.duplicateGroupTitle(newGroup)
		newGroup.afterModify()
		newGroup.save()
		assert newGroup.id is not None
		ev.groups.insert(index + 1, newGroup)
		ev.groups.save()
		self.groupIterById[newGroup.id] = self.treeModel.insert(
			None,
			index + 1,
			self.getGroupRow(newGroup),
		)

	def duplicateGroupWithEvents(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getGroupByPath(path)
		newGroup = group.deepCopy()
		ui.duplicateGroupTitle(newGroup)
		newGroup.save()
		ev.groups.insert(index + 1, newGroup)
		ev.groups.save()
		assert newGroup.id is not None
		newGroupIter = self.groupIterById[newGroup.id] = self.treeModel.insert(
			None,
			index + 1,
			self.getGroupRow(newGroup),
		)
		for event in newGroup:
			self.appendEventRow(newGroupIter, event)
		self.loadedGroupIds.add(newGroup.id)

	def syncGroupFromMenu(
		self,
		_menu: gtk.Menu,
		path: list[int],
		account: AccountType,
	) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		group = self.getGroupByPath(path)
		if not group.remoteIds:
			return
		assert group.id is not None
		_aid, remoteGid = group.remoteIds
		# info = {
		# 	"group": group.title,
		# 	"account": account.title,
		# }
		# account.showError is only used in google account
		account.showError = showError  # type: ignore[attr-defined]
		while gtk.events_pending():
			gtk.main_iteration_do(False)
		error = self.waitingDo(account.sync, group, remoteGid)
		if error:
			log.error(error)
		"""
			msg = _(
				"Error in synchronizing group "{group}" with "
				"account "{account}""
			).format(**info) + "\n" + error
			showError(msg, transient_for=self)
		else:
			msg = _(
				"Successful synchronizing of group "{group}" with "
				"account "{account}""
			).format(**info)
			showInfo(msg, transient_for=self)
		"""
		self.reloadGroupEvents(group.id)

	def duplicateGroupFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.duplicateGroup(path)

	def duplicateGroupWithEventsFromMenu(
		self,
		_menu: gtk.Menu,
		path: list[int],
	) -> None:
		self.duplicateGroupWithEvents(path)

	def duplicateSelectedObj(self, _w: gtk.Widget | None = None) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.duplicateGroup(path)
		elif len(path) == 2:  # FIXME
			self.toPasteEvent = (self.treeModel.get_iter(path), False)
			self.pasteEventToPath(path)

	def editGroupByPath(self, path: list[int]) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog

		checkEventsReadOnly()  # FIXME
		group = self.getGroupByPath(path)
		if isinstance(group, EventTrash):
			self.editTrash()
			return

		if group.isReadOnly():
			msg = _(
				'Event group "{groupTitle}" is synchronizing and read-only',
			).format(groupTitle=group.title)
			showError(msg, transient_for=self)
			return

		groupNew = GroupEditorDialog(group, transient_for=self).run()
		if groupNew is None:
			return
		groupIter = self.treeModel.get_iter(path)
		for i, value in enumerate(self.getGroupRow(groupNew)):
			self.treeModel.set_value(groupIter, i, value)
		self.onGroupModify(groupNew)
		ui.eventUpdateQueue.put("eg", groupNew, self)

	def editGroupFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.editGroupByPath(path)

	def _do_deleteGroup(self, path: list[int], group: EventGroupType) -> None:
		trashedIds = group.idList
		if ev.trash.addEventsToBeginning:
			for eid in reversed(trashedIds):
				event = group[eid]
				self.insertEventRow(self.trashIter, 0, event)
		else:
			for eid in trashedIds:
				event = group[eid]
				self.appendEventRow(self.trashIter, event)
		ev.groups.moveToTrash(group, ev.trash)
		ui.eventUpdateQueue.put("-g", group, self)
		self.treeModel.remove(self.treeModel.get_iter(path))

	def deleteGroup(self, path: list[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		group = self.getGroupByPath(path)
		eventCount = len(group)
		if eventCount > 0 and not confirm(
			_(
				'Press Confirm if you want to delete group "{groupTitle}" '
				"and move its {eventCount} events to {trashTitle}",
			).format(
				groupTitle=group.title,
				eventCount=_(eventCount),
				trashTitle=ev.trash.title,
			),
			transient_for=self,
		):
			return
		self.waitingDo(self._do_deleteGroup, path, group)

	def deleteGroupFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.deleteGroup(path)

	def addEventToGroupFromMenu(
		self,
		_menu: gtk.Menu,
		path: list[int],
		group: EventGroupType,
		eventType: str,
		title: str,
	) -> None:
		event = addNewEvent(
			group,
			eventType,
			title=title,
			transient_for=self,
		)
		if event is None:
			return
		ui.eventUpdateQueue.put("+", event, self)
		groupIter = self.treeModel.get_iter(path)
		self.addNewEventRow(group, groupIter, event)
		self.treeviewCursorChanged()

	def addNewEventRow(
		self,
		group: EventGroupType,
		groupIter: gtk.TreeIter,
		event: EventType,
	) -> None:
		if group.id not in self.loadedGroupIds:
			return
		if group.addEventsToBeginning:
			self.insertEventRow(groupIter, 0, event)
			return
		self.appendEventRow(groupIter, event)

	def addGenericEventToGroupFromMenu(
		self,
		_menu: gtk.Menu,
		path: list[int],
		group: EventGroupType,
	) -> None:
		event = addNewEvent(
			group,
			group.acceptsEventTypes[0],
			typeChangable=True,
			title=_("Add Event"),
			transient_for=self,
		)
		if event is None:
			return
		ui.eventUpdateQueue.put("+", event, self)
		groupIter = self.treeModel.get_iter(path)
		self.addNewEventRow(group, groupIter, event)
		self.treeviewCursorChanged()

	def updateEventRow(self, event: EventType) -> None:
		assert event.id is not None
		self.updateEventRowByIter(
			event,
			self.eventsIter[event.id],
		)

	def updateEventRowByIter(
		self,
		event: EventType,
		eventIter: gtk.TreeIter,
	) -> None:
		for i, value in enumerate(self.getEventRow(event)):
			self.treeModel.set_value(eventIter, i, value)
		self.treeviewCursorChanged()

	def editEventByPath(self, path: list[int]) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog

		event = self.getEventByPath(path)
		eventNew = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self,
		).run()
		if eventNew is None:
			return
		ui.eventUpdateQueue.put("e", eventNew, self)
		self.updateEventRow(eventNew)

	def editEventFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.editEventByPath(path)

	def moveEventToPathFromMenu(
		self,
		_menu: gtk.Menu,
		path: list[int],
		targetPath: list[int],
	) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), True)
		self.pasteEventToPath(targetPath, False)

	def moveEventToTrashByPath(self, path: list[int]) -> None:
		group, event = self.getEventAndGroupByPath(path)
		if not confirmEventTrash(event, transient_for=self):
			return
		ui.moveEventToTrash(group, event, self)
		self.treeModel.remove(self.treeModel.get_iter(path))
		self.addEventRowToTrash(event)

	def addEventRowToTrash(self, event: EventType) -> None:
		if ev.trash.addEventsToBeginning:
			self.insertEventRow(self.trashIter, 0, event)
		else:
			self.appendEventRow(self.trashIter, event)

	def moveEventToTrashFromMenu(self, _menu: gtk.Menu, path: list[int]) -> None:
		self.moveEventToTrashByPath(path)

	def moveSelectionToTrash(self) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.deleteGroup(path)
		elif len(path) == 2:
			self.moveEventToTrashByPath(path)

	def deleteEventFromTrash(self, _menu: gtk.Menu, path: list[int]) -> None:
		event = self.getEventByPath(path)
		assert event.id is not None
		ev.trash.delete(event.id)  # trash == ev.trash
		ev.trash.save()
		self.treeModel.remove(self.treeModel.get_iter(path))
		# no need to send to ui.eventUpdateQueue right now
		# since events in trash (or their occurrences) are not displayed
		# outside Event Manager

	def removeIterChildren(self, gIter: gtk.TreeIter) -> None:
		while (childIter := self.treeModel.iter_children(gIter)) is not None:
			self.treeModel.remove(childIter)

	def emptyTrash(self, _menuItem: gtk.MenuItem) -> None:
		ev.trash.empty()
		self.removeIterChildren(self.trashIter)
		self.treeviewCursorChanged()

	def editTrash(self, _menuItem: gtk.MenuItem | None = None) -> None:
		TrashEditorDialog(transient_for=self).run()
		self.treeModel.set_value(
			self.trashIter,
			2,
			eventTreeIconPixbuf(ev.trash.getIconRel()),
		)
		self.treeModel.set_value(
			self.trashIter,
			3,
			ev.trash.title,
		)
		# TODO: perhaps should put on eventUpdateQueue
		# ui.eventUpdateQueue.put("et", ev.trash, self)
		# as a UI improvement, in case icon of title is changed

	def moveUp(self, path: list[int]) -> None:
		srcIter = self.treeModel.get_iter(path)
		if not isinstance(path, list):
			raise TypeError(f"invalid {path = }")
		if len(path) == 1:
			if path[0] == 0:
				return
			if self.getRowId(srcIter) == -1:
				return
			tarIter = self.treeModel.get_iter(path[0] - 1)
			self.treeModel.move_before(srcIter, tarIter)
			ev.groups.moveUp(path[0])
			ev.groups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			parentObj, event = self.getEventAndParentByPath(path)
			parentIndex, eventIndex = path
			# log.debug(eventIndex, parentLen)
			if eventIndex > 0:
				tarIter = self.treeModel.get_iter(
					(parentIndex, eventIndex - 1),
				)
				self.treeModel.move_before(srcIter, tarIter)
				# ^ or use self.treeModel.swap FIXME
				parentObj.moveUp(eventIndex)
				parentObj.save()
			else:
				# move event to end of previous group
				# if isinstance(parentObj, EventTrash):
				# 	return
				if parentIndex < 1:
					return
				newParentIter = self.treeModel.get_iter(parentIndex - 1)
				newParentId = self.getRowId(newParentIter)
				if newParentId == -1:  # could not be!
					return
				newGroup = ev.groups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.treeModel.remove(srcIter)
				self.appendEventRow(newParentIter, event)
				# ---
				parentObj.remove(event)
				parentObj.save()
				newGroup.append(event)
				newGroup.save()
			ui.eventUpdateQueue.put("r", parentObj, self)
		else:
			raise ValueError(f"invalid tree path {path}")
		newPath = self.treeModel.get_path(srcIter)
		if len(path) == 2:
			self.treev.expand_to_path(newPath)
		self.treev.set_cursor(newPath)
		self.treev.scroll_to_cell(newPath)

	def moveDown(self, path: list[int]) -> None:
		if not isinstance(path, list):
			raise TypeError(f"invalid {path = }")
		srcIter = self.treeModel.get_iter(path)
		if len(path) == 1:
			if self.getRowId(srcIter) == -1:
				return
			tarIter = self.treeModel.get_iter(path[0] + 1)
			if self.getRowId(tarIter) == -1:
				return
			self.treeModel.move_after(srcIter, tarIter)
			# or use self.treeModel.swap FIXME
			ev.groups.moveDown(path[0])
			ev.groups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			parentObj, event = self.getEventAndParentByPath(path)
			parentLen = len(parentObj)
			parentIndex, eventIndex = path
			# log.debug(eventIndex, parentLen)
			if eventIndex < parentLen - 1:
				tarIter = self.treeModel.get_iter(
					(
						parentIndex,
						eventIndex + 1,
					),
				)
				self.treeModel.move_after(srcIter, tarIter)
				parentObj.moveDown(eventIndex)
				parentObj.save()
			else:
				# move event to top of next group
				if isinstance(parentObj, EventTrash):
					return
				newParentIter = self.treeModel.get_iter(parentIndex + 1)
				newParentId = self.getRowId(newParentIter)
				if newParentId == -1:
					return
				newGroup = ev.groups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.treeModel.remove(srcIter)
				srcIter = self.insertEventRow(newParentIter, 0, event)
				# ---
				parentObj.remove(event)
				parentObj.save()
				newGroup.insert(0, event)
				newGroup.save()
			ui.eventUpdateQueue.put("r", parentObj, self)
		else:
			raise RuntimeError(f"invalid tree path {path}")
		newPath = self.treeModel.get_path(srcIter)
		if len(path) == 2:
			self.treev.expand_to_path(newPath)
		self.treev.set_cursor(newPath)
		self.treev.scroll_to_cell(newPath)

	def moveUpFromMenu(self, _menuItem: gtk.MenuItem, path: list[int]) -> None:
		self.moveUp(path)

	def moveDownFromMenu(self, _menuItem: gtk.MenuItem, path: list[int]) -> None:
		self.moveDown(path)

	def moveUpByButton(self, _tb: gtk.Button) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.moveUp(path)

	def moveDownByButton(self, _tb: gtk.Button) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.moveDown(path)

	def groupExportFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		group: EventGroupType,
	) -> None:
		SingleGroupExportDialog(group, transient_for=self).run()

	def groupSortFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		path: list[int],
	) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		group = self.getGroupByPath(path)
		if not GroupSortDialog(group, transient_for=self).run():
			return
		if group.id not in self.loadedGroupIds and group.name != "trash":
			return
		groupIter = self.treeModel.get_iter(path)
		pathObj = gtk.TreePath(path)
		expanded = self.treev.row_expanded(pathObj)
		self.removeIterChildren(groupIter)
		for event in group:
			self.appendEventRow(groupIter, event)
		if expanded:
			self.treev.expand_row(pathObj, False)

	def groupConvertCalTypeFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		group: EventGroupType,
	) -> None:
		if GroupConvertCalTypeDialog(group, transient_for=self).perform():
			ui.eventUpdateQueue.put("r", group, self)

	def _do_groupConvertTo(
		self,
		group: EventGroupType,
		newGroupType: str,
	) -> None:
		idsCount = len(group.idList)
		newGroup = ev.groups.convertGroupTo(group, newGroupType)
		assert newGroup.id is not None
		# FIXME: reload its events in tree?
		# summary and description have been not changed!
		idsCount2 = len(newGroup.idList)
		if idsCount2 != idsCount:
			self.reloadGroupEvents(newGroup.id)
		self.treeviewCursorChanged()
		ui.eventUpdateQueue.put("eg", newGroup, self)

	def groupConvertToFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		group: EventGroupType,
		newGroupType: str,
	) -> None:
		self.waitingDo(self._do_groupConvertTo, group, newGroupType)

	def _do_groupBulkEdit(
		self,
		dialog: gtk.Dialog,
		group: EventGroupType,
		path: list[int],
	) -> None:
		pathObj = gtk.TreePath(path)
		expanded = self.treev.row_expanded(pathObj)
		dialog.doAction()
		dialog.destroy()
		self.treeModel.remove(self.treeModel.get_iter(pathObj))
		self.insertGroupTree(path[0], group)
		if expanded:
			self.treev.expand_row(pathObj, False)
		self.treev.set_cursor(pathObj)
		ui.eventUpdateQueue.put("r", group, self)

	def groupBulkEditFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		group: EventGroupType,
		path: list[int],
	) -> None:
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog

		dialog = EventsBulkEditDialog(group, transient_for=self)
		if dialog.run() == gtk.ResponseType.OK:
			self.waitingDo(self._do_groupBulkEdit, dialog, group, path)

	def onGroupActionClick(
		self,
		_menuItem: gtk.MenuItem,
		group: EventGroupType,
		actionFuncName: str,
	) -> None:
		func = getattr(group, actionFuncName, None)
		if func is None:
			setActionFuncs(group)
			func = getattr(group, actionFuncName)
		self.waitingDo(func, parentWin=self)

	def cutEvent(self, _menuItem: gtk.MenuItem, path: list[int]) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), True)

	def copyEvent(self, _menuItem: gtk.MenuItem, path: list[int]) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), False)

	def pasteEventFromMenu(
		self,
		_menuItem: gtk.MenuItem,
		targetPath: list[int],
	) -> None:
		self.pasteEventToPath(targetPath)

	def _pasteEventToPath(
		self,
		srcIter: gtk.TreeIter,
		move: bool,
		targetPath: list[int],
	) -> gtk.TreeIter:
		srcPath = self.treeModel.get_path(srcIter)
		srcGroup, srcEvent = self.getEventAndGroupByPath(srcPath)
		tarGroup = self.getGroupByPath(targetPath)
		self.checkEventToAdd(tarGroup, srcEvent)
		if len(targetPath) == 1:
			tarGroupIter = self.treeModel.get_iter(targetPath)
			tarEventIter = None
			tarEventIndex = len(tarGroup)
		elif len(targetPath) == 2:
			tarGroupIter = self.treeModel.get_iter(targetPath[:1])
			tarEventIter = self.treeModel.get_iter(targetPath)
			tarEventIndex = targetPath[1]
		# ----
		if move:
			srcGroup.remove(srcEvent)
			srcGroup.save()
			tarGroup.insert(tarEventIndex, srcEvent)
			tarGroup.save()
			self.treeModel.remove(self.treeModel.get_iter(srcPath))
			newEvent = srcEvent
			ui.eventUpdateQueue.put("r", srcGroup, self)
		else:
			newEvent = srcEvent.copy()
			newEvent.save()
			tarGroup.insert(tarEventIndex, newEvent)
			tarGroup.save()
		ui.eventUpdateQueue.put("+", newEvent, self)
		# although we insert the new event (not append) to group
		# it should not make any difference, since only occurrences (and not
		# events) are displayed outside Event Manager
		# ----
		if tarEventIter:
			newEventIter = self.insertEventRowAfter(
				tarGroupIter,
				tarEventIter,
				newEvent,
			)
		else:
			newEventIter = self.appendEventRow(tarGroupIter, newEvent)
		return newEventIter

	def pasteEventToPath(
		self,
		targetPath: list[int],
		doScroll: bool = True,
	) -> None:
		if not self.toPasteEvent:
			return
		srcIter, move = self.toPasteEvent
		newEventIter = self._pasteEventToPath(srcIter, move, targetPath)
		if doScroll:
			self.treev.set_cursor(self.treeModel.get_path(newEventIter))
		self.toPasteEvent = None
