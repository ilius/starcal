#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

class TaskEventWidget:
    def __init__(self, event):## FIXME
        self.event = event
        self.updateWidget()
    def updateWidget(self):## FIXME
        pass
    def updateVars(self):## FIXME
        pass


event_man.TaskEvent.WidgetClass = TaskEventWidget

