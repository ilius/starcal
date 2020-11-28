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

from scal3 import core
from scal3.core import pixDir
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	openWindow,
	dialog_add_button,
	hideList,
	labelImageButton,
)
from scal3.ui_gtk.mywidgets.icon import IconSelectButton


#class EventCategorySelect(gtk.Box):


class EventTagsAndIconSelect(gtk.Box):
	def __init__(self):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		#########
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Category") + ":"))
		#####
		ls = gtk.ListStore(GdkPixbuf.Pixbuf, str)
		combo = gtk.ComboBox()
		combo.set_model(ls)
		###
		cell = gtk.CellRendererPixbuf()
		pack(combo, cell, False)
		combo.add_attribute(cell, "pixbuf", 0)
		###
		cell = gtk.CellRendererText()
		pack(combo, cell, True)
		combo.add_attribute(cell, "text", 1)
		###
		ls.append([None, _("Custom")])  # first or last FIXME
		for item in ui.eventTags:
			ls.append([
				(
					GdkPixbuf.Pixbuf.new_from_file(item.icon)
					if item.icon else None
				),
				item.desc
			])
		###
		self.customItemIndex = 0  # len(ls) - 1
		pack(hbox, combo)
		self.typeCombo = combo
		self.typeStore = ls

		###
		vbox = VBox()
		pack(vbox, hbox)
		pack(self, vbox)
		#########
		iconLabel = gtk.Label(label=_("Icon"))
		pack(hbox, iconLabel)
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		tagsLabel = gtk.Label(label=_("Tags"))
		pack(hbox, tagsLabel)
		hbox3 = HBox()
		self.tagButtons = []
		for item in ui.eventTags:
			button = gtk.ToggleButton(label=item.desc)
			button.tagName = item.name
			self.tagButtons.append(button)
			pack(hbox3, button)
		self.swin = gtk.ScrolledWindow()
		self.swin.set_policy(
			gtk.PolicyType.ALWAYS,  # horizontal AUTOMATIC or ALWAYS FIXME
			gtk.PolicyType.NEVER,
		)
		self.swin.add(hbox3)
		pack(self, self.swin, 1, 1)
		self.customTypeWidgets = (iconLabel, self.iconSelect, tagsLabel, self.swin)
		#########
		self.typeCombo.connect("changed", self.typeComboChanged)
		self.connect("scroll-event", self.scrollEvent)
		#########
		self.show_all()
		hideList(self.customTypeWidgets)

	def scrollEvent(self, widget, gevent):
		self.swin.get_hscrollbar().emit("scroll-event", gevent)

	def typeComboChanged(self, combo):
		i = combo.get_active()
		if i is None:
			return
		if i == self.customItemIndex:
			showList(self.customTypeWidgets)
		else:
			hideList(self.customTypeWidgets)

	def getData(self):
		active = self.typeCombo.get_active()
		if active in (-1, None):
			icon = ""
			tags = []
		else:
			if active == self.customItemIndex:
				icon = self.iconSelect.get_filename()
				tags = [
					button.tagName
					for button in self.tagButtons
					if button.get_active()
				]
			else:
				item = ui.eventTags[active]
				icon = item.icon
				tags = [item.name]
		return {
			"icon": icon,
			"tags": tags,
		}


