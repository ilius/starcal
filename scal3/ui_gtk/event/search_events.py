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
from scal3.utils import cmp
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
from scal3.ui_gtk.utils import pixbufFromFile, labelStockMenuItem, labelImageMenuItem
from scal3.ui_gtk.drawing import newColorCheckPixbuf
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.multi_spin.date_time import DateTimeButton
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.event.utils import confirmEventTrash
from scal3.ui_gtk.event.common import SingleGroupComboBox


@registerSignals
class EventSearchWindow(gtk.Window, MyDialog, ud.BaseCalObj):
	def __init__(self, showDesc=False):
		gtk.Window.__init__(self)
		self.maximize()
		self.initVars()
		ud.windowList.appendItem(self)
		###
		self.set_title(_('Search Events'))
		self.connect('delete-event', self.closed)
		self.connect('key-press-event', self.keyPress)
		###
		self.vbox = gtk.VBox()
		self.add(self.vbox)
		######
		frame = TextFrame()
		frame.set_label(_('Text'))
		frame.set_border_width(5)
		pack(self.vbox, frame)
		self.textInput = frame
		##
		hbox = gtk.HBox()
		self.textCSensCheck = gtk.CheckButton(_('Case Sensitive'))
		self.textCSensCheck.set_active(False) ## FIXME
		pack(hbox, self.textCSensCheck)
		pack(self.vbox, hbox)
		######
		jd = core.getCurrentJd()
		year, month, day = jd_to_primary(jd)
		######
		hbox = gtk.HBox()
		frame = gtk.Frame()
		frame.set_label(_('Time'))
		frame.set_border_width(5)
		vboxIn = gtk.VBox()
		sgroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		####
		hboxIn = gtk.HBox()
		##
		self.timeFromCheck = gtk.CheckButton(_('From'))
		sgroup.add_widget(self.timeFromCheck)
		pack(hboxIn, self.timeFromCheck)
		pack(hboxIn, gtk.Label('  '))
		##
		self.timeFromInput = DateTimeButton()
		self.timeFromInput.set_value(((year, 1, 1), (0, 0, 0)))
		pack(hboxIn, self.timeFromInput)
		##
		pack(vboxIn, hboxIn)
		####
		hboxIn = gtk.HBox()
		##
		self.timeToCheck = gtk.CheckButton(_('To'))
		sgroup.add_widget(self.timeToCheck)
		pack(hboxIn, self.timeToCheck)
		pack(hboxIn, gtk.Label('  '))
		##
		self.timeToInput = DateTimeButton()
		self.timeToInput.set_value(((year+1, 1, 1), (0, 0, 0)))
		pack(hboxIn, self.timeToInput)
		##
		pack(vboxIn, hboxIn)
		##
		self.timeFromCheck.connect('clicked', self.updateTimeFromSensitive)
		self.timeToCheck.connect('clicked', self.updateTimeToSensitive)
		self.updateTimeFromSensitive()
		self.updateTimeToSensitive()
		####
		vboxIn.set_border_width(5)
		frame.add(vboxIn)
		pack(hbox, frame)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		######
		hbox = gtk.HBox()
		hbox.set_border_width(5)
		self.modifiedFromCheck = gtk.CheckButton(_('Modified From'))
		pack(hbox, self.modifiedFromCheck)
		pack(hbox, gtk.Label('  '))
		self.modifiedFromInput = DateTimeButton()
		self.modifiedFromInput.set_value(((year, 1, 1), (0, 0, 0)))
		pack(hbox, self.modifiedFromInput)
		##
		self.modifiedFromCheck.connect('clicked', self.updateModifiedFromSensitive)
		self.updateModifiedFromSensitive()
		pack(self.vbox, hbox)
		######
		hbox = gtk.HBox()
		hbox.set_border_width(5)
		self.typeCheck = gtk.CheckButton(_('Event Type'))
		pack(hbox, self.typeCheck)
		pack(hbox, gtk.Label('  '))
		##
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.event:
			combo.append_text(cls.desc)
		combo.set_active(0)
		pack(hbox, combo)
		self.typeCombo = combo
		##
		self.typeCheck.connect('clicked', self.updateTypeSensitive)
		self.updateTypeSensitive()
		pack(self.vbox, hbox)
		######
		hbox = gtk.HBox()
		hbox.set_border_width(5)
		self.groupCheck = gtk.CheckButton(_('Group'))
		pack(hbox, self.groupCheck)
		pack(hbox, gtk.Label('  '))
		self.groupCombo = SingleGroupComboBox()
		pack(hbox, self.groupCombo)
		##
		self.groupCheck.connect('clicked', self.updateGroupSensitive)
		self.updateGroupSensitive()
		pack(self.vbox, hbox)
		######
		bbox = gtk.HButtonBox()
		bbox.set_layout(gtk.ButtonBoxStyle.START)
		bbox.set_border_width(5)
		searchButton = gtk.Button()
		searchButton.set_label(_('_Search'))
		searchButton.set_image(gtk.Image.new_from_stock(gtk.STOCK_FIND, gtk.IconSize.BUTTON))
		searchButton.connect('clicked', self.searchClicked)
		bbox.add(searchButton)
		pack(self.vbox, bbox)
		######
		treev = gtk.TreeView()
		trees = gtk.TreeStore(int, int, str, GdkPixbuf.Pixbuf, str, str)
		## gid, eid, group_name, icon, summary, description
		treev.set_model(trees)
		treev.connect('button-press-event', self.treevButtonPress)
		treev.connect('row-activated', self.rowActivated)
		treev.connect('key-press-event', self.treevKeyPress)
		treev.set_headers_clickable(True)
		###
		self.colGroup = gtk.TreeViewColumn(_('Group'), gtk.CellRendererText(), text=2)
		self.colGroup.set_resizable(True)
		self.colGroup.set_sort_column_id(2)
		self.colGroup.set_property('expand', False)
		treev.append_column(self.colGroup)
		###
		self.colIcon = gtk.TreeViewColumn()
		cell = gtk.CellRendererPixbuf()
		pack(self.colIcon, cell)
		self.colIcon.add_attribute(cell, 'pixbuf', 3)
		#self.colIcon.set_sort_column_id(3)## FIXME
		self.colIcon.set_property('expand', False)
		treev.append_column(self.colIcon)
		###
		self.colSummary = gtk.TreeViewColumn(_('Summary'), gtk.CellRendererText(), text=4)
		self.colSummary.set_resizable(True)
		self.colSummary.set_sort_column_id(4)
		self.colSummary.set_property('expand', True)## FIXME
		treev.append_column(self.colSummary)
		###
		self.colDesc = gtk.TreeViewColumn(_('Description'), gtk.CellRendererText(), text=5)
		self.colDesc.set_sort_column_id(5)
		self.colDesc.set_visible(showDesc)
		self.colDesc.set_property('expand', True)## FIXME
		treev.append_column(self.colDesc)
		###
		trees.set_sort_func(2, self.sort_func_group)
		######
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		swin.add(treev)
		####
		vbox = gtk.VBox(spacing=5)
		vbox.set_border_width(5)
		###
		topHbox = gtk.HBox()
		self.resultLabel = gtk.Label('')
		pack(topHbox, self.resultLabel)
		pack(topHbox, gtk.Label(''), 1, 1)
		pack(vbox, topHbox)
		####
		columnBox = gtk.HBox(spacing=5)
		pack(columnBox, gtk.Label(_('Columns')+':    '))
		##
		check = gtk.CheckButton(_('Group'))
		check.set_active(True)
		check.connect('clicked', lambda w: self.colGroup.set_visible(w.get_active()))
		pack(columnBox, check)
		##
		check = gtk.CheckButton(_('Icon'))
		check.set_active(True)
		check.connect('clicked', lambda w: self.colIcon.set_visible(w.get_active()))
		pack(columnBox, check)
		##
		check = gtk.CheckButton(_('Summary'))
		check.set_active(True)
		check.connect('clicked', lambda w: self.colSummary.set_visible(w.get_active()))
		pack(columnBox, check)
		##
		check = gtk.CheckButton(_('Description'))
		check.set_active(showDesc)
		check.connect('clicked', lambda w: self.colDesc.set_visible(w.get_active()))
		pack(columnBox, check)
		##
		pack(vbox, columnBox)
		####
		pack(vbox, swin, 1, 1)
		##
		frame = gtk.Frame()
		frame.set_label(_('Search Results'))
		frame.set_border_width(10)
		frame.add(vbox)
		##
		pack(self.vbox, frame, 1, 1)
		###
		bbox2 = gtk.HButtonBox()
		bbox2.set_layout(gtk.ButtonBoxStyle.END)
		bbox2.set_border_width(10)
		closeButton = gtk.Button()
		closeButton.set_label(_('_Close'))
		closeButton.set_image(gtk.Image.new_from_stock(gtk.STOCK_CLOSE, gtk.IconSize.BUTTON))
		closeButton.connect('clicked', self.closed)
		bbox2.add(closeButton)
		pack(self.vbox, bbox2)
		######
		self.treev = treev
		self.trees = trees
		self.vbox.show_all()
		#self.maximize()## FIXME
	## FIXME
	sort_func_group = lambda self, model, iter1, iter2: cmp(
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
			conds['text'] = self.textInput.get_text()
		else:
			conds['text_lower'] = self.textInput.get_text().lower()
		if self.timeFromCheck.get_active():
			conds['time_from'] = self.timeFromInput.get_epoch(calTypes.primary)
		if self.timeToCheck.get_active():
			conds['time_to'] = self.timeToInput.get_epoch(calTypes.primary)
		if self.modifiedFromCheck.get_active():
			conds['modified_from'] = self.modifiedFromInput.get_epoch(calTypes.primary)
		if self.typeCheck.get_active():
			index = self.typeCombo.get_active()
			cls = event_lib.classes.event[index]
			conds['type'] = cls.name
		###
		self.trees.clear()
		for gid in groupIds:
			group = ui.eventGroups[gid]
			for evData in group.search(conds):
				self.trees.append(None, (
					group.id,
					evData['id'],
					group.title,
					pixbufFromFile(evData['icon']),
					evData['summary'],
					evData['description'],
				))
		self.resultLabel.set_label(_('Found %s events')%_(len(self.trees)))
	def searchClicked(self, obj=None):
		self.waitingDo(self._do_search)
	def editEventByPath(self, path):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		try:
			gid = self.trees[path][0]
			eid = self.trees[path][1]
		except:
			return
		group = ui.eventGroups[gid]
		event = group[eid]
		event = EventEditorDialog(
			event,
			title=_('Edit ')+event.desc,
			parent=self,
		).run()
		if event is None:
			return
		###
		ui.eventDiff.add('e', event)
		###
		eventIter = self.trees.get_iter(path)
		self.trees.set_value(eventIter, 3, pixbufFromFile(event.icon))
		self.trees.set_value(eventIter, 4, event.summary)
		self.trees.set_value(eventIter, 5, event.getShownDescription())
	def rowActivated(self, treev, path, col):
		self.editEventByPath(path)
	def editEventFromMenu(self, menu, path):
		self.editEventByPath(path)
	def moveEventToGroupFromMenu(self, menu, eventPath, event, old_group, new_group):
		old_group.remove(event)
		old_group.save()
		new_group.append(event)
		new_group.save()
		###
		ui.eventDiff.add('v', event)
		## FIXME
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
		ui.eventDiff.add('+', new_event)
		## FIXME
		###
		eventIter = self.trees.get_iter(eventPath)
	def moveEventToTrash(self, path):
		try:
			gid = self.trees[path][0]
			eid = self.trees[path][1]
		except:
			return
		group = ui.eventGroups[gid]
		event = group[eid]
		if not confirmEventTrash(event):
			return
		ui.moveEventToTrash(group, event)
		ui.reloadTrash = True
		ui.eventDiff.add('-', event)
		self.trees.remove(self.trees.get_iter(path))
	moveEventToTrashFromMenu = lambda self, menu, path: self.moveEventToTrash(path)
	def moveSelectionToTrash(self):
		path = self.treev.get_cursor()[0]
		if not path:
			return
		self.moveEventToTrash(path)
	def getMoveToGroupSubMenu(self, path, group, event):
		## returns a MenuItem instance
		item = labelStockMenuItem(
			_('Move to %s')%'...',
			None,## FIXME
		)
		subMenu = gtk.Menu()
		###
		for new_group in ui.eventGroups:
			if new_group.id == group.id:
				continue
			#if not new_group.enable:## FIXME
			#	continue
			if event.name in new_group.acceptsEventTypes:
				new_groupItem = ImageMenuItem()
				new_groupItem.set_label(new_group.title)
				##
				image = gtk.Image()
				image.set_from_pixbuf(newColorCheckPixbuf(new_group.color, 20, True))
				new_groupItem.set_image(image)
				##
				new_groupItem.connect(
					'activate',
					self.moveEventToGroupFromMenu,
					path,
					event,
					group,
					new_group,
				)
				##
				subMenu.add(new_groupItem)
		##
		item.set_submenu(subMenu)
		return item
	def getCopyToGroupSubMenu(self, path, event):
		## returns a MenuItem instance
		item = labelStockMenuItem(
			_('Copy to %s')%'...',
			None,## FIXME
		)
		subMenu = gtk.Menu()
		###
		for new_group in ui.eventGroups:
			#if not new_group.enable:## FIXME
			#	continue
			if event.name in new_group.acceptsEventTypes:
				new_groupItem = ImageMenuItem()
				new_groupItem.set_label(new_group.title)
				##
				image = gtk.Image()
				image.set_from_pixbuf(newColorCheckPixbuf(new_group.color, 20, True))
				new_groupItem.set_image(image)
				##
				new_groupItem.connect(
					'activate',
					self.copyEventToGroupFromMenu,
					path,
					event,
					new_group,
				)
				##
				subMenu.add(new_groupItem)
		##
		item.set_submenu(subMenu)
		return item
	def genRightClickMenu(self, path):
		gid = self.trees[path][0]
		eid = self.trees[path][1]
		group = ui.eventGroups[gid]
		event = group[eid]
		##
		menu = gtk.Menu()
		##
		menu.add(labelStockMenuItem(
			'Edit',
			gtk.STOCK_EDIT,
			self.editEventFromMenu,
			path,
		))
		##
		menu.add(self.getMoveToGroupSubMenu(path, group, event))
		menu.add(gtk.SeparatorMenuItem())
		menu.add(self.getCopyToGroupSubMenu(path, event))
		##
		menu.add(gtk.SeparatorMenuItem())
		menu.add(labelImageMenuItem(
			_('Move to %s')%ui.eventTrash.title,
			ui.eventTrash.icon,
			self.moveEventToTrashFromMenu,
			path,
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
	def treevButtonPress(self, widget, gevent):
		pos_t = self.treev.get_path_at_pos(int(gevent.x), int(gevent.y))
		if not pos_t:
			return
		path, col, xRel, yRel = pos_t
		#path, col = self.treev.get_cursor() ## FIXME
		if not path:
			return
		if gevent.button==3:
			self.openRightClickMenu(path, gevent.time)
		return False
	def treevKeyPress(self, treev, gevent):
		#from scal3.time_utils import getGtkTimeFromEpoch
		#print(gevent.time-getGtkTimeFromEpoch(now())## FIXME)
		#print(now()-gdk.CURRENT_TIME/1000.0)
		## gdk.CURRENT_TIME == 0## FIXME
		## gevent.time == gtk.get_current_event_time() ## OK
		kname = gdk.keyval_name(gevent.keyval).lower()
		#print('treevKeyPress', kname)
		if kname=='menu':## Simulate right click (key beside Right-Ctrl)
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
				dx, dy = treev.translate_coordinates(self, x, rect.y + rect.height)
				wx, wy = self.get_window().get_origin()
				self.tmpMenu = menu
				menu.popup(
					None,
					None,
					lambda *args: (
						wx+dx,
						wy+dy+20,
						True,
					),
					None,
					3,
					gevent.time,
				)
		elif kname=='delete':
			self.moveSelectionToTrash()
		else:
			#print(kname)
			return False
		return True
	def clearResults(self):
		self.trees.clear()
		self.resultLabel.set_label('')
	def closed(self, obj=None, gevent=None):
		self.hide()
		self.clearResults()
		self.onConfigChange()
		return True
	def present(self):
		self.groupCombo.updateItems()
		gtk.Window.present(self)
	def keyPress(self, arg, gevent):
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == 'escape':
			self.closed()
			return True
		return False



