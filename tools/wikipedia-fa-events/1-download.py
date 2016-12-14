#!/usr/bin/env python3

import sys, os, subprocess
from os.path import join, isfile

sys.path.append('/usr/share/starcal2')

from scal3 import core
from scal3.locale_man import tr as _

rawUrlBase = 'http://fa.wikipedia.org/w/index.php?title=%s_%s&action=raw'
saveDir = 'wikipedia-fa-events'

#skipExisingFiles = True

jalaliMonthLen = (31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 30)
jalaliMonthName = ('Farvardin','Ordibehesht','Khordad','Teer','Mordad','Shahrivar',
			 'Mehr','Aban','Azar','Dey','Bahman','Esfand')


for month in range(1, 13):
	for day in range(1, jalaliMonthLen[month-1]+1):
		direc = join(saveDir, str(month))
		fpath = join(direc, str(day))
		#if skipExisingFiles and isfile(fpath):
		#	continue
		try:
			os.makedirs(direc)
		except:
			pass
		url = rawUrlBase%(_(day), _(jalaliMonthName[month-1]))
		subprocess.call(['wget', '-c', url, '-O', fpath])








