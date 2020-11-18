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

from scal3.path import *
from scal3.utils import cmp
from scal3 import cal_types
from scal3.cal_types import calTypes
from scal3 import core
from scal3.core import jd_to_primary
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import event_lib
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import (
	labelImageButton,
	newHSep,
)
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.multi_spin.date_time import DateTimeButton
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.event.utils import (
	confirmEventTrash,
	eventWriteMenuItem,
	eventWriteImageMenuItem,
	eventTreeIconPixbuf,
	menuItemFromEventGroup,
)
from scal3.ui_gtk.event.common import SingleGroupComboBox
from scal3.ui_gtk.event.export import EventListExportDialog


@registerSignals
class EventSearchWindow(gtk.Window, MyDialog, ud.BaseCalObj):
	def __init__(self, showDesc=False):
		gtk.Window.__init__(self)
		self.maximize()
		self.initVars()
		ud.windowList.appendItem(self)
		###
		self.set_title(_("Search Events"))
		self.connect("delete-event", self.closed)
		self.connect("key-press-event", self.onKeyPress)
		###
		self.vbox = VBox()
		self.add(self.vbox)
		######
		vboxFilters = self.vboxFilters = VBox()
		pack(self.vbox, vboxFilters)
		######
		frame = TextFrame()
		frame.set_label(_("Text"))
		frame.set_border_width(5)
		pack(vboxFilters, frame)
		self.textInput = frame
		######
		hboxDouble = HBox()
		pack(vboxFilters, hboxDouble)
		##
		vboxHalf = VBox()
		pack(hboxDouble, vboxHalf)
		pack(hboxDouble, newHSep(), padding=5)
		###
		hbox = HBox()
		self.textCSensCheck = gtk.CheckButton(label=_("Case Sensitive"))
		self.textCSensCheck.set_active(False) ## FIXME
		pack(hbox, self.textCSensCheck)
		pack(vboxHalf, hbox)
		#####
		jd = core.getCurrentJd()
		year, month, day = jd_to_primary(jd)
		######
		hbox = HBox()
		frame = gtk.Frame()
		frame.set_label(_("Time"))
		frame.set_border_width(5)
		vboxIn = VBox()
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		####
		hboxIn = HBox()
		##
		self.timeFromCheck = gtk.CheckButton(label=_("From"))
		sgroup.add_widget(self.timeFromCheck)
		pack(hboxIn, self.timeFromCheck)
		pack(hboxIn, gtk.Label(label="  "))
		##
		self.timeFromInput = DateTimeButton()
		self.timeFromInput.set_value(((year, 1, 1), (0, 0, 0)))
		pack(hboxIn, self.timeFromInput)
		##
		pack(vboxIn, hboxIn)
		####
		hboxIn = HBox()
		##
		self.timeToCheck = gtk.CheckButton(label=_("To"))
		sgroup.add_widget(self.timeToCheck)
		pack(hboxIn, self.timeToCheck)
		pack(hboxIn, gtk.Label(label="  "))
		##
		self.timeToInput = DateTimeButton()
		self.timeToInput.set_value((
			(year + 1, 1, 1),
			(0, 0, 0),
		))
		pack(hboxIn, self.timeToInput)
		##
		pack(vboxIn, hboxIn)
		##
		self.timeFromCheck.connect("clicked", self.updateTimeFromSensitive)
		self.timeToCheck.connect("clicked", self.updateTimeToSensitive)
		self.updateTimeFromSensitive()
		self.updateTimeToSensitive()
		####
		vboxIn.set_border_width(5)
		frame.add(vboxIn)
		pack(hbox, frame)
		pack(hbox, gtk.Label(), 1, 1)
		pack(vboxHalf, hbox)
		######
		vboxHalf = VBox()
		pack(hboxDouble, vboxHalf, 1, 1)
		###
		hbox = HBox()
		hbox.set_border_width(5)
		self.modifiedFromCheck = gtk.CheckButton(label=_("Modified From"))
		pack(hbox, self.modifiedFromCheck)
		pack(hbox, gtk.Label(label="  "))
		self.modifiedFromInput = DateTimeButton()
		self.modifiedFromInput.set_value(((year, 1, 1), (0, 0, 0)))
		pack(hbox, self.modifiedFromInput)
		##
		self.modifiedFromCheck.connect("clicked", self.updateModifiedFromSensitive)
		self.updateModifiedFromSensitive()
		pack(vboxHalf, hbox)
		######
		hbox = HBox()
		hbox.set_border_width(5)
		self.typeCheck = gtk.CheckButton(label=_("Event Type"))
		pack(hbox, self.typeCheck)
		pack(hbox, gtk.Label(label="  "))
		##
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.event:
			combo.append_text(cls.desc)
		combo.set_active(0)
		pack(hbox, combo)
		self.typeCombo = combo
		##
		self.typeCheck.connect("clicked", self.updateTypeSensitive)
		self.updateTypeSensitive()
		pack(vboxHalf, hbox)
		######
		hbox = HBox()
		hbox.set_border_width(5)
		self.groupCheck = gtk.CheckButton(label=_("Group"))
		pack(hbox, self.groupCheck)
		pack(hbox, gtk.Label(label="  "))
		self.groupCombo = SingleGroupComboBox()
		pack(hbox, self.groupCombo)
		##
		self.groupCheck.connect("clicked", self.updateGroupSensitive)
		self.updateGroupSensitive()
		pack(vboxHalf, hbox)
		######
		hbox = HBox()
		hbox.set_border_width(5)
		self.timezoneCheck = gtk.CheckButton(label=_("Time Zone"))
		pack(hbox, self.timezoneCheck)
		pack(hbox, gtk.Label(label="  "))
		self.timezoneCombo = TimeZoneComboBoxEntry()
		pack(hbox, self.timezoneCombo)
		##
		self.timezoneCheck.connect("clicked", self.updateTimezoneSensitive)
		self.updateTimezoneSensitive()
		pack(vboxHalf, hbox)
		######
		bbox = MyHButtonBox()
		bbox.set_homogeneous(False)
		bbox.set_layout(gtk.ButtonBoxStyle.START)
		bbox.set_border_width(5)
		###
		searchButton = labelImageButton(
			label=_("_Search"),
			imageName="edit-find.png",
		)
		searchButton.connect("clicked", self.onSearchClick)
		bbox.add(searchButton)
		###
		exportButton = labelImageButton(
			label=_("_Export"),
			# FIXME: imageName="export-events.svg",
		)
		exportButton.connect("clicked", self.onExportClick)
		bbox.add(exportButton)
		###
		hideShowFiltersButton = labelImageButton(
			label=_("Hide Filters"),
			imageName="",
		)
		self.hideShowFiltersButton = hideShowFiltersButton
		hideShowFiltersButton.connect("clicked", self.onHideShowFiltersClick)
		bbox.add(hideShowFiltersButton)
		###
		pack(self.vbox, bbox)
		######
		treev = gtk.TreeView()
		trees = gtk.TreeStore(
			int,  # gid
			int,  # eid
			str,  # group_name
			GdkPixbuf.Pixbuf,  # icon
			str,  # summary
			str,  # description
		)
		###
		treev.set_model(trees)
		treev.connect("button-press-event", self.onTreeviewButtonPress)
		treev.connect("row-activated", self.rowActivated)
		treev.connect("key-press-event", self.onTreeviewKeyPress)
		treev.set_headers_clickable(True)
		###
		self.colGroup = gtk.TreeViewColumn(
			title=_("Group"),
			cell_renderer=gtk.CellRendererText(),
			text=2,
		)
		self.colGroup.set_resizable(True)
		self.colGroup.set_sort_column_id(2)
		self.colGroup.set_property("expand", False)
		treev.append_column(self.colGroup)
		###
		cell = gtk.CellRendererPixbuf()
		self.colIcon = gtk.TreeViewColumn(
			title="",
			cell_renderer=cell,
			pixbuf=3,
		)
		#self.colIcon.set_sort_column_id(3)  # FIXME
		self.colIcon.set_property("expand", False)
		treev.append_column(self.colIcon)
		###
		self.colSummary = gtk.TreeViewColumn(
			title=_("Summary"),
			cell_renderer=gtk.CellRendererText(),
			text=4,
		)
		self.colSummary.set_resizable(True)
		self.colSummary.set_sort_column_id(4)
		self.colSummary.set_property("expand", True)  # FIXME
		treev.append_column(self.colSummary)
		###
		self.colDesc = gtk.TreeViewColumn(
			title=_("Description"),
			cell_renderer=gtk.CellRendererText(),
			text=5,
		)
		self.colDesc.set_sort_column_id(5)
		self.colDesc.set_visible(showDesc)
		self.colDesc.set_property("expand", True)  # FIXME
		treev.append_column(self.colDesc)
		###
		trees.set_sort_func(2, self.sort_func_group)
		######
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.add(treev)
		####
		vbox = VBox(spacing=5)
		vbox.set_border_width(5)
		###
		topHbox = HBox()
		self.resultLabel = gtk.Label()
		pack(topHbox, self.resultLabel)
		pack(topHbox, gtk.Label(), 1, 1)
		pack(vbox, topHbox)
		####
		columnBox = HBox(spacing=5)
		pack(columnBox, gtk.Label(label=_("Columns") + ":    "))
		##
		check = gtk.CheckButton(label=_("Group"))
		check.set_active(True)
		check.connect(
			"clicked",
			lambda w: self.colGroup.set_visible(w.get_active()),
		)
		pack(columnBox, check)
		##
		check = gtk.CheckButton(label=_("Icon"))
		check.set_active(True)
		check.connect(
			"clicked",
			lambda w: self.colIcon.set_visible(w.get_active()),
		)
		pack(columnBox, check)
		##
		check = gtk.CheckButton(label=_("Summary"))
		check.set_active(True)
		check.connect(
			"clicked",
			lambda w: self.colSummary.set_visible(w.get_active()),
		)
		pack(columnBox, check)
		##
		check = gtk.CheckButton(label=_("Description"))
		check.set_active(showDesc)
		check.connect(
			"clicked",
			lambda w: self.colDesc.set_visible(w.get_active()),
		)
		pack(columnBox, check)
		##
		pack(vbox, columnBox)
		####
		pack(vbox, swin, 1, 1)
		##
		pack(self.vbox, vbox, 1, 1)
		###
		bbox2 = MyHButtonBox()
		bbox2.set_layout(gtk.ButtonBoxStyle.END)
		bbox2.set_border_width(10)
		closeButton = labelImageButton(
			label=_("_Close"),
			imageName="window-close.svg",
		)
		closeButton.connect("clicked", self.closed)
		bbox2.add(closeButton)
		pack(self.vbox, bbox2)
		######
		self.treev = treev
		self.trees = trees
		self.vbox.show_all()
		#self.maximize()## FIXME

	def sort_func_group(self, model, iter1, iter2, user_data=None):
		return cmp(
			ui.eventGroups.index(model.get(iter1, 0)[0]),
			ui.eventGroups.index(model.get(iter2, 0)[0]),
		)

	def updateTimeFromSensitive(self, obj=None):
		self.timeFromInput.set_sensitive(self.timeFromCheck.get_active())

	def updateTimeToSensitive(self, obj=None):
		self.timeToInput.set_sensitive(self.timeToCheck.get_active())

	def updateModifiedFromSensitive(self, obj=None):
		self.modifiedFromInput.set_sensitive(self.modifiedFromCheck.get_active())

	def updateTypeSensitive(self, obj=None):
		self.typeCombo.set_sensitive(self.typeCheck.get_active())

	def updateGroupSensitive(self, obj=None):
		self.groupCombo.set_sensitive(self.groupCheck.get_active())

	def updateTimezoneSensitive(self, obj=None):
		self.timezoneCombo.set_sensitive(self.timezoneCheck.get_active())

	def _do_search(self):
		if self.groupCheck.get_active():
			groupIds = [
				self.groupCombo.get_active()
			]
		else:
			groupIds = ui.eventGroups.getEnableIds()
		###
		conds = {}
		if self.textCSensCheck.get_active():
			conds["text"] = self.textInput.get_text()
		else:
			conds["text_lower"] = self.textInput.get_text().lower()
		if self.timeFromCheck.get_active():
			conds["time_from"] = self.timeFromInput.get_epoch(calTypes.primary)
		if self.timeToCheck.get_active():
			conds["time_to"] = self.timeToInput.get_epoch(calTypes.primary)
		if self.modifiedFromCheck.get_active():
			conds["modified_from"] = self.modifiedFromInput.get_epoch(calTypes.primary)
		if self.typeCheck.get_active():
			index = self.typeCombo.get_active()
			cls = event_lib.classes.event[index]
			conds["type"] = cls.name
		if self.timezoneCheck.get_active():
			conds["timezone"] = self.timezoneCombo.get_text()
		###
		self.trees.clear()
		for gid in groupIds:
			group = ui.eventGroups[gid]
			for event in group.search(conds):
				self.trees.append(None, (
					group.id,
					event.id,
					group.title,
					eventTreeIconPixbuf(event.getIcon()),
					event.summary,
					event.getShownDescription(),
				))
		self.resultLabel.set_label(
			_("Found {eventCount} events").format(eventCount=_(len(self.trees)))
		)

	def onSearchClick(self, obj=None):
		self.waitingDo(self._do_search)

	def onExportClick(self, obj=None):
		idsList = []
		for row in self.trees:
			gid = row[0]
			eid = row[1]
			idsList.append((gid, eid))
		y, m, d = cal_types.getSysDate(core.GREGORIAN)
		EventListExportDialog(
			idsList=idsList,
			defaultFileName=f"search-events-{y:04d}-{m:02d}-{d:02d}",
			groupTitle=f"Search Results ({y:04d}-{m:02d}-{d:02d})",
			transient_for=self,
		).run()

	def onHideShowFiltersClick(self, obj=None):
		visible = not self.vboxFilters.get_visible()
		self.vboxFilters.set_visible(visible)
		self.hideShowFiltersButton.set_label(
			_("Hide Filters") if visible else _("Show Filters")
		)

	def editEventByPath(self, path):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		try:
			gid = self.trees[path][0]
			eid = self.trees[path][1]
		except IndexError:
			# IndexError: could not find tree path 'N'
			# IndexError: column index is out of bounds: N
			return
		group = ui.eventGroups[gid]
		event = group[eid]
		event = EventEditorDialog(
			event,
			title=_("Edit ") + event.desc,
			transient_for=self,
		).run()
		if event is None:
			return
		###
		ui.eventUpdateQueue.put("e", event, self)
		###
		eventIter = self.trees.get_iter(path)
		self.trees.set_value(eventIter, 3, eventTreeIconPixbuf(event.icon))
		self.trees.set_value(eventIter, 4, event.summary)
		self.trees.set_value(eventIter, 5, event.getShownDescription())

	def rowActivated(self, treev, path, col):
		self.editEventByPath(path)

	def editEventFromMenu(self, menu, path):
		self.editEventByPath(path)

	def moveEventToGroupFromMenu(
		self,
		menu,
		eventPath,
		event,
		old_group,
		new_group,
	):
		old_group.remove(event)
		old_group.save()
		new_group.append(event)
		new_group.save()
		###
		ui.eventUpdateQueue.put("v", event, self)
		# FIXME
		###
		eventIter = self.trees.get_iter(eventPath)
		self.trees.set_value(eventIter, 0, new_group.id)
		self.trees.set_value(eventIter, 2, new_group.title)

	def copyEventToGroupFromMenu(self, menu, eventPath, event, new_group):
		new_event = event.copy()
		new_event.save()
		new_group.append(new_event)
		new_group.save()
		###
		ui.eventUpdateQueue.put("+", new_event, self)
		# FIXME
		###
		eventIter = self.trees.get_iter(eventPath)

	def moveEventToTrash(self, path):
		try:
			gid = self.trees[path][0]
			eid = self.trees[path][1]
		except IndexError:
			return
		group = ui.eventGroups[gid]
		event = group[eid]
		if not confirmEventTrash(event):
			return
		ui.moveEventToTrash(group, event, self)
		self.trees.remove(self.trees.get_iter(path))

	def moveEventToTrashFromMenu(self, menu, path):
		return self.moveEventToTrash(path)

	def moveSelectionToTrash(self):
		path = self.treev.get_cursor()[0]
		if not path:
			return
		self.moveEventToTrash(path)

	def getMoveToGroupSubMenu(self, path, group, event):
		# returns a MenuItem instance
		item = ImageMenuItem(
			_("Move to {title}").format(title="..."),
			iconName=None,## FIXME
		)
		subMenu = Menu()
		###
		for new_group in ui.eventGroups:
			if new_group.id == group.id:
				continue
			#if not new_group.enable:## FIXME
			#	continue
			if event.name in new_group.acceptsEventTypes:
				subMenu.add(menuItemFromEventGroup(
					new_group,
					func=self.moveEventToGroupFromMenu,
					args=(
						path,
						event,
						group,
						new_group,
					),
				))
		##
		item.set_submenu(subMenu)
		return item

	def getCopyToGroupSubMenu(self, path, event):
		# returns a MenuItem instance
		item = ImageMenuItem(
			_("Copy to {title}").format(title="..."),
			iconName=None,## FIXME
		)
		subMenu = Menu()
		###
		for new_group in ui.eventGroups:
			#if not new_group.enable:## FIXME
			#	continue
			if event.name in new_group.acceptsEventTypes:
				subMenu.add(menuItemFromEventGroup(
					new_group,
					func=self.copyEventToGroupFromMenu,
					args=(
						path,
						event,
						new_group,					
					),
				))
		##
		item.set_submenu(subMenu)
		return item

	def historyOfEventFromMenu(self, menu, path):
		from scal3.ui_gtk.event.history import EventHistoryDialog
		gid = self.trees[path][0]
		eid = self.trees[path][1]
		group = ui.eventGroups[gid]
		event = group[eid]
		EventHistoryDialog(event, transient_for=self).run()

	def genRightClickMenu(self, path):
		gid = self.trees[path][0]
		eid = self.trees[path][1]
		group = ui.eventGroups[gid]
		event = group[eid]
		##
		menu = Menu()
		##
		menu.add(eventWriteMenuItem(
			_("Edit"),
			imageName="document-edit.svg",
			func=self.editEventFromMenu,
			args=(path,),
		))
		##
		menu.add(eventWriteImageMenuItem(
			_("History"),
			"history.svg",
			func=self.historyOfEventFromMenu,
			args=(path,),
		))
		##
		menu.add(self.getMoveToGroupSubMenu(path, group, event))
		menu.add(gtk.SeparatorMenuItem())
		menu.add(self.getCopyToGroupSubMenu(path, event))
		##
		menu.add(gtk.SeparatorMenuItem())
		menu.add(ImageMenuItem(
			_("Move to {title}").format(title=ui.eventTrash.title),
			imageName=ui.eventTrash.getIconRel(),
			func=self.moveEventToTrashFromMenu,
			args=(path,),
		))
		##
		menu.show_all()
		return menu

	def openRightClickMenu(self, path, etime=None):
		menu = self.genRightClickMenu(path)
		if not menu:
			return
		if etime is None:
			etime = gtk.get_current_event_time()
		self.tmpMenu = menu
		menu.popup(None, None, None, None, 3, etime)

	def onTreeviewButtonPress(self, widget, gevent):
		pos_t = self.treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return
		path, col, xRel, yRel = pos_t
		#path, col = self.treev.get_cursor() ## FIXME
		if not path:
			return
		if gevent.button == 3:
			self.openRightClickMenu(path, gevent.time)
		return False

	def onTreeviewKeyPress(self, treev, gevent):
		#from scal3.time_utils import getGtkTimeFromEpoch
		# log.debug(gevent.time-getGtkTimeFromEpoch(now())## FIXME)
		# log.debug(now()-gdk.CURRENT_TIME/1000.0)
		# gdk.CURRENT_TIME == 0
		# gevent.time == gtk.get_current_event_time() ## OK
		kname = gdk.keyval_name(gevent.keyval).lower()
		# log.debug("onTreeviewKeyPress", kname)
		if kname == "menu":## Simulate right click (key beside Right-Ctrl)
			path = treev.get_cursor()[0]
			if path:
				menu = self.genRightClickMenu(path)
				if not menu:
					return
				rect = treev.get_cell_area(path, treev.get_column(1))
				x = rect.x
				if rtl:
					x -= 100
				else:
					x += 50
				dx, dy = treev.translate_coordinates(
					self,
					x,
					rect.y + rect.height,
				)
				wx, wy = self.get_window().get_origin()
				self.tmpMenu = menu
				menu.popup(
					None,
					None,
					lambda *args: (
						wx + dx,
						wy + dy + 20,
						True,
					),
					None,
					3,
					gevent.time,
				)
		elif kname == "delete":
			self.moveSelectionToTrash()
		else:
			# log.debug(kname)
			return False
		return True

	def clearResults(self):
		self.trees.clear()
		self.resultLabel.set_label("")

	def closed(self, obj=None, gevent=None):
		self.hide()
		self.clearResults()
		self.onConfigChange()
		return True

	def present(self):
		self.groupCombo.updateItems()
		gtk.Window.present(self)

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey):
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "escape":
			self.closed()
			return True
		return False
