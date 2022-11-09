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

from time import time as now

import os
import sys
from os.path import join, dirname, split, splitext
from collections import OrderedDict as odict
from contextlib import suppress

from typing import Optional, List, Tuple, Union, Any

from scal3.path import *
from scal3 import cal_types
from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3.json_utils import (
	loadModuleJsonConf,
	saveModuleJsonConf,
)
from scal3 import event_lib as lib
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	dialog_add_button,
	confirm,
	showError,
	showInfo,
	rectangleContainsPoint,
	labelImageButton,
	newHSep,
	get_menu_width,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)
from scal3.ui_gtk.mywidgets.resize_button import ResizeButton
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event import setActionFuncs
from scal3.ui_gtk.event.utils import (
	confirmEventTrash,
	confirmEventsTrash,
	checkEventsReadOnly,
	eventWriteMenuItem,
	eventWriteImageMenuItem,
	eventTreeIconPixbuf,
	menuItemFromEventGroup,
)
from scal3.ui_gtk.event.editor import addNewEvent
from scal3.ui_gtk.event.trash import TrashEditorDialog
from scal3.ui_gtk.event.export import (
	SingleGroupExportDialog,
	MultiGroupExportDialog,
)
from scal3.ui_gtk.event.import_event import EventsImportWindow
from scal3.ui_gtk.event.group_op import (
	GroupSortDialog,
	GroupConvertCalTypeDialog,
)
from scal3.ui_gtk.event.account_op import FetchRemoteGroupsDialog
from scal3.ui_gtk.event.history import EventHistoryDialog

# log.debug("Testing translator", __file__, _("About"))


EventOrGroup = Union[lib.Event, lib.EventGroup]

confPath = join(confDir, "event", "manager.json")

confParams = (
	"eventManPos",
	"eventManShowDescription",
)

# change date of a dailyNoteEvent when editing it
# dailyNoteChDateOnEdit = True

eventManPos = (0, 0)
eventManShowDescription = True


def loadConf() -> None:
	loadModuleJsonConf(__name__)


def saveConf() -> None:
	saveModuleJsonConf(__name__)


