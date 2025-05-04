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


import json
import os
import sys
import time
from os.path import dirname, isdir, isfile, join
from time import time as now

# _mypath = __file__
# if _mypath.endswith(".pyc"):
# 	_mypath = _mypath[:-1]
# dataDir = dirname(_mypath)
dataDir = dirname(__file__)
sourceDir = "/usr/share/starcal3"

sys.path.insert(0, dataDir)  # FIXME
sys.path.insert(0, sourceDir)  # FIXME

# from scal3 import event_lib  # needs core!! FIXME
from threading import Timer

from pray_times_backend import PrayTimes, timeNames

# if "gtk" in sys.modules:
from pray_times_gtk import TextPluginUI, showDisclaimer

import mytz
from scal3 import logger
from scal3.cal_types import hijri
from scal3.cal_types.gregorian import to_jd as gregorian_to_jd

# DO NOT IMPORT core IN PLUGINS
from scal3.config_utils import loadModuleConfig, saveModuleConfig
from scal3.locale_man import langSh
from scal3.locale_man import tr as _
from scal3.os_utils import goodkill
from scal3.path import confDir
from scal3.plugin_man import BaseJsonPlugin
from scal3.time_utils import (
	floatHourToTime,
	getUtcOffsetByJd,
)
from scal3.ui_gtk import gtk
from scal3.ui_gtk.app_info import popenFile

log = logger.get()

# else:
# 	from pray_times_qt import *

# ----------------------------------------------------

localTz = mytz.gettz()

timeDescByName = dict(timeNames)

# --------------------- Functions and Classes ------------------


def getCurrentJd() -> int:
	y, m, d = time.localtime()[:3]
	return gregorian_to_jd(y, m, d)


def readLocationData():
	locationsDir = join(sourceDir, "data", "locations")
	placeTransDict = {}

	def readTransFile(transPath) -> None:
		if not isfile(transPath):
			return
		log.info(f"------------- reading {transPath}")
		with open(transPath, encoding="utf8") as fp:
			placeTransDict.update(json.load(fp))
		log.info(f"------------- {len(placeTransDict)=}")

	readTransFile(join(locationsDir, f"{langSh}.json"))

	for dirName in os.listdir(locationsDir):
		dirPath = join(locationsDir, dirName)
		if not isdir(dirPath):
			continue
		readTransFile(join(dirPath, f"{langSh}.json"))

	def translatePlaceName(name: str) -> str:
		nameTrans = placeTransDict.get(name)
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
	for line in lines:
		p = line.split("\t")
		if len(p) < 2:
			# log.debug(p)
			continue
		if p[0]:
			continue
		if p[1]:
			country = p[1]
			continue
		city, lat, lng = p[2:5]
		log.debug(f"{city=}")
		if len(p) < 5:
			log.debug(f"{country=}, {p=}")
			continue
		cityData.append(
			(
				country + "/" + city,
				translatePlaceName(country) + "/" + translatePlaceName(city),
				float(lat),
				float(lng),
			),
		)

	return cityData


def guessLocation(cityData):  # noqa: ARG001
	# tzname = str(localTz)
	# TODO
	# for countryCity, countryCityLocale, lat, lng in cityData:
	return "Tehran", 35.705, 51.4216


