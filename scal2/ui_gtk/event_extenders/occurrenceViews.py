# -*- coding: utf-8 -*-

from os.path import join, dirname

from scal2 import core
from scal2.locale_man import tr as _
from scal2.locale_man import numLocale
from scal2.core import pixDir

from scal2 import event_man
from scal2 import ui

from scal2.ui_gtk.utils import imageFromFile, pixbufFromFile

import gtk
from gtk import gdk

class DayOccurrenceView(event_man.DayOccurrenceView, gtk.VBox):
    def __init__(self, jd):
        event_man.DayOccurrenceView.__init__(self, jd)
        gtk.VBox.__init__(self)
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
    def __init__(self, jd, abrivateWeekDays=False):
        self.abrivateWeekDays = abrivateWeekDays
        event_man.WeekOccurrenceView.__init__(self, jd)
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
    def __init__(self, jd):
        event_man.MonthOccurrenceView.__init__(self, jd)
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

