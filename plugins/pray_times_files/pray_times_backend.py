#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#--------------------- Copyright Block ----------------------
# 
# prayTimes.py: Prayer Times Calculator (ver 2.0b8)
# Copyright (C) 2007-2010 Hamid Zarrabi-Zadeh
# Copyright (C) 2011 Saeed Rasooli
# 
# Source: http:#praytimes.org
# License: GNU General Public License, version 3
# 
# Permission is granted to use self code, with or without 
# modification, in any website or application provided that 
# the following conditions are met:
# 
#    1. Credit is given to the original work with a 
#       link back to PrayTimes.org.
# 
#    2. Redistributions of the source code and its 
#       translations into other programming languages 
#       must retain the above copyright notice.
# 
# self program is distributed in the hope that it will 
# be useful, but WITHOUT ANY WARRANTY. 
# 
# PLEASE DO NOT REMOVE self COPYRIGHT BLOCK.


#--------------------- Help and Manual ----------------------
# 
# User's Manual: 
# http:#praytimes.org/manual
# 
# Calculation Formulas: 
# http:#praytimes.org/calculation
# 


#------------------------ User Interface -------------------------
# 
# 
#     getTimes (date, coordinates, timeZone [, dst [, timeFormat]]) 
#     
#     setMethod (method)       # set calculation method 
#     adjust (parameters)      # adjust calculation parameters    
#     tune (offsets)           # tune times by given offsets 
# 
#     getMethod ()             # get calculation method 
#     getSetting ()            # get current calculation parameters
#     getOffsets ()            # get current time offsets

#------------------------- Sample Usage --------------------------
# 
# 
#     PT = new PrayTimes('ISNA')
#     times = PT.getTimes(new Date(), [43, -80], -5)
#     document.write('Sunrise = '+ times.sunrise)

import time
import math
from math import floor

tr = str ## FIXME

timeNames = ('imsak', 'fajr', 'sunrise', 'dhuhr', 'asr', 'sunset', 'maghrib', 'isha', 'midnight')



ASR_STANDARD = 1
ASR_HANAFI = 2
## asr juristics:
##   standard => Shafi`i, Maliki, Ja`fari, Hanbali
##   hanafi => Hanafi ## used in which method? FIXME

MIDNIGHT_STANDARD, MIDNIGHT_JAFARI = range(2)
## midnight methods
##   standard => Mid Sunset to Sunrise
##   jafari => Mid Maghrib to Fajr

## Adjust Methods for Higher Latitudes
highLatMethods = (
    'NightMiddle', # middle of night
    'AngleBased',  # angle/60th of night
    'OneSeventh',  # 1/7th of night
    'None'         # No adjustment
)


# Time Formats
timeFormats = (
    '24h',         # 24-hour format
    '12h',         # 12-hour format
    '12hNS',       # 12-hour format with no suffix
    'Float'        # floating point number 
)

timeSuffixes = (tr('AM'), tr('PM'))
InvalidTime =  '-----'


class Method:
    def __init__(self, name, desc, fajr=15, isha=15, maghrib='0 min', midnight=MIDNIGHT_STANDARD):
        self.name = name
        self.desc = desc
        self.fajr = fajr
        self.isha = isha
        self.maghrib = maghrib
        self.midnight = midnight

methodsList = [
    Method('MWL', 'Muslim World League', fajr=18, isha=17),
    Method('ISNA', 'Islamic Society of North America', fajr=15, isha=15),
    Method('Egypt', 'Egyptian General Authority of Survey', fajr=19.5, isha=17.5),
    Method('Makkah', 'Umm Al-Qura University, Makkah', fajr=18.5, isha='90 min'),## fajr was 19 degrees before 1430 hijri
    Method('Karachi', 'University of Islamic Sciences, Karachi', fajr=18, isha=18),
    Method('Jafari', 'Shia Ithna-Ashari, Leva Research Institute, Qum', fajr=16, maghrib=4, isha=14, midnight=MIDNIGHT_JAFARI),
    Method('Tehran', 'Institute of Geophysics, University of Tehran', fajr=17.7, maghrib=4.5, midnight=MIDNIGHT_JAFARI),
]

methodsDict = dict([(m.name, m) for m in methodsList])

########################### Functions ####################################


isMin = lambda tm: isinstance(tm, basestring) and tm.endswith('min')
minEval = lambda tm: int(tm.split(' ')[0]) if isinstance(tm, basestring) else tm
isNaN = lambda var: not isinstance(var, (int, long, float))
dirSign = lambda direction: -1 if direction=='ccw' else 1