"""
event_classes = api.get("event_lib", "classes")
EventRule = api.get("event_lib", "EventRule")

@event_classes.rule.register
class PrayTimeEventRule(EventRule):
	plug = None # FIXME
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

	def __init__(self, _file) -> None:
		# log.debug("----------- praytime TextPlugin.__init__")
		# log.debug("From plugin: core.VERSION=%s" + api.get("core", "VERSION"))
		# log.debug("From plugin: core.aaa=%s" + api.get("core", "aaa"))
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = False
		self._cityData = None
		# --------------
		confNeedsSave = False
		# ------
		self.locName, self.lat, self.lng = "", 0, 0
		# method = ""
		# ------
		self.imsak = 10  # minutes before Fajr (Morning Azan)
		# self.asrMode = ASR_STANDARD
		# self.highLats = "NightMiddle"
		# self.timeFormat = "24h"
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
		# --
		self.azanEnable = False
		self.azanFile = None
		# --
		self.preAzanEnable = False
		self.preAzanFile = None
		self.preAzanMinutes = 2.0
		# --
		self.disclaimerLastEpoch = 0
		# ----
		loadModuleConfig(self)
		# ----
		if not isfile(self.confPath):
			confNeedsSave = True
		# ----
		if not self.locName:
			confNeedsSave = True
			self.locName, self.lat, self.lng = self.guessLocation()
			self.method = "Tehran"
			# TODO: guess method from location
		# -------
		self.backend = PrayTimes(
			self.lat,
			self.lng,
			methodName=self.method,
			imsak=f"{self.imsak:d} min",
		)
		# ----
		# -------
		# PrayTimeEventRule.plug = self
		# -------
		if confNeedsSave:
			self.saveConfig()
		# -------
		self.makeWidget()  # FIXME
		# self.onCurrentDateChange(localtime()[:3])
		# ---
		# self.doPlayPreAzan()
		# time.sleep(2)
		# self.doPlayAzan()  # for testing
		# ---
		self.checkShowDisclaimer()

	def getCityData(self):
		if self._cityData is not None:
			return self._cityData
		self._cityData = readLocationData()
		return self._cityData

	def guessLocation(self):
		return guessLocation(self.getCityData())

	def checkShowDisclaimer(self) -> None:
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

		_hyear, hmonth, hday = hijri.jd_to(getCurrentJd())
		# is it Ramadan?
		return hmonth == 9 and dt > hday * 24 * 3600

	def saveConfig(self) -> None:
		self.lat = self.backend.lat
		self.lng = self.backend.lng
		self.method = self.backend.method.name
		saveModuleConfig(self)

	# def date_change_after(self, widget, year, month, day):
	# 	self.dialog.menuCell.add(self.menuitem)
	# 	self.menu_unmap_id = self.dialog.menuCell.connect("unmap", self.menu_unmap)

	# def menu_unmap(self, menu):
	# 	menu.remove(self.menuitem)
	# 	menu.disconnect(self.menu_unmap_id)

	def get_times_jd(self, jd):
		times = self.backend.getTimesByJd(
			jd,
			getUtcOffsetByJd(jd, localTz) / 3600,
		)
		return [(name, times[name]) for name in self.shownTimeNames]

	@staticmethod
	def getFormattedTime(tm):  # tm is float hour
		try:
			h, m, _s = floatHourToTime(float(tm))
		except ValueError:
			return tm
		else:
			return f"{h:d}:{m:02d}"

	def getTextByJd(self, jd):
		return self.sep.join(
			[
				_(timeDescByName[name]) + ": " + self.getFormattedTime(tm)
				for name, tm in self.get_times_jd(jd)
			],
		)

	def updateCell(self, c) -> None:
		text = self.getTextByJd(c.jd)
		if text:
			c.addPluginText(self, text)

	def killPrevSound(self) -> None:
		try:
			p = self.proc
		except AttributeError:
			return
		if p is None:
			return

		log.info(f"pray_times: killing process {p.pid}")
		goodkill(p.pid, interval=0.01)
		# kill(p.pid, 15)
		# p.terminate()

	def doPlayAzan(self) -> None:
		# pass tm as argument?
		if not self.azanEnable:
			return
		# dt = tm - now()
		# log.debug(f"---------------------------- doPlayAzan, {dt=:.1f}")
		# if dt > 1:
		# 	Timer(
		# 		int(dt),
		# 		self.doPlayAzan,
		# 		#tm,
		# 	).start()
		# 	return
		self.killPrevSound()
		self.proc = popenFile(self.azanFile)

	def doPlayPreAzan(self) -> None:
		# pass tm as argument?
		if not self.preAzanEnable:
			return
		# dt = tm - now()
		# log.debug(f"---------------------------- doPlayPreAzan, {dt=:.1f}")
		# if dt > 1:
		# 	Timer(
		# 		int(dt),
		# 		self.doPlayPreAzan,
		# 		#tm,
		# 	).start()
		# 	return
		self.killPrevSound()
		self.proc = popenFile(self.preAzanFile)

	def onCurrentDateChange(self, gdate) -> None:
		log.debug(f"pray_times: onCurrentDateChange: {gdate}")
		if not self.enable:
			return
		jd = gregorian_to_jd(*tuple(gdate))
		# log.debug(
		# 	getUtcOffsetByJd(jd, localTz) / 3600,
		# 	getUtcOffsetCurrent() / 3600,
		# )
		# utcOffset = getUtcOffsetCurrent()
		utcOffset = getUtcOffsetByJd(jd, localTz)
		tmUtc = now()
		epochLocal = tmUtc + utcOffset
		secondsFromMidnight = epochLocal % (24 * 3600)
		# midnightUtc = tmUtc - secondsFromMidnight
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
			# -----
			toAzanSecs = int(azanSec - secondsFromMidnight)
			if toAzanSecs >= 0:
				preAzanSec = azanSec - self.preAzanMinutes * 60
				toPreAzanSec = max(0, int(preAzanSec - secondsFromMidnight))
				log.debug(f"{toPreAzanSec=:.1f}")
				Timer(
					toPreAzanSec,
					self.doPlayPreAzan,
					# midnightUtc + preAzanSec,
				).start()
				# ---
				log.debug(f"{toAzanSecs=:.1f}")
				Timer(
					toAzanSecs,
					self.doPlayAzan,
					# midnightUtc + azanSec,
				).start()


if __name__ == "__main__":
	# from scal3 import core
	# from scal3.locale_man import rtl
	# if rtl:
	# 	gtk.widget_set_default_direction(gtk.TextDirection.RTL)
	from pray_times_gtk import LocationDialog

	dialog = LocationDialog(readLocationData())
	dialog.connect("delete-event", gtk.main_quit)
	# dialog.connect("response", gtk.main_quit)
	dialog.resize(600, 600)
	result = dialog.run()
	log.info(f"{result}")
	# gtk.main()
