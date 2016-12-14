# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux


import sys, os, gettext

import time
from time import localtime
from time import time as now

from os.path import join, isfile, dirname


#_mypath = __file__
#if _mypath.endswith('.pyc'):
#	_mypath = _mypath[:-1]
#dataDir = dirname(_mypath)
dataDir = dirname(__file__)
rootDir = '/usr/share/starcal3'

sys.path.insert(0, dataDir)## FIXME
sys.path.insert(0, rootDir)## FIXME

from natz.local import get_localzone

from scal3 import plugin_api as api

from scal3.path import *
from pray_times_backend import PrayTimes

## DO NOT IMPORT core IN PLUGINS
from scal3.json_utils import *
from scal3.time_utils import floatHourToTime
from scal3.locale_man import tr as _
from scal3.cal_types.gregorian import to_jd as gregorian_to_jd
from scal3.time_utils import getUtcOffsetByJd, getUtcOffsetCurrent, getEpochFromJd
from scal3.os_utils import kill, goodkill
from scal3.utils import myRaise
#from scal3 import event_lib## needs core!! FIXME

from threading import Timer

#if 'gtk' in sys.modules:
from pray_times_gtk import *
#else:
#	from pray_times_qt import *

####################################################

localTz = get_localzone()


####################### Methods and Classes ##################

def readLocationData():
	lines = open(dataDir+'/locations.txt').read().split('\n')
	cityData = []
	country = ''
	for l in lines:
		p = l.split('\t')
		if len(p)<2:
			#print(p)
			continue
		if p[0]=='':
			if p[1]=='':
				city, lat, lng = p[2:5]
				#if country=='Iran':
				#	print(city)
				if len(p)>4:
					cityData.append((
						country + '/' + city,
						_(country) + '/' + _(city),
						float(lat),
						float(lng)
					))
				else:
					print(country, p)
			else:
				country = p[1]
	return cityData

def guessLocation(cityData):
	tzname = str(localTz)
	## FIXME
	#for countryCity, countryCityLocale, lat, lng in cityData:
	return 'Tehran', 35.705, 51.4216


'''
event_classes = api.get('event_lib', 'classes')
EventRule = api.get('event_lib', 'EventRule')

@event_classes.rule.register
class PrayTimeEventRule(EventRule):
	plug = None ## FIXME
	name = 'prayTime'
	desc = _('Pray Time')
	provide = ('time',)
	need = ()
	conflict = ('dayTimeRange', 'cycleLen',)
	def __init__(self, parent):
		EventRule.__init__(self, parent)
	def calcOccurrence(self, startEpoch, endEpoch, event):
		self.plug.get_times_jd(jd)
	getInfo = lambda self: self.desc
'''

