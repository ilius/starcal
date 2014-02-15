# -*- coding: utf-8 -*-

from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk import *

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
        pack(hbox, label)
        self.sizeGroup.add_widget(label)
        self.titleEntry = gtk.Entry()
        pack(hbox, self.titleEntry, 1, 1)
        pack(self, hbox)
    def updateWidget(self):
        self.titleEntry.set_text(self.account.title)
    def updateVars(self):
        self.account.title = self.titleEntry.get_text()







