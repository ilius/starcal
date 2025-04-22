# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger

log = logger.get()

import os
import os.path
import typing
from contextlib import suppress
from os.path import isabs, isdir, isfile, join
from time import perf_counter
from typing import Any

from scal3 import core, event_lib, locale_man
from scal3.cal_types import calTypes
from scal3.event_notification_thread import EventNotificationManager
from scal3.event_tags import eventTags
from scal3.event_update_queue import EventUpdateQueue
from scal3.font import Font
from scal3.json_utils import (
	loadJsonConf,
	saveJsonConf,
)
from scal3.locale_man import tr as _
from scal3.path import confDir, pixDir, sourceDir, svgDir, sysConfDir
from scal3.ui.funcs import checkEnabledNamesItems
from scal3.ui.params import (
	CUSTOMIZE,
	LIVE,
	MAIN_CONF,
	NEED_RESTART,
	confParamsData,
	getParamNamesWithFlag,
)

from . import conf

if typing.TYPE_CHECKING:
	from scal3.s_object import SObj


__all__ = [
	"Font",
	"cells",
	"checkMainWinItems",
	"checkNeedRestart",
	"checkWinControllerButtons",
	"dayCalWin",
	"disableRedraw",
	"dragGetCalType",
	"duplicateGroupTitle",
	"eventAccounts",
	"eventGroups",
	"eventManDialog",
	"eventNotif",
	"eventSearchWin",
	"eventTags",
	"eventTrash",
	"eventUpdateQueue",
	"focusTime",
	"fontDefault",
	"getActiveMonthCalParams",
	"getEvent",
	"getFont",
	"init",
	"initFonts",
	"iterAllEvents",
	"labelMenuDelay",
	"lastLiveConfChangeTime",
	"mainWin",
	"monthRMenuNum",
	"moveEventToTrash",
	"ntpServers",
	"prefWindow",
	"saveConf",
	"saveConfCustomize",
	"saveLiveConf",
	"saveLiveConfDelay",
	"timeLineWin",
	"timeout_repeat",
	"updateFocusTime",
	"withFS",
	"yearWheelWin",
]
# -------------------------------------------------------

sysConfPath = join(sysConfDir, "ui.json")  # also includes LIVE config

confPath = join(confDir, "ui.json")

confPathCustomize = join(confDir, "ui-customize.json")

confPathLive = join(confDir, "ui-live.json")


confParams = getParamNamesWithFlag(MAIN_CONF)
confParamsLive = getParamNamesWithFlag(LIVE)
confParamsCustomize = getParamNamesWithFlag(CUSTOMIZE)
# print(f"confParams = {sorted(confParams)}")
# print(f"confParamsLive = {sorted(confParamsLive)}")
# print(f"confParamsCustomize = {sorted(confParamsCustomize)}")


fontParams = ["fontDefault"] + [p.v3Name for p in confParamsData if p.type == "Font"]

confDecoders = dict.fromkeys(fontParams, Font.fromList)
confEncoders = {
	# param: Font.to_json for param in fontParams
}


def loadConf() -> None:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return
	loadJsonConf(
		conf,
		sysConfPath,
		decoders=confDecoders,
	)
	loadJsonConf(
		conf,
		confPath,
		decoders=confDecoders,
	)
	loadJsonConf(
		conf,
		confPathCustomize,
		decoders=confDecoders,
	)
	loadJsonConf(
		conf,
		confPathLive,
		decoders=confDecoders,
	)
	if not isabs(conf.statusIconImage):
		conf.statusIconImage = join(sourceDir, conf.statusIconImage)
	if not isabs(conf.statusIconImageHoli):
		conf.statusIconImageHoli = join(sourceDir, conf.statusIconImageHoli)
	if not isfile(conf.statusIconImage):
		conf.statusIconImage = conf.statusIconImageDefault
	if not isfile(conf.statusIconImageHoli):
		conf.statusIconImageHoli = conf.statusIconImageHoliDefault

	conf.mcalCornerMenuTextColor = conf.mcalCornerMenuTextColor or conf.borderTextColor


def saveConf() -> None:
	saveJsonConf(
		conf,
		confPath,
		confParams,
		encoders=confEncoders,
	)


def saveConfCustomize() -> None:
	saveJsonConf(
		conf,
		confPathCustomize,
		confParamsCustomize,
		encoders=confEncoders,
	)


