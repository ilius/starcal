# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux


import sys, time
from time import strftime
from os.path import join, split, splitext

from scal2.paths import *
from scal2.time_utils import getJhmsFromEpoch
from scal2.cal_modules import jd_to, to_jd, convert, DATE_GREG
from scal2.plugin_man import HolidayPlugin, BuiltinTextPlugin
from scal2 import core



icsTmFormat = '%Y%m%dT%H%M%S'## timezone? (Z%Z or Z%z) FIXME

icsHeader = '''BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Mozilla.org/NONSGML Mozilla Calendar V1.1//EN
'''

icsWeekDays = ('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA')

encodeIcsWeekDayList = lambda weekDayList: ','.join([icsWeekDays[wd] for wd in weekDayList])

def getIcsTimeByEpoch(epoch):
    (jd, hour, minute, second) = getJhmsFromEpoch(epoch)
    (year, month, day) = jd_to(jd, DATE_GREG)
    return strftime(icsTmFormat, (year, month, day, hour, minute, second, 0, 0, 0))

getIcsDate = lambda y, m, d: '%.4d%.2d%.2d'%(y, m, d)
getIcsDateByJd = lambda jd: getIcsDate(*jd_to(jd, DATE_GREG))

def convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix=''):
    icsText = icsHeader
    currentTimeStamp = strftime(icsTmFormat)
    for jd in range(startJd, endJd):
        isHoliday = False
        for mode in plug.holidays.keys():
            (myear, mmonth, mday) = jd_to(jd, mode)
            if (mmonth, mday) in plug.holidays[mode]:
                isHoliday = True
                break
        if isHoliday:
            (gyear, gmonth, gday) = jd_to(jd, DATE_GREG)
            (gyear_next, gmonth_next, gday_next) = jd_to(jd+1, DATE_GREG)
            #######
            icsText += 'BEGIN:VEVENT\n'
            icsText += 'CREATED:%s\n'%currentTimeStamp
            icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
            icsText += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear, gmonth, gday)
            icsText += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear_next, gmonth_next, gday_next)
            icsText += 'CATEGORIES:Holidays\n'
            icsText += 'TRANSP:TRANSPARENT\n'
            ## TRANSPARENT because being in holiday time, does not make you busy!
            ## see http://www.kanzaki.com/docs/ical/transp.html
            icsText += 'SUMMARY:تعطیل\n'
            icsText += 'END:VEVENT\n'
    icsText += 'END:VCALENDAR\n'
    fname = split(plug.path)[-1]
    fname = splitext(fname)[0] + '%s.ics'%namePostfix
    open(fname, 'w').write(icsText)

def convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix=''):
    plug.load() ## FIXME
    mode = plug.mode
    icsText = icsHeader
    currentTimeStamp = strftime(icsTmFormat)
    for jd in range(startJd, endJd):
        (myear, mmonth, mday) = jd_to(jd, mode)
        dayText = plug.get_text(myear, mmonth, mday)
        if dayText:
            (gyear, gmonth, gday) = jd_to(jd, DATE_GREG)
            (gyear_next, gmonth_next, gday_next) = jd_to(jd+1, DATE_GREG)
            #######
            icsText += 'BEGIN:VEVENT\n'
            icsText += 'CREATED:%s\n'%currentTimeStamp
            icsText += 'LAST-MODIFIED:%s\n'%currentTimeStamp
            icsText += 'DTSTART;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear, gmonth, gday)
            icsText += 'DTEND;VALUE=DATE:%.4d%.2d%.2d\n'%(gyear_next, gmonth_next, gday_next)
            icsText += 'SUMMARY:%s\n'%dayText
            icsText += 'END:VEVENT\n'
    icsText += 'END:VCALENDAR\n'
    fname = split(plug.path)[-1]
    fname = splitext(fname)[0] + '%s.ics'%namePostfix
    open(fname, 'w').write(icsText)

def convertAllPluginsToIcs(startYear, endYear):
    startJd = to_jd(startYear, 1, 1, DATE_GREG)
    endJd = to_jd(endYear+1, 1, 1, DATE_GREG)
    namePostfix = '-%d-%d'%(startYear, endYear)
    for plug in core.allPlugList:
        if isinstance(plug, HolidayPlugin):
            convertHolidayPlugToIcs(plug, startJd, endJd, namePostfix)
        elif isinstance(plug, BuiltinTextPlugin):
            convertBuiltinTextPlugToIcs(plug, startJd, endJd, namePostfix)
        else:
            print 'Ignoring unsupported plugin %s'%plug.path