class TextPlugin(BaseJsonPlugin, TextPluginUI):
	name = 'pray_times'
	## all options (except for "enable" and "show_date") will be saved in file confPath
	confPath = join(confDir, 'pray_times.json')
	confParams = (
		'lat',
		'lng',
		'method',
		'locName',
		'shownTimeNames',
		'imsak',
		'sep',
		'azanEnable',
		'azanFile',
		'preAzanEnable',
		'preAzanFile',
		'preAzanMinutes',
	)
	azanTimeNamesAll = (
		'fajr',
		'dhuhr',
		'asr',
		'maghrib',
		'isha',
	)
	def __init__(self, _file):
		#print('----------- praytime TextPlugin.__init__')
		#print('From plugin: core.VERSION=%s'%api.get('core', 'VERSION'))
		#print('From plugin: core.aaa=%s'%api.get('core', 'aaa'))
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = False
		self.cityData = readLocationData()
		##############
		confNeedsSave = False
		######
		self.locName, self.lat, self.lng = '', 0, 0
		method = ''
		#######
		self.imsak = 10 ## minutes before Fajr (Morning Azan)
		#self.asrMode=ASR_STANDARD
		#self.highLats='NightMiddle'
		#self.timeFormat='24h'
		self.shownTimeNames = (
			'fajr',
			'sunrise',
			'dhuhr',
			'maghrib',
			'midnight',
		)
		## FIXME rename shownTimeNames to activeTimeNames
		## or add another list azanSoundTimeNames
		self.sep = '     '
		##
		self.azanEnable = False
		self.azanFile = None
		##
		self.preAzanEnable = False
		self.preAzanFile = None
		self.preAzanMinutes = 2.0
		####
		loadModuleJsonConf(self)
		####
		if not isfile(self.confPath):
			confNeedsSave = True
		####
		if not self.locName:
			confNeedsSave = True
			self.locName, self.lat, self.lng = guessLocation(self.cityData)
			self.method = 'Tehran'
			## guess method from location FIXME
		#######
		self.backend = PrayTimes(
			self.lat,
			self.lng,
			methodName=self.method,
			imsak='%d min'%self.imsak,
		)
		####
		#######
		#PrayTimeEventRule.plug = self
		#######
		if confNeedsSave:
			self.saveConfig()
		#######
		self.makeWidget()## FIXME
		#self.onCurrentDateChange(localtime()[:3])
		###
		#self.doPlayPreAzan()
		#time.sleep(2)
		#self.doPlayAzan() ## for testing ## FIXME
	def saveConfig(self):
		self.lat = self.backend.lat
		self.lng = self.backend.lng
		self.method = self.backend.method.name
		saveModuleJsonConf(self)
	#def date_change_after(self, widget, year, month, day):
	#	self.dialog.menuCell.add(self.menuitem)
	#	self.menu_unmap_id = self.dialog.menuCell.connect('unmap', self.menu_unmap)
	#def menu_unmap(self, menu):
	#	menu.remove(self.menuitem)
	#	menu.disconnect(self.menu_unmap_id)
	def get_times_jd(self, jd):
		times = self.backend.getTimesByJd(
			jd,
			getUtcOffsetByJd(jd)/3600.0,
		)
		return [(name, times[name]) for name in self.shownTimeNames]
	def getFormattedTime(self, tm):## tm is float hour
		try:
			h, m, s = floatHourToTime(float(tm))
		except ValueError:
			return tm
		else:
			return '%d:%.2d'%(h, m)
	def get_text_jd(self, jd):
		return self.sep.join([
			'%s: %s'%(_(name.capitalize()), self.getFormattedTime(tm))
			for name, tm in self.get_times_jd(jd)
		])
	def get_text(self, year, month, day):## just for compatibity (usage by external programs)
		return self.get_text_jd(gregorian_to_jd(year, month, day))
	def update_cell(self, c):
		text = self.get_text_jd(c.jd)
		if text!='':
			if c.pluginsText!='':
				c.pluginsText += '\n'
			c.pluginsText += text
	def killPrevSound(self):
		try:
			p = self.proc
		except AttributeError:
			pass
		else:
			print('killing %s'%p.pid)
			goodkill(p.pid, interval=0.01)
			#kill(p.pid, 15)
			#p.terminate()
	def doPlayAzan(self):## , tm
		if not self.azanEnable:
			return
		#dt = tm - now()
		#print('---------------------------- doPlayAzan, dt=%.1f'%dt)
		#if dt > 1:
		#	Timer(
		#		int(dt),
		#		self.doPlayAzan,
		#		#tm,
		#	).start()
		#	return
		self.killPrevSound()
		self.proc = popenFile(self.azanFile)
	def doPlayPreAzan(self):## , tm
		if not self.preAzanEnable:
			return
		#dt = tm - now()
		#print('---------------------------- doPlayPreAzan, dt=%.1f'%dt)
		#if dt > 1:
		#	Timer(
		#		int(dt),
		#		self.doPlayPreAzan,
		#		#tm,
		#	).start()
		#	return
		self.killPrevSound()
		self.proc = popenFile(self.preAzanFile)
	def onCurrentDateChange(self, gdate):
		print('praytimes: onCurrentDateChange', gdate)
		if not self.enable:
			return
		jd = gregorian_to_jd(*tuple(gdate))
		#print(getUtcOffsetByJd(jd)/3600.0, getUtcOffsetCurrent()/3600.0)
		#utcOffset = getUtcOffsetCurrent()
		utcOffset = getUtcOffsetByJd(jd)
		tmUtc = now()
		epochLocal = tmUtc + utcOffset
		secondsFromMidnight = epochLocal % (24*3600)
		midnightUtc = tmUtc - secondsFromMidnight
		#print('------- hours from midnight', secondsFromMidnight/3600.0)
		for timeName, azanHour in self.backend.getTimesByJd(
			jd,
			utcOffset/3600.0,
		).items():
			if timeName not in self.azanTimeNamesAll:
				continue
			if timeName not in self.shownTimeNames:
				continue
			azanSec = azanHour * 3600.0
			#####
			toAzanSecs = int(azanSec - secondsFromMidnight)
			if toAzanSecs >= 0:
				preAzanSec = azanSec - self.preAzanMinutes * 60
				toPreAzanSec = max(
					0,
					int(preAzanSec - secondsFromMidnight)
				)
				print('toPreAzanSec=%.1f'%toPreAzanSec)
				Timer(
					toPreAzanSec,
					self.doPlayPreAzan,
					#midnightUtc + preAzanSec,
				).start()
				###
				print('toAzanSecs=%.1f'%toAzanSecs)
				Timer(
					toAzanSecs,
					self.doPlayAzan,
					#midnightUtc + azanSec,
				).start()



if __name__=='__main__':
	#from scal3 import core
	#from scal3.locale_man import rtl
	#if rtl:
	#	gtk.widget_set_default_direction(gtk.TextDirection.RTL)
	dialog = LocationDialog(readLocationData())
	dialog.connect('delete-event', gtk.main_quit)
	#dialog.connect('response', gtk.main_quit)
	dialog.resize(600, 600)
	print(dialog.run())
	#gtk.main()




