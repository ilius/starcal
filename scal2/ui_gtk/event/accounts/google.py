# -*- coding: utf-8 -*-

from scal2.locale_man import tr as _

import gtk
from gtk import gdk

from scal2.ui_gtk.event.accounts import common

class AccountWidget(common.AccountWidget):
    def __init__(self, account):
        common.AccountWidget.__init__(self, account)
        #####
        hbox = gtk.HBox()
        label = gtk.Label(_('Email'))
        label.set_alignment(0, 0.5)
        hbox.pack_start(label, 0, 0)
        self.sizeGroup.add_widget(label)
        self.emailEntry = gtk.Entry()
        hbox.pack_start(self.emailEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
    def updateWidget(self):
        common.AccountWidget.updateWidget(self)
        self.emailEntry.set_text(self.account.email)
    def updateVars(self):
        common.AccountWidget.updateVars(self)
        self.account.email = self.emailEntry.get_text()

