#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton, TimeButton
from scal2.ui_gtk.event_extenders import common

import gtk
from gtk import gdk

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ###
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Date')), 0, 0)
        self.dateInput = DateButton(lang=core.langSh)
        hbox.pack_start(self.dateInput, 0, 0)
        ##
        hbox.pack_start(gtk.Label(''), 1, 1)
        ##
        hbox.pack_start(gtk.Label(_('Time')), 0, 0)
        self.timeInput = TimeButton(lang=core.langSh)
        hbox.pack_start(self.timeInput, 0, 0)
        ##
        self.pack_start(hbox, 0, 0)
        self.updateWidget()
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        self.dateInput.set_date(self.event.getDate())
        self.timeInput.set_time(self.event.getTime())
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)
        self.event.setDate(*self.dateInput.get_date())
        self.event.setTime(*self.dateInput.get_time())

