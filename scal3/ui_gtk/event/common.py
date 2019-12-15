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

import os
from os.path import join, split

from scal3.utils import toBytes
from scal3.time_utils import durationUnitsAbs, durationUnitValues
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	getStyleColor,
	labelImageButton,
)
from scal3.ui_gtk.drawing import newColorCheckPixbuf
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
from scal3.ui_gtk.mywidgets.expander import ExpanderFrame
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event.utils import *
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


def getTreeGroupPixbuf(group):
	return newColorCheckPixbuf(
		group.color,
		ui.eventTreeGroupIconSize,
		group.enable,
	)


def getGroupRow(group):
	return (
		group.id,
		getTreeGroupPixbuf(group),
		group.title
	)


class WidgetClass(gtk.Box):
	expandDescription = True

	def __init__(self, event):
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.event = event
		###########
		hbox = HBox()
		###
		pack(hbox, gtk.Label(label=_("Calendar Type")))
		combo = CalTypeCombo()
		combo.set_active(calTypes.primary)## overwritten in updateWidget()
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = combo
		###
		pack(self, hbox)
		###########
		if event.isAllDay:
			self.tzCheck = None
		else:
			hbox = HBox()
			self.tzCheck = gtk.CheckButton(label=_("Time Zone"))
			set_tooltip(self.tzCheck, _("For input times of event"))
			pack(hbox, self.tzCheck)
			combo = TimeZoneComboBoxEntry()
			pack(hbox, combo)
			pack(hbox, gtk.Label(), 1, 1)
			self.tzCombo = combo
			pack(self, hbox)
			self.tzCheck.connect(
				"clicked",
				lambda check: self.tzCombo.set_sensitive(
					check.get_active(),
				),
			)
		###########
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Summary")))
		self.summaryEntry = gtk.Entry()
		pack(hbox, self.summaryEntry, 1, 1)
		pack(self, hbox)
		###########
		self.descriptionInput = TextFrame()
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.add(self.descriptionInput)
		###
		frame = gtk.Frame()
		frame.set_label(_("Description"))
		frame.add(swin)
		pack(self, frame, self.expandDescription, self.expandDescription)
		###########
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Icon") + ":"))
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		##########
		self.calTypeCombo.connect(
			"changed",
			self.calTypeComboChanged,
		)  # right place? before updateWidget? FIXME

	def focusSummary(self):
		self.summaryEntry.select_region(0, -1)
		self.summaryEntry.grab_focus()

	def updateWidget(self):
		# log.debug("updateWidget", self.event.files)
		self.calTypeCombo.set_active(self.event.calType)
		if self.tzCheck:
			if self.event.timeZone:
				self.tzCheck.set_active(self.event.timeZoneEnable)
				self.tzCombo.set_sensitive(self.event.timeZoneEnable)
				self.tzCombo.set_text(self.event.timeZone)
			else:
				self.tzCheck.set_active(False)
				self.tzCombo.set_sensitive(False)
		###
		self.summaryEntry.set_text(self.event.summary)
		self.descriptionInput.set_text(self.event.description)
		self.iconSelect.set_filename(self.event.icon)
		#####
		for attr in ("notificationBox", "filesBox"):
			try:
				getattr(self, attr).updateWidget()
			except AttributeError:
				pass
		#####
		self.calTypeComboChanged()

	def updateVars(self):
		self.event.calType = self.calTypeCombo.get_active()
		if self.tzCheck:
			self.event.timeZoneEnable = self.tzCheck.get_active()
			self.event.timeZone = self.tzCombo.get_text()
		else:
			self.event.timeZoneEnable = False ## FIXME
		self.event.summary = self.summaryEntry.get_text()
		self.event.description = self.descriptionInput.get_text()
		self.event.icon = self.iconSelect.get_filename()
		#####
		for attr in ("notificationBox", "filesBox"):
			try:
				getattr(self, attr).updateVars()
			except AttributeError:
				pass
		#####

	def calTypeComboChanged(self, obj=None):## FIXME
		pass