class EventManagerToolbar(StaticToolBox):
	def __init__(self, parent):
		StaticToolBox.__init__(
			self,
			parent,
			vertical=True,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		# self.append(ToolBoxItem(
		# 	name="goto-top",
		# 	imageName="go-top.svg",
		# 	onClick="",
		# 	desc=_("Move to top"),
		# 	continuousClick=False,
		# ))
		self.extend([
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
		])


@registerSignals
class EventManagerDialog(gtk.Dialog, MyDialog, ud.BaseCalObj):  # FIXME
	_name = "eventMan"
	desc = _("Event Manager")

	def onShow(self, widget: gtk.Widget) -> None:
		global eventManPos
		self.move(*eventManPos)
		self.onConfigChange()

	def onDeleteEvent(self, dialog: gtk.Dialog, gevent: gdk.Event) -> bool:
		# onResponse is called before onDeleteEvent
		# just return True, no need to do anything else
		# without this signal handler, the window will be distroyed
		# and can not be opened again
		return True

	def onResponse(self, dialog: gtk.Dialog, response_id: int) -> None:
		global eventManPos
		eventManPos = self.get_position()
		saveConf()
		###
		self.hide()

	# def findEventByPath(self, eid: int, path: List[int]):
	# 	groupIndex, eventIndex = path

	def onConfigChange(self, *a, **kw) -> None:
		ud.BaseCalObj.onConfigChange(self, *a, **kw)
		###
		if not self.isLoaded:
			if self.get_property("visible"):
				self.waitingDo(self.reloadEvents)  # FIXME
			return

	def onEventUpdate(self, record: "EventUpdateRecord") -> None:
		action = record.action

		if action == "r":  # reload group or trash
			if isinstance(record.obj, lib.EventTrash):
				if self.trashIter:
					self.treeModel.remove(self.trashIter)
				self.appendTrash()
				return
			self.reloadGroupEvents(record.obj.id)

		elif action == "+g":  # new group with events inside it (imported)
			self.appendGroupTree(record.obj)

		elif action == "-g":
			log.error(f"Event Manager: onEventUpdate: unexpected {action=}")

		elif action == "eg":  # edit group
			group = record.obj
			groupIter = self.groupIterById[group.id]
			for i, value in enumerate(self.getGroupRow(group)):
				self.treeModel.set_value(groupIter, i, value)

		elif action == "-":
			eventIter = self.eventsIter.get(record.obj.id)
			if eventIter is None:
				if record.obj.parent.id in self.loadedGroupIds:
					log.error(
						"trying to delete non-existing event row, " +
						f"eid={record.obj.id}, {path=}"
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
			if record.obj.parent.id not in self.loadedGroupIds:
				return
			parentIter = self.groupIterById[record.obj.parent.id]
			# event is always added to the end of group (at least from
			# outside Event Manager dialog), unless we add a bool global option
			# to add all created events to the beginning of group (prepend)
			self.appendEventRow(parentIter, record.obj)

		elif action == "e":
			eventIter = self.eventsIter.get(record.obj.id)
			if eventIter is None:
				if record.obj.parent.id in self.loadedGroupIds:
					log.error(
						"trying to edit non-existing event row, " +
						f"eid={record.obj.id}"
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
		####
		self.syncing = None  # or a tuple of (groupId, statusText)
		self.groupIterById = {}
		self.trashIter = None
		self.isLoaded = False
		self.loadedGroupIds = set()
		self.eventsIter = {}
		####
		self.multiSelect = False
		self.multiSelectPathDict = odict()
		self.multiSelectToPaste = None  # Optional[Tuple[bool, List[gtk.TreeIter]]]
		####
		self.set_title(_("Event Manager"))
		self.resize(800, 600)
		self.connect("delete-event", self.onDeleteEvent)
		self.set_transient_for(None)
		self.set_type_hint(gdk.WindowTypeHint.NORMAL)
		##
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_Apply", ctx="window action"),
			res=gtk.ResponseType.OK,
		)
		# self.connect("response", lambda w, e: self.hide())
		self.connect("response", self.onResponse)
		self.connect("show", self.onShow)
		#######
		menubar = self.menubar = gtk.MenuBar()
		####
		fileItem = self.fileItem = MenuItem(_("_File"))
		fileMenu = Menu()
		fileItem.set_submenu(fileMenu)
		menubar.append(fileItem)
		##
		addGroupItem = MenuItem(_("Add New Group"))
		addGroupItem.set_sensitive(not lib.allReadOnly)
		addGroupItem.connect("activate", self.addGroupBeforeSelection)
		# FIXME: or before selected group?
		fileMenu.append(addGroupItem)
		##
		# FIXME right place?
		searchItem = MenuItem(_("_Search Events"))
		searchItem.connect("activate", self.onMenuBarSearchClick)
		fileMenu.append(searchItem)
		##
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", self.onMenuBarExportClick)
		fileMenu.append(exportItem)
		##
		importItem = MenuItem(_("_Import", ctx="menu"))
		importItem.set_sensitive(not lib.allReadOnly)
		importItem.connect("activate", self.onMenuBarImportClick)
		fileMenu.append(importItem)
		##
		orphanItem = MenuItem(_("Check for Orphan Events"))
		orphanItem.set_sensitive(not lib.allReadOnly)
		orphanItem.connect("activate", self.onMenuBarOrphanClick)
		fileMenu.append(orphanItem)
		####
		editItem = self.editItem = MenuItem(_("_Edit"))
		if lib.allReadOnly:
			editItem.set_sensitive(False)
		else:
			editMenu = Menu()
			editItem.set_submenu(editMenu)
			menubar.append(editItem)
			##
			editEditItem = MenuItem(_("Edit"))
			editEditItem.connect("activate", self.onMenuBarEditClick)
			editMenu.append(editEditItem)
			editMenu.connect("show", self.mbarEditMenuPopup)
			self.mbarEditItem = editEditItem
			##
			editMenu.append(gtk.SeparatorMenuItem())
			##
			cutItem = MenuItem(_("Cu_t"))
			cutItem.connect("activate", self.onMenuBarCutClick)
			editMenu.append(cutItem)
			self.mbarCutItem = cutItem
			##
			copyItem = MenuItem(_("_Copy"))
			copyItem.connect("activate", self.onMenuBarCopyClick)
			editMenu.append(copyItem)
			self.mbarCopyItem = copyItem
			##
			pasteItem = MenuItem(_("_Paste"))
			pasteItem.connect("activate", self.onMenuBarPasteClick)
			editMenu.append(pasteItem)
			self.mbarPasteItem = pasteItem
			##
			editMenu.append(gtk.SeparatorMenuItem())
			##
			dupItem = MenuItem(_("_Duplicate"))
			dupItem.connect("activate", self.duplicateSelectedObj)
			editMenu.append(dupItem)
			self.mbarDupItem = dupItem
			##
			editMenu.append(gtk.SeparatorMenuItem())
			##
			enableAllItem = MenuItem(_("Enable All Groups"))
			enableAllItem.connect("activate", self.onEnableAllClick)
			editMenu.append(enableAllItem)
			self.mbarEnableAllItem = enableAllItem
			##
			disableAllItem = MenuItem(_("Disable All Groups"))
			disableAllItem.connect("activate", self.onDisableAllClick)
			editMenu.append(disableAllItem)
			self.mbarDisableAllItem = disableAllItem
		####
		viewItem = MenuItem(_("_View"))
		viewMenu = Menu()
		viewItem.set_submenu(viewMenu)
		menubar.append(viewItem)
		##
		collapseItem = MenuItem(_("Collapse All"))
		collapseItem.connect("activate", self.onCollapseAllClick)
		viewMenu.append(collapseItem)
		##
		expandItem = MenuItem(_("Expand All"))
		expandItem.connect("activate", self.onExpandAllAllClick)
		viewMenu.append(expandItem)  # noqa: FURB113
		##
		viewMenu.append(gtk.SeparatorMenuItem())
		##
		self.showDescItem = gtk.CheckMenuItem(label=_("Show _Description"))
		self.showDescItem.set_use_underline(True)
		self.showDescItem.set_active(eventManShowDescription)
		self.showDescItem.connect("toggled", self.showDescItemToggled)
		viewMenu.append(self.showDescItem)
		####
		# testItem = MenuItem(_("Test"))
		# testMenu = Menu()
		# testItem.set_submenu(testMenu)
		# menubar.append(testItem)
		###
		# item = MenuItem("")
		# item.connect("activate", )
		# testMenu.append(item)
		####
		multiSelectMenu = Menu()
		multiSelectItemMain = MenuItem(label=_("Multi-select"))
		self.multiSelectItemMain = multiSelectItemMain
		multiSelectItemMain.set_submenu(multiSelectMenu)
		menubar.append(multiSelectItemMain)
		##
		multiSelectItem = gtk.CheckMenuItem(label=_("Multi-select"))
		multiSelectItem.connect("activate", self.multiSelectToggle)
		multiSelectMenu.append(multiSelectItem)
		self.multiSelectItem = multiSelectItem
		self.multiSelectItemsOther = []
		####
		multiSelectMenu.append(gtk.SeparatorMenuItem())
		####
		cutItem = MenuItem(_("Cu_t"))
		cutItem.connect("activate", self.multiSelectCut)
		self.multiSelectItemsOther.append(cutItem)
		##
		copyItem = MenuItem(_("_Copy"))
		copyItem.connect("activate", self.multiSelectCopy)
		self.multiSelectItemsOther.append(copyItem)
		##
		pasteItem = MenuItem(_("_Paste"))
		pasteItem.connect("activate", self.multiSelectPaste)
		self.multiSelectItemsOther.append(pasteItem)
		##
		self.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		##
		deleteItem = MenuItem(_("Delete", ctx="event manager"))
		deleteItem.connect("activate", self.multiSelectDelete)
		self.multiSelectItemsOther.append(deleteItem)
		##
		self.multiSelectItemsOther.append(gtk.SeparatorMenuItem())
		##
		bulkEditItem = MenuItem(_("Bulk Edit Events"))
		# imageName="document-edit.svg",
		# native CheckMenuItem and ImageMenuItem are not aligned
		bulkEditItem.connect("activate", self.multiSelectBulkEdit)
		self.multiSelectItemsOther.append(bulkEditItem)
		##
		exportItem = MenuItem(_("_Export", ctx="menu"))
		exportItem.connect("activate", self.multiSelectExport)
		self.multiSelectItemsOther.append(exportItem)
		###
		for item in self.multiSelectItemsOther:
			item.set_sensitive(False)
			multiSelectMenu.append(item)
		####
		menubar.show_all()
		pack(self.vbox, menubar)
		#######
		# multi-select bar
		self.multiSelectHBox = hbox = HBox(spacing=3)
		self.multiSelectLabel = gtk.Label(label=_("No event selected"))
		self.multiSelectLabel.set_xalign(0)
		self.multiSelectLabel.get_style_context().add_class("smaller")
		pack(hbox, self.multiSelectLabel, 1, 1)

		pack(hbox, self.smallerButton(
			label=_("Copy"),
			# imageName="edit-copy.svg",
			func=self.multiSelectCopy,
			tooltip=_("Copy"),
		))
		pack(hbox, self.smallerButton(
			label=_("Cut"),
			# imageName="edit-cut.svg",
			func=self.multiSelectCut,
			tooltip=_("Cut"),
		))
		self.multiSelectPasteButton = self.smallerButton(
			label=_("Paste"),
			# imageName="edit-paste.svg",
			func=self.multiSelectPaste,
			tooltip=_("Paste"),
		)
		pack(hbox, self.multiSelectPasteButton)
		self.multiSelectPasteButton.set_sensitive(False)
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.smallerButton(
			label=_("Delete", ctx="event manager"),
			imageName="edit-delete.svg",
			func=self.multiSelectDelete,
			tooltip=_("Move to {title}").format(title=ui.eventTrash.title),
		))
		pack(hbox, gtk.Label(), 1, 1)
		pack(hbox, self.smallerButton(
			label=_("Cancel"),
			imageName="dialog-cancel.svg",
			func=self.multiSelectCancel,
			tooltip=_("Cancel"),
		))
		###
		pack(self.vbox, hbox)
		#######
		treeBox = HBox()
		#####
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
		#####
		swin = gtk.ScrolledWindow()
		swin.add(self.treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(treeBox, swin, 1, 1)
		###
		self.toolbar = EventManagerToolbar(self)
		###
		pack(treeBox, self.toolbar)
		#####
		pack(self.vbox, treeBox, 1, 1)
		#######
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
		###
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
		###
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
		###
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
		###
		cell = gtk.CellRendererText()
		col = self.colDesc = gtk.TreeViewColumn(
			title=_("Description"),
			cell_renderer=cell,
			text=4,
		)
		col.set_sizing(gtk.TreeViewColumnSizing.FIXED)
		col.set_property("expand", True)
		if eventManShowDescription:
			self.treev.append_column(col)
		###
		# self.treev.set_search_column(2)## or 3
		###
		self.toPasteEvent = None  # (treeIter, bool move)
		#####
		hbox = HBox()
		hbox.set_direction(gtk.TextDirection.LTR)
		self.sbar = gtk.Statusbar()
		self.sbar.set_direction(gtk.TextDirection.LTR)
		pack(hbox, self.sbar, 1, 1)
		pack(hbox, ResizeButton(self))
		pack(self.vbox, hbox)
		#####
		self.vbox.show_all()
		self.multiSelectHBox.hide()

	def multiSelectTreeviewToggleStatus(
		self,
		column,
		cell,
		model,
		_iter,
		userData,
	):
		if not self.multiSelect:
			return

		path = model.get_path(_iter).get_indices()
		value = model.get_value(_iter, 0)
		if len(path) == 2:
			cell.set_property("inconsistent", False)
			cell.set_active(value)
			return

		groupIndex = path[0]
		group = self.getObjsByPath(path)[0]
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

	def smallerButton(self, label="", imageName="", func=None, tooltip=""):
		button = labelImageButton(
			label=label,
			imageName=imageName,
			func=func,
			tooltip=tooltip,
			spacing=4,
		)
		button.get_style_context().add_class("smaller")
		return button

	def multiSelectSetEnable(self, enable: bool):
		self.multiSelectHBox.set_visible(enable)
		self.multiSelectColumn.set_visible(enable)
		self.editItem.set_sensitive(not enable)
		self.fileItem.set_sensitive(not enable)
		self.toolbar.set_sensitive(not enable)
		for item in self.multiSelectItemsOther:
			item.set_sensitive(enable)
		self.multiSelect = enable

	def multiSelectToggle(self, menuItem: gtk.MenuItem):
		enable = menuItem.get_active()
		self.multiSelectSetEnable(enable)

	def multiSelectShiftUpDownPress(self, isDown: bool):
		path = self.getSelectedPath()
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
		path: "List[int]",
		col: "gtk.TreeViewColumn",
		group,
		event,
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
		return True

	def multiSelectLabelUpdate(self):
		self.multiSelectLabel.set_label(_("{count} events selected").format(
			count=_(sum([
				len(eventIndexes)
				for eventIndexes in self.multiSelectPathDict.values()
			])),
		))

	def multiSelectTreeviewToggleSelected(self):
		path = self.getSelectedPath()
		self.multiSelectTreeviewTogglePath(path)

	def multiSelectTreeviewToggle(
		self,
		cell: "gtk.CellRendererToggle",
		pathStr: str,
	):
		path = gtk.TreePath.new_from_string(pathStr).get_indices()
		self.multiSelectTreeviewTogglePath(path)

	def multiSelectCBActivate(self, groupIndex, eventIndex):
		if groupIndex not in self.multiSelectPathDict:
			self.multiSelectPathDict[groupIndex] = odict()
		self.multiSelectPathDict[groupIndex][eventIndex] = None

	def multiSelectCBSetEvent(self, groupIndex, eventIndex, active):
		model = self.treeModel
		itr = model.get_iter((groupIndex, eventIndex))
		model.set_value(itr, 0, active)
		if active:
			self.multiSelectCBActivate(groupIndex, eventIndex)
		else:
			if groupIndex in self.multiSelectPathDict:
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
				count == len(ui.eventGroups[self.getRowId(parentIter)]),
			)

		self.multiSelectLabelUpdate()

	def multiSelectCBSetGroup(self, groupIndex, eventIndex, active):
		if active:
			return self.multiSelectCBActivate(groupIndex, eventIndex)

		if groupIndex in self.multiSelectPathDict:
			del self.multiSelectPathDict[groupIndex]

	def multiSelectTreeviewTogglePath(self, path: "List[int]"):
		model = self.treeModel
		if len(path) not in (1, 2):
			raise RuntimeError(f"invalid path depth={len(path)}, {pathStr=}")
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

	def multiSelectCopy(self, obj=None):
		model = self.treeModel
		iterList = list(self.multiSelectIters())
		self.multiSelectToPaste = (False, iterList)
		self.multiSelectPasteButton.set_sensitive(True)

	def multiSelectCut(self, obj=None):
		model = self.treeModel
		iterList = list(self.multiSelectIters())
		self.multiSelectToPaste = (True, iterList)
		self.multiSelectPasteButton.set_sensitive(True)

	def multiSelectPaste(self, obj=None):
		toPaste = self.multiSelectToPaste
		if toPaste is None:
			log.error("nothing to paste")
			return

		treev = self.treev
		model = self.treeModel
		move, iterList = toPaste
		if not iterList:
			return

		targetPath = self.getSelectedPath()
		newEventIter = None

		if len(targetPath) == 2:
			iterList = list(reversed(iterList))
			# so that events are inserted in the same order as they are selected

		for srcIter in iterList:
			_iter = self._pasteEventToPath(srcIter, move, targetPath)
			if newEventIter is None:
				newEventIter = _iter

		if not move:
			for _iter in iterList:
				model.set_value(_iter, 0, False)

		if move:
			msg = _("{count} events successfully moved")
		else:
			msg = _("{count} events successfully copied")
		self.sbar.push(0, msg.format(
			count=_(len(iterList)),
		))

		self.multiSelectOperationFinished()
		self.multiSelectToPaste = None

		if newEventIter:
			self.treev.set_cursor(self.treeModel.get_path(newEventIter))

	def _do_multiSelectDelete(self, iterList):
		model = self.treeModel

		saveGroupSet = set()
		ui.eventUpdateQueue.pauseLoop()

		for _iter in iterList:
			path = model.get_path(_iter)
			group, event = self.getObjsByPath(path)

			if group.name == "trash":
				group.delete(event.id)  # group == ui.eventTrash
				saveGroupSet.add(group)
				model.remove(_iter)
				continue

			ui.moveEventToTrash(group, event, self, save=False)
			saveGroupSet.add(group)
			saveGroupSet.add(ui.eventTrash)
			model.remove(_iter)
			self.addEventRowToTrash(event)

		for group in saveGroupSet:
			group.save()

		ui.eventUpdateQueue.resumeLoop()

	def multiSelectOperationFinished(self):
		model = self.treeModel
		for groupIndex in self.multiSelectPathDict:
			with suppress(ValueError):
				model.set_value(model.get_iter([groupIndex]), 0, False)

		self.multiSelectPathDict = odict()
		self.multiSelectLabelUpdate()
		self.multiSelectPasteButton.set_sensitive(False)

	def multiSelectDelete(self, obj=None):
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
			msgs.append(_("Moved {count} events to {title}").format(
				count=_(toTrashCount),
				title=ui.eventTrash.title,
			))
		if deleteCount:
			msgs.append(_("Deleted {count} events from {title}").format(
				count=_(deleteCount),
				title=ui.eventTrash.title,
			))
		self.sbar.push(0, _(", ").join(msgs))

		self.multiSelectOperationFinished()

	def multiSelectIters(self):
		model = self.treeModel
		for groupIndex, eventIndexes in self.multiSelectPathDict.items():
			for eventIndex in eventIndexes:
				yield model.get_iter((groupIndex, eventIndex))

	def multiSelectCancel(self, obj=None):
		model = self.treeModel
		self.multiSelectSetEnable(False)
		self.multiSelectItem.set_active(False)
		for _iter in self.multiSelectIters():
			model.set_value(_iter, 0, False)
		self.multiSelectOperationFinished()

	def multiSelectEventIdsDict(self) -> "Dict[int, List[int]]":
		model = self.treeModel
		idsDict = odict()
		for groupIndex, eventIndexes in self.multiSelectPathDict.items():
			groupId = self.getRowId(model.get_iter((groupIndex,)))
			idsDict[groupId] = [
				self.getRowId(model.get_iter((groupIndex, eventIndex)))
				for eventIndex in eventIndexes
			]
		return idsDict

	def multiSelectEventIdsList(self) -> "List[Tuple[int, int]]":
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

	def multiSelectBulkEdit(self, widget=None):
		from scal3.event_container import DummyEventContainer
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog

		idsDict = self.multiSelectEventIdsDict()
		container = DummyEventContainer(idsDict)
		dialog = EventsBulkEditDialog(container, transient_for=self)

		if dialog.run() == gtk.ResponseType.OK:
			self.waitingDo(self._do_multiSelectBulkEdit, dialog, container)

	def _do_multiSelectBulkEdit(
		self,
		dialog: gtk.Dialog,
		container: "DummyEventContainer",
	) -> None:
		dialog.doAction()
		dialog.destroy()
		for event in container:
			self.updateEventRow(event)
			ui.eventUpdateQueue.put("e", event, self)

		self.multiSelectOperationFinished()

	def multiSelectExport(self, widget=None):
		from scal3.ui_gtk.event.export import EventListExportDialog
		idsList = self.multiSelectEventIdsList()
		y, m, d = cal_types.getSysDate(core.GREGORIAN)
		dialog = EventListExportDialog(
			idsList,
			defaultFileName=f"selected-events-{y:04d}-{m:02d}-{d:02d}",
			# groupTitle="",
		)
		dialog.run()
		self.sbar.push(0, _("Exporting {count} events finished").format(
			count=_(len(idsList)),
		))
		self.multiSelectOperationFinished()

	def getRowId(self, _iter) -> int:
		return self.treeModel.get_value(_iter, self.idColIndex)

	def canPasteToGroup(self, group: lib.EventGroup) -> bool:
		if self.toPasteEvent is None:
			return False
		if not group.acceptsEventTypes:
			return False
		# FIXME: check event type here?
		return True

	def checkEventToAdd(
		self,
		group: lib.EventGroup,
		event: lib.Event,
	) -> None:
		if not group.checkEventToAdd(event):
			msg = _(
				"Group type \"{groupType}\" can not contain "
				"event type \"{eventType}\""
			).format(
				groupType=group.desc,
				eventType=event.desc,
			)
			showError(msg, transient_for=self)
			raise RuntimeError("Invalid event type for this group")

	def getGroupRow(self, group: lib.EventGroup) -> None:
		return (False,) + common.getGroupRow(group) + ("",)

	def getEventRow(self, event: lib.Event) -> Tuple[
		bool,
		int,
		GdkPixbuf.Pixbuf,
		str,
		str,
	]:
		pixbuf = eventTreeIconPixbuf(event.getIconRel())
		if event.icon and pixbuf is None:
			log.error(
				f"getEventRow: invalid {event.icon=} " +
				f"for {event.id=} in {event.parent=}"
			)
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
		event: lib.Event,
	) -> gtk.TreeIter:
		eventIter = self.treeModel.append(parentIter, self.getEventRow(event))
		self.eventsIter[event.id] = eventIter
		return eventIter

	def insertEventRow(
		self,
		parentIter: gtk.TreeIter,
		position: int,
		event: lib.Event,
	) -> gtk.TreeIter:
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
		event: lib.Event,
	) -> gtk.TreeIter:
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
		group: lib.EventGroup,
	) -> gtk.TreeIter:
		self.groupIterById[group.id] = groupIter = self.treeModel.insert(
			None,
			position,
			self.getGroupRow(group),
		)
		return groupIter

	def appendGroupEvents(
		self,
		group: lib.EventGroup,
		groupIter: gtk.TreeIter,
	) -> None:
		for event in group:
			self.appendEventRow(groupIter, event)
		self.loadedGroupIds.add(group.id)

	def insertGroupTree(self, position: int, group: lib.EventGroup) -> None:
		groupIter = self.insertGroup(position, group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendGroup(self, group: lib.EventGroup) -> gtk.TreeIter:
		self.groupIterById[group.id] = groupIter = self.treeModel.insert_before(
			None,
			self.trashIter,
			self.getGroupRow(group),
		)
		return groupIter

	def appendGroupTree(self, group: lib.EventGroup) -> None:
		groupIter = self.appendGroup(group)
		if group.enable:
			self.appendGroupEvents(group, groupIter)

	def appendTrash(self) -> None:
		self.trashIter = self.treeModel.append(None, (
			False,
			-1,
			eventTreeIconPixbuf(ui.eventTrash.getIconRel()),
			ui.eventTrash.title,
			"",
		))
		for event in ui.eventTrash:
			self.appendEventRow(self.trashIter, event)

	def reloadGroupEvents(self, gid: int) -> None:
		groupIter = self.groupIterById[gid]
		assert self.getRowId(groupIter) == gid
		##
		self.removeIterChildren(groupIter)
		##
		group = ui.eventGroups[gid]
		if gid not in self.loadedGroupIds:
			return
		for event in group:
			self.appendEventRow(groupIter, event)

	def reloadEvents(self) -> None:
		self.treeModel.clear()
		self.appendTrash()
		for group in ui.eventGroups:
			self.appendGroupTree(group)
		self.treeviewCursorChanged()
		####
		self.isLoaded = True

	def getObjsByPath(self, path: List[int]) -> List[EventOrGroup]:
		obj_list = []
		for i in range(len(path)):
			it = self.treeModel.get_iter(path[:i + 1])
			obj_id = self.getRowId(it)
			if i == 0:
				if obj_id == -1:
					obj_list.append(ui.eventTrash)
				else:
					obj_list.append(ui.eventGroups[obj_id])
			else:
				obj_list.append(obj_list[i - 1][obj_id])
		return obj_list

	def historyOfEventFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		group, event = self.getObjsByPath(path)
		EventHistoryDialog(event, transient_for=self).run()

	def trashAddRightClickMenuItems(self, menu, path, group):
		# log.debug("right click on trash", group.title)
		menu.add(eventWriteMenuItem(
			_("Edit"),
			imageName="document-edit.svg",
			func=self.editTrash,
		))

		menu.add(eventWriteMenuItem(
			_("Sort Events"),
			imageName="view-sort-ascending.svg",
			func=self.groupSortFromMenu,
			args=(path,),
			sensitive=bool(group.idList),
		))

		# FIXME: _("Empty {title}").format(title=group.title),
		menu.add(eventWriteMenuItem(
			_("Empty Trash"),
			imageName="sweep.svg",
			func=self.emptyTrash,
			sensitive=bool(group.idList),
		))
		# menu.add(gtk.SeparatorMenuItem())
		# menu.add(eventWriteMenuItem(
		# 	"Add New Group",
		# 	imageName="document-new.svg",
		# 	func=self.addGroupBeforeSelection,
		# ))  # FIXME

	def groupAddRightClickMenuItems(self, menu, path, group):
		# log.debug("right click on group", group.title)
		menu.add(eventWriteMenuItem(
			_("Edit"),
			imageName="document-edit.svg",
			func=self.editGroupFromMenu,
			args=(path,),
		))
		eventTypes = group.acceptsEventTypes
		if eventTypes is None:
			eventTypes = lib.classes.event.names
		if len(eventTypes) > 3:
			menu.add(eventWriteMenuItem(
				_("Add Event"),
				imageName="list-add.svg",
				func=self.addGenericEventToGroupFromMenu,
				args=(path, group,),
			))
		else:
			for eventType in eventTypes:
				# if eventType == "custom":  # FIXME
				# 	eventTypeDesc = _("Event")
				# else:
				eventTypeDesc = lib.classes.event.byName[eventType].desc
				label = _("Add {eventType}").format(
					eventType=eventTypeDesc,
				)
				menu.add(eventWriteMenuItem(
					label,
					imageName="list-add.svg",
					func=self.addEventToGroupFromMenu,
					args=(
						path,
						group,
						eventType,
						label,
					),
				))
		pasteItem = eventWriteMenuItem(
			_("Paste Event"),
			imageName="edit-paste.svg",
			func=self.pasteEventFromMenu,
			args=(path,),
		)
		menu.add(pasteItem)
		pasteItem.set_sensitive(self.canPasteToGroup(group))
		##
		if group.remoteIds:
			aid, remoteGid = group.remoteIds
			try:
				account = ui.eventAccounts[aid]
			except KeyError:
				log.exception("")
			else:
				if account.enable:
					menu.add(gtk.SeparatorMenuItem())
					menu.add(eventWriteMenuItem(
						_("Synchronize"),
						imageName="",
						# FIXME: sync-events.svg
						func=self.syncGroupFromMenu,
						args=(
							path,
							account,
						),
					))
				# else:  # FIXME
		##
		menu.add(gtk.SeparatorMenuItem())
		# menu.add(eventWriteMenuItem(
		# 	_("Add New Group"),
		# 	imageName="document-new.svg",
		# 	func=self.addGroupBeforeGroup,
		# 	args=(path,),
		# ))  # FIXME
		menu.add(eventWriteMenuItem(
			_("Duplicate"),
			imageName="edit-copy.svg",
			func=self.duplicateGroupFromMenu,
			args=(path,)
		))
		###
		dupAllItem = eventWriteMenuItem(
			_("Duplicate with All Events"),
			imageName="edit-copy.svg",
			func=self.duplicateGroupWithEventsFromMenu,
			args=(path,)
		)
		menu.add(dupAllItem)
		dupAllItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList)
		)
		###
		menu.add(gtk.SeparatorMenuItem())
		menu.add(eventWriteMenuItem(
			_("Delete Group"),
			imageName="edit-delete.svg",
			func=self.deleteGroupFromMenu,
			args=(path,)
		))
		menu.add(gtk.SeparatorMenuItem())
		##
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
		##
		menu.add(ImageMenuItem(
			_("Export", ctx="menu"),
			# imageName="export-events.svg",  # FIXME
			func=self.groupExportFromMenu,
			args=(group,),
		))
		###
		menu.add(eventWriteMenuItem(
			_("Sort Events"),
			imageName="view-sort-ascending.svg",
			func=self.groupSortFromMenu,
			args=(path,),
			sensitive=not group.isReadOnly() and bool(group.idList)
		))
		###
		convertItem = eventWriteMenuItem(
			_("Convert Calendar Type"),
			imageName="convert-calendar.svg",
			func=self.groupConvertCalTypeFromMenu,
			args=(group,)
		)
		menu.add(convertItem)
		convertItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList)
		)
		###
		for newGroupType in group.canConvertTo:
			newGroupTypeDesc = lib.classes.group.byName[newGroupType].desc
			menu.add(eventWriteMenuItem(
				_("Convert to {groupType}").format(
					groupType=newGroupTypeDesc,
				),
				func=self.groupConvertToFromMenu,
				args=(
					group,
					newGroupType,
				),
			))
		###
		bulkItem = eventWriteMenuItem(
			_("Bulk Edit Events"),
			imageName="document-edit.svg",
			func=self.groupBulkEditFromMenu,
			args=(group, path,)
		)
		menu.add(bulkItem)
		bulkItem.set_sensitive(
			not group.isReadOnly() and bool(group.idList)
		)
		###
		for actionName, actionFuncName in group.actions:
			menu.add(eventWriteMenuItem(
				_(actionName),
				func=self.onGroupActionClick,
				args=(
					group,
					actionFuncName,
				),
			))

	def eventAddRightClickMenuItems(self, menu, path, group, event):
		# log.debug("right click on event", event.summary)
		menu.add(eventWriteMenuItem(
			_("Edit"),
			imageName="document-edit.svg",
			func=self.editEventFromMenu,
			args=(path,)
		))
		####
		menu.add(eventWriteImageMenuItem(
			_("History"),
			"history.svg",
			func=self.historyOfEventFromMenu,
			args=(path,),
		))
		####
		moveToItem = eventWriteMenuItem(
			_("Move to {title}").format(title="..."),
		)
		moveToMenu = Menu()
		for new_group in ui.eventGroups:
			if new_group.id == group.id:
				continue
			# if not new_group.enable:  # FIXME
			# 	continue
			new_groupPath = self.treeModel.get_path(self.groupIterById[new_group.id])
			if event.name in new_group.acceptsEventTypes:
				moveToMenu.add(menuItemFromEventGroup(
					new_group,
					func=self.moveEventToPathFromMenu,
					args=(
						path,
						new_groupPath,
					),
				))
		moveToItem.set_submenu(moveToMenu)
		menu.add(moveToItem)
		####
		menu.add(gtk.SeparatorMenuItem())
		####
		menu.add(eventWriteMenuItem(
			_("Cut"),
			imageName="edit-cut.svg",
			func=self.cutEvent,
			args=(path,),
		))
		menu.add(eventWriteMenuItem(
			_("Copy"),
			imageName="edit-copy.svg",
			func=self.copyEvent,
			args=(path,)
		))
		##
		if group.name == "trash":
			menu.add(gtk.SeparatorMenuItem())
			menu.add(eventWriteMenuItem(
				_("Delete", ctx="event manager"),
				imageName="edit-delete.svg",
				func=self.deleteEventFromTrash,
				args=(path,),
			))
		else:
			pasteItem = eventWriteMenuItem(
				_("Paste"),
				imageName="edit-paste.svg",
				func=self.pasteEventFromMenu,
				args=(path,),
			)
			menu.add(pasteItem)
			pasteItem.set_sensitive(self.canPasteToGroup(group))
			##
			menu.add(gtk.SeparatorMenuItem())
			menu.add(eventWriteMenuItem(
				_("Move to {title}").format(title=ui.eventTrash.title),
				imageName=ui.eventTrash.getIconRel(),
				func=self.moveEventToTrashFromMenu,
				args=(path,),
			))

	def genRightClickMenu(self, path: List[int]) -> gtk.Menu:
		# and Select _All menu item
		obj_list = self.getObjsByPath(path)
		# log.debug(len(obj_list))
		menu = Menu()
		if len(obj_list) == 1:
			group = obj_list[0]
			if group.name == "trash":
				self.trashAddRightClickMenuItems(menu, path, group)
			else:
				self.groupAddRightClickMenuItems(menu, path, group)

		elif len(obj_list) == 2:
			group, event = obj_list
			self.eventAddRightClickMenuItems(menu, path, group, event)

		else:
			return
		menu.show_all()
		return menu

	def openRightClickMenu(
		self,
		path: List[int],
		etime: Optional[int] = None,
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
		path: List[int],
		col: gtk.TreeViewColumn,
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

	def onKeyPress(self, dialog, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "escape":
			return self.onEscape()
		if kname == "menu":  # simulate right click (key beside Right-Ctrl)
			if self.multiSelect:
				self.menubar.select_item(self.multiSelectItemMain)
				return True
		return False
		# return self.onTreeviewKeyPress(self.treev, gevent)

	def menuKeyPressOnPath(self, path: "List[str]", gevent: "gdk.EventKey"):
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
		foo, wx, wy = self.get_window().get_origin()
		self.tmpMenu = menu
		menu.popup(
			None, None,
			lambda *args: (
				wx + dx,
				wy + dy,
				True,
			),
			None, 3, gevent.time,
		)

	def onTreeviewKeyPress(
		self,
		treev: "gtk.TreeView",
		gevent: "gdk.EventKey",
	) -> bool:
		# from scal3.time_utils import getGtkTimeFromEpoch
		# log.debug(gevent.time-getGtkTimeFromEpoch(now()))
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

		elif kname in ("up", "down"):
			if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
				isDown = kname == "down"
				self.multiSelectShiftUpDownPress(isDown)
				return True

		return False

	def onEscape(self):
		if self.multiSelect:
			self.multiSelectCancel()
			return True
		self.hide()
		return True

	def onMenuBarExportClick(self, menuItem: gtk.MenuItem) -> None:
		MultiGroupExportDialog(transient_for=self).run()

	def onMenuBarImportClick(self, menuItem: gtk.MenuItem) -> None:
		EventsImportWindow(self).present()

	def onMenuBarSearchClick(self, menuItem: gtk.MenuItem) -> None:
		ui.mainWin.eventSearchShow()

	def _do_checkForOrphans(self) -> None:
		newGroup = ui.eventGroups.checkForOrphans()
		if newGroup is not None:
			self.appendGroupTree(newGroup)

	def onMenuBarOrphanClick(self, menuItem: gtk.MenuItem) -> None:
		self.waitingDo(self._do_checkForOrphans)

	def getSelectedPath(self) -> Optional[List[int]]:
		_iter = self.treev.get_selection().get_selected()[1]
		if _iter is None:
			return
		return self.treeModel.get_path(_iter).get_indices()

	def mbarEditMenuPopup(self, menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		selected = bool(path)
		eventSelected = selected and len(path) == 2
		###
		self.mbarEditItem.set_sensitive(selected)
		self.mbarCutItem.set_sensitive(eventSelected)
		self.mbarCopyItem.set_sensitive(eventSelected)
		self.mbarDupItem.set_sensitive(selected)
		###
		self.mbarPasteItem.set_sensitive(
			selected and self.canPasteToGroup(self.getObjsByPath(path)[0])
		)

	def onMenuBarEditClick(self, menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.editGroupByPath(path)
		elif len(path) == 2:
			self.editEventByPath(path)

	def onMenuBarCutClick(self, menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.treeModel.get_iter(path), True)

	def onMenuBarCopyClick(self, menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 2:
			self.toPasteEvent = (self.treeModel.get_iter(path), False)

	def onMenuBarPasteClick(self, menuItem: gtk.MenuItem) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.pasteEventToPath(path)

	def onCollapseAllClick(self, menuItem: gtk.MenuItem) -> None:
		return self.treev.collapse_all()

	def onExpandAllAllClick(self, menuItem: gtk.MenuItem) -> None:
		return self.treev.expand_all()

	def _do_showDescItemToggled(self) -> None:
		global eventManShowDescription
		active = self.showDescItem.get_active()
		eventManShowDescription = active
		saveConf()
		if active:
			self.treev.append_column(self.colDesc)
		else:
			self.treev.remove_column(self.colDesc)

	def showDescItemToggled(self, menuItem: gtk.MenuItem) -> None:
		self.waitingDo(self._do_showDescItemToggled)

	def treeviewCursorChangedPath(self, path: "List[int]") -> None:
		text = ""
		if len(path) == 1:
			group = self.getObjsByPath(path)[0]
			if group.name == "trash":
				text = _("contains {eventCount} events").format(
					eventCount=_(len(group)),
				)
			else:
				text = _(
					"contains {eventCount} events"
					" and {occurCount} occurrences"
				).format(
					eventCount=_(len(group)),
					occurCount=_(group.occurCount),
				) + _(",") + " " + _("Group ID: {groupId}").format(
					groupId=_(group.id),
				)
			modified = group.modified
			# log.info(f"group, id = {group.id}, uuid = {group.uuid}")
		elif len(path) == 2:
			group, event = self.getObjsByPath(path)
			text = _("Event ID: {eventId}").format(eventId=_(event.id))
			modified = event.modified
			# log.info(f"event, id = {event.id}, uuid = {event.uuid}")
			for rule in event.rulesOd.values():
				log.debug(f"Rule {rule.name}: '{rule}', info='{rule.getInfo()}'")

		comma = _(",")
		modifiedLabel = _("Last Modified")
		modifiedTime = locale_man.textNumEncode(
			core.epochDateTimeEncode(modified),
		)
		text += f"{comma} {modifiedLabel}: {modifiedTime}"
		if hasattr(self, "sbar"):
			message_id = self.sbar.push(0, text)

	def treeviewCursorChanged(self, selection: Any = None) -> None:
		path = self.getSelectedPath()

		if not self.syncing:
			if path:
				self.treeviewCursorChangedPath(path)
			elif hasattr(self, "sbar"):
				self.sbar.push(0, "")

		self.toolbar.set_sensitive(bool(path))

		return True

	def _do_onGroupModify(self, group: lib.EventGroup) -> None:
		group.afterModify()
		group.save()  # FIXME
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

	def onGroupModify(self, group: lib.EventGroup) -> None:
		self.waitingDo(self._do_onGroupModify, group)

	def setGroupEnable(
		self,
		enable: bool,
		group: lib.EventGroup,
		path: "Optional[Tuple[int]]",
	) -> bool:
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
		ui.eventGroups.save()
		if (
			group.enable and
			self.treeModel.iter_n_children(groupIter) == 0 and
			len(group) > 0
		):
			for event in group:
				self.appendEventRow(groupIter, event)
			self.loadedGroupIds.add(group.id)
		self.onGroupModify(group)

	def onEnableAllClick(self, menuItem: gtk.MenuItem) -> None:
		for group in ui.eventGroups:
			self.setGroupEnable(True, group, None)

	def onDisableAllClick(self, menuItem: gtk.MenuItem) -> None:
		for group in ui.eventGroups:
			self.setGroupEnable(False, group, None)

	def toggleEnableGroup(self, group: lib.EventGroup, path: List[int]) -> bool:
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
		path: "List[int]",
		col: "gtk.TreeViewColumn",
	) -> None:
		objs = self.getObjsByPath(path)

		if len(objs) == 1:  # group, not event
			group = objs[0]
			if group.name != "trash" and col == self.pixbufCol:
				if self.toggleEnableGroup(group, path):
					treev.set_cursor(path)
					return True
			return False

		if len(objs) != 2:
			log.error(f"onTreeviewLeftButtonPress: unexpected {objs=}, {path=}")
			return False

		if self.multiSelect and gevent.state & gdk.ModifierType.SHIFT_MASK > 0:
			return self.multiSelectShiftButtonPress(path, col, objs[0], objs[1])

		return False

	def onTreeviewButtonPress(
		self,
		treev: gtk.TreeView,
		gevent: gdk.EventButton,
	) -> None:
		pos_t = treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return
		pathObj, col, xRel, yRel = pos_t
		# pathObj is either None of gtk.TreePath
		if not pathObj:
			return
		path = pathObj.get_indices()
		if gevent.button == 3:
			if self.multiSelect:
				return False
			self.openRightClickMenu(path, gevent.time)
		elif gevent.button == 1:
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
		ui.eventGroups.insert(groupIndex, group)
		ui.eventGroups.save()
		beforeGroupIter = self.treeModel.get_iter((groupIndex,))
		self.groupIterById[group.id] = self.treeModel.insert_before(
			self.treeModel.iter_parent(beforeGroupIter),  # parent
			beforeGroupIter,  # sibling
			self.getGroupRow(group),
		)
		self.onGroupModify(group)
		self.loadedGroupIds.add(group.id)

	def addGroupBeforeGroup(self, menu: gtk.Menu, path: List[int]) -> None:
		self.insertNewGroup(path[0])

	def addGroupBeforeSelection(self, w: Optional[gtk.Widget] = None) -> None:
		path = self.getSelectedPath()
		if path is None:
			groupIndex = len(self.treeModel) - 1
		else:
			if not isinstance(path, list):
				raise RuntimeError(f"invalid {path = }")
			groupIndex = path[0]
		self.insertNewGroup(groupIndex)

	def duplicateGroup(self, path: List[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getObjsByPath(path)[0]
		newGroup = group.copy()
		ui.duplicateGroupTitle(newGroup)
		newGroup.afterModify()
		newGroup.save()
		ui.eventGroups.insert(index + 1, newGroup)
		ui.eventGroups.save()
		self.groupIterById[newGroup.id] = self.treeModel.insert(
			None,
			index + 1,
			self.getGroupRow(newGroup),
		)

	def duplicateGroupWithEvents(self, path: List[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getObjsByPath(path)[0]
		newGroup = group.deepCopy()
		ui.duplicateGroupTitle(newGroup)
		newGroup.save()
		ui.eventGroups.insert(index + 1, newGroup)
		ui.eventGroups.save()
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
		menu: gtk.Menu,
		path: List[int],
		account: lib.Account,
	) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getObjsByPath(path)[0]
		if not group.remoteIds:
			return
		aid, remoteGid = group.remoteIds
		info = {
			"group": group.title,
			"account": account.title,
		}
		account.showError = showError
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

	def duplicateGroupFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		self.duplicateGroup(path)

	def duplicateGroupWithEventsFromMenu(
		self,
		menu: gtk.Menu,
		path: List[int],
	) -> None:
		self.duplicateGroupWithEvents(path)

	def duplicateSelectedObj(self, w: Optional[gtk.Widget] = None) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		if len(path) == 1:
			self.duplicateGroup(path)
		elif len(path) == 2:  # FIXME
			self.toPasteEvent = (self.treeModel.get_iter(path), False)
			self.pasteEventToPath(path)

	def editGroupByPath(self, path: List[int]) -> None:
		from scal3.ui_gtk.event.group.editor import GroupEditorDialog
		checkEventsReadOnly()  # FIXME
		group = self.getObjsByPath(path)[0]
		if group.name == "trash":
			self.editTrash()
			return

		if group.isReadOnly():
			msg = _(
				"Event group \"{groupTitle}\" is synchronizing and read-only"
			).format(groupTitle=group.title)
			showError(msg, transient_for=self)
			return

		group = GroupEditorDialog(group, transient_for=self).run()
		if group is None:
			return
		groupIter = self.treeModel.get_iter(path)
		for i, value in enumerate(self.getGroupRow(group)):
			self.treeModel.set_value(groupIter, i, value)
		self.onGroupModify(group)
		ui.eventUpdateQueue.put("eg", group, self)

	def editGroupFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		self.editGroupByPath(path)

	def _do_deleteGroup(self, path: List[int], group: lib.EventGroup) -> None:
		trashedIds = group.idList
		if ui.eventTrash.addEventsToBeginning:
			for eid in reversed(trashedIds):
				event = group[eid]
				self.insertEventRow(self.trashIter, 0, event)
		else:
			for eid in trashedIds:
				event = group[eid]
				self.appendEventRow(self.trashIter, event)
		ui.eventGroups.moveToTrash(group, ui.eventTrash)
		ui.eventUpdateQueue.put("-g", group, self)
		self.treeModel.remove(self.treeModel.get_iter(path))

	def deleteGroup(self, path: List[int]) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getObjsByPath(path)[0]
		eventCount = len(group)
		if eventCount > 0:
			if not confirm(
				_(
					"Press Confirm if you want to delete group \"{groupTitle}\" "
					"and move its {eventCount} events to {trashTitle}"
				).format(
					groupTitle=group.title,
					eventCount=_(eventCount),
					trashTitle=ui.eventTrash.title,
				),
				transient_for=self,
			):
				return
		self.waitingDo(self._do_deleteGroup, path, group)

	def deleteGroupFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		self.deleteGroup(path)

	def addEventToGroupFromMenu(
		self,
		menu: gtk.Menu,
		path: List[int],
		group: lib.EventGroup,
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
		group: lib.EventGroup,
		groupIter: gtk.TreeIter,
		event: lib.Event,
	) -> None:
		if group.id not in self.loadedGroupIds:
			return
		if group.addEventsToBeginning:
			self.insertEventRow(groupIter, 0, event)
			return
		self.appendEventRow(groupIter, event)

	def addGenericEventToGroupFromMenu(
		self,
		menu: gtk.Menu,
		path: List[int],
		group: lib.EventGroup,
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

	def updateEventRow(self, event: lib.Event) -> None:
		self.updateEventRowByIter(
			event,
			self.eventsIter[event.id],
		)

	def updateEventRowByIter(
		self,
		event: lib.Event,
		eventIter: gtk.TreeIter,
	) -> None:
		for i, value in enumerate(self.getEventRow(event)):
			self.treeModel.set_value(eventIter, i, value)
		self.treeviewCursorChanged()

	def editEventByPath(self, path: List[int]) -> None:
		from scal3.ui_gtk.event.editor import EventEditorDialog
		group, event = self.getObjsByPath(path)
		event = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self,
		).run()
		if event is None:
			return
		ui.eventUpdateQueue.put("e", event, self)
		self.updateEventRow(event)

	def editEventFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		self.editEventByPath(path)

	def moveEventToPathFromMenu(
		self,
		menu: gtk.Menu,
		path: List[int],
		targetPath: List[int],
	) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), True)
		self.pasteEventToPath(targetPath, False)

	def moveEventToTrashByPath(self, path: List[int]) -> None:
		group, event = self.getObjsByPath(path)
		if not confirmEventTrash(event, transient_for=self):
			return
		ui.moveEventToTrash(group, event, self)
		self.treeModel.remove(self.treeModel.get_iter(path))
		self.addEventRowToTrash(event)

	def addEventRowToTrash(self, event: "lib.Event") -> None:
		if ui.eventTrash.addEventsToBeginning:
			self.insertEventRow(self.trashIter, 0, event)
		else:
			self.appendEventRow(self.trashIter, event)

	def moveEventToTrashFromMenu(self, menu: gtk.Menu, path: List[int]) -> None:
		self.moveEventToTrashByPath(path)

	def moveSelectionToTrash(self) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		objs = self.getObjsByPath(path)
		if len(path) == 1:
			self.deleteGroup(path)
		elif len(path) == 2:
			self.moveEventToTrashByPath(path)

	def deleteEventFromTrash(self, menu: gtk.Menu, path: List[int]) -> None:
		trash, event = self.getObjsByPath(path)
		trash.delete(event.id)  # trash == ui.eventTrash
		trash.save()
		self.treeModel.remove(self.treeModel.get_iter(path))
		# no need to send to ui.eventUpdateQueue right now
		# since events in trash (or their occurrences) are not displayed
		# outside Event Manager

	def removeIterChildren(self, _iter: gtk.TreeIter) -> None:
		while (childIter := self.treeModel.iter_children(_iter)) is not None:
			self.treeModel.remove(childIter)

	def emptyTrash(self, menuItem: gtk.MenuItem) -> None:
		ui.eventTrash.empty()
		self.removeIterChildren(self.trashIter)
		self.treeviewCursorChanged()

	def editTrash(self, menuItem: Optional[gtk.MenuItem] = None) -> None:
		TrashEditorDialog(transient_for=self).run()
		self.treeModel.set_value(
			self.trashIter,
			2,
			eventTreeIconPixbuf(ui.eventTrash.getIconRel()),
		)
		self.treeModel.set_value(
			self.trashIter,
			3,
			ui.eventTrash.title,
		)
		# TODO: perhaps should put on eventUpdateQueue
		# ui.eventUpdateQueue.put("et", ui.eventTrash, self)
		# as a UI improvement, in case icon of title is changed

	def moveUp(self, path: List[int]) -> None:
		srcIter = self.treeModel.get_iter(path)
		if not isinstance(path, list):
			raise RuntimeError(f"invalid {path = }")
		if len(path) == 1:
			if path[0] == 0:
				return
			if self.getRowId(srcIter) == -1:
				return
			tarIter = self.treeModel.get_iter((path[0] - 1))
			self.treeModel.move_before(srcIter, tarIter)
			ui.eventGroups.moveUp(path[0])
			ui.eventGroups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			parentObj, event = self.getObjsByPath(path)
			parentLen = len(parentObj)
			parentIndex, eventIndex = path
			# log.debug(eventIndex, parentLen)
			if eventIndex > 0:
				tarIter = self.treeModel.get_iter((
					parentIndex,
					eventIndex - 1),
				)
				self.treeModel.move_before(srcIter, tarIter)
				# ^ or use self.treeModel.swap FIXME
				parentObj.moveUp(eventIndex)
				parentObj.save()
			else:
				# move event to end of previous group
				# if parentObj.name == "trash":
				# 	return
				if parentIndex < 1:
					return
				newParentIter = self.treeModel.get_iter((parentIndex - 1))
				newParentId = self.getRowId(newParentIter)
				if newParentId == -1:  # could not be!
					return
				newGroup = ui.eventGroups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.treeModel.remove(srcIter)
				self.appendEventRow(newParentIter, event)
				###
				parentObj.remove(event)
				parentObj.save()
				newGroup.append(event)
				newGroup.save()
			ui.eventUpdateQueue.put("r", parentObj, self)
		else:
			raise RuntimeError(f"invalid tree path {path}")
		newPath = self.treeModel.get_path(srcIter)
		if len(path) == 2:
			self.treev.expand_to_path(newPath)
		self.treev.set_cursor(newPath)
		self.treev.scroll_to_cell(newPath)

	def moveDown(self, path: List[int]) -> None:
		if not isinstance(path, list):
			raise RuntimeError(f"invalid {path = }")
		srcIter = self.treeModel.get_iter(path)
		if len(path) == 1:
			if self.getRowId(srcIter) == -1:
				return
			tarIter = self.treeModel.get_iter((path[0] + 1))
			if self.getRowId(tarIter) == -1:
				return
			self.treeModel.move_after(srcIter, tarIter)
			# or use self.treeModel.swap FIXME
			ui.eventGroups.moveDown(path[0])
			ui.eventGroups.save()
			# do we need to put on ui.eventUpdateQueue?
		elif len(path) == 2:
			parentObj, event = self.getObjsByPath(path)
			parentLen = len(parentObj)
			parentIndex, eventIndex = path
			# log.debug(eventIndex, parentLen)
			if eventIndex < parentLen - 1:
				tarIter = self.treeModel.get_iter((
					parentIndex,
					eventIndex + 1,
				))
				self.treeModel.move_after(srcIter, tarIter)
				parentObj.moveDown(eventIndex)
				parentObj.save()
			else:
				# move event to top of next group
				if parentObj.name == "trash":
					return
				newParentIter = self.treeModel.get_iter((parentIndex + 1))
				newParentId = self.getRowId(newParentIter)
				if newParentId == -1:
					return
				newGroup = ui.eventGroups[newParentId]
				self.checkEventToAdd(newGroup, event)
				self.treeModel.remove(srcIter)
				srcIter = self.insertEventRow(newParentIter, 0, event)
				###
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

	def moveUpFromMenu(self, menuItem: gtk.MenuItem, path: List[int]) -> None:
		self.moveUp(path)

	def moveDownFromMenu(self, menuItem: gtk.MenuItem, path: List[int]) -> None:
		self.moveDown(path)

	def moveUpByButton(self, tb: gtk.Button) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.moveUp(path)

	def moveDownByButton(self, tb: gtk.Button) -> None:
		path = self.getSelectedPath()
		if not path:
			return
		self.moveDown(path)

	def groupExportFromMenu(
		self,
		menuItem: gtk.MenuItem,
		group: lib.EventGroup,
	) -> None:
		SingleGroupExportDialog(group, transient_for=self).run()

	def groupSortFromMenu(
		self,
		menuItem: gtk.MenuItem,
		path: List[int],
	) -> None:
		if not (isinstance(path, list) and len(path) == 1):
			raise RuntimeError(f"invalid {path = }")
		index = path[0]
		group = self.getObjsByPath(path)[0]
		if GroupSortDialog(group, transient_for=self).run():
			if group.id in self.loadedGroupIds or group.name == "trash":
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
		menuItem: gtk.MenuItem,
		group: lib.EventGroup,
	) -> None:
		if GroupConvertCalTypeDialog(group, transient_for=self).perform():
			ui.eventUpdateQueue.put("r", group, self)

	def _do_groupConvertTo(
		self,
		group: lib.EventGroup,
		newGroupType: str,
	) -> None:
		idsCount = len(group.idList)
		newGroup = ui.eventGroups.convertGroupTo(group, newGroupType)
		# FIXME: reload its events in tree?
		# summary and description have been not changed!
		idsCount2 = len(newGroup.idList)
		if idsCount2 != idsCount:
			self.reloadGroupEvents(newGroup.id)
		self.treeviewCursorChanged()
		ui.eventUpdateQueue.put("eg", newGroup, self)

	def groupConvertToFromMenu(
		self,
		menuItem: gtk.MenuItem,
		group: lib.EventGroup,
		newGroupType: str,
	) -> None:
		self.waitingDo(self._do_groupConvertTo, group, newGroupType)

	def _do_groupBulkEdit(
		self,
		dialog: gtk.Dialog,
		group: lib.EventGroup,
		path: List[int],
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
		menuItem: gtk.MenuItem,
		group: lib.EventGroup,
		path: List[int],
	) -> None:
		from scal3.ui_gtk.event.bulk_edit import EventsBulkEditDialog
		dialog = EventsBulkEditDialog(group, transient_for=self)
		if dialog.run() == gtk.ResponseType.OK:
			self.waitingDo(self._do_groupBulkEdit, dialog, group, path)

	def onGroupActionClick(
		self,
		menuItem: gtk.MenuItem,
		group: lib.EventGroup,
		actionFuncName: str,
	) -> None:
		func = getattr(group, actionFuncName, None)
		if func is None:
			setActionFuncs(group)
			func = getattr(group, actionFuncName)
		self.waitingDo(func, parentWin=self)

	def cutEvent(self, menuItem: gtk.MenuItem, path: List[int]) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), True)

	def copyEvent(self, menuItem: gtk.MenuItem, path: List[int]) -> None:
		self.toPasteEvent = (self.treeModel.get_iter(path), False)

	def pasteEventFromMenu(
		self,
		menuItem: gtk.MenuItem,
		targetPath: List[int],
	) -> None:
		self.pasteEventToPath(targetPath)

	def _pasteEventToPath(
		self,
		srcIter: "gtk.TreeIter",
		move: bool,
		targetPath: List[int],
	):
		srcPath = self.treeModel.get_path(srcIter)
		srcGroup, srcEvent = self.getObjsByPath(srcPath)
		tarGroup = self.getObjsByPath(targetPath)[0]
		self.checkEventToAdd(tarGroup, srcEvent)
		if len(targetPath) == 1:
			tarGroupIter = self.treeModel.get_iter(targetPath)
			tarEventIter = None
			tarEventIndex = len(tarGroup)
		elif len(targetPath) == 2:
			tarGroupIter = self.treeModel.get_iter(targetPath[:1])
			tarEventIter = self.treeModel.get_iter(targetPath)
			tarEventIndex = targetPath[1]
		####
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
		####
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
		targetPath: List[int],
		doScroll: bool = True,
	) -> None:
		if not self.toPasteEvent:
			return
		srcIter, move = self.toPasteEvent
		newEventIter = self._pasteEventToPath(srcIter, move, targetPath)
		if doScroll:
			self.treev.set_cursor(self.treeModel.get_path(newEventIter))
		self.toPasteEvent = None