def saveLiveConf() -> None:  # rename to saveConfLive FIXME
	log.debug(f"saveLiveConf: {conf.winX=}, {conf.winY=}, {conf.winWidth=}")
	saveJsonConf(
		conf,
		confPathLive,
		confParamsLive,
		encoders=confEncoders,
	)


def saveLiveConfLoop() -> None:  # rename to saveConfLiveLoop FIXME
	tm = perf_counter()
	if tm - lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


def updateLocalTimezoneHistory() -> bool:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return False

	localTzName = str(locale_man.localTz)
	if not conf.localTzHist:
		conf.localTzHist.insert(0, localTzName)
		return True

	if conf.localTzHist[0] != localTzName:
		with suppress(ValueError):
			conf.localTzHist.remove(localTzName)
		conf.localTzHist.insert(0, localTzName)
		if len(conf.localTzHist) > 10:
			conf.localTzHist = conf.localTzHist[:10]
		return True

	return False


# -----------------------------------------------------------------------

# moved to cells.:
# getMonthPlus, changeDate, gotoJd, gotoJd, jdPlus, monthPlus, yearPlus


def getFont(
	scale=1.0,
	family=True,
	bold=False,
) -> tuple[str | None, bool, bool, float]:
	f = conf.fontCustom if conf.fontCustomEnable else fontDefaultInit
	return Font(
		family=f.family if family else None,
		bold=f.bold or bold,
		italic=f.italic,
		size=f.size * scale,
	)