class FilesBox(gtk.Box):
	def __init__(self, event):
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.event = event
		self.vbox = VBox()
		pack(self, self.vbox)
		hbox = HBox()
		pack(hbox, gtk.Label(), 1, 1)
		addButton = labelImageButton(
			label=_("_Add File"),
			imageName="list-add.svg",
		)
		addButton.connect("clicked", self.onAddClick)
		pack(hbox, addButton)
		pack(self, hbox)
		self.show_all()
		self.newFiles = []

	def showFile(self, fname):
		hbox = HBox()
		link = gtk.LinkButton(
			self.event.getUrlForFile(fname),
			_("File") + ": " + fname,
		)
		pack(hbox, link)
		pack(hbox, gtk.Label(), 1, 1)
		delButton = labelImageButton(
			label=_("_Delete"),
			imageName="edit-delete.svg",
		)
		delButton.fname = fname
		delButton.hbox = hbox
		delButton.connect("clicked", self.onDelClick)
		pack(hbox, delButton)
		pack(self.vbox, hbox)
		hbox.show_all()

	def onAddClick(self, button):
		fcd = gtk.FileChooserDialog(
			title=_("Add File"),
		)
		dialog_add_button(
			fcd,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		dialog_add_button(
			fcd,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		fcd.set_local_only(True)
		fcd.connect("response", lambda w, e: fcd.hide())
		if fcd.run() == gtk.ResponseType.OK:
			from shutil import copy
			fpath = fcd.get_filename()
			fname = split(fpath)[-1]
			dstDir = self.event.filesDir
			os.makedirs(dstDir, exist_ok=True)
			# exist_ok parameter is added in Python 3.2
			copy(fpath, join(dstDir, fname))
			self.event.files.append(fname)
			self.newFiles.append(fname)
			self.showFile(fname)

	def onDelClick(self, button):
		os.remove(join(self.event.filesDir, button.fname))
		try:
			self.event.files.remove(button.fname)
		except Exception:
			pass
		button.hbox.destroy()

	def removeNewFiles(self):
		for fname in self.newFiles:
			os.remove(join(self.event.filesDir, fname))
		self.newFiles = []

	def updateWidget(self):
		for hbox in self.vbox.get_children():
			hbox.destroy()
		for fname in self.event.files:
			self.showFile(fname)

	def updateVars(self):## FIXME
		pass


class NotificationBox(ExpanderFrame):## or NotificationBox FIXME
	def __init__(self, event):
		ExpanderFrame.__init__(self, label=_("Notification"))
		self.event = event
		self.hboxDict = {}
		totalVbox = VBox()
		###
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Notify") + " "))
		self.notifyBeforeInput = DurationInputBox()
		pack(hbox, self.notifyBeforeInput, 0, 0)
		pack(hbox, gtk.Label(label=" " + _("before event")))
		pack(hbox, gtk.Label(), 1, 1)
		pack(totalVbox, hbox)
		###
		for cls in event_lib.classes.notifier:
			notifier = cls(self.event)
			inputWidget = makeWidget(notifier)
			if not inputWidget:
				log.error(f"notifier {cls.name}, inputWidget = {inputWidget!r}")
				continue
			hbox = HBox()
			cb = gtk.CheckButton(label=notifier.desc)
			cb.inputWidget = inputWidget
			cb.connect(
				"clicked",
				lambda check: check.inputWidget.set_sensitive(
					check.get_active(),
				),
			)
			cb.set_active(False)
			pack(hbox, cb)
			hbox.cb = cb
			#pack(hbox, gtk.Label(), 1, 1)
			pack(hbox, inputWidget, 1, 1)
			hbox.inputWidget = inputWidget
			self.hboxDict[notifier.name] = hbox
			pack(totalVbox, hbox)
		self.add(totalVbox)

	def updateWidget(self):
		self.notifyBeforeInput.setDuration(*self.event.notifyBefore)
		for hbox in self.hboxDict.values():
			hbox.cb.set_active(False)
			hbox.inputWidget.set_sensitive(False)
		for notifier in self.event.notifiers:
			hbox = self.hboxDict[notifier.name]
			hbox.cb.set_active(True)
			hbox.inputWidget.set_sensitive(True)
			hbox.inputWidget.notifier = notifier
			hbox.inputWidget.updateWidget()
		self.set_expanded(bool(self.event.notifiers))

	def updateVars(self):
		self.event.notifyBefore = self.notifyBeforeInput.getDuration()
		###
		notifiers = []
		for hbox in self.hboxDict.values():
			if hbox.cb.get_active():
				hbox.inputWidget.updateVars()
				notifiers.append(hbox.inputWidget.notifier)
		self.event.notifiers = notifiers


class DurationInputBox(gtk.Box):
	def __init__(self):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		##
		self.valueSpin = FloatSpinButton(0, 999, 1)
		pack(self, self.valueSpin)
		##
		combo = gtk.ComboBoxText()
		for unitValue, unitName in durationUnitsAbs:
			combo.append_text(_(
				" " + unitName.capitalize() + "s"
			))
		combo.set_active(2) ## hour FIXME
		pack(self, combo)
		self.unitCombo = combo

	def getDuration(self):
		return (
			self.valueSpin.get_value(),
			durationUnitValues[self.unitCombo.get_active()],
		)

	def setDuration(self, value, unit):
		self.valueSpin.set_value(value)
		self.unitCombo.set_active(durationUnitValues.index(unit))


class StrListEditor(gtk.Box):
	def __init__(self, defaultValue=""):
		self.defaultValue = defaultValue
		#####
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(False)
		self.trees = gtk.ListStore(str)
		self.treev.set_model(self.trees)
		##########
		cell = gtk.CellRendererText()
		cell.set_property("editable", True)
		col = gtk.TreeViewColumn(title="", cell_renderer=cell, text=0)
		self.treev.append_column(col)
		####
		pack(self, self.treev, 1, 1)
		##########
		toolbar = StaticToolBox(self, vertical=True)
		toolbar.append(ToolBoxItem(
			name="add",
			imageName="list-add.svg",
			onClick="onAddClick",
			desc=_("Add"),
			continuousClick=False,
		))
		####
		toolbar.append(ToolBoxItem(
			name="moveUp",
			imageName="go-up.svg",
			onClick="onMoveUpClick",
			desc=_("Move up"),
			continuousClick=False,
		))
		####
		toolbar.append(ToolBoxItem(
			name="moveDown",
			imageName="go-down.svg",
			onClick="onMoveDownClick",
			desc=_("Move down"),
			continuousClick=False,
		))
		#######
		pack(self, toolbar)

	def onAddClick(self, button):
		cur = self.treev.get_cursor()
		if cur:
			self.trees.insert(cur[0], [self.defaultValue])
		else:
			self.trees.append([self.defaultValue])

	def onMoveUpClick(self, button):
		cur = self.treev.get_cursor()
		if not cur:
			return
		i = cur[0]
		t = self.trees
		if i <= 0 or i >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(i - 1),
			t.get_iter(i),
		)
		self.treev.set_cursor(i - 1)

	def onMoveDownClick(self, button):
		cur = self.treev.get_cursor()
		if not cur:
			return
		i = cur[0]
		t = self.trees
		if i < 0 or i >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(i),
			t.get_iter(i + 1),
		)
		self.treev.set_cursor(i + 1)

	def setData(self, strList):
		self.trees.clear()
		for st in strList:
			self.trees.append([st])

	def getData(self):
		return [row[0] for row in self.trees]


