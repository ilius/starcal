# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

import os, sys
from os.path import join, dirname, split, splitext

from scal2.path import *

from scal2 import core
from scal2.core import myRaise, jd_to

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2 import event_lib
from scal2 import ui

import gtk
from gtk import gdk

from scal2.ui_gtk.decorators import *
from scal2.ui_gtk.utils import pixbufFromFile
from scal2.ui_gtk.mywidgets import TextFrame
from scal2.ui_gtk.mywidgets.multi_spin_button import DateTimeButton
from scal2.ui_gtk.mywidgets.dialog import MyDialog
from scal2.ui_gtk import gtk_ud as ud

from scal2.ui_gtk.event.common import SingleGroupComboBox, EventEditorDialog


@registerSignals
class EventSearchWindow(gtk.Window, MyDialog, ud.IntegratedCalObj):
    def __init__(self):
        gtk.Window.__init__(self)
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
        self.vbox.pack_start(frame, 0, 0)
        self.textInput = frame
        ##
        hbox = gtk.HBox()
        self.textCSensCheck = gtk.CheckButton(_('Case Sensitive'))
        self.textCSensCheck.set_active(False) ## FIXME
        hbox.pack_start(self.textCSensCheck, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ######
        jd = core.getCurrentJd()
        year, month, day = jd_to(jd, core.primaryMode)
        ######
        hbox = gtk.HBox()
        frame = gtk.Frame(_('Time'))
        frame.set_border_width(5)
        vboxIn = gtk.VBox()
        sgroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ####
        hboxIn = gtk.HBox()
        ##
        self.timeFromCheck = gtk.CheckButton(_('From'))
        sgroup.add_widget(self.timeFromCheck)
        hboxIn.pack_start(self.timeFromCheck, 0, 0)
        hboxIn.pack_start(gtk.Label('  '), 0, 0)
        ##
        self.timeFromInput = DateTimeButton()
        self.timeFromInput.set_value(((year, 1, 1), (0, 0, 0)))
        hboxIn.pack_start(self.timeFromInput, 0, 0)
        ##
        vboxIn.pack_start(hboxIn, 0, 0)
        ####
        hboxIn = gtk.HBox()
        ##
        self.timeToCheck = gtk.CheckButton(_('To'))
        sgroup.add_widget(self.timeToCheck)
        hboxIn.pack_start(self.timeToCheck, 0, 0)
        hboxIn.pack_start(gtk.Label('  '), 0, 0)
        ##
        self.timeToInput = DateTimeButton()
        self.timeToInput.set_value(((year+1, 1, 1), (0, 0, 0)))
        hboxIn.pack_start(self.timeToInput, 0, 0)
        ##
        vboxIn.pack_start(hboxIn, 0, 0)
        ##
        self.timeFromCheck.connect('clicked', self.updateTimeFromSensitive)
        self.timeToCheck.connect('clicked', self.updateTimeToSensitive)
        self.updateTimeFromSensitive()
        self.updateTimeToSensitive()
        ####
        vboxIn.set_border_width(5)
        frame.add(vboxIn)
        hbox.pack_start(frame, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        hbox.set_border_width(5)
        self.modifiedFromCheck = gtk.CheckButton(_('Modified From'))
        hbox.pack_start(self.modifiedFromCheck, 0, 0)
        hbox.pack_start(gtk.Label('  '), 0, 0)
        self.modifiedFromInput = DateTimeButton()
        self.modifiedFromInput.set_value(((year, 1, 1), (0, 0, 0)))
        hbox.pack_start(self.modifiedFromInput, 0, 0)
        ##
        self.modifiedFromCheck.connect('clicked', self.updateModifiedFromSensitive)
        self.updateModifiedFromSensitive()
        self.vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        hbox.set_border_width(5)
        self.typeCheck = gtk.CheckButton(_('Event Type'))
        hbox.pack_start(self.typeCheck, 0, 0)
        hbox.pack_start(gtk.Label('  '), 0, 0)
        ##
        combo = gtk.combo_box_new_text()
        for cls in event_lib.classes.event:
            combo.append_text(cls.desc)
        combo.set_active(0)
        hbox.pack_start(combo, 0, 0)
        self.typeCombo = combo
        ##
        self.typeCheck.connect('clicked', self.updateTypeSensitive)
        self.updateTypeSensitive()
        self.vbox.pack_start(hbox, 0, 0)
        ######
        hbox = gtk.HBox()
        hbox.set_border_width(5)
        self.groupCheck = gtk.CheckButton(_('Group'))
        hbox.pack_start(self.groupCheck, 0, 0)
        hbox.pack_start(gtk.Label('  '), 0, 0)
        self.groupCombo = SingleGroupComboBox()
        hbox.pack_start(self.groupCombo, 0, 0)
        ##
        self.groupCheck.connect('clicked', self.updateGroupSensitive)
        self.updateGroupSensitive()
        self.vbox.pack_start(hbox, 0, 0)
        ######
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_START)
        bbox.set_border_width(5)
        searchButton = gtk.Button()
        searchButton.set_label(_('_Search'))
        searchButton.set_image(gtk.image_new_from_stock(gtk.STOCK_FIND, gtk.ICON_SIZE_BUTTON))
        searchButton.connect('clicked', self.searchClicked)
        bbox.add(searchButton)
        self.vbox.pack_start(bbox, 0, 0)
        ######
        treev = gtk.TreeView()
        trees = gtk.TreeStore(int, int, str, gdk.Pixbuf, str, str)
        ## gid, eid, group_name, icon, summary, description
        treev.set_model(trees)
        treev.connect('row-activated', self.rowActivated)
        treev.set_headers_clickable(True)
        ###
        self.colGroup = gtk.TreeViewColumn(_('Group'), gtk.CellRendererText(), text=2)
        self.colGroup.set_resizable(True)
        self.colGroup.set_sort_column_id(2)
        treev.append_column(self.colGroup)
        ###
        self.colIcon = gtk.TreeViewColumn()
        cell = gtk.CellRendererPixbuf()
        self.colIcon.pack_start(cell)
        self.colIcon.add_attribute(cell, 'pixbuf', 3)
        #self.colIcon.set_sort_column_id(3)## FIXME
        treev.append_column(self.colIcon)
        ###
        self.colSummary = gtk.TreeViewColumn(_('Summary'), gtk.CellRendererText(), text=4)
        self.colSummary.set_resizable(True)
        self.colSummary.set_sort_column_id(4)
        treev.append_column(self.colSummary)
        ###
        self.colDesc = gtk.TreeViewColumn(_('Description'), gtk.CellRendererText(), text=5)
        self.colDesc.set_sort_column_id(5)
        treev.append_column(self.colDesc)
        ###
        trees.set_sort_func(2, self.sort_func_group)
        ######
        swin = gtk.ScrolledWindow()
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        swin.add(treev)
        ####
        vbox = gtk.VBox(spacing=5)
        vbox.set_border_width(5)
        ###
        topHbox = gtk.HBox()
        self.resultLabel = gtk.Label('')
        topHbox.pack_start(self.resultLabel, 0, 0)
        topHbox.pack_start(gtk.Label(''), 1, 1)
        vbox.pack_start(topHbox, 0, 0)
        ####
        columnBox = gtk.HBox(spacing=5)
        columnBox.pack_start(gtk.Label(_('Columns')+':    '), 0, 0)
        ##
        check = gtk.CheckButton(_('Group'))
        check.set_active(True)
        check.connect('clicked', lambda w: self.colGroup.set_visible(w.get_active()))
        columnBox.pack_start(check, 0, 0)
        ##
        check = gtk.CheckButton(_('Icon'))
        check.set_active(True)
        check.connect('clicked', lambda w: self.colIcon.set_visible(w.get_active()))
        columnBox.pack_start(check, 0, 0)
        ##
        check = gtk.CheckButton(_('Summary'))
        check.set_active(True)
        check.connect('clicked', lambda w: self.colSummary.set_visible(w.get_active()))
        columnBox.pack_start(check, 0, 0)
        ##
        check = gtk.CheckButton(_('Description'))
        check.set_active(True)
        check.connect('clicked', lambda w: self.colDesc.set_visible(w.get_active()))
        columnBox.pack_start(check, 0, 0)
        ##
        vbox.pack_start(columnBox, 0, 0)
        ####
        vbox.pack_start(swin, 1, 1)
        ##
        frame = gtk.Frame(_('Search Results'))
        frame.set_border_width(10)
        frame.add(vbox)
        ##
        self.vbox.pack_start(frame, 1, 1)
        ###
        bbox2 = gtk.HButtonBox()
        bbox2.set_layout(gtk.BUTTONBOX_END)
        bbox2.set_border_width(10)
        closeButton = gtk.Button()
        closeButton.set_label(_('_Close'))
        closeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_BUTTON))
        closeButton.connect('clicked', self.closed)
        bbox2.add(closeButton)
        self.vbox.pack_start(bbox2, 0, 0)
        ######
        self.treev = treev
        self.trees = trees
        self.vbox.show_all()
        #self.maximize()## FIXME
    def sort_func_group(self, model, iter1, iter2):
        return cmp(## FIXME
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
            conds['time_from'] = self.timeFromInput.get_epoch(core.primaryMode)
        if self.timeToCheck.get_active():
            conds['time_to'] = self.timeToInput.get_epoch(core.primaryMode)
        if self.modifiedFromCheck.get_active():
            conds['modified_from'] = self.modifiedFromInput.get_epoch(core.primaryMode)
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
    def rowActivated(self, treev, path, col):
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
        ui.reloadGroups.append(gid)
        eventIter = self.trees.get_iter(path)
        self.trees.set_value(eventIter, 3, pixbufFromFile(event.icon))
        self.trees.set_value(eventIter, 4, event.summary)
        self.trees.set_value(eventIter, 5, event.getShownDescription())
    def clearResults(self):
        self.trees.clear()
        self.resultLabel.set_label('')
    def closed(self, obj=None, event=None):
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