def initFonts(fontDefaultNew: Font) -> None:
	global fontDefault
	fontDefault = fontDefaultNew
	if not conf.fontCustom:
		conf.fontCustom = fontDefault
	# --------
	# ---
	if conf.mcalTypeParams[0]["font"] is None:
		conf.mcalTypeParams[0]["font"] = getFont(1.0, family=False)
	# ---
	for item in conf.mcalTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(0.6, family=False)
	# ------
	if conf.dcalDayParams[0]["font"] is None:
		conf.dcalDayParams[0]["font"] = getFont(10.0, family=False)
	# ---
	for item in conf.dcalDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(3.0, family=False)
	# ------
	if conf.dcalMonthParams[0]["font"] is None:
		conf.dcalMonthParams[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in conf.dcalMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if conf.dcalWinDayParams[0]["font"] is None:
		conf.dcalWinDayParams[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in conf.dcalWinDayParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if conf.dcalWinMonthParams[0]["font"] is None:
		conf.dcalWinMonthParams[0]["font"] = getFont(2.5, family=False)
	# ---
	for item in conf.dcalWinMonthParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(1.5, family=False)
	# ------
	if conf.dcalWeekdayParams["font"] is None:
		conf.dcalWeekdayParams["font"] = getFont(1.0, family=False)
	if conf.dcalWinWeekdayParams["font"] is None:
		conf.dcalWinWeekdayParams["font"] = getFont(1.0, family=False)


# ----------------------------------------------------------------------


def checkNeedRestart() -> bool:
	for key in needRestartPref:
		if needRestartPref[key] != evalParam(key):
			log.info(
				f"checkNeedRestart: {key!r}, "
				f"{needRestartPref[key]!r}, {evalParam(key)!r}",
			)
			return True
	return False


def checkMainWinItems() -> None:
	conf.mainWinItems = checkEnabledNamesItems(
		conf.mainWinItems,
		conf.mainWinItemsDefault,
	)
	# TODO: make sure there are no duplicates, by removing duplicates


def checkWinControllerButtons() -> None:
	conf.winControllerButtons = checkEnabledNamesItems(
		conf.winControllerButtons,
		conf.winControllerButtonsDefault,
	)
	# "sep" button can have duplicates


# ----------------------------------------------------------------------


def moveEventToTrash(
	group: event_lib.EventGroup,
	event: event_lib.Event,
	sender,  # write BaseCalType based on BaseCalObj
	save: bool = True,
) -> int:
	eventIndex = group.remove(event)
	eventTrash.add(event)  # or append? FIXME
	if save:
		group.save()
		eventTrash.save()
	eventUpdateQueue.put("-", event, sender)
	return eventIndex


def getEvent(groupId: int, eventId: int) -> event_lib.Event:
	return eventGroups[groupId][eventId]


def duplicateGroupTitle(group: event_lib.EventGroup) -> None:
	title = group.title
	usedTitles = {g.title for g in eventGroups}
	parts = title.split("#")
	try:
		index = int(parts[-1])
		title = "#".join(parts[:-1])
	except (IndexError, ValueError):
		# log.exception("")
		index = 1

	def makeTitle(n: int) -> str:
		return title + "#" + _(n)

	newTitle, index = makeTitle(index), index + 1
	while newTitle in usedTitles:
		newTitle, index = makeTitle(index), index + 1

	group.title = newTitle


# ----------------------------------------------------------------------


def init() -> None:
	global fs, eventAccounts, eventGroups, eventTrash, eventNotif
	core.init()

	fs = core.fs
	event_lib.init(fs)
	# Load accounts, groups and trash? FIXME
	eventAccounts = event_lib.EventAccountsHolder.load(fs)
	eventGroups = event_lib.EventGroupsHolder.load(fs)
	eventTrash = event_lib.EventTrash.load(fs)
	eventNotif = EventNotificationManager(eventGroups)


def withFS(obj: SObj) -> SObj:
	obj.fs = fs
	return obj


# ----------------------------------------------------------------------


def getActiveMonthCalParams():
	return list(
		zip(
			calTypes.active,
			conf.mcalTypeParams,
			strict=False,
		),
	)


# --------------------------------

fs: event_lib.FileSystem | None = None
eventAccounts: list[event_lib.Account] = []
eventGroups: list[event_lib.EventGroup] = []
eventTrash: event_lib.EventTrash | None = None
eventNotif: EventNotificationManager | None = None


def iterAllEvents():  # dosen"t include orphan events
	for group in eventGroups:
		for event in group:
			yield event
	for event in eventTrash:
		yield event


eventUpdateQueue = EventUpdateQueue()

# -------------------
# BUILD CACHE AFTER SETTING calTypes.primary

cells = None  # FIXME: CellCacheType based on CellCache
# ---------------------------
# appLogo = join(pixDir, "starcal.png")
appLogo = join(svgDir, "starcal.svg")
appIcon = join(pixDir, "starcal-48.png")
# ---------------------------
# themeDir = join(sourceDir, "themes")
# theme = None

# _________________________ Options _________________________ #


# delay for shift up/down items of menu for right click on YearLabel
labelMenuDelay = 0.1

# --------------------
dragGetCalType = core.GREGORIAN  # apply in Pref FIXME
# dragGetDateFormat = "%Y/%m/%d"
dragRecMode = core.GREGORIAN  # apply in Pref FIXME
# --------------------
monthRMenuNum = True
# monthRMenu

_wmDir = join(svgDir, "wm")
winControllerThemeList = [
	name for name in os.listdir(_wmDir) if isdir(join(_wmDir, name))
]

# --------------------

fontDefault = Font(family="Sans", size=12)
fontDefaultInit = fontDefault

# ---------------------

ntpServers = (
	"pool.ntp.org",
	"ir.pool.ntp.org",
	"asia.pool.ntp.org",
	"europe.pool.ntp.org",
	"north-america.pool.ntp.org",
	"oceania.pool.ntp.org",
	"south-america.pool.ntp.org",
	"ntp.ubuntu.com",
)


# ---------------------

disableRedraw = False
# when set disableRedraw=True, widgets will not re-draw their contents

focusTime = 0
lastLiveConfChangeTime = 0


saveLiveConfDelay = 0.5  # seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime(*_args):
	global focusTime
	focusTime = perf_counter()


def evalParam(param: str) -> Any:
	parts = param.split(".")
	if not parts:
		raise ValueError(f"invalid {param = }")

	if len(parts) == 1:
		return getattr(conf, param)

	if parts[0] == "locale_man":
		value = locale_man
		parts = parts[1:]
	else:
		value = conf
	for part in parts:
		if isinstance(value, dict):
			value = value[part]
		else:
			value = getattr(value, part)

	return value


# --------------------------------------------------------

loadConf()

if updateLocalTimezoneHistory():
	saveConf()

needRestartPref = {
	name: evalParam(name) for name in getParamNamesWithFlag(NEED_RESTART)
}
needRestartPref.update(locale_man.getNeedRestartParams())

# ----------------------------------

# move to gtk_ud ? FIXME
mainWin = None
prefWindow = None
eventManDialog = None
eventSearchWin = None
timeLineWin = None
dayCalWin = None
yearWheelWin = None
weekCalWin = None
