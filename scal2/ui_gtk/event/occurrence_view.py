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

from scal2.utils import toStr, toUnicode
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib
from scal2 import ui

from scal2.ui_gtk import *
from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import imageFromFile, labelStockMenuItem, labelImageMenuItem, setClipboard
from scal2.ui_gtk.drawing import newOutlineSquarePixbuf
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.event.common import EventEditorDialog, confirmEventTrash, menuItemFromEventGroup

@registerSignals
class DayOccurrenceView(gtk.ScrolledWindow, ud.IntegratedCalObj):
    _name = 'eventDayView'
    desc = _('Events of Day')
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.connect('size-request', self.onSizeRequest)
        self.vbox = gtk.VBox(spacing=5)
        self.add_with_viewport(self.vbox)
        self.initVars()
        self.maxHeight = 200
        self.showDesc = True
    def onSizeRequest(self, widget, requisition):
        #print('onSizeRequest', requisition.width, requisition.height)
        requisition.height = min(
            self.maxHeight,## FIXME
            self.vbox.size_request()[1] + 2,## >=2 FIXME
        )
        return True
    def onDateChange(self, *a, **kw):
        ud.IntegratedCalObj.onDateChange(self, *a, **kw)
        cell = ui.cell
        ## destroy all VBox contents and add again
        for hbox in self.vbox.get_children():
            hbox.destroy()
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
                label = gtk.Label(occurData['time'])
                label.set_direction(gtk.TEXT_DIR_LTR)
                label.set_selectable(True)
                label.connect('populate-popup', self.onLabelPopup)## FIXME
                pack(hbox, label)
                pack(hbox, gtk.Label('  '))
            label = gtk.Label(text)
            label.set_selectable(True)
            label.set_line_wrap(True)
            label.set_use_markup(False)## should escape text if using markup FIXME
            label.connect('populate-popup', self.onEventLabelPopup, occurData)
            pack(hbox, label)## or 1, 1 (center) FIXME
            pack(self.vbox, hbox)
            pack(self.vbox, gtk.HSeparator())
        self.show_all()
        self.vbox.show_all()
        self.set_visible(bool(cell.eventsData))
    def labelMenuAddCopyItems(self, label, menu):
        menu.add(labelStockMenuItem(
            'Copy _All',
            gtk.STOCK_COPY,
            self.copyAll,
            label
        ))
        ####
        itemCopy = labelStockMenuItem(
            '_Copy',
            gtk.STOCK_COPY,
            self.copy,
            label,
        )
        if label.get_property('cursor-position') == label.get_property('selection-bound'):
            itemCopy.set_sensitive(False)
        menu.add(itemCopy)
    def onLabelPopup(self, label, menu):
        menu = gtk.Menu()
        self.labelMenuAddCopyItems(label, menu)
        ####
        menu.show_all()
        menu.popup(None, None, None, 3, 0)
        ui.updateFocusTime()
    def moveEventToGroupFromMenu(self, item, event, prev_group, newGroup):
        prev_group.remove(event)
        prev_group.save()
        ui.reloadGroups.append(prev_group.id)
        ###
        newGroup.append(event)
        newGroup.save()
        ui.reloadGroups.append(newGroup.id)
        ###
        self.onConfigChange()
    def onEventLabelPopup(self, label, menu, occurData):
        menu = gtk.Menu()
        self.labelMenuAddCopyItems(label, menu)
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
        menu.popup(None, None, None, 3, 0)
        ui.updateFocusTime()
    def editEventClicked(self, item, winTitle, event, groupId):
        event = EventEditorDialog(
            event,
            title=winTitle,
            #parent=self,## FIXME
        ).run()
        if event is None:
            return
        ui.reloadGroups.append(groupId)
        self.onConfigChange()
    def moveEventToTrash(self, item, event, groupId):
        #if not confirm(_('Press OK if you are sure to move event "%s" to trash')%event.summary):
        #    return
        if not confirmEventTrash(event):
            return
        ui.moveEventToTrashFromOutside(ui.eventGroups[groupId], event)
        self.onConfigChange()
    def copy(self, item, label):
        bound = label.get_property('selection-bound')
        cursor = label.get_property('cursor-position')
        start = min(bound, cursor)
        end = max(bound, cursor)
        setClipboard(toStr(toUnicode(label.get_text())[start:end]))
    copyAll = lambda self, item, label: setClipboard(label.get_label())

class WeekOccurrenceView(gtk.TreeView):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self, abrivateWeekDays=False):
        self.abrivateWeekDays = abrivateWeekDays
        self.absWeekNumber = core.getAbsWeekNumberFromJd(ui.cell.jd)## FIXME
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
class MonthOccurrenceView(event_lib.MonthOccurrenceView, gtk.TreeView):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self):
        event_lib.MonthOccurrenceView.__init__(self, ui.cell.jd)
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
            if not item['show'][2]:
                continue
            self.ls.append(
                pixbufFromFile(item['icon']),
                _(item['day']),
                item['time'],
                item['text'],
            )
'''




