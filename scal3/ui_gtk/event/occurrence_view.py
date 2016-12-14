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

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.utils import imageFromFile, labelStockMenuItem, labelImageMenuItem
from scal3.ui_gtk import gtk_ud as ud


@registerSignals
class DayOccurrenceView(gtk.ScrolledWindow, ud.BaseCalObj):
	_name = 'eventDayView'
	desc = _('Events of Day')
	updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		self.connect('size-allocate', self.onSizeRequest)
		self.vbox = gtk.VBox(spacing=5)
		self.add_with_viewport(self.vbox)
		self.initVars()
		self.maxHeight = 200
		self.showDesc = True
	def onSizeRequest(self, widget, requisition):
		#print('onSizeRequest', requisition.width, requisition.height)
		requisition.height = min(
			self.maxHeight,## FIXME
			self.vbox.size_request().height + 2,## >=2 FIXME
		)
		return True
	def onDateChange(self, *a, **kw):
		from scal3.ui_gtk.mywidgets.text_widgets import ReadOnlyLabel
		ud.BaseCalObj.onDateChange(self, *a, **kw)
		cell = ui.cell
		## destroy all VBox contents and add again
		for hbox in self.vbox.get_children():
			hbox.destroy()
		self.labels = []## we don't use it, just to prevent garbage collector from removing it
		for occurData in cell.eventsData:
			if not occurData['show'][0]:
				continue
			## occurData['time'], occurData['text'], occurData['icon']
			text = ''.join(occurData['text']) if self.showDesc else occurData['text'][0]
			###
			hbox = gtk.HBox(spacing=5)
			if occurData['icon']:
				pack(hbox, imageFromFile(occurData['icon']))
			if occurData['time']:
				label = ReadOnlyLabel(occurData['time'])
				self.labels.append(label)
				label.set_direction(gtk.TextDirection.LTR)
				label.connect('populate-popup', self.onEventLabelPopup, occurData)
				pack(hbox, label)
				pack(hbox, gtk.Label('  '))
			label = ReadOnlyLabel(text)
			self.labels.append(label)
			label.set_line_wrap(True)
			label.set_use_markup(False)## should escape text if using markup FIXME
			label.connect('populate-popup', self.onEventLabelPopup, occurData)
			pack(hbox, label)## or 1, 1 (center) FIXME
			pack(self.vbox, hbox)
			pack(self.vbox, gtk.HSeparator())
		self.show_all()
		self.vbox.show_all()
		self.set_visible(bool(cell.eventsData))
	def moveEventToGroupFromMenu(self, item, event, prev_group, newGroup):
		prev_group.remove(event)
		prev_group.save()
		ui.reloadGroups.append(prev_group.id)
		###
		newGroup.append(event)
		newGroup.save()
		###
		ui.eventDiff.add('v', event)
		###
		self.onConfigChange()
	def copyOccurToGroupFromMenu(self, item, newGroup, newEventType, event, occurData):
		newEvent = newGroup.createEvent(newEventType)
		newEvent.copyFrom(event)
		startEpoch, endEpoch = occurData['time_epoch']
		newEvent.setStartEpoch(startEpoch)
		newEvent.setEnd('epoch', endEpoch)
		newEvent.afterModify()
		newEvent.save()
		###
		newGroup.append(newEvent)
		newGroup.save()
		ui.eventDiff.add('+', newEvent)
		###
		self.onConfigChange()
	def onEventLabelPopup(self, label, menu, occurData):
		from scal3.ui_gtk.event.utils import menuItemFromEventGroup
		if event_lib.readOnly:
			return
		# instead of creating a new menu, we should remove the current items from current menu
		# but here we will keep the items from ReadOnlyLabel
		####
		groupId, eventId = occurData['ids']
		event = ui.getEvent(groupId, eventId)
		group = ui.eventGroups[groupId]
		if not event.readOnly:
			menu.add(gtk.SeparatorMenuItem())
			###
			winTitle = _('Edit ') + event.desc
			menu.add(labelStockMenuItem(
				winTitle,
				gtk.STOCK_EDIT,
				self.editEventClicked,
				winTitle,
				event,
				groupId,
			))
			###
			moveToItem = labelStockMenuItem(
				_('Move to %s')%'...',
				None,## FIXME
			)
			moveToMenu = gtk.Menu()
			for newGroup in ui.eventGroups:
				if newGroup.id == group.id:
					continue
				if not newGroup.enable:
					continue
				if event.name in newGroup.acceptsEventTypes:
					newGroupItem = menuItemFromEventGroup(newGroup)
					newGroupItem.connect(
						'activate',
						self.moveEventToGroupFromMenu,
						event,
						group,
						newGroup,
					)
					moveToMenu.add(newGroupItem)
			moveToItem.set_submenu(moveToMenu)
			menu.add(moveToItem)
			###
			if not event.isSingleOccur:
				newEventType = 'allDayTask' if occurData['is_allday'] else 'task'
				copyOccurItem = labelStockMenuItem(
					_('Copy as %s to...') % event_lib.classes.event.byName[newEventType].desc,## FIXME
					None,
				)
				copyOccurMenu = gtk.Menu()
				for newGroup in ui.eventGroups:
					if not newGroup.enable:
						continue
					if newEventType in newGroup.acceptsEventTypes:
						newGroupItem = menuItemFromEventGroup(newGroup)
						newGroupItem.connect(
							'activate',
							self.copyOccurToGroupFromMenu,
							newGroup,
							newEventType,
							event,
							occurData,
						)
						copyOccurMenu.add(newGroupItem)
				copyOccurItem.set_submenu(copyOccurMenu)
				menu.add(copyOccurItem)
				###
				menu.add(gtk.SeparatorMenuItem())
			###
			menu.add(labelImageMenuItem(
				_('Move to %s') % ui.eventTrash.title,
				ui.eventTrash.icon,
				self.moveEventToTrash,
				event,
				groupId,
			))
		####
		menu.show_all()
		label.tmpMenu = menu
		ui.updateFocusTime()
	def editEventClicked(self, item, winTitle, event, groupId):
		from scal3.ui_gtk.event.editor import EventEditorDialog
		event = EventEditorDialog(
			event,
			title=winTitle,
			#parent=self,## FIXME
		).run()
		if event is None:
			return
		ui.eventDiff.add('e', event)
		self.onConfigChange()
	def moveEventToTrash(self, item, event, groupId):
		from scal3.ui_gtk.event.utils import confirmEventTrash
		if not confirmEventTrash(event, parent=ui.mainWin):
			return
		ui.moveEventToTrashFromOutside(ui.eventGroups[groupId], event)
		self.onConfigChange()


