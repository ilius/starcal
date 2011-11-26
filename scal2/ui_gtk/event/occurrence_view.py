from scal2.utils import toStr, toUnicode
from scal2.locale_man import tr as _

from scal2 import event_man
from scal2 import ui

import gtk

from scal2.ui_gtk.utils import imageFromFile
from scal2.ui_gtk.event.common import EventEditorDialog

class DayOccurrenceView(event_man.DayOccurrenceView, gtk.VBox):
    updateData = lambda self: self.updateDataByGroups(ui.eventGroups)
    def __init__(self, populatePopupFunc=None):
        event_man.DayOccurrenceView.__init__(self, ui.cell.jd)
        gtk.VBox.__init__(self)
        ## what to do with populatePopupFunc FIXME
        ## self.textview.connect('populate-popup', populatePopupFunc)
        self.clipboard = gtk.clipboard_get()
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
            label.connect('populate-popup', self.onLabelPopupPopulate, item['ids'])
            hbox.pack_start(label, 1, 1)
            self.pack_start(hbox, 0, 0)
        self.show_all()
        self.set_visible(bool(self.data))
    def onLabelPopupPopulate(self, label, menu, ids):
        menu = gtk.Menu()
        ##
        itemCopyAll = gtk.ImageMenuItem(_('Copy _All'))
        itemCopyAll.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        itemCopyAll.connect('activate', self.copyAll, label)
        menu.add(itemCopyAll)
        ##
        itemCopy = gtk.ImageMenuItem(_('_Copy'))
        itemCopy.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))
        if label.get_property('cursor-position') > label.get_property('selection-bound'):
            itemCopy.connect('activate', self.copy, label)
        else:
            itemCopy.set_sensitive(False)
        menu.add(itemCopy)
        ##
        menu.add(gtk.SeparatorMenuItem())
        ##
        (group_id, event_id) = ids
        event = ui.eventGroups[group_id].getEvent(event_id)
        winTitle = _('Edit ') + event.desc
        itemEdit = gtk.ImageMenuItem(winTitle)
        itemEdit.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))
        itemEdit.connect('activate', self.editEventClicked, winTitle, event, group_id)
        menu.add(itemEdit)
        ## How about moving event to trash from here?
        ##
        menu.show_all()
        menu.popup(None, None, None, 3, 0)
    def editEventClicked(self, item, winTitle, event, group_id):
        event = EventEditorDialog(
            event=event,
            title=winTitle,
            #parent=self,## FIXME
        ).run()
        if event is None:
            return
        self.updateWidget()
        ui.changedEvents.append((group_id, event.eid))
    def copy(self, item, label):
        start = label.get_property('selection-bound')
        end = label.get_property('cursor-position')
        self.clipboard.set_text(toStr(toUnicode(label.get_text())[start:end]))
    copyAll = lambda self, item, label: self.clipboard.set_text(label.get_label())

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
