#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# 
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Or on Debian systems, from /usr/share/common-licenses/GPL

import sys, os
from os import listdir, makedirs
from os.path import join, isfile, isdir, exists, dirname
from time import time, localtime, sleep
from subprocess import Popen, PIPE


from gobject import timeout_add_seconds
import glib
from glib import MainLoop

sys.path.append(dirname(dirname(__file__))) ## FIXME

from scal2.paths import *
from scal2.os_utils import getUsersData
from scal2.time_utils import getCurrentTime
from scal2.cal_modules import to_jd, DATE_GREG
from scal2 import event_man
from scal2.event_man import eventsDir

try:
    import logging
    import logging.config
    logging.config.fileConfig(join(rootDir, 'conf', 'logging-system.conf'))
    log = logging.getLogger('daemon')## FIXME
except:
    from scal2.utils import FallbackLogger
    log = FallbackLogger()


########################## Global Variables #########################
uiName = 'gtk'
notifyCmd = [join(rootDir, 'scripts', 'run'), join('scal2', 'ui_'+uiName, 'event', 'notify.py')]
pid = os.getpid()
thisUid = os.getuid()

pidFile = join(confDir, 'event', 'daemon.pid')
uidList = [thisUid]


import atexit

def onDaemonExit():
    #log.debug('daemon: exiting')
    os.remove(pidFile)

open(pidFile, 'w').write(str(pid))
atexit.register(onDaemonExit)

eventGroups = event_man.EventGroupsHolder()

########################## Functions #################################

def assertDir(path):
    if not exists(path):
        makedirs(path)
    elif not isdir(path):
        raise IOError('%r must be a directory'%path)

def notify(eid):
    #log.debug('notify eid %s'%eid)
    for uid in uidList:
        print 'notify, uid=%s, eid=%s'%(uid, eid)
        Popen(notifyCmd+[str(eid), str(uid)], stdout=PIPE)

def prepareToday():
    tm = getCurrentTime()
    (y, m, d) = localtime(tm)[:3]
    #log.debug('Date: %s/%s/%s   Epoch: %s'%(y, m, d, tm))
    todayJd = to_jd(y, m, d, DATE_GREG)
    dayRemainSecondsCeil = int(-(tm - 1)%(24*3600))
    timeout_add_seconds(dayRemainSecondsCeil, prepareToday)
    for group in eventGroups:
        if not group.enable:
            continue
        for event in group:
            if not event:
                continue
            if not event.notifiers:
                continue
            eid = event.id
            occur = event.calcOccurrenceForJdRange(todayJd, todayJd+1)
            if not occur:
                continue
            #addList = []
            for (start, end) in occur.getTimeRangeList():
                dt = start - event.getNotifyBeforeSec() - tm
                if dt >= 0:
                    #print 'start=%s, seconds_later=%s'%(start, int(start-tm)+1)
                    timeout_add_seconds(int(dt)+1, notify, eid)
                    #log.debug(str(int(dt)+1))
                    #addList.append(int(dt)+1)
                #log.debug('start=%s, tm=%s, start-tm=%s'%(start, tm, start-tm))
    #addList.sort()
    #log.debug('addList=%r'%addList[:20])


########################## Starting Program ###########################

eventGroups.load()
prepareToday()
MainLoop().run()


