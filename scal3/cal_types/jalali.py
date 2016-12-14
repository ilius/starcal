# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
# Copyright (C) 2001 Roozbeh Pournader <roozbeh@sharif.edu>
# Copyright (C) 2001 Mohammad Toossi <mohammad@bamdad.org>
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

#		('','','','','','',
#		 '','','','','','')


getMonthName = lambda m, y=None: monthNameVars[monthNameMode][0][m-1]

def getMonthNameAb(m, y=None):
	v = monthNameVars[monthNameMode]
	try:
		l = v[1]
	except IndexError:
		l = v[0]
	return l[m-1]



getMonthsInYear = lambda y: 12


epoch = 1948321
minMonthLen = 29
maxMonthLen = 31
avgYearLen = 365.2425 ## FIXME

GREGORIAN_EPOCH = 1721426
monthLen = (31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30)

monthLenSum = [0]
for i in range(12):
	monthLenSum.append(monthLenSum[-1] + monthLen[i])

#print(monthLenSum)
## monthLenSum[i] == sum(monthLen[:i])

import os
from bisect import bisect_left

from scal3.path import sysConfDir, confDir
from scal3.utils import iceil
from scal3.utils import myRaise
from scal3.json_utils import *

## Here load user options(jalaliAlg) from file
sysConfPath = '%s/%s.json'%(sysConfDir, name)
loadJsonConf(__name__, sysConfPath)


confPath = '%s/%s.json'%(confDir, name)
loadJsonConf(__name__, confPath)



def save():## Here save user options to file
	saveJsonConf(__name__, confPath, (
		'monthNameMode',
		'jalaliAlg',
	))


def isLeap(year):
	"isLeap: Is a given year a leap year in the Jalali calendar ?"
	if jalaliAlg==1:## 2820-years
		return (( (year - 473 - (year>0)) % 2820) * 682) % 2816 < 682
	elif jalaliAlg==0:## 33-years
		jy = year - 979
		gdays = ( 365*jy + (jy//33)*8 + (jy%33+3)//4 + 79 ) % 146097
		## 36525 = 365*100 + 100//4
		if gdays >= 36525:
			gdays = (gdays-1) % 36524 + 1
			if gdays < 366:
				return False
		if gdays % 1461 >= 366:
			return False
		return True

	else:
		raise RuntimeError('bad option jalaliAlg=%s'%jalaliAlg)

def getMonthDayFromYdays(yday):
	month = bisect_left(monthLenSum, yday)
	day = yday - monthLenSum[month - 1]
	return month, day

def to_jd(year, month, day):
	"TO_JD: Determine Julian day from Jalali date"
	if jalaliAlg==1:## 2820-years
		epbase = year - 474 if year>=0 else 473
		epyear = 474 + epbase % 2820
		return day + \
			(month-1) * 30 + min(6, month-1) + \
			(epyear * 682 - 110) // 2816 + \
			(epyear - 1) * 365 + \
			epbase // 2820 * 1029983 + \
			epoch - 1
	elif jalaliAlg==0:## 33-years
		y2 = year - 979
		jdays = 365*y2 + y2//33 * 8 + (y2%33+3)//4 + monthLenSum[month-1] + (day-1)
		return jdays + 584101 + GREGORIAN_EPOCH
	else:
		raise RuntimeError('bad option jalaliAlg=%s'%jalaliAlg)

def jd_to(jd):
	"JD_TO_JALALI: Calculate Jalali date from Julian day"
	if jalaliAlg==1:## 2820-years
		cycle, cyear = divmod(jd - to_jd(475, 1, 1), 1029983)
		if cyear == 1029982 :
			ycycle = 2820
		else:
			aux1, aux2 = divmod(cyear, 366)
			ycycle = (2134*aux1 + 2816*aux2 + 2815) // 1028522 + aux1 + 1
		year = 2820*cycle + ycycle + 474
		if year <= 0 :
			year -= 1
		yday = jd - to_jd(year, 1, 1) + 1
		month, day = getMonthDayFromYdays(yday)
	elif jalaliAlg==0:## 33-years
		jdays = int(jd - GREGORIAN_EPOCH - 584101)
		## -(1600*365 + 1600//4 - 1600//100 + 1600//400) + 365    -79 +1== -584101
		#print('jdays =',jdays)
		j_np = jdays // 12053
		jdays %= 12053
		year = 979 + 33*j_np + 4*(jdays//1461)
		jdays %= 1461
		if jdays >= 366:
			year += (jdays-1) // 365
			jdays = (jdays-1) % 365
		yday = jdays+1
		month, day = getMonthDayFromYdays(yday)
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

