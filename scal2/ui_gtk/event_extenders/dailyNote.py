#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.mywidgets.multi_spin_button import DateButton
from scal2.ui_gtk.event_extenders.common import EventWidget

import gtk
from gtk import gdk

class DailyNoteEventWidget(EventWidget):
    def __init__(self, event):## FIXME
        EventWidget.__init__(self, event)
        ###
        #hbox = gtk.HBox()
        #hbox.pack_start(gtk.Label(_('Date')))
        #dateInput = DateButton(lang=core.langSh)
        self.updateWidget()
    def updateWidget(self):## FIXME
        pass
    def updateVars(self):## FIXME
        pass

event_man.DailyNoteEvent.WidgetClass = DailyNoteEventWidget

