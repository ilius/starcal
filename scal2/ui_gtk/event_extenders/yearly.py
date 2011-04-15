#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

class YearlyEventWidget(gtk.VBox):
    def __init__(self, event):## FIXME
        gtk.VBox.__init__(self)
        ################
        self.event = event
        ################
        #hbox = 
        
        
        
        self.updateWidget()
    def updateWidget(self):## FIXME
        pass
    def updateVars(self):## FIXME
        pass


event_man.YearlyEvent.WidgetClass = YearlyEventWidget