class TagsListBox(gtk.Box):
	"""
		[x] Only related tags     tt: Show only tags related to this event type
		Sort by:
			Name
			Usage


		Related to this event type (first)
		Most used (first)
		Most used for this event type (first)
	"""
	def __init__(self, eventType=""):## "" == "custom"
		gtk.Box.__init__(self, orientation=gtk.Orientation.VERTICAL)
		####
		self.eventType = eventType
		########
		if eventType:
			hbox = HBox()
			self.relatedCheck = gtk.CheckButton(label=_("Only related tags"))
			set_tooltip(
				self.relatedCheck,
				_("Show only tags related to this event type"),
			)
			self.relatedCheck.set_active(True)
			self.relatedCheck.connect("clicked", self.optionsChanged)
			pack(hbox, self.relatedCheck)
			pack(hbox, gtk.Label(), 1, 1)
			pack(self, hbox)
		########
		treev = gtk.TreeView()
		treeModel = gtk.ListStore(
			str,  # name(hidden)
			bool,  # enable
			str,  # description
			int,  # usage(hidden)
			str,  # usage(locale)
		)
		treev.set_model(treeModel)
		###
		cell = gtk.CellRendererToggle()
		#cell.set_property("activatable", True)
		cell.connect("toggled", self.enableCellToggled)
		col = gtk.TreeViewColumn(title=_("Enable"), cell_renderer=cell)
		col.add_attribute(cell, "active", 1)
		#cell.set_active(False)
		col.set_resizable(True)
		col.set_sort_column_id(1)
		col.set_sort_indicator(True)
		treev.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Name"), cell_renderer=cell, text=2)## really desc, not name
		col.set_resizable(True)
		col.set_sort_column_id(2)
		col.set_sort_indicator(True)
		treev.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Usage"), cell_renderer=cell, text=4)
		#col.set_resizable(True)
		col.set_sort_column_id(3) ## previous column (hidden and int)
		col.set_sort_indicator(True)
		treev.append_column(col)
		###
		swin = gtk.ScrolledWindow()
		swin.add(treev)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(self, swin, 1, 1)
		####
		self.treeview = treev
		self.treeModel = treeModel
		####
		#ui.updateEventTagsUsage()## FIXME
		#for (i, tagObj) in enumerate(ui.eventTags):  # for testing
		#	tagObj.usage = i*10
		self.optionsChanged()
		self.show_all()

	def optionsChanged(self, widget=None, tags=None):
		if not tags:
			tags = self.getData()
		tagObjList = ui.eventTags
		if self.eventType:
			if self.relatedCheck.get_active():
				tagObjList = [t for t in tagObjList if self.eventType in t.eventTypes]
		self.treeModel.clear()
		for t in tagObjList:
			self.treeModel.append((
				t.name,
				t.name in tags, ## True or False
				t.desc,
				t.usage,
				_(t.usage)
			))

	def enableCellToggled(self, cell, path):
		i = int(path)
		active = not cell.get_active()
		self.treeModel[i][1] = active
		cell.set_active(active)

	def getData(self):
		tags = []
		for row in self.treeModel:
			if row[1]:
				tags.append(row[0])
		return tags

	def setData(self, tags):
		self.optionsChanged(tags=tags)


class TagEditorDialog(gtk.Dialog):
	def __init__(self, eventType="", **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_("Tags"))
		self.set_transient_for(None)
		self.tags = []
		self.tagsBox = TagsListBox(eventType)
		pack(self.vbox, self.tagsBox, 1, 1)
		####
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("_Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)
		####
		self.vbox.show_all()
		self.getData = self.tagsBox.getData
		self.setData = self.tagsBox.setData


class ViewEditTagsHbox(gtk.Box):
	def __init__(self, eventType=""):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.tags = []
		pack(self, gtk.Label(label=_("Tags") + ":  "))
		self.tagsLabel = gtk.Label()
		pack(self, self.tagsLabel, 1, 1)
		self.dialog = TagEditorDialog(eventType, transient_for=self.get_toplevel())
		self.dialog.connect("response", self.dialogResponse)
		self.editButton = labelImageButton(
			label=_("_Edit"),
			imageName="document-edit.svg",
		)
		self.editButton.connect("clicked", self.onEditButtonClick)
		pack(self, self.editButton)
		self.show_all()

	def onEditButtonClick(self, widget):
		openWindow(self.dialog)

	def dialogResponse(self, dialog, resp):
		# log.debug("dialogResponse", dialog, resp)
		if resp == gtk.ResponseType.OK:
			self.setData(dialog.getData())
		dialog.hide()

	def setData(self, tags):
		self.tags = tags
		self.dialog.setData(tags)
		sep = _(",") + " "
		self.tagsLabel.set_label(sep.join([ui.eventTagsDesc[tag] for tag in tags]))

	def getData(self):
		return self.tags
