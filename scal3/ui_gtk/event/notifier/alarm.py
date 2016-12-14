#!/usr/bin/env python
# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib

from scal3.ui_gtk import *
#from scal3.ui_gtk import player


#class WidgetClass(player.PlayerBox):
#	def __init__(self, notifier):
#		self.notifier = notifier
#		player.PlayerBox.__init__(self)
#	def updateWidget(self):
#		if self.notifier.alarmSound:
#			self.openFile(self.notifier.alarmSound)
#	def updateVars(self):
#		self.notifier.alarmSound = self.getFile()

class WidgetClass(gtk.FileChooserButton):
	def __init__(self, notifier):
		self.notifier = notifier
		gtk.FileChooserButton.__init__(self, _('Select Sound'))
		self.set_local_only(True)
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
	#import thread
	#thread.start_new_thread(notifyWait, (notifier, finishFunc))
	finishFunc()
	Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE)

## event_lib.AlarmNotifier.WidgetClass = AlarmWidgetClass
## event_lib.AlarmNotifier.notify = notify

