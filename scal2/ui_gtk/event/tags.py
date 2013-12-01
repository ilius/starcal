# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir, myRaise

from scal2 import event_lib
from scal2 import ui
from scal2.ui_gtk.utils import openWindow, dialog_add_button
from scal2.ui_gtk.mywidgets.icon import IconSelectButton

import gtk
from gtk import gdk

#class EventCategorySelect(gtk.HBox):

class EventTagsAndIconSelect(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        #########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Category')+':'), 0, 0)
        #####
        ls = gtk.ListStore(gdk.Pixbuf, str)
        combo = gtk.ComboBox(ls)
        ###
        cell = gtk.CellRendererPixbuf()
        combo.pack_start(cell, False)
        combo.add_attribute(cell, 'pixbuf', 0)
        ###
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 1)
        ###
        ls.append([None, _('Custom')])## first or last FIXME
        for item in ui.eventTags:
            ls.append([
                gdk.pixbuf_new_from_file(item.icon) if item.icon else None,
                item.desc
            ])
        ###
        self.customItemIndex = 0 ## len(ls)-1
        hbox.pack_start(combo, 0, 0)
        self.typeCombo = combo
        self.typeStore = ls

        ###
        vbox = gtk.VBox()
        vbox.pack_start(hbox, 0, 0)
        self.pack_start(vbox, 0, 0)
        #########
        iconLabel = gtk.Label(_('Icon'))
        hbox.pack_start(iconLabel, 0, 0)
        self.iconSelect = IconSelectButton()
        hbox.pack_start(self.iconSelect, 0, 0)
        tagsLabel = gtk.Label(_('Tags'))
        hbox.pack_start(tagsLabel, 0, 0)
        hbox3 = gtk.HBox()
        self.tagButtons = []
        for item in ui.eventTags:
            button = gtk.ToggleButton(item.desc)
            button.tagName = item.name
            self.tagButtons.append(button)
            hbox3.pack_start(button, 0, 0)
        self.swin = gtk.ScrolledWindow()
        self.swin.set_policy(gtk.POLICY_ALWAYS, gtk.POLICY_NEVER)## horizontal AUTOMATIC or ALWAYS FIXME
        self.swin.add_with_viewport(hbox3)
        self.pack_start(self.swin, 1, 1)
        self.customTypeWidgets = (iconLabel, self.iconSelect, tagsLabel, self.swin)
        #########
        self.typeCombo.connect('changed', self.typeComboChanged)
        self.connect('scroll-event', self.scrollEvent)
        #########
        self.show_all()
        hideList(self.customTypeWidgets)
    def scrollEvent(self, widget, event):
        self.swin.get_hscrollbar().emit('scroll-event', event)
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
            icon = ''
            tags = []
        else:
            if active == self.customItemIndex:
                icon = self.iconSelect.get_filename()
                tags = [button.tagName for button in self.tagButtons if button.get_active()]
            else:
                item = ui.eventTags[active]
                icon = item.icon
                tags = [item.name]
        return {
            'icon': icon,
            'tags': tags,
        }


class TagsListBox(gtk.VBox):
    '''
        [x] Only related tags     tt: Show only tags related to this event type
        Sort by:
            Name
            Usage


        Related to this event type (first)
        Most used (first)
        Most used for this event type (first)
    '''
    def __init__(self, eventType=''):## '' == 'custom'
        gtk.VBox.__init__(self)
        ####
        self.eventType = eventType
        ########
        if eventType:
            hbox = gtk.HBox()
            self.relatedCheck = gtk.CheckButton(_('Only related tags'))
            set_tooltip(self.relatedCheck, _('Show only tags related to this event type'))
            self.relatedCheck.set_active(True)
            self.relatedCheck.connect('clicked', self.optionsChanged)
            hbox.pack_start(self.relatedCheck, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
            self.pack_start(hbox, 0, 0)
        ########
        treev = gtk.TreeView()
        trees = gtk.ListStore(str, bool, str, int, str)## name(hidden), enable, desc, usage(hidden), usage(locale)
        treev.set_model(trees)
        ###
        cell = gtk.CellRendererToggle()
        #cell.set_property('activatable', True)
        cell.connect('toggled', self.enableCellToggled)
        col = gtk.TreeViewColumn(_('Enable'), cell)
        col.add_attribute(cell, "active", 1)
        #cell.set_active(False)
        col.set_resizable(True)
        col.set_sort_column_id(1)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Name'), cell, text=2)## really desc, not name
        col.set_resizable(True)
        col.set_sort_column_id(2)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Usage'), cell, text=4)
        #col.set_resizable(True)
        col.set_sort_column_id(3) ## previous column (hidden and int)
        col.set_sort_indicator(True)
        treev.append_column(col)
        ###
        swin = gtk.ScrolledWindow()
        swin.add(treev)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(swin, 1, 1)
        ####
        self.treeview = treev
        self.treestore = trees
        ####
        #ui.updateEventTagsUsage()## FIXME
        #for (i, tagObj) in enumerate(ui.eventTags): tagObj.usage = i*10 ## for testing
        self.optionsChanged()
        self.show_all()
    def optionsChanged(self, widget=None, tags=[]):
        if not tags:
            tags = self.getData()
        tagObjList = ui.eventTags
        if self.eventType:
            if self.relatedCheck.get_active():
                tagObjList = [t for t in tagObjList if self.eventType in t.eventTypes]
        self.treestore.clear()
        for t in tagObjList:
            self.treestore.append((
                t.name,
                t.name in tags, ## True or False
                t.desc,
                t.usage,
                _(t.usage)
            ))
    def enableCellToggled(self, cell, path):
        i = int(path)
        active = not cell.get_active()
        self.treestore[i][1] = active
        cell.set_active(active)
    def getData(self):
        tags = []
        for row in self.treestore:
            if row[1]:
                tags.append(row[0])
        return tags
    def setData(self, tags):
        self.optionsChanged(tags=tags)



class TagEditorDialog(gtk.Dialog):
    def __init__(self, eventType='', parent=None):
        gtk.Dialog.__init__(self, title=_('Tags'))
        self.set_transient_for(None)
        self.tags = []
        self.tagsBox = TagsListBox(eventType)
        self.vbox.pack_start(self.tagsBox, 1, 1)
        ####
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ####
        self.vbox.show_all()
        self.getData = self.tagsBox.getData
        self.setData = self.tagsBox.setData




class ViewEditTagsHbox(gtk.HBox):
    def __init__(self, eventType=''):
        gtk.HBox.__init__(self)
        self.tags = []
        self.pack_start(gtk.Label(_('Tags')+':  '), 0, 0)
        self.tagsLabel = gtk.Label('')
        self.pack_start(self.tagsLabel, 1, 1)
        self.dialog = TagEditorDialog(eventType, parent=self)
        self.dialog.connect('response', self.dialogResponse)
        self.editButton = gtk.Button()
        self.editButton.set_label(_('_Edit'))
        self.editButton.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON))
        self.editButton.connect('clicked', self.editButtonClicked)
        self.pack_start(self.editButton, 0, 0)
        self.show_all()
    def editButtonClicked(self, widget):
        openWindow(self.dialog)
    def dialogResponse(self, dialog, resp):
        #print('dialogResponse', dialog, resp)
        if resp==gtk.RESPONSE_OK:
            self.setData(dialog.getData())
        dialog.hide()
    def setData(self, tags):
        self.tags = tags
        self.dialog.setData(tags)
        sep = _(',') + ' '
        self.tagsLabel.set_label(sep.join([ui.eventTagsDesc[tag] for tag in tags]))
    getData = lambda self: self.tags


