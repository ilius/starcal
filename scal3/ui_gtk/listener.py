#!/usr/bin/env python3

from scal3 import logger
log = logger.get()

import time
from time import localtime
from time import time as now

from scal3.time_utils import getUtcOffsetCurrent
from scal3 import core
from scal3 import ui

from scal3.ui_gtk import gtk, timeout_add_seconds

dayLen = 24 * 3600


class DateChangeListener:
	def __init__(self, timeout=1):
		self.timeout = timeout ## seconds
		self.receivers = []
		self.gdate = localtime()[:3]
		self.check()

	def add(self, receiver):
		self.receivers.append(receiver)

	def check(self):
		tm = now()
		gdate = localtime(tm)[:3]
		if gdate != self.gdate:
			self.gdate = gdate
			ui.todayCell = ui.cellCache.getTodayCell()
			for obj in self.receivers:
				obj.onCurrentDateChange(gdate)
		#timeout_add_seconds(
		#	int(dayLen - (tm + getUtcOffsetCurrent()) % dayLen) + 1,
		#	self.check,
		#)
		timeout_add_seconds(self.timeout, self.check)
		if ui.mainWin:
			ui.mainWin.statusIconUpdateTooltip()

#class TimeChangeListener:


dateChange = DateChangeListener()
#timeChange = TimeChangeListener()

if __name__ == "__main__":
	from gi.repository import GLib as glib

	class TestRec:
		def onCurrentDateChange(self, gdate):
			log.info(f"current date changed to {gdate!r}")

	dateChange.add(TestRec())
	glib.MainLoop().run()
