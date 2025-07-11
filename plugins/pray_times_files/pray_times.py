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
from os.path import dirname, isdir, isfile, join
from time import time as now
from typing import Final

from scal3.cell_type import CellType
from scal3.option import Option

# _mypath = __file__
# if _mypath.endswith(".pyc"):
# 	_mypath = _mypath[:-1]
# dataDir = dirname(_mypath)
dataDir = dirname(__file__)
sourceDir = "/usr/share/starcal3"

sys.path.insert(0, dataDir)  # FIXME
sys.path.insert(0, sourceDir)  # FIXME

# from scal3 import event_lib  # needs core!! FIXME
from datetime import datetime
from threading import Timer

from pray_times_backend import PrayTimes, timeNames

# if "gtk" in sys.modules:
from pray_times_gtk import TextPluginUI, showDisclaimer

import mytz
from scal3 import logger
from scal3.cal_types import hijri
from scal3.cal_types.gregorian import to_jd as gregorian_to_jd

# DO NOT IMPORT core IN PLUGINS
from scal3.config_utils import loadModuleConfig, saveSingleConfig
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
	return datetime.now().toordinal() + 1721425


def readLocationData() -> list[tuple[str, str, float, float]]:
	locationsDir = join(sourceDir, "data", "locations")
	placeTransDict = {}

	def readTransFile(transPath: str) -> None:
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


