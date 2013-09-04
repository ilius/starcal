from scal2.locale_man import tr as _
from scal2 import ui

import gtk

from scal2.ui_gtk.utils import dialog_add_button
from scal2.ui_gtk.mywidgets.icon import IconSelectButton


class TrashEditorDialog(gtk.Dialog):
    def __init__(self):
        gtk.Dialog.__init__(self)
        self.set_title(_('Edit Trash'))
        #self.connect('delete-event', lambda obj, e: self.destroy())
        #self.resize(800, 600)
        ###
        dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
        dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
        ##
        self.connect('response', lambda w, e: self.hide())
        #######
        self.trash = ui.eventTrash
        ##
        sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #######
        hbox = gtk.HBox()
        label = gtk.Label(_('Title'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        hbox.pack_start(self.titleEntry, 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        hbox = gtk.HBox()
        label = gtk.Label(_('Icon'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        sizeGroup.add_widget(label)
        self.iconSelect = IconSelectButton()
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.vbox.pack_start(hbox, 0, 0)
        ####
        self.vbox.show_all()
        self.updateWidget()
    def run(self):
        if gtk.Dialog.run(self)==gtk.RESPONSE_OK:
            self.updateVars()
        self.destroy()
    def updateWidget(self):
        self.titleEntry.set_text(self.trash.title)
        self.iconSelect.set_filename(self.trash.icon)
    def updateVars(self):
        self.trash.title = self.titleEntry.get_text()
        self.trash.icon = self.iconSelect.filename
        self.trash.save()

