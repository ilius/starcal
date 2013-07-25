# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# Using libkal code
#        The 'libkal' library for date conversion:
#        Copyright (C) 1996-1998 Petr Tomasek <tomasek@etf.cuni.cz>
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

name = 'julian'
desc = 'Julian'
origLang = 'en'

from math import floor
ifloor = lambda x: int(floor(x))

monthName = ('January','February','March','April','May','June',
             'July','August','September','October','November','December')

monthNameAb = ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')

getMonthName = lambda m, y=None: monthName.__getitem__(m-1)
getMonthNameAb = lambda m, y=None: monthNameAb.__getitem__(m-1)

getMonthsInYear = lambda y: 12

epoch = 1721058
minMonthLen = 28
maxMonthLen = 32
avgYearLen = 365.2425 ## FIXME

options = ()

def save():
    pass

def kal_s(m, p):
 if m==13:
     return 365
 else:
     t = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
     ## (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)
     #m = (m-1)%12 + 1 ## for stability reasons
     b = t[m-1]
     if m<3:
         b -= p
     return b

def to_jd(y, m, d):
    p1, p2 = divmod(y, 4)
    return ifloor(d + kal_s(m, int(p2==0)) + 1461*p1 + 365*p2 + epoch)

def jd_to(jd):
    ##wjd = ifloor(jd - 0.5) + 1
    p1, q1 = divmod(jd-epoch, 1461)
    #if q1==0:## ??????????????????
    #    return (4*p1, 1, 1)
    #else:
    if True:
        p2, q2 = divmod(q1-1, 365)
        y = 4*p1 + p2;
        q = int(y%4==0)
        m = 1;
        while m<12 and q2+1 > kal_s(m+1, q):
            m += 1
        d = q2 + 1 - kal_s(m, q)
        return (y, m, d)

def getMonthLen(y, m):
    if m==12:
        return to_jd(y+1, 1, 1) - to_jd(y, 12, 1)
    else:
        return to_jd(y, m+1, 1) - to_jd(y, m, 1)