class WeekOccurrenceView(gtk.TreeView):
	updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
	def __init__(self, abrivateWeekDays=False):
		self.abrivateWeekDays = abrivateWeekDays
		self.absWeekNumber = core.getAbsWeekNumberFromJd(ui.cell.jd)## FIXME
		gtk.TreeView.__init__(self)
		self.set_headers_visible(False)
		self.ls = gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)## icon, weekDay, time, text
		self.set_model(self.ls)
		###
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn(_('Icon'), cell)
		col.add_attribute(cell, 'pixbuf', 0)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Week Day'), cell)
		col.add_attribute(cell, 'text', 1)
		col.set_resizable(True)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Time'), cell)
		col.add_attribute(cell, 'text', 2)
		col.set_resizable(True)## FIXME
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Description'), cell)
		col.add_attribute(cell, 'text', 3)
		col.set_resizable(True)
		self.append_column(col)
	def updateWidget(self):
		cells, wEventData = ui.cellCache.getWeekData(self.absWeekNumber)
		self.ls.clear()
		for item in wEventData:
			if not item['show'][1]:
				continue
			self.ls.append(
				pixbufFromFile(item['icon']),
				core.weekDayNameAuto(self.abrivateWeekDays)[item['weekDay']],
				item['time'],
				item['text'],
			)


'''
class MonthOccurrenceView(gtk.TreeView, event_lib.MonthOccurrenceView):
	updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
	def __init__(self):
		event_lib.MonthOccurrenceView.__init__(self, ui.cell.jd)
		gtk.TreeView.__init__(self)
		self.set_headers_visible(False)
		self.ls = gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)## icon, day, time, text
		self.set_model(self.ls)
		###
		cell = gtk.CellRendererPixbuf()
		col = gtk.TreeViewColumn('', cell)
		col.add_attribute(cell, 'pixbuf', 0)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Day'), cell)
		col.add_attribute(cell, 'text', 1)
		col.set_resizable(True)
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Time'), cell)
		col.add_attribute(cell, 'text', 2)
		col.set_resizable(True)## FIXME
		self.append_column(col)
		###
		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(_('Description'), cell)
		col.add_attribute(cell, 'text', 3)
		col.set_resizable(True)
		self.append_column(col)
	def updateWidget(self):
		self.updateData()
		self.ls.clear()## FIXME
		for item in self.data:
			if not item['show'][2]:
				continue
			self.ls.append(
				pixbufFromFile(item['icon']),
				_(item['day']),
				item['time'],
				item['text'],
			)
'''