def guessLocation(
	cityData: list[tuple[str, str, float, float]],  # noqa: ARG001
) -> tuple[str, float, float]:  # noqa: ARG001
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

	azanTimeNamesAll = (
		"fajr",
		"dhuhr",
		"asr",
		"maghrib",
		"isha",
	)

	def open_configure(self) -> None:
		TextPluginUI.open_configure(self)

	def open_about(self) -> bool:
		return TextPluginUI.open_about(self)

	def __init__(self, _file: str) -> None:
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
		self.locName = Option("")
		self.lat = Option(0)
		self.lng = Option(0)
		self.method = Option("")
		# ------
		self.imsak = Option(10)  # minutes before Fajr (Morning Azan)
		# self.asrMode = ASR_STANDARD
		# self.highLats = "NightMiddle"
		# self.timeFormat = "24h"
		self.shownTimeNames = Option(
			[
				"fajr",
				"sunrise",
				"dhuhr",
				"maghrib",
				"midnight",
			],
		)
		# FIXME rename shownTimeNames to activeTimeNames
		# 		or add another list azanSoundTimeNames
		self.sep = Option("     ")
		# --
		self.azanEnable = Option(False)
		self.azanFile = Option("")
		# --
		self.preAzanEnable = Option(False)
		self.preAzanFile = Option("")
		self.preAzanMinutes = Option(2.0)
		# --
		self.disclaimerLastEpoch = Option(0)
		# -------
		self.confOptions: Final[dict[str, Option]] = {
			"lat": self.lat,
			"lng": self.lng,
			"method": self.method,
			"locName": self.locName,
			"shownTimeNames": self.shownTimeNames,
			"imsak": self.imsak,
			"sep": self.sep,
			"azanEnable": self.azanEnable,
			"azanFile": self.azanFile,
			"preAzanEnable": self.preAzanEnable,
			"preAzanFile": self.preAzanFile,
			"preAzanMinutes": self.preAzanMinutes,
			"disclaimerLastEpoch": self.disclaimerLastEpoch,
		}
		# ----
		loadModuleConfig(
			confPath=self.confPath,
			sysConfPath=None,
			options=self.confOptions,
			decoders={},
		)
		# ----
		if not isfile(self.confPath):
			confNeedsSave = True
		# ----
		if not self.locName.v:
			confNeedsSave = True
			self.locName.v, self.lat.v, self.lng.v = self.guessLocation()
			self.method.v = "Tehran"
			# TODO: guess method from location
		# -------
		self.backend = PrayTimes(
			self.lat.v,
			self.lng.v,
			methodName=self.method.v,
			imsak=f"{self.imsak.v:d} min",
		)
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

	def getCityData(self) -> list[tuple[str, str, float, float]]:
		if self._cityData is not None:
			return self._cityData
		self._cityData = readLocationData()
		return self._cityData

	def guessLocation(self) -> tuple[str, float, float]:
		return guessLocation(self.getCityData())

	def checkShowDisclaimer(self) -> None:
		if not self.shouldShowDisclaimer():
			return
		showDisclaimer(self)
		self.disclaimerLastEpoch.v = int(now())
		self.saveConfig()

	def shouldShowDisclaimer(self) -> bool:
		if self.disclaimerLastEpoch.v <= 0:
			return True

		tm = now()
		dt = tm - self.disclaimerLastEpoch.v
		if dt > 256 * 86400:
			return True

		_hyear, hmonth, hday = hijri.jd_to(getCurrentJd())
		# is it Ramadan?
		return hmonth == 9 and dt > hday * 86400

	def saveConfig(self) -> None:
		self.lat.v = self.backend.lat
		self.lng.v = self.backend.lng
		self.method.v = self.backend.method.name
		saveSingleConfig(self.confPath, self.confOptions, {})

	# def date_change_after(self, widget, year, month, day):
	# 	self.dialog.menuCell.add(self.menuitem)
	# 	self.menu_unmap_id = self.dialog.menuCell.connect("unmap", self.menu_unmap)

	# def menu_unmap(self, menu):
	# 	menu.remove(self.menuitem)
	# 	menu.disconnect(self.menu_unmap_id)

	def get_times_jd(self, jd: int) -> list[tuple[str, int]]:
		times = self.backend.getTimesByJd(
			jd,
			getUtcOffsetByJd(jd, localTz) / 3600,
		)
		return [(name, times[name]) for name in self.shownTimeNames.v]

	@staticmethod
	def getFormattedTime(tm: float) -> str:  # tm is float hour
		try:
			h, m, _s = floatHourToTime(float(tm))
		except ValueError:
			log.exception(f"bad float hour {tm=}")
			return str(tm)
		else:
			return f"{h:d}:{m:02d}"

	def getTextByJd(self, jd: int) -> str:
		return self.sep.v.join(
			[
				_(timeDescByName[name]) + ": " + self.getFormattedTime(tm)
				for name, tm in self.get_times_jd(jd)
			],
		)

	def updateCell(self, c: CellType) -> None:
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
		if not self.azanEnable.v:
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
		self.proc = popenFile(self.azanFile.v)

	def doPlayPreAzan(self) -> None:
		# pass tm as argument?
		if not self.preAzanEnable.v:
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
		self.proc = popenFile(self.preAzanFile.v)

	def onCurrentDateChange(self, gdate: tuple[int, int, int]) -> None:
		log.debug(f"pray_times: onCurrentDateChange: {gdate}")
		if not self.enable:
			return
		jd = gregorian_to_jd(*gdate)
		# log.debug(
		# 	getUtcOffsetByJd(jd, localTz) / 3600,
		# 	getUtcOffsetCurrent() / 3600,
		# )
		# utcOffset = getUtcOffsetCurrent()
		utcOffset = getUtcOffsetByJd(jd, localTz)
		tmUtc = now()
		epochLocal = tmUtc + utcOffset
		secondsFromMidnight = epochLocal % 86400
		# midnightUtc = tmUtc - secondsFromMidnight
		# log.debug("------- hours from midnight", secondsFromMidnight/3600.0)
		for timeName, azanHour in self.backend.getTimesByJd(
			jd,
			utcOffset / 3600,
		).items():
			if timeName not in self.azanTimeNamesAll:
				continue
			if timeName not in self.shownTimeNames.v:
				continue
			azanSec = azanHour * 3600.0
			# -----
			toAzanSecs = int(azanSec - secondsFromMidnight)
			if toAzanSecs >= 0:
				preAzanSec = azanSec - self.preAzanMinutes.v * 60
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
