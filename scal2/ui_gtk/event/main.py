# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from time import time as now

import os, sys, shlex, thread
from os.path import join, dirname, split, splitext

from scal2.path import *

from scal2 import core
from scal2.core import myRaise

from scal2 import locale_man
from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2 import event_lib
from scal2 import ui

import gtk
from gtk import gdk


from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import set_tooltip, dialog_add_button, confirm, showError
from scal2.ui_gtk.utils import toolButtonFromStock, labelImageMenuItem, labelStockMenuItem
from scal2.ui_gtk.utils import pixbufFromFile, rectangleContainsPoint

from scal2.ui_gtk.color_utils import gdkColorToRgb
from scal2.ui_gtk.drawing import newOutlineSquarePixbuf
from scal2.ui_gtk import gtk_ud as ud
from scal2.ui_gtk.mywidgets.dialog import MyDialog
from scal2.ui_gtk.event import common
from scal2.ui_gtk.event.common import EventEditorDialog, addNewEvent, GroupEditorDialog
from scal2.ui_gtk.event.trash import TrashEditorDialog
from scal2.ui_gtk.event.export import SingleGroupExportDialog, MultiGroupExportDialog
from scal2.ui_gtk.event.import_event import EventsImportWindow
from scal2.ui_gtk.event.group_op import GroupSortDialog, GroupConvertModeDialog, GroupBulkEditDialog
from scal2.ui_gtk.event.account_op import FetchRemoteGroupsDialog
from scal2.ui_gtk.event.search_events import EventSearchWindow

#print 'Testing translator', __file__, _('About')


