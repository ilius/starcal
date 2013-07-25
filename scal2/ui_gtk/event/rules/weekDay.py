#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
import gtk
from gtk import gdk


class RuleWidget(gtk.HBox):
    def __init__(self, rule):
        self.rule = rule
        ###
        gtk.HBox.__init__(self)
        self.set_homogeneous(True)
        ls = [gtk.ToggleButton(item) for item in core.weekDayNameAb]
        s = core.firstWeekDay
        for i in range(7):
            self.pack_start(ls[(s+i)%7], 1, 1)
        self.cbList = ls
        self.start = s
    def setStart(self, s):
        b = self.widget
        ls = self.cbList
        for j in range(7):## or range(6)
            b.reorder_child(ls[(s+j)%7], j)
        self.start = s
    def updateVars(self):
        weekDayList = []
        cbl = self.cbList
        for j in range(7):
            if cbl[j].get_active():
                weekDayList.append(j)
        self.rule.weekDayList = tuple(weekDayList)
    def updateWidget(self):
        cbl = self.cbList
        for cb in cbl:
            cb.set_active(False)
        for j in self.rule.weekDayList:
            cbl[j].set_active(True)

