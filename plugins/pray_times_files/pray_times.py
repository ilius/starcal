#!/usr/bin/env python3
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


import sys
import os
import gettext

import time
from time import localtime
from time import time as now

from os.path import join, isfile, isdir, dirname


#_mypath = __file__
#if _mypath.endswith(".pyc"):
#	_mypath = _mypath[:-1]
#dataDir = dirname(_mypath)
dataDir = dirname(__file__)
sourceDir = "/usr/share/starcal3"

sys.path.insert(0, dataDir)## FIXME
sys.path.insert(0, sourceDir)## FIXME

import natz

from scal3 import plugin_api as api

from scal3.path import *
from pray_times_backend import PrayTimes

# DO NOT IMPORT core IN PLUGINS
from scal3.json_utils import *
from scal3.time_utils import floatHourToTime
from scal3.locale_man import tr as _
from scal3.locale_man import langSh
from scal3.cal_types.gregorian import to_jd as gregorian_to_jd
from scal3.cal_types import hijri
from scal3.time_utils import (
	getUtcOffsetByJd,
	getUtcOffsetCurrent,
	getEpochFromJd,
)
from scal3.os_utils import kill, goodkill
#from scal3 import event_lib## needs core!! FIXME

from threading import Timer

#if "gtk" in sys.modules:
from pray_times_gtk import *
#else:
#	from pray_times_qt import *

####################################################

localTz = natz.gettz()

# ##################### Functions and Classes ##################


def getCurrentJd() -> int:
	y, m, d = time.localtime()[:3]
	return gregorian_to_jd(y, m, d)



def readLocationData():
	locationsDir = join(sourceDir, "data", "locations")
	cityTransDict = {}
	for dirName in os.listdir(locationsDir):
		dirPath = join(locationsDir, dirName)
		if not isdir(dirPath):
			continue
		transPath = join(dirPath, f"{langSh}.json")
		if isfile(transPath):
			log.info(f"------------- reading {transPath}")
			with open(transPath, encoding="utf8") as fp:
				cityTransDict.update(json.load(fp))

	def translateCityName(name: str) -> str:
		nameTrans = cityTransDict.get(name)
		if nameTrans:
			return nameTrans
		return _(name)

	fpath = join(locationsDir, "world.txt.bz2")
	log.info(f"------------- reading {fpath}")
	import bz2
	with bz2.open(fpath, mode="rt", encoding="utf8") as fp:
		lines = fp.read().split("\n")
	cityData = []
	country = ""
	for l in lines:
		p = l.split("\t")
		if len(p) < 2:
			# log.debug(p)
			continue
		if p[0] == "":
			if p[1] == "":
				city, lat, lng = p[2:5]
				log.debug(f"city={city}")
				if len(p) > 4:
					cityData.append((
						country + "/" + city,
						_(country) + "/" + translateCityName(city),
						float(lat),
						float(lng)
					))
				else:
					log.debug(f"country={country}, p={p}")
			else:
				country = p[1]
	return cityData


def guessLocation(cityData):
	tzname = str(localTz)
	# TODO
	#for countryCity, countryCityLocale, lat, lng in cityData:
	return "Tehran", 35.705, 51.4216


"""
event_classes = api.get("event_lib", "classes")
EventRule = api.get("event_lib", "EventRule")

@event_classes.rule.register
class PrayTimeEventRule(EventRule):
	plug = None ## FIXME
	name = "prayTime"
	desc = _("Pray Time")
	provide = ("time",)
	need = ()
	conflict = ("dayTimeRange", "cycleLen",)
	def __init__(self, parent):
		EventRule.__init__(self, parent)
	def calcOccurrence(self, startEpoch, endEpoch, event):
		self.plug.get_times_jd(jd)
	getInfo = lambda self: self.desc
"""