class Scale10PowerComboBox(gtk.ComboBox):
	def __init__(self):
		ls = gtk.ListStore(int, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 1)
		###
		ls.append((1, _("Years")))
		ls.append((100, _("Centuries")))
		ls.append((1000, _("Thousand Years")))
		ls.append((1000 ** 2, _("Million Years")))
		ls.append((1000 ** 3, _("Billion (10^9) Years")))
		###
		self.set_active(0)

	def get_value(self):
		return self.get_model()[self.get_active()][0]

	def set_value(self, value):
		ls = self.get_model()
		for i, row in enumerate(ls):
			if row[0] == value:
				self.set_active(i)
				return
		ls.append((
			value,
			_("{yearCount} Years").format(yearCount=_(value)),
		))
		self.set_active(len(ls) - 1)


class GroupsTreeCheckList(gtk.TreeView):
	def __init__(self):
		gtk.TreeView.__init__(self)
		self.trees = gtk.ListStore(int, bool, str)## groupId(hidden), enable, summary
		self.set_model(self.trees)
		self.set_headers_visible(False)
		###
		cell = gtk.CellRendererToggle()
		#cell.set_property("activatable", True)
		cell.connect("toggled", self.enableCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		#cell.set_active(True)
		col.set_resizable(True)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Title"), cell_renderer=cell, text=2)
		col.set_resizable(True)
		self.append_column(col)
		###
		for group in ui.eventGroups:
			self.trees.append([group.id, True, group.title])

	def enableCellToggled(self, cell, path):
		i = int(path)
		active = not cell.get_active()
		self.trees[i][1] = active
		cell.set_active(active)

	def getValue(self):
		return [
			row[0] for row in self.trees if row[1]
		]

	def setValue(self, gids):
		for row in self.trees:
			row[1] = (row[0] in gids)


class SingleGroupComboBox(gtk.ComboBox):
	def __init__(self):
		ls = gtk.ListStore(int, GdkPixbuf.Pixbuf, str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		#####
		cell = gtk.CellRendererPixbuf()
		pack(self, cell)
		self.add_attribute(cell, "pixbuf", 1)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, 1)
		self.add_attribute(cell, "text", 2)
		#####
		self.updateItems()

	def updateItems(self):
		ls = self.get_model()
		activeGid = self.get_active()
		ls.clear()
		###
		for group in ui.eventGroups:
			if not group.enable:## FIXME
				continue
			ls.append(getGroupRow(group))
		###
		#try:
		gtk.ComboBox.set_active(self, 0)
		#except:
		#	pass
		if activeGid not in (None, -1):
			try:
				self.set_active(activeGid)
			except ValueError:
				pass

	def get_active(self):
		index = gtk.ComboBox.get_active(self)
		if index in (None, -1):
			return
		gid = self.get_model()[index][0]
		return gid

	def set_active(self, gid):
		ls = self.get_model()
		for i, row in enumerate(ls):
			if row[0] == gid:
				gtk.ComboBox.set_active(self, i)
				break
		else:
			raise ValueError(
				"SingleGroupComboBox.set_active: " +
				f"Group ID {gid} is not in items"
			)


if __name__ == "__main__":
	from pprint import pformat
	dialog = gtk.Window()
	dialog.vbox = VBox()
	dialog.add(dialog.vbox)
	#widget = ViewEditTagsHbox()
	#widget = EventTagsAndIconSelect()
	#widget = TagsListBox("task")
	widget = SingleGroupComboBox()
	pack(dialog.vbox, widget, 1, 1)
	#dialog.vbox.show_all()
	#dialog.resize(300, 500)
	#dialog.run()
	dialog.show_all()
	gtk.main()
	log.info(pformat(widget.getData()))
