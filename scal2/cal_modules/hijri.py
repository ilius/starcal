# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

## Islamic (Hijri) calendar: http://en.wikipedia.org/wiki/Islamic_calendar

name = 'hijri'
desc = 'Hijri(Islamic)'
origLang = 'ar'

monthName = ('Muharram','Safar','Rabia\' 1','Rabia\' 2','Jumada 1','Jumada 2',
             'Rajab','Sha\'aban','Ramadan','Shawwal','Dhu\'l Qidah','Dhu\'l Hijjah')

monthNameAb = ('Moh', 'Saf', 'Rb1', 'Rb2', 'Jm1', 'Jm2',
               'Raj', 'Shb', 'Ram', 'Shw', 'DhQ', 'DhH')

getMonthName = lambda m, y=None: monthName.__getitem__(m-1)
getMonthNameAb = lambda m, y=None: monthNameAb.__getitem__(m-1)

getMonthsInYear = lambda y: 12

from math import floor, ceil
ifloor = lambda x: int(floor(x))

epoch = 1948439.5

hijriAlg = 0
hijriUseDB = True



#('hijriAlg', list, 'Hijri Calculation Algorithm',
#('Internal', 'ITL (idate command)', 'ITL (idate command) Umm_Alqura')),
options = (
('hijriUseDB',bool,'Use (Iranian) database for Hijri months length'),
)


minMonthLen = 29
maxMonthLen = 30

hijriDbInitH = (1426,2,1) ; hijriDbInitJD = 2453441 ## load from file
hijriDbEndJD = hijriDbInitJD = 0 ## load from file
hijriMonthLen = {} ## load and calc from file

import os
from scal_mod_paths import sysConfDir, confDir, modDir

## Here load user options (hijriUseDB) from file
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

def save():## Here save user options (hijriUseDB) to file
    file(confPath, 'w').write('hijriAlg=%s\nhijriUseDB=%s'%(hijriAlg, hijriUseDB))


#if cal.hijriAlg>0:#???????????
#    out = os.popen('idate').read()
#    if out=='':
#        print('''Command "idate" not found! (make sure to install package "itools")
#Using default(internal) Hijri algorithm...''')
#        cal.hijriAlg = 0


#global hijriDbInitH, hijriMonthLen, hijriDbEndJD, hijriDbInitJD
dbPath = '%s/hijri.db'%modDir
if os.path.isfile(dbPath):
    hijriMonthLenY = {}
    lines = file(dbPath).read().splitlines()
    for line in lines[1:]:
        if line!='' and not line.startswith('#'):
            parts = [int(p) for p in line.split(' ')]
            hijriMonthLenY[parts[0]] = parts[1:]
    parts = [int(p) for p in lines[0].split(' ')]
    hijriDbInitH = parts[:3]
    hijriDbEndJD = hijriDbInitJD = parts[3]
    for y in hijriMonthLenY.keys():
        lst = hijriMonthLenY[y]
        for m in xrange(len(lst)):
            ml = lst[m]
            if ml!=0:
                hijriMonthLen[y*12+m] = ml
                hijriDbEndJD += ml
    ## hijriDbEndJD += 29 ## FIXME


is_leap = lambda year: (((year * 11) + 14) % 30) < 11

def to_jd_c(year, month, day):
    return ifloor(
        day + ceil(29.5 * (month - 1)) + \
        (year - 1) * 354               + \
        floor((3 + (11 * year)) / 30)  + \
        epoch,
    )

def to_jd(year, month, day):
    #assert 1 <= month <= 12
    #assert 1 <= day <= maxMonthLen
    if hijriUseDB:## and hijriAlg==0
        ym = year*12 + month-1
        (y0, m0, d0) = hijriDbInitH
        ym0 = y0*12 + m0-1
        if not ym in hijriMonthLen.keys():
            return to_jd_c(year, month, day)
        jd = hijriDbInitJD
        for ymi in range(ym0, ym):
            jd += hijriMonthLen[ymi]
        return jd + day - 1
    else:
        return to_jd_c(year, month, day)


"""def jd_to_hijri_idate(jd, umm_alqura=False):
    import os, gregorian
    (y, m, d) = gregorian.jd_to(jd)
    fixed = str(y).zfill(4) + str(m).zfill(2) + str(d).zfill(2)
    cmd = 'idate --gregorian %s'%fixed
    if umm_alqura:
        cmd += ' --umm_alqura'
    output = os.popen(cmd).read()
    (hd, hm, hy) = output.split('\n')[3].split(':')[1].split('/')
    hy = hy.split(' ')[0]
    return (ifloor(hy), ifloor(hm), ifloor(hd))"""

## def hijri_to_jd_idate(jd, umm_alqura=False):



def jd_to(jd):
    assert type(jd)==int
    #if hijriAlg==1:
    #    return jd_to_hijri_idate(jd, umm_alqura=False)
    #elif hijriAlg==2:
    #    return jd_to_hijri_idate(jd, umm_alqura=True)
    ## Now hijriAlg==0
    if hijriUseDB:
        #jd = ifloor(jd)
        if hijriDbEndJD >= jd >= hijriDbInitJD:
            #(yi, mi, di) = hijriDbInitH
            #ymi = yi*12 + mi
            (y, m, d) = hijriDbInitH
            ym = y*12 + m-1
            while jd > hijriDbInitJD:
                monthLen = hijriMonthLen[ym]
                if jd-monthLen > hijriDbInitJD:
                    ym += 1
                    jd -= monthLen
                elif d+jd-hijriDbInitJD > monthLen:
                    ym += 1
                    d = d + jd - hijriDbInitJD - monthLen
                    jd = hijriDbInitJD
                else:
                    d = d + jd - hijriDbInitJD
                    jd = hijriDbInitJD
            (y, m) = divmod(ym, 12)
            m += 1
            return (y, m, d)
    ##jd = floor(jd) + 0.5
    year = ifloor(((30 * (jd - epoch)) + 10646) / 10631)
    month = int(min(12, ceil((jd - (29 + to_jd(year, 1, 1))) / 29.5) + 1))
    day = int(jd - to_jd(year, month, 1)) + 1
    return year, month, day


def getMonthLen(y, m):
    """
    if hijriUseDB:## and hijriAlg==0
        try:
            return hijriMonthLen[y*12+m]
        except KeyError:
            pass
    """
    if m==12:
        return to_jd(y+1, 1, 1) - to_jd(y, 12, 1)
    else:
        return to_jd(y, m+1, 1) - to_jd(y, m, 1)


if __name__=='__main__':
    for ym in hijriMonthLen.keys():
        (y, m) = divmod(ym, 12)
        m += 1
        print to_jd(y, m, 1) - to_jd_c(y, m, 1)
        

