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

from scal3.path import *
from scal3.utils import myRaise
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import toolButtonFromStock, set_tooltip, dialog_add_button
from scal3.ui_gtk.tree_utils import tree_path_split

class CustomizeDialog(gtk.Dialog):
	def appendItemTree(self, item, parentIter):
		itemIter = self.model.append(parentIter)
		self.model.set(itemIter, 0, item.enable, 1, item.desc)
		for child in item.items:
			if child.customizable:
				self.appendItemTree(child, itemIter)
	def __init__(self, widget, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Customize'))
		#self.set_has_separator(False)## not in gtk3
		self.connect('delete-event', self.close)
		dialog_add_button(self, gtk.STOCK_CLOSE, _('_Close'), 0, self.close)
		###
		self._widget = widget
		self.activeOptionsWidget = None
		###
		self.model = gtk.TreeStore(bool, str) ## (GdkPixbuf.Pixbuf, str)
		treev = self.treev = gtk.TreeView(self.model)
		##
		treev.set_enable_tree_lines(True)
		treev.set_headers_visible(False)
		treev.connect('row-activated', self.rowActivated)
		##
		col = gtk.TreeViewColumn('Widget')
		##
		cell = gtk.CellRendererToggle()
		cell.connect('toggled', self.enableCellToggled)
		pack(col, cell)
		col.add_attribute(cell, 'active', 0)
		col.set_property('expand', False)
		##
		treev.append_column(col)
		col = gtk.TreeViewColumn('Widget')
		col.set_property('expand', False)
		##
		cell = gtk.CellRendererText()
		pack(col, cell)
		col.add_attribute(cell, 'text', 1)
		col.set_property('expand', True)
		##
		treev.append_column(col)
		###
		for item in widget.items:
			if item.customizable:
				self.appendItemTree(item, None)
		###
		hbox = gtk.HBox()
		vbox_l = gtk.VBox()
		pack(vbox_l, treev, 1, 1)
		pack(hbox, vbox_l, 1, 1)
		###
		toolbar = gtk.Toolbar()
		toolbar.set_orientation(gtk.Orientation.VERTICAL)
		size = gtk.IconSize.SMALL_TOOLBAR
		toolbar.set_icon_size(size)
		## argument2 to image_new_from_stock does not affect
		###
		tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
		set_tooltip(tb, _('Move up'))
		tb.connect('clicked', self.upClicked)
		toolbar.insert(tb, -1)
		###
		tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
		set_tooltip(tb, _('Move down'))
		tb.connect('clicked', self.downClicked)
		toolbar.insert(tb, -1)
		###
		pack(hbox, toolbar)
		pack(self.vbox, hbox, 1, 1)
		self.vbox_l = vbox_l
		###
		self.vbox.connect('size-allocate', self.vboxSizeRequest)
		self.vbox.show_all()
		treev.get_selection().connect('changed', self.treevCursorChanged)
	def vboxSizeRequest(self, widget, req):
		self.resize(self.get_size()[0], 1)
	def getItemByPath(self, path):
		if isinstance(path, gtk.TreePath):
			path = path.get_indices()
		elif isinstance(path, str):
			path = tree_path_split(path)
		elif isinstance(path, int):
			path = [path]
		elif not isinstance(path, (tuple, list)):
			raise TypeError('argument %s given to getItemByPath has bad type %s'%(path, type(path)))
		item = self._widget.items[path[0]]
		for i in path[1:]:
			item = item.items[i]
		return item
	def treevCursorChanged(self, selection):
		if self.activeOptionsWidget:
			try:
				self.vbox_l.remove(self.activeOptionsWidget)
			except:
				myRaise(__file__)
			self.activeOptionsWidget = None
		index_list = self.treev.get_cursor()[0]
		if not index_list:
			return
		item = self.getItemByPath(index_list)
		item.optionsWidgetCreate()
		if item.optionsWidget:
			item.optionsWidget.set_sensitive(item.enable)
			self.activeOptionsWidget = item.optionsWidget
			pack(self.vbox_l, item.optionsWidget)
			item.optionsWidget.show()
	def upClicked(self, button):
		model = self.model
		index_list = self.treev.get_cursor()[0]
		if not index_list:
			return
		i = index_list[-1]
		if len(index_list)==1:
			if i<=0 or i>=len(model):
				gdk.beep()
				return
			###
			self._widget.moveItemUp(i)
			model.swap(model.get_iter(i-1), model.get_iter(i))
			self.treev.set_cursor(i-1)
		else:
			if i<=0:
				gdk.beep()
				return
			###
			root = self.getItemByPath(index_list[:-1])
			if i>=len(root.items):
				gdk.beep()
				return
			###
			root.moveItemUp(i)
			index_list2 = list(index_list)
			index_list2[-1] = i - 1
			model.swap(model.get_iter(index_list), model.get_iter(index_list2))
			self.treev.set_cursor(index_list2)
	def downClicked(self, button):
		model = self.model
		index_list = self.treev.get_cursor()[0]
		if not index_list:
			return
		i = index_list[-1]
		if len(index_list)==1:
			if i<0 or i>=len(model)-1:
				gdk.beep()
				return
			###
			self._widget.moveItemUp(i+1)
			model.swap(model.get_iter(i), model.get_iter(i+1))
			self.treev.set_cursor(i+1)
		else:
			if i<0:
				gdk.beep()
				return
			###
			root = self.getItemByPath(index_list[:-1])
			if i>=len(root.items)-1:
				gdk.beep()
				return
			###
			root.moveItemUp(i+1)
			index_list2 = list(index_list)
			index_list2[-1] = i + 1
			model.swap(model.get_iter(index_list), model.get_iter(index_list2))
			self.treev.set_cursor(index_list2)
	def rowActivated(self, treev, path, col):
		if treev.row_expanded(path):
			treev.collapse_row(path)
		else:
			treev.expand_row(path, False)
	def enableCellToggled(self, cell, path):## FIXME
		active = not cell.get_active()
		self.model.set_value(self.model.get_iter(path), 0, active) ## or set(...)
		parentItem = self._widget
		pp = tree_path_split(path)
		item = parentItem.items[pp[0]]
		for i in pp[1:]:
			parentItem, item = item, item.items[i]
		itemIndex = int(pp[-1])
		assert parentItem.items[itemIndex] == item
		###
		if active:
			item = self.loadItem(parentItem, itemIndex, path)
		item.enable = active
		item.showHide()
		if item.customizable:
			if item.optionsWidget:
				item.optionsWidget.set_sensitive(item.enable)
		if ui.mainWin:
			ui.mainWin.setMinHeight()
	def loadItem(self, parentItem, itemIndex, itemPath):
		itemIter = self.model.get_iter(itemPath)
		item = parentItem.items[itemIndex]
		if item.loaded:
			return item
		###
		item = item.getLoadedObj()
		parentItem.replaceItem(itemIndex, item)
		parentItem.insertItemWidget(itemIndex)
		for child in item.items:
			if item.customizable:
				self.appendItemTree(child, itemIter)
		item.onConfigChange()
		item.onDateChange()
		return item
	def findItem(self, item):
		return self._widget.items.index(item)
	def updateTreeEnableChecks(self):
		for i, item in enumerate(self._widget.items):
			self.model.set_value(self.model.get_iter((i,)), 0, item.enable)
	def save(self):
		self._widget.updateVars()
		ui.ud__wcalToolbarData = ud.wcalToolbarData
		ui.ud__mainToolbarData = ud.mainToolbarData
		ui.saveConfCustomize()
		#data = self._widget.getData()## remove? FIXME
	def close(self, button=None, event=None):
		self.save()
		self.hide()
		return True



