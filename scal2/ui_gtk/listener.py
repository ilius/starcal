import time
from time import localtime
from time import time as now

from scal2.time_utils import getUtcOffsetCurrent
from scal2 import core
from scal2 import ui

import gobject, glib
from gobject import timeout_add, timeout_add_seconds

dayLen = 24*3600

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
        if gdate!=self.gdate:
            self.gdate = gdate
            ui.todayCell = ui.cellCache.getTodayCell()
            for obj in self.receivers:
                obj.onCurrentDateChange(gdate)
        #timeout_add_seconds(int(dayLen-(tm+getUtcOffsetCurrent())%dayLen)+1, self.check)
        timeout_add_seconds(self.timeout, self.check)

#class TimeChangeListener:

dateChange = DateChangeListener()
#timeChange = TimeChangeListener()

if __name__=='__main__':
    class TestRec:
        def onCurrentDateChange(self, date):
            print('current date changed to %s/%s/%s'%date)
    dateChange.add(TestRec())
    glib.MainLoop().run()


