#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man

from scal2 import ui
from scal2.ui_gtk.event import common

import gtk
from gtk import gdk

class EventWidget(common.EventWidget):
    def __init__(self, event):## FIXME
        common.EventWidget.__init__(self, event)
        ###
        
        
        self.updateWidget()
    def updateWidget(self):## FIXME
        common.EventWidget.updateWidget(self)
        
    def updateVars(self):## FIXME
        common.EventWidget.updateVars(self)


