# -*- coding: utf-8 -*-

import gtk
from gtk import gdk


class AccountWidget(gtk.VBox):
    def __init__(self, account):
        gtk.VBox.__init__(self)
        self.account = account
        ########
        self.sizeGroup = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Title'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        hbox.pack_start(self.titleEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        self.titleEntry.set_text(self.account.title)
    def updateVars(self):
        self.account.title = self.titleEntry.get_text()







