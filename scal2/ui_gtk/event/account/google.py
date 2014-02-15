# -*- coding: utf-8 -*-

from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.event.account import common

class AccountWidget(common.AccountWidget):
    def __init__(self, account):
        common.AccountWidget.__init__(self, account)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Email'))
        label.set_alignment(0, 0.5)
        pack(hbox, label)
        self.sizeGroup.add_widget(label)
        self.emailEntry = gtk.Entry()
        pack(hbox, self.emailEntry, 1, 1)
        pack(self, hbox)
    def updateWidget(self):
        common.AccountWidget.updateWidget(self)
        self.emailEntry.set_text(self.account.email)
    def updateVars(self):
        common.AccountWidget.updateVars(self)
        self.account.email = self.emailEntry.get_text()

