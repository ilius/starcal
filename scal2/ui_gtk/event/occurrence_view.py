# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal2.utils import toStr, toUnicode
from scal2.locale_man import tr as _

from scal2 import event_man
from scal2 import ui

import gtk

from scal2.ui_gtk.utils import imageFromFile, labelStockMenuItem, labelImageMenuItem
from scal2.ui_gtk.gcommon import IntegratedCalObj
from scal2.ui_gtk.event.common import EventEditorDialog

class DayOccurrenceView(gtk.VBox, IntegratedCalObj):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self, populatePopupFunc=None):
        self.jd = ui.cell.jd
        gtk.VBox.__init__(self)
        ## what to do with populatePopupFunc FIXME
        ## self.textview.connect('populate-popup', populatePopupFunc)
        self.clipboard = gtk.clipboard_get()
    def updateWidget(self):
        cell = ui.cellCache.getCell(self.jd)
        ## destroy all VBox contents and add again
        for hbox in self.get_children():
            hbox.destroy()
        for item in cell.eventsData:
            ## item['time'], item['text'], item['icon']
            hbox = gtk.HBox()
            if item['icon']:
                hbox.pack_start(imageFromFile(item['icon']), 0, 0)
            if item['time']:
                label = gtk.Label(item['time'])
                label.set_direction(gtk.TEXT_DIR_LTR)
                hbox.pack_start(label, 0, 0)
                hbox.pack_start(gtk.Label('  '), 0, 0)
            label = gtk.Label(item['text'])
            label.set_selectable(True)
            label.set_line_wrap(True)
            label.set_use_markup(True)
            label.connect('populate-popup', self.onLabelPopupPopulate, item['ids'])
            hbox.pack_start(label, 0, 0)## or 1, 1 (center) FIXME
            self.pack_start(hbox, 0, 0)
        self.show_all()
        self.set_visible(bool(cell.eventsData))
    def onLabelPopupPopulate(self, label, menu, ids):
        menu = gtk.Menu()
        ####
        itemCopyAll = gtk.ImageMenuItem(_('Copy _All'))
        itemCopyAll.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopyAll.connect('activate', self.copyAll, label)
        menu.add(itemCopyAll)
        ####
        itemCopy = gtk.ImageMenuItem(_('_Copy'))
        itemCopy.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        if label.get_property('cursor-position') != label.get_property('selection-bound'):
            itemCopy.connect('activate', self.copy, label)
        else:
            itemCopy.set_sensitive(False)
        menu.add(itemCopy)
        ####
        menu.add(gtk.SeparatorMenuItem())
        ####
        (groupId, eventId) = ids
        event = ui.getEvent(groupId, eventId)
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
        menu.add(gtk.SeparatorMenuItem())
        ###
        menu.add(labelImageMenuItem(
            _('Move to %s')%ui.eventTrash.title,
            ui.eventTrash.icon,
            self.moveEventToTrash,
            event,
            groupId,
        ))
        ####
        menu.show_all()
        menu.popup(None, None, None, 3, 0)
    def editEventClicked(self, item, winTitle, event, groupId):
        event = EventEditorDialog(
            event,
            title=winTitle,
            #parent=self,## FIXME
        ).run()
        if event is None:
            return
        ui.changedEvents.append((groupId, event.id))
        self.onConfigChange()
    def moveEventToTrash(self, item, event, groupId):
        #if not confirm(_('Press OK if you are sure to move event "%s" to trash')%event.summary):
        #    return
        ui.moveEventToTrashFromOutside(ui.eventGroups[groupId], event)
        self.onConfigChange()
    def copy(self, item, label):
        bound = label.get_property('selection-bound')
        cursor = label.get_property('cursor-position')
        start = min(bound, cursor)
        end = max(bound, cursor)
        self.clipboard.set_text(toStr(toUnicode(label.get_text())[start:end]))
    copyAll = lambda self, item, label: self.clipboard.set_text(label.get_label())

class WeekOccurrenceView(gtk.TreeView):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self, abrivateWeekDays=False):
        self.abrivateWeekDays = abrivateWeekDays
        self.absWeekNumber = core.getAbsWeekNumberFromJd(ui.cell.jd)
        gtk.TreeView.__init__(self)
        self.set_headers_visible(False)
        self.ls = gtk.ListStore(gdk.Pixbuf, str, str, str)## icon, weekDay, time, text
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
        (cells, wEventData) = ui.cellCache.getWeekData(self.absWeekNumber)
        self.ls.clear()
        for item in wEventData:
            self.ls.append(
                pixbufFromFile(item['icon']),
                core.weekDayNameAb(item['weekDay']) if self.abrivateWeekDays else core.weekDayName(item['weekDay']),
                item['time'],
                item['text'],
            )


'''
class MonthOccurrenceView(event_man.MonthOccurrenceView, gtk.TreeView):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self):
        event_man.MonthOccurrenceView.__init__(self, ui.cell.jd)
        gtk.TreeView.__init__(self)
        self.set_headers_visible(False)
        self.ls = gtk.ListStore(gdk.Pixbuf, str, str, str)## icon, day, time, text
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
            self.ls.append(
                pixbufFromFile(item['icon']),
                _(item['day']),
                item['time'],
                item['text'],
            )
'''


