#!/usr/bin/env python
# -*- coding: utf-8 -*-
import thread

from scal2 import core
from scal2.locale import tr as _

from scal2 import event_man
import gtk
from gtk import gdk

from scal2.ui_gtk import player
from subprocess import Popen, PIPE

class AlarmNotifierWidget(player.PlayerBox):
    def __init__(self, notifier):
        self.notifier = notifier
        player.PlayerBox.__init__(self)
        self.updateWidget()
    def updateWidget(self):
        if self.notifier.alarmSound:
            self.openFile(self.notifier.alarmSound)
    def updateVars(self):
        self.notifier.alarmSound = self.getFile()

def notifyWait(notifier, finishFunc):
    if notifier.alarmSound and notifier.playerCmd:
        Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE).communicate()
    #finishFunc()

def notify(notifier, finishFunc):
    #thread.start_new_thread(notifyWait, (notifier, finishFunc))
    finishFunc()
    Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE)

event_man.AlarmNotifier.WidgetClass = AlarmNotifierWidget
event_man.AlarmNotifier.notify = notify

