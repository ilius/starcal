#!/usr/bin/env python
# -*- coding: utf-8 -*-
import thread

from scal2 import core
from scal2.locale_man import tr as _

from scal2 import event_lib
import gtk
from gtk import gdk

from scal2.ui_gtk import player
from subprocess import Popen, PIPE

#class NotifierWidget(player.PlayerBox):
#    def __init__(self, notifier):
#        self.notifier = notifier
#        player.PlayerBox.__init__(self)
#    def updateWidget(self):
#        if self.notifier.alarmSound:
#            self.openFile(self.notifier.alarmSound)
#    def updateVars(self):
#        self.notifier.alarmSound = self.getFile()

class NotifierWidget(gtk.FileChooserButton):
    def __init__(self, notifier):
        self.notifier = notifier
        gtk.FileChooserButton.__init__(self, _('Select Sound'))
    def updateWidget(self):
        if self.notifier.alarmSound:
            self.set_filename(self.notifier.alarmSound)
    def updateVars(self):
        self.notifier.alarmSound = self.get_filename()

def notifyWait(notifier, finishFunc):
    if notifier.alarmSound and notifier.playerCmd:
        Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE).communicate()
    #finishFunc()

def notify(notifier, finishFunc):
    #thread.start_new_thread(notifyWait, (notifier, finishFunc))
    finishFunc()
    Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE)

## event_lib.AlarmNotifier.WidgetClass = AlarmNotifierWidget
## event_lib.AlarmNotifier.notify = notify

