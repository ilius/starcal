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

from scal3 import cal_types
from scal3 import core
from scal3.date_utils import dateEncode, dateDecode
from scal3.locale_man import tr as _
from scal3.locale_man import textNumEncode, textNumDecode
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	set_tooltip,
	labelImageButton,
)
from scal3.ui_gtk.toolbox import (
	ToolBoxItem,
	StaticToolBox,
)


def encode(d):
	return textNumEncode(dateEncode(d))


def decode(s):
	return dateDecode(textNumDecode(s))


def validate(s):
	return encode(decode(s))


class WidgetClass(gtk.Box):
	def __init__(self, rule):
		self.rule = rule
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		###
		self.countLabel = gtk.Label()
		pack(self, self.countLabel)
		###
		self.trees = gtk.ListStore(str)
		self.dialog = None
		###
		self.editButton = labelImageButton(
			label=_("Edit"),
			imageName="document-edit.svg",
		)
		self.editButton.connect("clicked", self.showDialog)
		pack(self, self.editButton)

	def updateCountLabel(self):
		self.countLabel.set_label(
			" " * 2 +
			_("{count} items").format(count=_(len(self.trees))) +
			" " * 2
		)

	def createDialog(self):
		if self.dialog:
			return
		log.debug("----- toplevel: {self.get_toplevel()}")
		self.dialog = gtk.Dialog(
			title=self.rule.desc,
			transient_for=self.get_toplevel(),
		)
		###
		self.treev = gtk.TreeView()
		self.treev.set_headers_visible(True)
		self.treev.set_model(self.trees)
		##
		cell = gtk.CellRendererText()
		cell.set_property("editable", True)
		cell.connect("edited", self.dateCellEdited)
		col = gtk.TreeViewColumn(title=_("Date"), cell_renderer=cell, text=0)
		# col.set_title
		self.treev.append_column(col)
		##
		toolbar = StaticToolBox(self, vertical=True)
		##
		toolbar.append(ToolBoxItem(
			name="add",
			imageName="list-add.svg",
			onClick="onAddClick",
			desc=_("Add"),
			continuousClick=False,
		))
		##
		toolbar.append(ToolBoxItem(
			name="delete",
			imageName="edit-delete.svg",
			onClick="onDeleteClick",
			desc=_("Delete"),
			continuousClick=False,
		))
		##
		toolbar.append(ToolBoxItem(
			name="moveUp",
			imageName="go-up.svg",
			onClick="onMoveUpClick",
			desc=_("Move up"),
			continuousClick=False,
		))
		##
		toolbar.append(ToolBoxItem(
			name="moveDown",
			imageName="go-down.svg",
			onClick="onMoveDownClick",
			desc=_("Move down"),
			continuousClick=False,
		))
		##
		dialogHbox = HBox()
		pack(dialogHbox, self.treev, 1, 1)
		pack(dialogHbox, toolbar)
		pack(self.dialog.vbox, dialogHbox, 1, 1)
		self.dialog.vbox.show_all()
		self.dialog.resize(200, 300)
		self.dialog.connect("response", lambda w, e: self.dialog.hide())
		##
		okButton = dialog_add_button(
			self.dialog,
			imageName="dialog-ok.svg",
			label=_("_OK"),
			res=gtk.ResponseType.OK,
		)

	def showDialog(self, w=None):
		self.createDialog()
		self.dialog.run()
		self.updateCountLabel()

	def dateCellEdited(self, cell, path, newText):
		index = int(path)
		self.trees[index][0] = validate(newText)

	def getSelectedIndex(self):
		path = self.treev.get_cursor()[0]
		if path is None:
			return None
		if len(path) < 1:
			return None
		return path[0]

	def onAddClick(self, button):
		index = self.getSelectedIndex()
		calType = self.rule.getCalType()## FIXME
		row = [encode(cal_types.getSysDate(calType))]
		if index is None:
			newIter = self.trees.append(row)
		else:
			newIter = self.trees.insert(index + 1, row)
		self.treev.set_cursor(self.trees.get_path(newIter))
		#col = self.treev.get_column(0)
		#cell = col.get_cell_renderers()[0]
		#cell.start_editing(...) ## FIXME

	def onDeleteClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		del self.trees[index]

	def onMoveUpClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index <= 0 or index >= len(t):
			gdk.beep()
			return
		t.swap(
			t.get_iter(index - 1),
			t.get_iter(index),
		)
		self.treev.set_cursor(index - 1)

	def onMoveDownClick(self, button):
		index = self.getSelectedIndex()
		if index is None:
			return
		t = self.trees
		if index < 0 or index >= len(t) - 1:
			gdk.beep()
			return
		t.swap(
			t.get_iter(index),
			t.get_iter(index + 1),
		)
		self.treev.set_cursor(index + 1)

	def updateWidget(self):
		for date in self.rule.dates:
			self.trees.append([encode(date)])
		self.updateCountLabel()

	def updateVars(self):
		dates = []
		for row in self.trees:
			dates.append(decode(row[0]))
		self.rule.setDates(dates)
