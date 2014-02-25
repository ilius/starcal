# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin_button import IntSpinButton

class WidgetClass(IntSpinButton):
    def __init__(self, rule):
        self.rule = rule
        IntSpinButton.__init__(self, 0, 999999)
    def updateWidget(self):
        self.set_value(self.rule.getData())
    def updateVars(self):
        self.rule.setData(self.get_value())

