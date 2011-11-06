from scal2.locale_man import tr as _

from scal2 import event_man
from scal2 import ui

import gtk

class DayOccurrenceView(event_man.DayOccurrenceView, gtk.VBox):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self, populatePopupFunc=None):
        event_man.DayOccurrenceView.__init__(self, ui.cell.jd)
        gtk.VBox.__init__(self)
        ## what to do with populatePopupFunc FIXME
        ## self.textview.connect('populate-popup', populatePopupFunc)
        self.updateWidget()
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
            label.set_line_wrap(True)
            label.set_use_markup(True)
            hbox.pack_start(label, 1, 1)
            self.pack_start(hbox, 0, 0)
        self.show_all()
        self.set_visible(bool(self.data))


class WeekOccurrenceView(event_man.WeekOccurrenceView, gtk.TreeView):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
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
                numLocale(item['day']),
                item['time'],
                item['text'],
            )