class TextPlugin(BaseJsonPlugin, TextPluginUI):
	name = "pray_times"
	# all options (except for "enable" and "show_date") will be
	# saved in file confPath
	confPath = join(confDir, "pray_times.json")
	confParams = (
		"lat",
		"lng",
		"method",
		"locName",
		"shownTimeNames",
		"imsak",
		"sep",
		"azanEnable",
		"azanFile",
		"preAzanEnable",
		"preAzanFile",
		"preAzanMinutes",
		"disclaimerLastEpoch",
	)
	azanTimeNamesAll = (
		"fajr",
		"dhuhr",
		"asr",
		"maghrib",
		"isha",
	)

	def __init__(self, _file):
		# log.debug("----------- praytime TextPlugin.__init__")
		# log.debug("From plugin: core.VERSION=%s" + api.get("core", "VERSION"))
		# log.debug("From plugin: core.aaa=%s" + api.get("core", "aaa"))
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = False
		self._cityData = None
		##############
		confNeedsSave = False
		######
		self.locName, self.lat, self.lng = "", 0, 0
		method = ""
		#######
		self.imsak = 10 ## minutes before Fajr (Morning Azan)
		#self.asrMode=ASR_STANDARD
		#self.highLats="NightMiddle"
		#self.timeFormat="24h"
		self.shownTimeNames = (
			"fajr",
			"sunrise",
			"dhuhr",
			"maghrib",
			"midnight",
		)
		# FIXME rename shownTimeNames to activeTimeNames
		# 		or add another list azanSoundTimeNames
		self.sep = "     "
		##
		self.azanEnable = False
		self.azanFile = None
		##
		self.preAzanEnable = False
		self.preAzanFile = None
		self.preAzanMinutes = 2.0
		##
		self.disclaimerLastEpoch = 0
		####
		loadModuleJsonConf(self)
		####
		if not isfile(self.confPath):
			confNeedsSave = True
		####
		if not self.locName:
			confNeedsSave = True
			self.locName, self.lat, self.lng = self.guessLocation()
			self.method = "Tehran"
			# TODO: guess method from location
		#######
		self.backend = PrayTimes(
			self.lat,
			self.lng,
			methodName=self.method,
			imsak=f"{self.imsak:d} min",
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
		###
		self.checkShowDisclaimer()

	def getCityData(self):
		if self._cityData is not None:
			return self._cityData
		self._cityData = readLocationData()
		return self._cityData

	def guessLocation(self):
		return guessLocation(self.getCityData())

	def checkShowDisclaimer(self):
		if not self.shouldShowDisclaimer():
			return
		showDisclaimer(self)
		self.disclaimerLastEpoch = int(now())
		self.saveConfig()

	def shouldShowDisclaimer(self) -> bool:
		if self.disclaimerLastEpoch <= 0:
			return True

		tm = now()
		dt = tm - self.disclaimerLastEpoch
		if dt > 256 * 24 * 3600:
			return True

		hyear, hmonth, hday = hijri.jd_to(getCurrentJd())
		if hmonth == 9: # Ramadan
			if dt > hday * 24 * 3600:
				return True

		return False

	def saveConfig(self):
		self.lat = self.backend.lat
		self.lng = self.backend.lng
		self.method = self.backend.method.name
		saveModuleJsonConf(self)

	#def date_change_after(self, widget, year, month, day):
	#	self.dialog.menuCell.add(self.menuitem)
	#	self.menu_unmap_id = self.dialog.menuCell.connect("unmap", self.menu_unmap)

	#def menu_unmap(self, menu):
	#	menu.remove(self.menuitem)
	#	menu.disconnect(self.menu_unmap_id)

	def get_times_jd(self, jd):
		times = self.backend.getTimesByJd(
			jd,
			getUtcOffsetByJd(jd, localTz) / 3600,
		)
		return [
			(name, times[name])
			for name in self.shownTimeNames
		]

	def getFormattedTime(self, tm):## tm is float hour
		try:
			h, m, s = floatHourToTime(float(tm))
		except ValueError:
			return tm
		else:
			return f"{h:d}:{m:02d}"

	def getTextByJd(self, jd):
		return self.sep.join([
			_(name.capitalize()) +
			": " +
			self.getFormattedTime(tm)
			for name, tm in self.get_times_jd(jd)
		])

	def updateCell(self, c):
		text = self.getTextByJd(c.jd)
		if text:
			c.addPluginText(text)

	def killPrevSound(self):
		try:
			p = self.proc
		except AttributeError:
			pass
		else:
			log.info(f"pray_times: killing process {p.pid}")
			goodkill(p.pid, interval=0.01)
			#kill(p.pid, 15)
			#p.terminate()

	def doPlayAzan(self):## , tm
		if not self.azanEnable:
			return
		#dt = tm - now()
		# log.debug(f"---------------------------- doPlayAzan, dt={dt:.1f}")
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
		# log.debug(f"---------------------------- doPlayPreAzan, dt={dt:.1f}")
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
		log.debug(f"pray_times: onCurrentDateChange: {gdate}")
		if not self.enable:
			return
		jd = gregorian_to_jd(*tuple(gdate))
		# log.debug(
		#	getUtcOffsetByJd(jd, localTz) / 3600,
		#	getUtcOffsetCurrent() / 3600,
		#)
		#utcOffset = getUtcOffsetCurrent()
		utcOffset = getUtcOffsetByJd(jd, localTz)
		tmUtc = now()
		epochLocal = tmUtc + utcOffset
		secondsFromMidnight = epochLocal % (24 * 3600)
		midnightUtc = tmUtc - secondsFromMidnight
		# log.debug("------- hours from midnight", secondsFromMidnight/3600.0)
		for timeName, azanHour in self.backend.getTimesByJd(
			jd,
			utcOffset / 3600,
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
				log.debug(f"toPreAzanSec={toPreAzanSec:.1f}")
				Timer(
					toPreAzanSec,
					self.doPlayPreAzan,
					#midnightUtc + preAzanSec,
				).start()
				###
				log.debug(f"toAzanSecs={toAzanSecs:.1f}")
				Timer(
					toAzanSecs,
					self.doPlayAzan,
					#midnightUtc + azanSec,
				).start()


if __name__ == "__main__":
	#from scal3 import core
	#from scal3.locale_man import rtl
	#if rtl:
	#	gtk.widget_set_default_direction(gtk.TextDirection.RTL)
	dialog = LocationDialog(readLocationData())
	dialog.connect("delete-event", gtk.main_quit)
	#dialog.connect("response", gtk.main_quit)
	dialog.resize(600, 600)
	result = dialog.run()
	log.info("{result}")
	#gtk.main()
