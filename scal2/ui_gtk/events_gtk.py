# -*- coding: utf-8 -*-
# 
# Copyright (C) 2007    Mola Pahnadayan
# Copyright (C) 2009    Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
# Or on Debian systems, from /usr/share/common-licenses/GPL

import os, sys, shlex
from os.path import join

from scal2 import core
from scal2.core import pixDir, convert, numLocale

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2 import event_man
#from scal2.event import dateEncode, timeEncode, dateDecode, timeDecode

from scal2 import ui

#from scal2.ui_gtk.mywidgets.multi_spin_box import DateBox, TimeBox


from xml.dom.minidom import getDOMImplementation, parse
from xml.parsers.expat import ExpatError

import gtk
from gtk import gdk




def combo_model_delete_text(model, path, itr, text_to_del):
    ## Usage: combo.get_model().foreach(combo_model_delete_text, 'The Text')
    if model[path[0]][0]==text_to_del:
        del model[path[0]]
        return

def cellToggled(cell, path=None):
    print 'cellToggled', path
    cell.set_active(not cell.get_active())##????????????????????????
    return True

def comboToggleActivate(combo, *args):
    print combo.get_property('popup-shown')
    if not combo.get_property('popup-shown'):
        combo.popup()
        return True
    return False



class EventEditorDialog(gtk.Dialog):
    def __init__(self, event=None):
        gtk.Dialog.__init__(self)
        cancelB = self.add_button(gtk.STOCK_CANCEL, 1)
        okB = self.add_button(gtk.STOCK_OK, 0)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        okB.connect('clicked', self.okClicked)
        #######
        self.event = event
        #######
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Date Mode')), 0, 0)
        combo = gtk.combo_box_new_text()
        for mod in core.modules:
            combo.append_text(mod.desc)
        #combo.set_active(core.primaryMode)
        combo.set_active(ui.shownCals[0]['mode'])
        combo.connect('changed', self.dateModeChanged)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        self.comboDateMode = combo
        ####
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Event Type')), 0, 0)
        combo = gtk.combo_box_new_text()
        for cls in core.modules:
            combo.append_text(mod.desc)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        self.comboDateMode = combo
        #####
        hbox = gtk.HBox()
        combo = gtk.combo_box_new_text()
        for cls in geventsClassList:
            combo.append_text(cls.desc)
        self.vbox.pack_start(hbox, 0, 0)
        self.comboEventType = combo
        #####
        self.activeEventWidget = None
        #####
        self.comboDateMode.set_active(ui.shownCals[0]['mode'])## or core.primaryMode
        self.comboDateMode.connect('changed', self.dateModeChanged)
        self.comboEventType.connect('changed', self.eventTypeChanged)
        if self.event:
            self.comboEventType.set_active(geventsClassList.find(self.event.__class__))
        else:
            self.comboEventType.set_active(event.defaultEventTypeIndex)
    def dateModeChanged(self, combo):
        pass
    def eventTypeChanged(self, combo):
        if self.activeEventWidget:
            self.activeEventWidget.destroy()
        cls = geventsClassList[combo.get_active()]
        if self.event:
            self.activeEventWidget = cls.makeWidget(self.event)## FIXME
            #cls.updateWidget(self.event, self.activeEventWidget)## needed? FIXME
        else:
            event = cls()
            self.activeEventWidget = event.makeWidget()
            self.event = event ## needed? FIXME
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
    def okClicked(self, button):## FIXME
        #if self.activeEventWidget:
        #    self.event = self.activeEventWidget.event
        #    self.event.updateVars(self.activeEventWidget)
        #else:
        #    self.event = None
        if self.event and self.activeEventWidget:
            self.event.updateVars(self.activeEventWidget)


class EventsManagerDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        vpan = gtk.VPaned()
        headerBox = gtk.HBox()
        treeBox = gtk.HBox()
        vpan.add1(headerBox)
        vpan.add2(treeBox)
        self.infoTextvew = gtk.TextView()
        headerBox.pack_start(self.infoTextvew, 1, 1)
        headerButtonBox = gtk.VButtonBox()
        headerButtonBox.set_layout(gtk.BUTTONBOX_END)
        addButton = gtk.Button(stock=gtk.STOCK_ADD)
        editButton = gtk.Button(stock=gtk.STOCK_EDIT)
        delButton = gtk.Button(stock=gtk.STOCK_DELETE)
        if ui.autoLocale:
            addButton.set_label(_('_Add'))
            addButton.set_use_underline(True)
            addButton.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
            ##########
            editButton.set_label(_('_Edit'))
            editButton.set_use_underline(True)
            editButton.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_BUTTON))
            ##########
            delButton.set_label(_('_Delete'))
            delButton.set_use_underline(True)
            delButton.set_image(gtk.image_new_from_stock(gtk.STOCK_DELETE, gtk.ICON_SIZE_BUTTON))
        headerButtonBox.add(addButton)
        headerButtonBox.add(editButton)
        headerButtonBox.add(delButton)
        headerBox.pack_start(headerButtonBox, 0, 0)
        self.treeview = gtk.TreeView()
        swin.add(self.treeview)
        swin.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        treeBox.pack_start(swin, 1, 1)
        self.vbox.pack_start(vpan)
        #####
        self.treestore = gtk.ListStore(gdk.Pixbuf,str,str)
        self.treeview.set_model(self.treestore)
        ###         
        col = gtk.TreeViewColumn('', gtk.CellRendererPixbuf(), pixbuf=0)
        col.set_resizable(True)
        self.treeview.append_column(col)
        ###
        col = gtk.TreeViewColumn(_('Summary'), gtk.CellRendererText(), text=1)
        col.set_resizable(True)
        self.treeview.append_column(col)
        self.treeview.set_search_column(1)
        ###
        col = gtk.TreeViewColumn(_('Description'), gtk.CellRendererText(), text=2)
        self.treeview.append_column(col)
        #self.treeview.set_search_column(2)
        #####
        addButton.connect('clicked', self.addClicked)
        editButton.connect('clicked', self.editClicked)
        delButton.connect('clicked', self.delClicked)
    def addClicked(self, button):
        pass
    def editClicked(self, button):
        pass
    def delClicked(self, button):
        pass

def makeWidget(obj):## obj is an instance of Event or EventRule or EventNotifier
    if hasattr(obj, 'WidgetClass'):
        return obj.WidgetClass(obj)
    else:
        return None

##############################################################################





##############################################################################

if rtl:
    gtk.widget_set_default_direction(gtk.TEXT_DIR_RTL)

__import__('scal2.ui_gtk.event_extenders', fromlist=['*'])
__import__('scal2.ui_gtk.event_extenders.rules', fromlist=['*'])
print __import__('scal2.ui_gtk.event_extenders.notifiers', fromlist=['*'])
#from scal2.ui_gtk.event_extenders import *
#from scal2.ui_gtk.event_extenders.rules import *
#from scal2.ui_gtk.event_extenders.notifiers import *


event_man.EventRule.makeWidget = makeWidget
event_man.EventNotifier.makeWidget = makeWidget
event_man.Event.makeWidget = makeWidget

ui.loadEvents()

if __name__=='__main__':
    from pprint import pprint, pformat
    dialog = gtk.Dialog()
    #dialog.vbox.pack_start(IconSelectButton('/usr/share/starcal2/pixmaps/starcal2.png'))
    event = event_man.Event(1)
    event.loadConfig()
    widget = event.makeWidget()
    dialog.vbox.pack_start(widget)
    dialog.vbox.show_all()
    dialog.add_button('OK', 0)
    def on_response(d, e):
        widget.updateVars()
        widget.event.saveConfig()
        pprint(widget.event.getData())
    dialog.connect('response', on_response)
    dialog.run()


