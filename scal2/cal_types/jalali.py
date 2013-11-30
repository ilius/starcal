# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
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

## Iranian (Jalali) calendar:
## http://en.wikipedia.org/wiki/Iranian_calendar

name = 'jalali'
desc = 'Jalali'
origLang = 'fa'

monthNameMode = 0
jalaliAlg = 0
options = (
    (
        'monthNameMode',
        list,
        'Jalali Month Names',
        ('Iranian', 'Kurdish', 'Dari', 'Pashto'),
    ),
    (
        'jalaliAlg',
        list,
        'Jalali Calculation Algorithm',
        ('33 year algorithm', '2820 year algorithm'),
    ),
)


monthNameVars = (
    (
        ('Farvardin','Ordibehesht','Khordad','Teer','Mordad','Shahrivar',
         'Mehr','Aban','Azar','Dey','Bahman','Esfand'),
        ('Far', 'Ord', 'Khr', 'Tir', 'Mor', 'Shr',
         'Meh', 'Abn', 'Azr', 'Dey', 'Bah', 'Esf'),
    ),
    (
        ('Xakelêwe','Gullan','Cozerdan','Pûşper','Gelawêj','Xermanan',
         'Rezber','Gelarêzan','Sermawez','Befranbar','Rêbendan','Reşeme'),
    ),
    (
        ('Hamal','Sawr','Jawzā','Saratān','Asad','Sonbola',
         'Mizān','Aqrab','Qaws','Jadi','Dalvæ','Hūt'),
    ),
    (
        ('Wray','Ǧwayay','Ǧbargolay','Čungāx̌','Zmaray','Waǵay',
         'Təla','Laṛam','Līndəi','Marǧūmay','Salwāǧa','Kab'),
    ),
)

#        ('','','','','','',
#         '','','','','','')


getMonthName = lambda m, y=None: monthNameVars[monthNameMode][0][m-1]

def getMonthNameAb(m, y=None):
    v = monthNameVars[monthNameMode]
    try:
        l = v[1]
    except IndexError:
        l = v[0]
    return l[m-1]



getMonthsInYear = lambda y: 12

from math import floor, ceil
ifloor = lambda x: int(floor(x))

epoch = 1948321
minMonthLen = 29
maxMonthLen = 31
avgYearLen = 365.2425 ## FIXME

GREGORIAN_EPOCH = 1721426
monthLen = (31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29)


import os
from scal2.path import sysConfDir, confDir

## Here load user options(jalaliAlg) from file
sysConfPath = '%s/%s.conf'%(sysConfDir, name)
if os.path.isfile(sysConfPath):
    try:
        exec(file(sysConfPath).read())
    except:
        myRaise(__file__)

confPath = '%s/%s.conf'%(confDir, name)
if os.path.isfile(confPath):
    try:
        exec(file(confPath).read())
    except:
        myRaise(__file__)



def save():## Here save user options to file
    text = ''
    text += 'monthNameMode=%s\n'%monthNameMode
    text += 'jalaliAlg=%s\n'%jalaliAlg
    file(confPath, 'w').write(text)



def isLeap(year):
    "isLeap: Is a given year a leap year in the Jalali calendar ?"
    if jalaliAlg==1:
        return (( (year - 473 - (year>0)) %2820 + 512) * 682) % 2816 < 682
    elif jalaliAlg==0:
        ## Use 33 year algorithm
        ## taken from farsiweb code writen by Roozbeh Pournader <roozbeh@sharif.edu>
        ## and Mohammad Toossi <mohammad@bamdad.org> at 2001
        jy = year - 979
        gdays = ( 365*jy + (jy/33)*8 + (jy%33+3)/4    +    79 ) % 146097
        leap = True
        if gdays >= 36525: # 36525 = 365*100 + 100/4
            gdays -= 1
            gdays = gdays % 36524
            if gdays >= 365:
                gdays += 1
            else:
                leap = False
        if gdays % 1461 >= 366:
            leap = False
        return leap
    else:
        raise RuntimeError('bad option jalaliAlg=%s'%jalaliAlg)

def to_jd(year, month, day):
    "TO_JD: Determine Julian day from Jalali date"
    if jalaliAlg==1:
        # Python <= 2.5
        if year >=0 :
            rm = 474
        else:
            rm = 473
        epbase = year - (rm)
        # Python 2.5
        #epbase = year - 474 if year>=0 else 473
        epyear = 474 + (epbase % 2820)
        if month <= 7 :
            mm = (month - 1) * 31
        else:
            mm = ((month - 1) * 30) + 6
        return ifloor(
            day + mm + \
            ifloor(((epyear * 682) - 110) / 2816) + \
            (epyear - 1) * 365 + \
            ifloor(epbase / 2820) * 1029983 + \
            epoch - 1
        )
    elif jalaliAlg==0:
        ## Use 33 year algorithm
        ##taken from farsiweb code writen by Roozbeh Pournader <roozbeh@sharif.edu>
        ## and Mohammad Toossi <mohammad@bamdad.org> at 2001
        y2 = year-979
        jdays = 365*y2 + (y2/33)*8 + (y2%33+3)/4
        for i in range(month-1):
            jdays += monthLen[i]
        jdays += (day-1)
        return jdays + 584101 + GREGORIAN_EPOCH
    else:
        raise RuntimeError('bad option jalaliAlg=%s'%jalaliAlg)

def jd_to(jd):
    "JD_TO_JALALI: Calculate Jalali date from Julian day"
    if jalaliAlg==1:## 2820
        cycle, cyear = divmod(jd - to_jd(475, 1, 1), 1029983)
        if cyear == 1029982 :
            ycycle = 2820
        else :
            aux1, aux2 = divmod(cyear, 366)
            ycycle = floor(((2134 * aux1) + (2816 * aux2) + 2815) / 1028522) + aux1 + 1
        year = ifloor(2820*cycle + ycycle + 474)
        if year <= 0 :
            year -= 1
        yday = jd - to_jd(year, 1, 1) + 1
        if yday <= 186:
            month = int(ceil(yday / 31))
        else:
            month = int(ceil((yday - 6) / 30))
        day = int(jd - to_jd(year, month, 1)) + 1
        if day > 31:
            day -= 31
            if month==12:
                month = 1
                year += 1
            else:
                month += 1
    elif jalaliAlg==0:
        ## Use 33 year algorithm
        ##taken from farsiweb code writen by Roozbeh Pournader <roozbeh@sharif.edu> and Mohammad Toossi <mohammad@bamdad.org> at 2001
        jdays = int(jd - GREGORIAN_EPOCH - 584101)
        # -(1600*365 + 1600/4 - 1600/100 + 1600/400) + 365    -79 +1== -584101
        #print 'jdays =',jdays
        j_np = jdays / 12053
        jdays %= 12053
        year = 979+33*j_np+4*(jdays/1461)
        jdays %= 1461
        if jdays >= 366:
            year += (jdays-1)/365
            jdays = (jdays-1)%365
        month = 12
        for i in range(11):
            if jdays >= monthLen[i]:
                jdays -= monthLen[i]
            else:
                month = i+1
                break
        day = jdays+1
    else:
        raise RuntimeError('bad option jalaliAlg=%s'%jalaliAlg)
    return year, month, day


## Normal: esfand = 29 days
## Leap: esfand = 30 days

def getMonthLen(year, month):
    if month==12:
        return 29 + isLeap(year)
    else:
        return monthLen[month-1]