@registerSignals
class EventManagerDialog(gtk.Dialog, MyDialog, ud.IntegratedCalObj):## FIXME
    _name = 'eventMan'
    desc = _('Event Manager')
    def checkEventToAdd(self, group, event):
        if not group.checkEventToAdd(event):
            showError(_('Group type "%s" can not contain event type "%s"')%(group.desc, event.desc), self)
            raise RuntimeError('Invalid event type for this group')
    def onResponse(self, dialog, response_id):
        self.hide()
        self.emit('config-change')
        #thread.start_new_thread(event_lib.restartDaemon, ())
    def showNewGroupAtIndex(self, group, groupIndex):
        groupIter = self.trees.insert(
            None,
            groupIndex,
            self.getGroupRow(group),
        )
        for event in group:
            self.trees.append(
                groupIter,
                self.getEventRow(event),
            )
    showNewGroup = lambda self, group: self.showNewGroupAtIndex(
        group,
        ui.eventGroups.index(group.id),
    )
    def onConfigChange(self, *a, **kw):
        ud.IntegratedCalObj.onConfigChange(self, *a, **kw)
        ###
        if not self.isLoaded:
            if self.get_property('visible'):
                self.waitingDo(self.reloadEvents)## FIXME
            return
        ###
        for gid in ui.changedGroups:
            groupIndex = ui.eventGroups.index(gid)
            group = ui.eventGroups[gid]
            try:
                groupIter = self.trees.get_iter((groupIndex,))
            except:
                print 'changed group: invalid tree path: (%s,)'%groupIndex
            else:
                for i, value in enumerate(self.getGroupRow(group)):
                    self.trees.set_value(groupIter, i, value)
        ui.changedGroups = []
        ###
        for gid in ui.reloadGroups:
            self.reloadGroupEvents(gid)
        ui.reloadGroups = []
        ###
        if ui.reloadTrash:
            if self.trashIter:
                self.trees.remove(self.trashIter)
            self.appendTrash()
        ui.reloadTrash = False
    def onShow(self, widget):
        self.onConfigChange()
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.initVars()
        ud.windowList.appendItem(self)
        ####
        self.isLoaded = False
        self.set_title(_('Event Manager'))
        self.resize(600, 300)
        self.connect('delete-event', self.onDeleteEvent)
        self.set_transient_for(None)
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
        ##
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        #self.connect('response', lambda w, e: self.hide())
        self.connect('response', self.onResponse)
        self.connect('show', self.onShow)
        #######
        self.searchWin = EventSearchWindow()
        #######
        menubar = gtk.MenuBar()
        ####
        fileItem = gtk.MenuItem(_('_File'))
        fileMenu = gtk.Menu()
        fileItem.set_submenu(fileMenu)
        menubar.append(fileItem)
        ##
        addGroupItem = gtk.MenuItem(_('Add New Group'))
        addGroupItem.connect('activate', self.addGroupBeforeSelection)
        ## or before selected group? FIXME
        fileMenu.append(addGroupItem)
        ##
        searchItem = gtk.MenuItem(_('_Search Events'))## FIXME right place?
        searchItem.connect('activate', self.mbarSearchClicked)
        fileMenu.append(searchItem)
        ##
        exportItem = gtk.MenuItem(_('_Export'))
        exportItem.connect('activate', self.mbarExportClicked)
        fileMenu.append(exportItem)
        ##
        importItem = gtk.MenuItem(_('_Import'))
        importItem.connect('activate', self.mbarImportClicked)
        fileMenu.append(importItem)
        ##
        orphanItem = gtk.MenuItem(_('Check for Orphan Events'))
        orphanItem.connect('activate', self.mbarOrphanClicked)
        fileMenu.append(orphanItem)
        ####
        editItem = gtk.MenuItem(_('_Edit'))
        editMenu = gtk.Menu()
        editItem.set_submenu(editMenu)
        menubar.append(editItem)
        ##
        editEditItem = gtk.MenuItem(_('Edit'))
        editEditItem.connect('activate', self.mbarEditClicked)
        editMenu.append(editEditItem)
        editMenu.connect('show', self.mbarEditMenuPopup)
        self.mbarEditItem = editEditItem
        ##
        editMenu.append(gtk.SeparatorMenuItem())
        ##
        cutItem = gtk.MenuItem(_('Cu_t'))
        cutItem.connect('activate', self.mbarCutClicked)
        editMenu.append(cutItem)
        self.mbarCutItem = cutItem
        ##
        copyItem = gtk.MenuItem(_('_Copy'))
        copyItem.connect('activate', self.mbarCopyClicked)
        editMenu.append(copyItem)
        self.mbarCopyItem = copyItem
        ##
        pasteItem = gtk.MenuItem(_('_Paste'))
        pasteItem.connect('activate', self.mbarPasteClicked)
        editMenu.append(pasteItem)
        self.mbarPasteItem = pasteItem
        ##
        editMenu.append(gtk.SeparatorMenuItem())
        ##
        dupItem = gtk.MenuItem(_('_Duplicate'))
        dupItem.connect('activate', self.duplicateSelectedObj)
        editMenu.append(dupItem)
        self.mbarDupItem = dupItem
        ####
        viewItem = gtk.MenuItem(_('_View'))
        viewMenu = gtk.Menu()
        viewItem.set_submenu(viewMenu)
        menubar.append(viewItem)
        ##
        collapseItem = gtk.MenuItem(_('Collapse All'))
        collapseItem.connect('activate', self.collapseAllClicked)
        viewMenu.append(collapseItem)
        ##
        expandItem = gtk.MenuItem(_('Expand All'))
        expandItem.connect('activate', self.expandAllClicked)
        viewMenu.append(expandItem)
        ##
        viewMenu.append(gtk.SeparatorMenuItem())
        ##
        self.showDescItem = gtk.CheckMenuItem(_('Show _Description'))
        self.showDescItem.set_active(ui.eventManShowDescription)
        self.showDescItem.connect('toggled', self.showDescItemToggled)
        viewMenu.append(self.showDescItem)
        ####
        #testItem = gtk.MenuItem(_('Test'))
        #testMenu = gtk.Menu()
        #testItem.set_submenu(testMenu)
        #menubar.append(testItem)
        ###
        #item = gtk.MenuItem('')
        #item.connect('activate', )
        #testMenu.append(item)
        ####
        menubar.show_all()
        self.vbox.pack_start(menubar, 0, 0)
        #######
        treeBox = gtk.HBox()
        #####
        self.treev = gtk.TreeView()
        self.treev.set_search_column(2)
        #self.treev.set_headers_visible(False)## FIXME
        #self.treev.get_selection().set_mode(gtk.SELECTION_MULTIPLE)## FIXME
        #self.treev.set_rubber_banding(gtk.SELECTION_MULTIPLE)## FIXME
        #self.treev.connect('realize', self.onTreeviewRealize)
        self.treev.connect('cursor-changed', self.treeviewCursorChanged)## FIXME
        self.treev.connect('button-press-event', self.treeviewButtonPress)
        self.treev.connect('row-activated', self.rowActivated)
        self.treev.connect('key-press-event', self.keyPress)
        #####
        swin = gtk.ScrolledWindow()
        swin.add(self.treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        treeBox.pack_start(swin, 1, 1)
        ###
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.ORIENTATION_VERTICAL)
        size = gtk.ICON_SIZE_SMALL_TOOLBAR
        ###
        tb = toolButtonFromStock(gtk.STOCK_GO_UP, size)
        set_tooltip(tb, _('Move up'))
        tb.connect('clicked', self.moveUpByButton)
        toolbar.insert(tb, -1)
        ###
        tb = toolButtonFromStock(gtk.STOCK_GO_DOWN, size)
        set_tooltip(tb, _('Move down'))
        tb.connect('clicked', self.moveDownByButton)
        toolbar.insert(tb, -1)
        ###
        tb = toolButtonFromStock(gtk.STOCK_COPY, size)
        set_tooltip(tb, _('Duplicate'))
        tb.connect('clicked', self.duplicateSelectedObj)
        toolbar.insert(tb, -1)
        ###
        treeBox.pack_start(toolbar, 0, 0)
        #####
        self.vbox.pack_start(treeBox)
        #######
        self.trees = gtk.TreeStore(int, gdk.Pixbuf, str, str)
        ## event: eid,  event_icon,   event_summary, event_description
        ## group: gid,  group_pixbuf, group_title,   ?description
        ## trash: -1,        trash_icon,   _('Trash'),    ''
        self.treev.set_model(self.trees)
        ###
        col = gtk.TreeViewColumn()
        cell = gtk.CellRendererPixbuf()
        col.pack_start(cell)
        col.add_attribute(cell, 'pixbuf', 1)
        self.treev.append_column(col)
        ###
        col = gtk.TreeViewColumn(
            _('Summary'),
            gtk.CellRendererText(),
            text=2,
        )
        col.set_resizable(True)
        self.treev.append_column(col)
        ###
        self.colDesc = gtk.TreeViewColumn(
            _('Description'),
            gtk.CellRendererText(),
            text=3,
        )
        if ui.eventManShowDescription:
            self.treev.append_column(self.colDesc)
        ###
        #self.treev.set_search_column(2)## or 3
        ###
        #self.clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        #self.clipboard = gtk.clipboard_get()
        self.toPasteEvent = None ## (path, bool move)
        #####
        self.sbar = gtk.Statusbar()
        self.sbar.set_direction(gtk.TEXT_DIR_LTR)
        #self.sbar.set_has_resize_grip(False)
        self.vbox.pack_start(self.sbar, 0, 0)
        #####
        self.syncing = None ## or a tuple of (groupId, statusText)
        self.trashIter = None
        #####
        self.vbox.show_all()
    def canPasteToGroup(self, group):
        if self.toPasteEvent is None:
            return False
        if not group.acceptsEventTypes:
            return False
        ## check event type here? FIXME
        return True
    def genRightClickMenu(self, path):
        ## how about multi-selection? FIXME
        ## and Select _All menu item
        obj_list = self.getObjsByPath(path)
        #print len(obj_list)
        menu = gtk.Menu()
        if len(obj_list)==1:
            group = obj_list[0]
            if group.name == 'trash':
                #print 'right click on trash', group.title
                menu.add(labelStockMenuItem(
                    'Edit',
                    gtk.STOCK_EDIT,
                    self.editTrash,
                ))
                menu.add(labelStockMenuItem(
                    'Empty Trash',
                    gtk.STOCK_CLEAR,
                    self.emptyTrash,
                ))
                #menu.add(gtk.SeparatorMenuItem())
                #menu.add(labelStockMenuItem(
                #    'Add New Group',
                #    gtk.STOCK_NEW,
                #    self.addGroupBeforeSelection,
                #))## FIXME
            else:
                #print 'right click on group', group.title
                menu.add(labelStockMenuItem(
                    'Edit',
                    gtk.STOCK_EDIT,
                    self.editGroupFromMenu,
                    path,
                ))
                eventTypes = group.acceptsEventTypes
                if eventTypes is None:
                    eventTypes = event_lib.classes.event.names
                if len(eventTypes) > 3:
                    menu.add(labelStockMenuItem(
                        _('Add Event'),
                        gtk.STOCK_ADD,
                        self.addGenericEventToGroupFromMenu,
                        path,
                        group,
                    ))
                else:
                    for eventType in eventTypes:
                        #if eventType == 'custom':## FIXME
                        #    desc = _('Add ') + _('Event')
                        #else:
                        label = _('Add ') + event_lib.classes.event.byName[eventType].desc
                        menu.add(labelStockMenuItem(
                            label,
                            gtk.STOCK_ADD,
                            self.addEventToGroupFromMenu,
                            path,
                            group,
                            eventType,
                            label,
                        ))
                pasteItem = labelStockMenuItem(
                    'Paste Event',
                    gtk.STOCK_PASTE,
                    self.pasteEventFromMenu,
                    path,
                )
                menu.add(pasteItem)
                pasteItem.set_sensitive(self.canPasteToGroup(group))
                ##
                menu.add(gtk.SeparatorMenuItem())
                #menu.add(labelStockMenuItem(
                #    'Add New Group',
                #    gtk.STOCK_NEW,
                #    self.addGroupBeforeGroup,
                #    path,
                #))## FIXME
                menu.add(labelStockMenuItem(
                    'Duplicate',
                    gtk.STOCK_COPY,
                    self.duplicateGroupFromMenu,
                    path,
                ))
                ###
                dupAllItem = labelStockMenuItem(
                    'Duplicate with All Events',
                    gtk.STOCK_COPY,
                    self.duplicateGroupWithEventsFromMenu,
                    path,
                )
                menu.add(dupAllItem)
                dupAllItem.set_sensitive(bool(group.idList))
                ###
                menu.add(gtk.SeparatorMenuItem())
                menu.add(labelStockMenuItem(
                    'Delete Group',
                    gtk.STOCK_DELETE,
                    self.deleteGroupFromMenu,
                    path,
                ))
                menu.add(gtk.SeparatorMenuItem())
                ##
                #menu.add(labelStockMenuItem(
                #    'Move Up',
                #    gtk.STOCK_GO_UP,
                #    self.moveUpFromMenu,
                #    path,
                #))
                #menu.add(labelStockMenuItem(
                #    'Move Down',
                #    gtk.STOCK_GO_DOWN,
                #    self.moveDownFromMenu,
                #    path,
                #))
                ##
                menu.add(labelStockMenuItem(
                    _('Export'),
                    gtk.STOCK_CONVERT,
                    self.groupExportFromMenu,
                    group,
                ))
                ###
                sortItem = labelStockMenuItem(
                    _('Sort Events'),
                    gtk.STOCK_SORT_ASCENDING,
                    self.groupSortFromMenu,
                    path,
                )
                menu.add(sortItem)
                sortItem.set_sensitive(bool(group.idList))
                ###
                convertItem = labelStockMenuItem(
                    _('Convert Calendar Type'),
                    gtk.STOCK_CONVERT,
                    self.groupConvertModeFromMenu,
                    group,
                )
                menu.add(convertItem)
                convertItem.set_sensitive(bool(group.idList))
                ###
                #if group.remoteIds:
                #    account = ui.eventAccounts[group.remoteIds[0]]
                #    menu.add(labelImageMenuItem(
                #    _('Synchronize with %s') % account.title,
                #    gtk.STOCK_REFRESH,
                #    self.syncGroup,
                #    path,
                #))
                ###
                for newGroupType in group.canConvertTo:
                    menu.add(labelStockMenuItem(
                        _('Convert to %s')%event_lib.classes.group.byName[newGroupType].desc,
                        None,
                        self.groupConvertTo,
                        group,
                        newGroupType,
                    ))
                ###
                bulkItem = labelStockMenuItem(
                    _('Bulk Edit Events'),
                    gtk.STOCK_EDIT,
                    self.groupBulkEditFromMenu,
                    group,
                    path,
                )
                menu.add(bulkItem)
                bulkItem.set_sensitive(bool(group.idList))
                ###
                for actionName, actionFuncName in group.actions:
                    menu.add(labelStockMenuItem(
                        _(actionName),
                        None,
                        self.groupActionClicked,
                        group,
                        actionFuncName,
                    ))
        elif len(obj_list) == 2:
            group, event = obj_list
            #print 'right click on event', event.summary
            if group.name != 'trash':
                menu.add(labelStockMenuItem(
                    'Edit',
                    gtk.STOCK_EDIT,
                    self.editEventFromMenu,
                    path,
                ))
            ####
            moveToItem = labelStockMenuItem(
                _('Move to %s')%'...',
                None,## FIXME
            )
            moveToMenu = gtk.Menu()
            for new_group in ui.eventGroups:
                if new_group.id == group.id:
                    continue
                #if not new_group.enable:## FIXME
                #    continue
                new_groupIndex = ui.eventGroups.index(new_group.id) ## FIXME
                if event.name in new_group.acceptsEventTypes:
                    new_groupItem = gtk.ImageMenuItem()
                    new_groupItem.set_label(new_group.title)
                    ##
                    image = gtk.Image()
                    image.set_from_pixbuf(newOutlineSquarePixbuf(new_group.color, 20))
                    new_groupItem.set_image(image)
                    ##
                    new_groupItem.connect(
                        'activate',
                        self.moveEventToPathFromMenu,
                        path,
                        (new_groupIndex,)
                    )
                    ##
                    moveToMenu.add(new_groupItem)
            moveToItem.set_submenu(moveToMenu)
            menu.add(moveToItem)
            ####
            menu.add(gtk.SeparatorMenuItem())
            ####
            menu.add(labelStockMenuItem(
                'Cut',
                gtk.STOCK_CUT,
                self.cutEvent,
                path,
            ))
            menu.add(labelStockMenuItem(
                'Copy',
                gtk.STOCK_COPY,
                self.copyEvent,
                path,
            ))
            ##
            if group.name == 'trash':
                menu.add(gtk.SeparatorMenuItem())
                menu.add(labelStockMenuItem(
                    'Delete',
                    gtk.STOCK_DELETE,
                    self.deleteEventFromTrash,
                    path,
                ))
            else:
                pasteItem = labelStockMenuItem(
                    'Paste',
                    gtk.STOCK_PASTE,
                    self.pasteEventFromMenu,
                    path,
                )
                menu.add(pasteItem)
                pasteItem.set_sensitive(self.canPasteToGroup(group))
                ##
                menu.add(gtk.SeparatorMenuItem())
                menu.add(labelImageMenuItem(
                    _('Move to %s')%ui.eventTrash.title,
                    ui.eventTrash.icon,
                    self.moveEventToTrashFromMenu,
                    path,
                ))
        else:
            return
        menu.show_all()
        return menu
    def openRightClickMenu(self, path, etime=None):
        menu = self.genRightClickMenu(path)
        if not menu:
            return
        if etime is None:
            etime = gtk.get_current_event_time()
        menu.popup(None, None, None, 3, etime)
    #def onTreeviewRealize(self, event):
    #    #self.reloadEvents()## FIXME
    #    pass
    def rowActivated(self, treev, path, col):
        if len(path)==1:
            if treev.row_expanded(path):
                treev.collapse_row(path)
            else:
                treev.expand_row(path, False)
        elif len(path)==2:
            self.editEventByPath(path)
    def keyPress(self, treev, g_event):
        #from scal2.time_utils import getGtkTimeFromEpoch
        #print g_event.time-getGtkTimeFromEpoch(now())## FIXME
        #print now()-gdk.CURRENT_TIME/1000.0
        ## gdk.CURRENT_TIME == 0## FIXME
        ## g_event.time == gtk.get_current_event_time() ## OK
        kname = gdk.keyval_name(g_event.keyval).lower()
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
                wx, wy = self.window.get_origin()
                menu.popup(
                    None,
                    None,
                    lambda m: (wx+dx, wy+dy+20, True),
                    3,
                    g_event.time,
                )
        elif kname=='delete':
            self.moveSelectionToTrash()
        else:
            #print kname
            return False
        return True
    getRowBgColor = lambda self: \
        gdkColorToRgb(self.treev.style.base[gtk.STATE_NORMAL])
        ## bg color of non-selected rows
    getEventRow = lambda self, event: (
        event.id,
        pixbufFromFile(event.icon),
        event.summary,
        event.getShownDescription(),
    )
    def getGroupRow(self, group):
        return common.getGroupRow(group, self.getRowBgColor()) + ('',)
    def appendGroupTree(self, group):
        groupIter = self.trees.insert_before(
            None,
            self.trashIter,
            self.getGroupRow(group),
        )
        for event in group:
            self.trees.append(groupIter, self.getEventRow(event))
    def reloadGroupEvents(self, gid):
        groupIndex = ui.eventGroups.index(gid)
        groupIter = self.trees.get_iter((groupIndex,))
        assert self.trees.get_value(groupIter, 0) == gid
        ##
        self.removeIterChildren(groupIter)
        ##
        group = ui.eventGroups[gid]
        for event in group:
            self.trees.append(groupIter, self.getEventRow(event))
    def appendTrash(self):
        self.trashIter = self.trees.append(None, (
            -1,
            pixbufFromFile(ui.eventTrash.icon),
            ui.eventTrash.title,
            '',
        ))
        for event in ui.eventTrash:
            self.trees.append(self.trashIter, self.getEventRow(event))
    def reloadEvents(self):
        self.trees.clear()
        for group in ui.eventGroups:
            self.appendGroupTree(group)
        self.appendTrash()
        self.treeviewCursorChanged()
        ####
        ui.changedGroups = []
        ui.reloadGroups = []
        ui.reloadTrash = False
        ####
        self.isLoaded = True
    def onDeleteEvent(self, obj, event):
        self.hide()
        return True
    def getObjsByPath(self, path):
        obj_list = []
        for i in range(len(path)):
            it = self.trees.get_iter(path[:i+1])
            obj_id = self.trees.get_value(it, 0)
            if i==0:
                if obj_id==-1:
                    obj_list.append(ui.eventTrash)
                else:
                    obj_list.append(ui.eventGroups[obj_id])
            else:
                obj_list.append(obj_list[i-1][obj_id])
        return obj_list
    def mbarExportClicked(self, obj):
        MultiGroupExportDialog().run()
    def mbarImportClicked(self, obj):
        EventsImportWindow(self).present()
    def mbarSearchClicked(self, obj):
        self.searchWin.present()
    def _do_checkForOrphans(self):
        newGroup = ui.eventGroups.checkForOrphans()
        if newGroup is not None:
            self.showNewGroup(newGroup)
    def mbarOrphanClicked(self, obj):
        self.waitingDo(self._do_checkForOrphans)
    def mbarEditMenuPopup(self, obj):
        path = self.treev.get_cursor()[0]
        selected = bool(path)
        eventSelected = selected and len(path)==2
        ###
        self.mbarEditItem.set_sensitive(selected)
        self.mbarCutItem.set_sensitive(eventSelected)
        self.mbarCopyItem.set_sensitive(eventSelected)
        self.mbarDupItem.set_sensitive(selected)
        ###
        self.mbarPasteItem.set_sensitive(
            selected and self.canPasteToGroup(self.getObjsByPath(path)[0])
        )
    def mbarEditClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==1:
            self.editGroupByPath(path)
        elif len(path)==2:
            self.editEventByPath(path)
    def mbarCutClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==2:
            self.toPasteEvent = (path, True)
    def mbarCopyClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==2:
            self.toPasteEvent = (path, False)
    def mbarPasteClicked(self, obj):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.pasteEventToPath(path)
    collapseAllClicked = lambda self, obj: self.treev.collapse_all()
    expandAllClicked = lambda self, obj: self.treev.expand_all()
    def _do_showDescItemToggled(self):
        active = self.showDescItem.get_active()
        #self.showDescItem.set_active(active)
        ui.eventManShowDescription = active
        ui.saveLiveConf()## FIXME
        if active:
            self.treev.append_column(self.colDesc)
        else:
            self.treev.remove_column(self.colDesc)
    def showDescItemToggled(self, obj=None):
        self.waitingDo(self._do_showDescItemToggled)
    def treeviewCursorChanged(self, treev=None):
        path = self.treev.get_cursor()[0]
        ## update eventInfoBox
        #print 'treeviewCursorChanged', path
        if not self.syncing:
            text = ''
            if path:
                if len(path)==1:
                    group, = self.getObjsByPath(path)
                    if group.name == 'trash':
                        text = _('contains %s events')%_(len(group))
                    else:
                        text = _('contains %s events and %s occurences')%(
                            _(len(group)),
                            _(group.occurCount),
                        ) + _(',') + ' ' + _('Group ID: %s')%_(group.id)
                    modified = group.modified
                elif len(path)==2:
                    group, event = self.getObjsByPath(path)
                    text = _('Event ID: %s')%_(event.id)
                    modified = event.modified
                text += '%s %s: %s'%(
                    _(','),
                    _('Last Modified'),
                    locale_man.textNumEncode(core.epochDateTimeEncode(modified)),
                )
            message_id = self.sbar.push(0, text)
        return True
    def _do_onGroupModify(self, group, groupIter):
        group.afterModify()
        group.save()## FIXME
        try:
            if group.name == 'universityTerm':## FIXME
                n = self.trees.iter_n_children(groupIter)
                for i in range(n):
                    eventIter = self.trees.iter_nth_child(groupIter, i)
                    eid = self.trees.get(eventIter, 0)[0]
                    self.trees.set(eventIter, 2, group[eid].summary)
        except:
            myRaise()
    def onGroupModify(self, group, groupIter):
        self.waitingDo(self._do_onGroupModify, group, groupIter)
    def treeviewButtonPress(self, treev, g_event):
        pos_t = treev.get_path_at_pos(int(g_event.x), int(g_event.y))
        if not pos_t:
            return
        path, col, xRel, yRel = pos_t
        if not path:
            return
        if g_event.button == 3:
            self.openRightClickMenu(path, g_event.time)
        elif g_event.button == 1:
            if not col:
                return
            if not rectangleContainsPoint(
                treev.get_cell_area(path, col),
                g_event.x,
                g_event.y,
            ):
                return
            obj_list = self.getObjsByPath(path)
            if len(obj_list) == 1:## group, not event
                group = obj_list[0]
                if group.name != 'trash':
                    cell = col.get_cell_renderers()[0]
                    try:
                        cell.get_property('pixbuf')
                    except:
                        pass
                    else:
                        group.enable = not group.enable
                        groupIter = self.trees.get_iter(path)
                        self.trees.set_value(
                            groupIter,
                            1,
                            newOutlineSquarePixbuf(
                                group.color,
                                20,
                                0 if group.enable else 15,
                                self.getRowBgColor(),
                            ),
                        )
                        group.save()
                        self.onGroupModify(group, groupIter)
                        treev.set_cursor(path)
                        return True
    def insertNewGroup(self, groupIndex):
        group = GroupEditorDialog().run()
        if group is None:
            return
        ui.eventGroups.insert(groupIndex, group)
        ui.eventGroups.save()
        beforeGroupIter = self.trees.get_iter((groupIndex,))
        groupIter = self.trees.insert_before(
            #self.trees.get_iter_root(),## parent
            self.trees.iter_parent(beforeGroupIter),
            beforeGroupIter,## sibling
            self.getGroupRow(group),
        )
        self.onGroupModify(group, groupIter)
    def addGroupBeforeGroup(self, menu, path):
        self.insertNewGroup(path[0])
    def addGroupBeforeSelection(self, obj=None):
        path = self.treev.get_cursor()[0]
        if path:
            groupIndex = path[0]
        else:
            groupIndex = len(self.trees)-1
        self.insertNewGroup(groupIndex)
    def duplicateGroup(self, path):
        index, = path
        group, = self.getObjsByPath(path)
        newGroup = group.copy()
        ui.duplicateGroupTitle(newGroup)
        newGroup.save()
        ui.eventGroups.insert(index+1, newGroup)
        ui.eventGroups.save()
        self.trees.insert(
            None,
            index+1,
            self.getGroupRow(newGroup),
        )
    def duplicateGroupWithEvents(self, path):
        index, = path
        group, = self.getObjsByPath(path)
        newGroup = group.deepCopy()
        ui.duplicateGroupTitle(newGroup)
        newGroup.save()
        ui.eventGroups.insert(index+1, newGroup)
        ui.eventGroups.save()
        newGroupIter = self.trees.insert(
            None,
            index+1,
            self.getGroupRow(newGroup),
        )
        for event in newGroup:
            self.trees.append(newGroupIter, self.getEventRow(event))
    duplicateGroupFromMenu = lambda self, menu, path: self.duplicateGroup(path)
    duplicateGroupWithEventsFromMenu = lambda self, menu, path: \
        self.duplicateGroupWithEvents(path)
    def duplicateSelectedObj(self, button=None):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        if len(path)==1:
            self.duplicateGroup(path)
        elif len(path)==2:## FIXME
            self.toPasteEvent = (path, False)
            self.pasteEventToPath(path)
    def editGroupByPath(self, path):
        group, = self.getObjsByPath(path)
        if group.name == 'trash':
            self.editTrash()
        else:
            group = GroupEditorDialog(group).run()
            if group is None:
                return
            groupIter = self.trees.get_iter(path)
            for i, value in enumerate(self.getGroupRow(group)):
                self.trees.set_value(groupIter, i, value)
            self.onGroupModify(group, groupIter)
    editGroupFromMenu = lambda self, menu, path: self.editGroupByPath(path)
    def _do_deleteGroup(self, path, group):
        trashedIds = group.idList
        if core.eventTrashLastTop:
            for eid in reversed(trashedIds):
                self.trees.insert(
                    self.trashIter,
                    0,
                    self.getEventRow(group[eid]),
                )
        else:
            for eid in trashedIds:
                self.trees.append(
                    self.trashIter,
                    self.getEventRow(group[eid]),
                )
        ui.deleteEventGroup(group)
        self.trees.remove(self.trees.get_iter(path))
    def deleteGroup(self, path):
        index, = path
        group, = self.getObjsByPath(path)
        if not confirm(_('Press OK if you want to delete group "%s" and move all its events to trash')%group.title):
            return
        self.waitingDo(self._do_deleteGroup, path, group)
    deleteGroupFromMenu = lambda self, menu, path: self.deleteGroup(path)
    def addEventToGroupFromMenu(self, menu, path, group, eventType, title):
        event = addNewEvent(
            group,
            eventType,
            title,
            parent=self,
        )
        if event is None:
            return
        self.trees.append(
            self.trees.get_iter(path),## parent
            self.getEventRow(event), ## row
        )
        self.treeviewCursorChanged()
    def addGenericEventToGroupFromMenu(self, menu, path, group):
        event = addNewEvent(
            group,
            group.acceptsEventTypes[0],
            _('Add Event'),
            typeChangable=True,
            parent=self,
        )
        if event is None:
            return
        self.trees.append(
            self.trees.get_iter(path),## parent
            self.getEventRow(event), ## row
        )
        self.treeviewCursorChanged()
    def editEventByPath(self, path):
        group, event = self.getObjsByPath(path)
        if group.name == 'trash':## FIXME
            return
        event = EventEditorDialog(
            event,
            title=_('Edit ')+event.desc,
            parent=self,
        ).run()
        if event is None:
            return
        eventIter = self.trees.get_iter(path)
        for i, value in enumerate(self.getEventRow(event)):
            self.trees.set_value(eventIter, i, value)
    editEventFromMenu = lambda self, menu, path: self.editEventByPath(path)
    def moveEventToPathFromMenu(self, menu, path, tarPath):
        self.toPasteEvent = (path, True)
        self.pasteEventToPath(tarPath, False)
    def moveEventToTrash(self, path):
        group, event = self.getObjsByPath(path)
        ui.moveEventToTrash(group, event)
        self.trees.remove(self.trees.get_iter(path))
        if core.eventTrashLastTop:
            self.trees.insert(
                self.trashIter,
                0,
                self.getEventRow(event),
            )
        else:
            self.trees.append(
                self.trashIter,
                self.getEventRow(event),
            )
    moveEventToTrashFromMenu = lambda self, menu, path: self.moveEventToTrash(path)
    def moveSelectionToTrash(self):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        objs = self.getObjsByPath(path)
        if len(path)==1:
            self.deleteGroup(path)
        elif len(path)==2:
            if confirm(_('Press OK if you want to move event "%s" to trash')%objs[1].summary):
                self.moveEventToTrash(path)
    def deleteEventFromTrash(self, menu, path):
        trash, event = self.getObjsByPath(path)
        trash.delete(event.id)## trash == ui.eventTrash
        trash.save()
        self.trees.remove(self.trees.get_iter(path))
    def removeIterChildren(self, _iter):
        while True:
            childIter = self.trees.iter_children(_iter)
            if childIter is None:
                break
            self.trees.remove(childIter)
    def emptyTrash(self, menu):
        ui.eventTrash.empty()
        self.removeIterChildren(self.trashIter)
        self.treeviewCursorChanged()
    def editTrash(self, obj=None):
        TrashEditorDialog().run()
        self.trees.set_value(
            self.trashIter,
            1,
            pixbufFromFile(ui.eventTrash.icon),
        )
        self.trees.set_value(
            self.trashIter,
            2,
            ui.eventTrash.title,
        )
    def moveUp(self, path):
        srcIter = self.trees.get_iter(path)
        if len(path)==1:
            if path[0]==0:
                return
            if self.trees.get_value(srcIter, 0)==-1:
                return
            tarIter = self.trees.get_iter((path[0]-1))
            self.trees.move_before(srcIter, tarIter)
            ui.eventGroups.moveUp(path[0])
            ui.eventGroups.save()
        elif len(path)==2:
            parentObj, event = self.getObjsByPath(path)
            parentLen = len(parentObj)
            parentIndex, eventIndex = path
            #print eventIndex, parentLen
            if eventIndex > 0:
                tarIter = self.trees.get_iter((parentIndex, eventIndex-1))
                self.trees.move_before(srcIter, tarIter)## or use self.trees.swap FIXME
                parentObj.moveUp(eventIndex)
                parentObj.save()
            else:
                ## move event to end of previous group
                #if parentObj.name == 'trash':
                #    return
                if parentIndex < 1:
                    return
                newParentIter = self.trees.get_iter((parentIndex - 1))
                newParentId = self.trees.get_value(newParentIter, 0)
                if newParentId==-1:## could not be!
                    return
                newGroup = ui.eventGroups[newParentId]
                self.checkEventToAdd(newGroup, event)
                self.trees.remove(srcIter)
                srcIter = self.trees.append(
                    newParentIter,## parent
                    self.getEventRow(event), ## row
                )
                ###
                parentObj.remove(event)
                parentObj.save()
                newGroup.append(event)
                newGroup.save()
        else:
            raise RuntimeError('invalid tree path %s'%path)
        newPath = self.trees.get_path(srcIter)
        if len(path)==2:
            self.treev.expand_to_path(newPath)
        self.treev.set_cursor(newPath)
        self.treev.scroll_to_cell(newPath)
    def moveDown(self, path):
        srcIter = self.trees.get_iter(path)
        if len(path)==1:
            if self.trees.get_value(srcIter, 0)==-1:
                return
            tarIter = self.trees.get_iter((path[0]+1))
            if self.trees.get_value(tarIter, 0)==-1:
                return
            self.trees.move_after(srcIter, tarIter)## or use self.trees.swap FIXME
            ui.eventGroups.moveDown(path[0])
            ui.eventGroups.save()
        elif len(path)==2:
            parentObj, event = self.getObjsByPath(path)
            parentLen = len(parentObj)
            parentIndex, eventIndex = path
            #print eventIndex, parentLen
            if eventIndex < parentLen-1:
                tarIter = self.trees.get_iter((parentIndex, eventIndex+1))
                self.trees.move_after(srcIter, tarIter)
                parentObj.moveDown(eventIndex)
                parentObj.save()
            else:
                ## move event to top of next group
                if parentObj.name == 'trash':
                    return
                newParentIter = self.trees.get_iter((parentIndex + 1))
                newParentId = self.trees.get_value(newParentIter, 0)
                if newParentId==-1:
                    return
                newGroup = ui.eventGroups[newParentId]
                self.checkEventToAdd(newGroup, event)
                self.trees.remove(srcIter)
                srcIter = self.trees.insert(
                    newParentIter,## parent
                    0,## position
                    self.getEventRow(event), ## row
                )
                ###
                parentObj.remove(event)
                parentObj.save()
                newGroup.insert(0, event)
                newGroup.save()
        else:
            raise RuntimeError('invalid tree path %s'%path)
        newPath = self.trees.get_path(srcIter)
        if len(path)==2:
            self.treev.expand_to_path(newPath)
        self.treev.set_cursor(newPath)
        self.treev.scroll_to_cell(newPath)
    moveUpFromMenu = lambda self, menu, path: self.moveUp(path)
    moveDownFromMenu = lambda self, menu, path: self.moveDown(path)
    def moveUpByButton(self, button):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.moveUp(path)
    def moveDownByButton(self, button):
        path = self.treev.get_cursor()[0]
        if not path:
            return
        self.moveDown(path)
    def groupExportFromMenu(self, menu, group):
        SingleGroupExportDialog(group).run()
    def groupSortFromMenu(self, menu, path):
        index, = path
        group, = self.getObjsByPath(path)
        if GroupSortDialog(group).run():
            groupIter = self.trees.get_iter(path)
            expanded = self.treev.row_expanded(path)
            self.removeIterChildren(groupIter)
            for event in group:
                self.trees.append(groupIter, self.getEventRow(event))
            if expanded:
                self.treev.expand_row(path, False)
    def groupConvertModeFromMenu(self, menu, group):
        GroupConvertModeDialog(group).run()
    def _do_groupConvertTo(self, group, newGroupType):
        newGroup = ui.eventGroups.convertGroupTo(group, newGroupType)
        ## reload it's events in tree? FIXME
        ## summary and description haven't changed!
    def groupConvertTo(self, menu, group, newGroupType):
        self.waitingDo(self._do_groupConvertTo, group, newGroupType)
    def _do_groupBulkEdit(self, dialog, group, path):
        expanded = self.treev.row_expanded(path)
        dialog.doAction()
        dialog.destroy()
        self.trees.remove(self.trees.get_iter(path))
        self.showNewGroupAtIndex(group, path[0])
        if expanded:
            self.treev.expand_row(path, False)
    def groupBulkEditFromMenu(self, menu, group, path):
        dialog = GroupBulkEditDialog(group)
        if dialog.run()==gtk.RESPONSE_OK:
            self.waitingDo(self._do_groupBulkEdit, dialog, group, path)
    def groupActionClicked(self, menu, group, actionFuncName):
        func = getattr(group, actionFuncName)
        self.waitingDo(func, parentWin=self)
    def cutEvent(self, menu, path):
        self.toPasteEvent = (path, True)
    def copyEvent(self, menu, path):
        self.toPasteEvent = (path, False)
    pasteEventFromMenu = lambda self, menu, tarPath: self.pasteEventToPath(tarPath)
    def pasteEventToPath(self, tarPath, doScroll=True):
        if not self.toPasteEvent:
            return
        srcPath, move = self.toPasteEvent
        srcGroup, srcEvent = self.getObjsByPath(srcPath)
        tarGroup = self.getObjsByPath(tarPath)[0]
        self.checkEventToAdd(tarGroup, srcEvent)
        if len(tarPath)==1:
            tarGroupIter = self.trees.get_iter(tarPath)
            tarEventIter = None
            tarEventIndex = len(tarGroup)
        elif len(tarPath)==2:
            tarGroupIter = self.trees.get_iter(tarPath[:1])
            tarEventIter = self.trees.get_iter(tarPath)
            tarEventIndex = tarPath[1]
        ####
        if move:
            srcGroup.remove(srcEvent)
            srcGroup.save()
            tarGroup.insert(tarEventIndex, srcEvent)
            tarGroup.save()
            self.trees.remove(self.trees.get_iter(srcPath))
            newEvent = srcEvent
        else:
            newEvent = srcEvent.copy()
            newEvent.save()
            tarGroup.insert(tarEventIndex, newEvent)
            tarGroup.save()
        ####
        if tarEventIter:
            newEventIter = self.trees.insert_after(
                tarGroupIter,## parent
                tarEventIter,## sibling
                self.getEventRow(newEvent), ## row
            )
        else:
            newEventIter = self.trees.append(
                tarGroupIter,## parent
                self.getEventRow(newEvent), ## row
            )
        if doScroll:
            self.treev.set_cursor(self.trees.get_path(newEventIter))
        self.toPasteEvent = None
    #def selectAllEventInGroup(self, menu):## FIXME
    #    pass
    #def selectAllEventInTrash(self, menu):## FIXME
    #    pass





