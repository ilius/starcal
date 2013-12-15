from os.path import isfile

from scal2.cal_types import calTypes
from scal2.import_customday import customFile, importAndDeleteCustomDB
from scal2.locale_man import tr as _
from scal2 import core
from scal2 import ui

import gtk
from gtk import gdk

from scal2.ui_gtk.utils import dialog_add_button, DateTypeCombo

class CustomDayImporterDialog(gtk.Dialog):
    def onResponse(self, dialog, response_id):
        if response_id==gtk.RESPONSE_OK:
            importAndDeleteCustomDB(
                self.modeCombo.get_active(),
                self.groupTitleEntry.get_text(),
            )
        self.destroy()
    def __init__(self):
        gtk.Dialog.__init__(self)
        ####
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        self.connect('response', self.onResponse)
        ####
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Calendar Type'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        combo = DateTypeCombo()
        combo.set_active(calTypes.primary)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        self.modeCombo = combo
        ####
        hbox = gtk.HBox()
        hbox = gtk.HBox()
        label = gtk.Label(_('Group Title'))
        label.set_alignment(0, 0.5)
        sizeGroup.add_widget(label)
        hbox.pack_start(label, 0, 0)
        self.groupTitleEntry = gtk.Entry()
        self.groupTitleEntry.set_text(_('Imported Events'))
        hbox.pack_start(self.groupTitleEntry, 0, 0)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()

if isfile(customFile):
    CustomDayImporterDialog().run()

