# -*- coding: utf-8 -*-
# 
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from os.path import join, dirname

from scal2 import core
from scal2.core import pixDir, convert, numLocale, myRaise

from scal2.locale_man import tr as _
from scal2.locale_man import rtl

from scal2 import event_man
#from scal2.event import dateEncode, timeEncode, dateDecode, timeDecode

from scal2 import ui
from scal2.ui_gtk.utils import imageFromFile, pixbufFromFile
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


class DayOccurrenceView(event_man.DayOccurrenceView, gtk.VBox):
    def __init__(self, populatePopupFunc=None)
        event_man.DayOccurrenceView.__init__(self, ui.cell.jd)
        gtk.VBox.__init__(self)
        ## what to do with populatePopupFunc FIXME
        ## self.textview.connect('populate-popup', populatePopupFunc)
    def updateWidget(self):
        self.updateData()
        ## destroy all VBox contents and add again
        for hbox in self.get_children():
            hbox.destroy()
        for item in self.data:
            ## item['time'], item['text'], item['icon']
            hbox = gtk.HBox()
            if item['icon']:
                hbox.pack_start(imageFromFile(item['icon']), 0, 0)
            if item['time']:
                hbox.pack_start(gtk.Label(item['time']), 0, 0)
            label = gtk.Label(item['text'])
            label.set_selectable(True)
            hbox.pack_start(label, 1, 1)
            self.pack_start(hbox, 0, 0)


class WeekOccurrenceView(event_man.WeekOccurrenceView, gtk.TreeView):
    def __init__(self, abrivateWeekDays=False):
        self.abrivateWeekDays = abrivateWeekDays
        event_man.WeekOccurrenceView.__init__(self, ui.cell.jd)
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
        self.updateData()
        self.ls.clear()
        for item in self.data:
            self.ls.append(
                pixbufFromFile(item['icon']),
                core.weekDayNameAb(item['weekDay']) if self.abrivateWeekDays else core.weekDayName(item['weekDay']),
                item['time'],
                item['text'],
            )
        

class MonthOccurrenceView(event_man.MonthOccurrenceView, gtk.TreeView):
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
                numLocale(item['day']),
                item['time'],
                item['text'],
            )


class EventEditorDialog(gtk.Dialog):
    def __init__(self, event=None, eventType=''):
        gtk.Dialog.__init__(self)
        cancelB = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        okB = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        if ui.autoLocale:
            cancelB.set_label(_('_Cancel'))
            cancelB.set_image(gtk.image_new_from_stock(gtk.STOCK_CANCEL,gtk.ICON_SIZE_BUTTON))
            okB.set_label(_('_OK'))
            okB.set_image(gtk.image_new_from_stock(gtk.STOCK_OK,gtk.ICON_SIZE_BUTTON))
        okB.connect('clicked', self.okClicked)
        #######
        self.event = event
        self.activeEventWidget = None
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
        self.comboDateMode.set_active(ui.shownCals[0]['mode'])## or core.primaryMode
        self.comboDateMode.connect('changed', self.dateModeChanged)
        ####
        if eventType:
            cls = event_man.eventsClassDict[eventType]
            if self.event:## is this case usable that give both event and eventType? ## FIXME
                self.activeEventWidget = cls.makeWidget(self.event)## FIXME
            else:
                event = cls()
                self.activeEventWidget = event.makeWidget()
                self.event = event ## needed? FIXME
        else:
            hbox = gtk.HBox()
            combo = gtk.combo_box_new_text()
            for cls in event_man.eventsClassList:
                combo.append_text(cls.desc)
            self.vbox.pack_start(hbox, 0, 0)
            if self.event:
                combo.set_active(event_man.eventsClassList.find(self.event.__class__))
            else:
                combo.set_active(event.defaultEventTypeIndex)
            combo.connect('changed', self.eventTypeChanged)
            self.comboEventType = combo
    def dateModeChanged(self, combo):
        pass
    def eventTypeChanged(self, combo):
        if self.activeEventWidget:
            self.activeEventWidget.destroy()
        cls = event_man.eventsClassList[combo.get_active()]
        if self.event:
            self.activeEventWidget = cls.makeWidget(self.event)## FIXME
        else:
            event = cls()
            self.activeEventWidget = event.makeWidget()
            self.event = event ## needed? FIXME
        self.vbox.pack_start(self.activeEventWidget, 0, 0)
    def okClicked(self, button):## FIXME
        if self.activeEventWidget:
            self.activeEventWidget.updateVars()


class EventManagerDialog(gtk.Dialog):## FIXME
    def __init__(self, mainWin=None):## mainWin is needed? FIXME
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
        ####
        addButton = gtk.Button(stock=gtk.STOCK_ADD)
        '''
        addButton = gtk.OptionMenu(stock=gtk.STOCK_ADD)
        menu = gtk.Menu()
        menu.set_border_width(0)
        #for eventType in ('custom', 'yearly', 'dailyNote', 'task'):## FIXME
        for cls in eventsClassList:## order? FIXME
            item = gtk.MenuItem(cls.desc)## ImageMenuItem
            #item.set_image(imageFromFile(...))
            item.connect('activate', self.addEvent, cls)
        '''
        ####
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
        self.treestore = gtk.ListStore(gdk.Pixbuf, str, str)
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
        addButton.connect('clicked', self.addEvent)
        editButton.connect('clicked', self.editClicked)
        delButton.connect('clicked', self.delClicked)
        #####
        self.reloadEvents()
    def reloadEvents(self):
        for event in ui.events:
            self.treestore.append(
                pixbufFromFile(event.icon),
                event.summary,
                event.description,
            )
    def addEvent(self, obj=None):
        pass
    def addYearlyEvent(self, obj=None):
        pass
    def addDailyNote(self, obj=None):
        pass
    def showDialog(self, obj=None):
        self.present()
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


modPrefix = 'scal2.ui_gtk.event_extenders.'

for cls in event_man.eventsClassList:
    try:
        module = __import__(modPrefix + cls.name, fromlist=['EventWidget'])
        cls.WidgetClass = module.EventWidget
    except:
        myRaise()

for cls in event_man.eventRulesClassList:
    try:
        module = __import__(modPrefix + 'rules.' + cls.name, fromlist=['RuleWidget'])
        cls.WidgetClass = module.RuleWidget
    except:
        myRaise()

for cls in event_man.eventNotifiersClassList:
    try:
        module = __import__(modPrefix + 'notifiers.' + cls.name, fromlist=['NotifierWidget', 'notify'])
        cls.WidgetClass = module.NotifierWidget
        cls.notify = module.notify
    except:
        myRaise()

event_man.Event.makeWidget = makeWidget
event_man.EventRule.makeWidget = makeWidget
event_man.EventNotifier.makeWidget = makeWidget


ui.loadEvents()

def testCustomEventEditor():
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
    #dialog.run()
    dialog.present()
    gtk.main()

if __name__=='__main__':
    testCustomEventEditor()