def makeWidget(obj):## obj is an instance of Event, EventRule, EventNotifier or EventGroup
    if hasattr(obj, 'WidgetClass'):
        widget = obj.WidgetClass(obj)
        try:
            widget.show_all()
        except AttributeError:
            widget.show()
        widget.updateWidget()## FIXME
        return widget
    else:
        return None


##############################################################################

modPrefix = 'scal2.ui_gtk.event.'

for cls in event_lib.classes.event:
    try:
        module = __import__(modPrefix + cls.name, fromlist=['EventWidget'])
        cls.WidgetClass = module.EventWidget
    except:
        myRaise()

for cls in event_lib.classes.rule:
    try:
        module = __import__(modPrefix + 'rules.' + cls.name, fromlist=['RuleWidget'])
    except:
        #if not cls.name.startswith('ex_'):
        myRaise()
        continue
    try:
        cls.WidgetClass = module.RuleWidget
    except AttributeError:
        print 'no class RuleWidget defined in module "%s"'%cls.name

for cls in event_lib.classes.notifier:
    try:
        module = __import__(modPrefix + 'notifiers.' + cls.name, fromlist=['NotifierWidget', 'notify'])
        cls.WidgetClass = module.NotifierWidget
        cls.notify = module.notify
    except:
        myRaise()

for cls in event_lib.classes.group:
    try:
        module = __import__(modPrefix + 'groups.' + cls.name, fromlist=['GroupWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.GroupWidget
    except AttributeError:
        print 'no class GroupWidget defined in module "%s"'%cls.name

    for actionDesc, actionName in cls.actions:
        try:
            func = getattr(module, actionName)
        except AttributeError:
            print 'no function %s defined in module "%s"'%(actionName, cls.name)
        else:
            setattr(cls, actionName, func)


for cls in event_lib.classes.account:
    try:
        module = __import__(modPrefix + 'accounts.' + cls.name, fromlist=['AccountWidget'])
    except:
        myRaise()
        continue
    try:
        cls.WidgetClass = module.AccountWidget
    except AttributeError:
        print 'no class AccountWidget defined in module "%s"'%cls.name


event_lib.EventRule.makeWidget = makeWidget
event_lib.EventNotifier.makeWidget = makeWidget
event_lib.Event.makeWidget = makeWidget
event_lib.EventGroup.makeWidget = makeWidget
event_lib.Account.makeWidget = makeWidget


### Load accounts, groups and trash? FIXME



import scal2.ui_gtk.event.import_customday ## opens a dialog if neccessery


##############################################################################