dtr = lambda d: (d * math.pi) / 180.0
rtd = lambda r: (r * 180.0) / math.pi

sin = lambda d: math.sin(dtr(d))
cos = lambda d: math.cos(dtr(d))
tan = lambda d: math.tan(dtr(d))

arcsin = lambda d: rtd(math.asin(d))## FIXME
arccos = lambda d: rtd(math.acos(d))
arctan = lambda d: rtd(math.atan(d))

arccot = lambda x: rtd(math.atan(1/x))
arctan2 = lambda y, x: rtd(math.atan2(y, x))

fixAngle = lambda a: fix(a, 360)
fixHour = lambda a: fix(a, 24)

def fix(a, b):
    a = a - b*floor(a/b)
    return a+b if a<0 else a

timeDiff = lambda time1, time2: fixHour(time2 - time1)
timesMiddle = lambda time1, time2: time1 + fixHour(time2 - time1)/2.0

# convert a calendar date to julian date
def julian(year, month, day):
    if month <= 2:
        year -= 1
        month += 12
    
    A = floor(year/100.0)
    B = 2 - A + floor(A/4.0)

    return floor(365.25 * (year+4716)) + floor(30.6001 * (month+1)) + day + B - 1524.5

################################ Classes ################################

class PrayTimes:
    numIterations = 1
    def __init__(self, lat, lng, elv=0, methodName='Tehran', imsak='10 min', asrMode=ASR_STANDARD,
                 highLats='NightMiddle', timeFormat='24h'):
        self.lat = lat
        self.lng = lng
        self.elv = elv
        self.method = methodsDict[methodName]
        self.imsak = imsak
        self.asrMode = asrMode
        self.highLats = highLats
        self.timeFormat = timeFormat

    # detect timezone and DST (daylight saving time) from system
    def detectTimeZone(self):
        import time
        if time.daylight and time.localtime(time.mktime((self.year, self.month, self.day, 0, 0, 0, 0, 0, -1))).tm_isdst:
            self.timeZone = -time.altzone/3600.0
        else:
            self.timeZone = -time.timezone/3600.0
        #print 'timeZone', self.timeZone

    # return prayer times for a given date
    def getTimes(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.detectTimeZone()
        self.jDate = julian(year, month, day) - self.lng/(15*24)
        return self.computeTimes()
    # convert float time to the given format (see timeFormats)
    def getFormattedTime(self, time):
        if isNaN(time):
            return InvalidTime
        if self.timeFormat == 'Float':
            return time
        else:
            time = fixHour(time+0.5/60) ## add 0.5 minutes to round
            hours = floor(time)
            minutes = floor((time-hours)*60)
            if self.timeFormat == '12h':
                return '%d:%.2d %s'%(
                    (hours-1)%12 + 1,
                    minutes,
                    timeSuffixes[hours<12]
                )
            else:## '24h'
                return '%d:%.2d'%(hours, minutes)
    
    # compute mid-day time
    def midDay(self, time):
        return fixHour(12-self.sunPosition(self.jDate+time)['equation'])


    # compute the time at which sun reaches a specific angle below horizon
    def sunAngleTime(self, angle, time, direction='cw'):
        decl = self.sunPosition(self.jDate+time)['declination']
        noon = self.midDay(time)
        ratio = (-sin(angle) - sin(decl)*sin(self.lat)) / (cos(decl)*cos(self.lat))
        ratio = min(max(ratio, -1.0), 1.0)
        #try:
        t = arccos(ratio) / 15.0
        #except:
        #    print 'sunAngleTime: angle=%s, time=%s, direction=%s ==> ratio=%s'%(angle, time, direction, ratio)
        #    return 0
        return noon + dirSign(direction)*t

    # compute asr time 
    def asrTime(self, factor, time):
        decl = self.sunPosition(self.jDate+time)['declination']
        angle = -arccot(factor+tan(abs(self.lat-decl)))
        return self.sunAngleTime(angle, time)


    # compute declination angle of sun and equation of time
    # Ref: http:#aa.usno.navy.mil/faq/docs/SunApprox.php
    def sunPosition(self, jd):
        D = jd - 2451545.0
        g = fixAngle(357.529 + 0.98560028*D)
        q = fixAngle(280.459 + 0.98564736*D)
        L = fixAngle(q + 1.915*sin(g) + 0.020*sin(2*g))

        R = 1.00014 - 0.01671*cos(g) - 0.00014*cos(2*g)
        e = 23.439 - 0.00000036*D

        RA = arctan2(cos(e)*sin(L), cos(L)) / 15
        eqt = q/15 - fixHour(RA)
        decl = arcsin(sin(e)*sin(L))

        return {'declination': decl, 'equation': eqt}

    #---------------------- Compute Prayer Times -----------------------


    # compute prayer times at given julian date
    def computePrayerTimes(self, times):
        times = self.dayPortion(times)
        
        times['imsak']   = self.sunAngleTime(minEval(self.imsak), times['imsak'], 'ccw')
        times['fajr']    = self.sunAngleTime(minEval(self.method.fajr), times['fajr'], 'ccw')
        times['sunrise'] = self.sunAngleTime(self.riseSetAngle(), times['sunrise'], 'ccw')
        times['dhuhr']   = self.midDay(times['dhuhr'])
        times['asr']     = self.asrTime(self.asrMode, times['asr'])
        times['sunset']  = self.sunAngleTime(self.riseSetAngle(), times['sunset'])
        times['maghrib'] = self.sunAngleTime(minEval(self.method.maghrib), times['maghrib'])
        times['isha']    = self.sunAngleTime(minEval(self.method.isha), times['isha'])

        return times

    # compute prayer times 
    def computeTimes(self):
        # default times
        times = {
            'imsak': 5,
            'fajr': 5,
            'sunrise': 6,
            'dhuhr': 12, 
            'asr': 13,
            'sunset': 18,
            'maghrib': 18,
            'isha': 18,
        }

        # main iterations
        for i in range(self.numIterations):
            times = self.computePrayerTimes(times)

        times = self.adjustTimes(times)
        
        # add midnight time
        if self.method.midnight == MIDNIGHT_JAFARI:
            ## middle(maghrib, fajr)  give incompatible times with http://calendar.ut.ac.ir/Fa/Prayers/IrCenters.asp
            ## middle(sunset, fajr)   is compatible (with max 1 minute different)
            times['midnight'] = timesMiddle(times['sunset'], times['fajr'])
        else:
            times['midnight'] = timesMiddle(times['sunset'], times['sunrise'])

        #times = self.tuneTimes(times) ## FIXME
        return self.modifyFormats(times)

    # adjust times 
    def adjustTimes(self, times):
        for key in times:
            times[key] += self.timeZone - self.lng/15.0
            
        if self.highLats != 'None':
            times = self.adjustHighLats(times)
            
        if isMin(self.imsak):
            times['imsak'] = times['fajr'] - minEval(self.imsak)/60.0
        if isMin(self.method.maghrib):
            times['maghrib'] = times['sunset'] + minEval(self.method.maghrib)/60.0
        if isMin(self.method.isha):
            times['isha'] = times['maghrib'] + minEval(self.method.isha)/60.0

        return times;


    # return sun angle for sunset/sunrise
    def riseSetAngle(self):
        #earthRad = 6371009 ## in meters
        #angle = arccos(earthRad/(earthRad+self.elv))
        angle = 0.0347 * math.sqrt(self.elv) ## an approximation
        return 0.833 + angle

    #def tuneTimes: ## FIXME
    
    # convert times to given time format
    def modifyFormats(self, times):
        for key in times:
            times[key] = self.getFormattedTime(times[key])
        return times

    # adjust times for locations in higher latitudes
    def adjustHighLats(self, times):
        nightTime = timeDiff(times['sunset'], times['sunrise'])

        times['imsak'] = self.adjustHLTime(times['imsak'], times['sunrise'], minEval(self.imsak), nightTime, 'ccw')
        times['fajr']  = self.adjustHLTime(times['fajr'], times['sunrise'], minEval(self.method.fajr), nightTime, 'ccw')
        times['isha']  = self.adjustHLTime(times['isha'], times['sunset'], minEval(self.method.isha), nightTime)
        times['maghrib'] = self.adjustHLTime(times['maghrib'], times['sunset'], minEval(self.method.maghrib), nightTime)
        
        return times;

    # adjust a time for higher latitudes
    def adjustHLTime(self, time, base, angle, night, direction='cw'):
        portion = self.nightPortion(angle, night)
        if direction == 'ccw':
            diff = timeDiff(time, base)
        else:
            diff = timeDiff(base, time)

        if isNaN(time) or diff > portion:
            time = base + dirSign(direction)*portion
        return time

    # the night portion used for adjusting times in higher latitudes
    def nightPortion(self, angle, night):
        portion = 0.5 ## MidNight
        if self.highLats == 'AngleBased':
            portion = angle/60.0
        if self.highLats == 'OneSeventh':
            portion = 1.0/7
        return portion*night;

    # convert hours to day portions 
    def dayPortion(self, times):
        for key in times:
            times[key] /= 24.0
        return times





