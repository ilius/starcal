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
from scal3.cell_type import DummyCellCache

log = logger.get()

import os
import typing
from contextlib import suppress
from os.path import isabs, isdir, isfile, join
from time import perf_counter
from typing import Any

from scal3 import core, event_lib, locale_man
from scal3.cal_types import calTypes
from scal3.color_utils import ColorType
from scal3.config_utils import (
	loadSingleConfig,
	saveSingleConfig,
)
from scal3.event_lib import ev
from scal3.event_lib.accounts_holder import EventAccountsHolder
from scal3.event_lib.event_base import Event
from scal3.event_lib.groups_holder import EventGroupsHolder
from scal3.event_notification_thread import EventNotificationManager
from scal3.event_tags import eventTags
from scal3.event_update_queue import EventUpdateQueue
from scal3.filesystem import FileSystem
from scal3.font import Font
from scal3.locale_man import tr as _
from scal3.option import Option
from scal3.path import confDir, pixDir, sourceDir, svgDir, sysConfDir
from scal3.s_object import SObj
from scal3.ui import conf
from scal3.ui.conf import (
	confOptions,
	confOptionsCustomize,
	confOptionsLive,
)
from scal3.ui.funcs import checkEnabledNamesItems
from scal3.ui.options import (
	CUSTOMIZE,
	LIVE,
	MAIN_CONF,
	NEED_RESTART,
	confOptionsData,
	getParamNamesWithFlag,
)

if typing.TYPE_CHECKING:
	from collections.abc import Callable, Iterable

	from scal3.cell_type import CellCacheType
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.ui.pytypes import CalTypeOptionsDict
	from scal3.ui_gtk.gtk_ud import CalObjType
	from scal3.ui_gtk.starcal import MainWin


__all__ = [
	"CUSTOMIZE",
	"LIVE",
	"MAIN_CONF",
	"NEED_RESTART",
	"ColorType",
	"Event",
	"EventAccountsHolder",
	"EventGroupsHolder",
	"EventNotificationManager",
	"FileSystem",
	"Font",
	"Option",
	"SObj",
	"cells",
	"checkMainWinItems",
	"checkNeedRestart",
	"checkWinControllerButtons",
	"dayCalWin",
	"disableRedraw",
	"dragGetCalType",
	"duplicateGroupTitle",
	"ev",
	"eventManDialog",
	"eventSearchWin",
	"eventTags",
	"eventUpdateQueue",
	"focusTime",
	"fontDefault",
	"getActiveMonthCalOptions",
	"getEvent",
	"getFont",
	"getParamNamesWithFlag",
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
	"yearWheelWin",
]
# -------------------------------------------------------

sysConfPath = join(sysConfDir, "ui.json")  # also includes LIVE config

confPath = join(confDir, "ui.json")

confPathCustomize = join(confDir, "ui-customize.json")

confPathLive = join(confDir, "ui-live.json")

fontOptions = ["fontDefault"] + [
	p.v3Name for p in confOptionsData if p.type.startswith("Font")
]

confDecoders: dict[str, Callable[[Any], Any]] = dict.fromkeys(
	fontOptions, Font.fromList
)
confEncoders: dict[str, Callable[[Any], Any]] = {
	# param: Font.to_json for param in fontOptions
}


def loadConf() -> None:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return
	loadSingleConfig(
		sysConfPath,
		confOptions,
		decoders=confDecoders,
	)
	loadSingleConfig(
		confPath,
		confOptions,
		decoders=confDecoders,
	)
	loadSingleConfig(
		confPathCustomize,
		confOptionsCustomize,
		decoders=confDecoders,
	)
	loadSingleConfig(
		confPathLive,
		confOptionsLive,
		decoders=confDecoders,
	)
	if not isabs(conf.statusIconImage.v):
		conf.statusIconImage.v = join(sourceDir, conf.statusIconImage.v)
	if not isabs(conf.statusIconImageHoli.v):
		conf.statusIconImageHoli.v = join(sourceDir, conf.statusIconImageHoli.v)
	if not isfile(conf.statusIconImage.v):
		conf.statusIconImage.v = conf.statusIconImage.default
	if not isfile(conf.statusIconImageHoli.v):
		conf.statusIconImageHoli.v = conf.statusIconImageHoli.default

	conf.mcalCornerMenuTextColor.v = (
		conf.mcalCornerMenuTextColor.v or conf.borderTextColor.v
	)


def saveConf() -> None:
	saveSingleConfig(
		confPath,
		confOptions,
		encoders=confEncoders,
	)


def saveConfCustomize() -> None:
	saveSingleConfig(
		confPathCustomize,
		confOptionsCustomize,
		encoders=confEncoders,
	)


def saveLiveConf() -> None:  # rename to saveConfLive FIXME
	# log.debug(f"saveLiveConf: {conf.winX.v=}, {conf.winY.v=}, {conf.winWidth.v=}")
	saveSingleConfig(
		confPathLive,
		confOptionsLive,
		encoders=confEncoders,
	)


def saveLiveConfLoop() -> bool:  # rename to saveConfLiveLoop FIXME
	tm = perf_counter()
	if tm - lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


def updateLocalTimezoneHistory() -> bool:
	if os.getenv("STARCAL_NO_LOAD_CONFIG"):
		return False

	localTzName = str(locale_man.localTz)
	hist = conf.localTzHist.v
	if not hist:
		hist.insert(0, localTzName)
		return True

	if hist[0] != localTzName:
		with suppress(ValueError):
			hist.remove(localTzName)
		hist.insert(0, localTzName)
		if len(hist) > 10:
			conf.localTzHist.v = hist[:10]
		return True

	return False


# -----------------------------------------------------------------------

# moved to cells.:
# getMonthPlus, changeDate, gotoJd, gotoJd, jdPlus, monthPlus, yearPlus


def getFont(
	scale: float = 1.0,
	family: bool = True,
	bold: bool = False,
) -> Font:
	f = (conf.fontCustom.v if conf.fontCustomEnable.v else None) or fontDefaultInit
	# assert isinstance(f.family, str), f"{f.family=}"
	return Font(
		family=f.family if family else None,
		bold=f.bold or bold,
		italic=f.italic,
		size=f.size * scale,
	)


def initFonts(fontDefaultNew: Font) -> None:
	global fontDefault
	fontDefault = fontDefaultNew
	if not conf.fontCustom.v:
		conf.fontCustom.v = fontDefault.copy()
	# --------
	# ---
	if conf.mcalTypeParams.v[0]["font"] is None:
		conf.mcalTypeParams.v[0]["font"] = getFont(1.0, family=False)
	# ---
	for item in conf.mcalTypeParams.v[1:]:
		if item["font"] is None:
			item["font"] = getFont(0.6, family=False)
	# ------
	if conf.dcalDayParams.v[0]["font"] is None:
		conf.dcalDayParams.v[0]["font"] = getFont(10.0, family=False)
	# ---
	for item in conf.dcalDayParams.v[1:]:
		if item["font"] is None:
			item["font"] = getFont(3.0, family=False)
	# ------
	if conf.dcalMonthParams.v[0]["font"] is None:
		conf.dcalMonthParams.v[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in conf.dcalMonthParams.v[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if conf.dcalWinDayParams.v[0]["font"] is None:
		conf.dcalWinDayParams.v[0]["font"] = getFont(5.0, family=False)
	# ---
	for item in conf.dcalWinDayParams.v[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, family=False)
	# ------
	if conf.dcalWinMonthParams.v[0]["font"] is None:
		conf.dcalWinMonthParams.v[0]["font"] = getFont(2.5, family=False)
	# ---
	for item in conf.dcalWinMonthParams.v[1:]:
		if item["font"] is None:
			item["font"] = getFont(1.5, family=False)
	# ------
	if conf.dcalWeekdayParams.v["font"] is None:
		conf.dcalWeekdayParams.v["font"] = getFont(1.0, family=False)
	if conf.dcalWinWeekdayParams.v["font"] is None:
		conf.dcalWinWeekdayParams.v["font"] = getFont(1.0, family=False)


# ----------------------------------------------------------------------


def checkNeedRestart() -> bool:
	return any(opt.v != value for opt, value in needRestartList)


def checkMainWinItems() -> None:
	conf.mainWinItems.v = checkEnabledNamesItems(
		conf.mainWinItems.v,
		conf.mainWinItems.default,
	)
	# TODO: make sure there are no duplicates, by removing duplicates


def checkWinControllerButtons() -> None:
	conf.winControllerButtons.v = checkEnabledNamesItems(
		conf.winControllerButtons.v,
		conf.winControllerButtons.default,
	)
	# "sep" button can have duplicates


# ----------------------------------------------------------------------


def moveEventToTrash(
	group: EventGroupType,
	event: EventType,
	sender: CalObjType,
	save: bool = True,
) -> int:
	eventIndex = group.remove(event)
	ev.trash.add(event)  # or append? FIXME
	if save:
		group.save()
		ev.trash.save()
	eventUpdateQueue.put("-", event, sender)
	return eventIndex


def getEvent(groupId: int, eventId: int) -> EventType:
	return ev.groups[groupId][eventId]


def duplicateGroupTitle(group: EventGroupType) -> None:
	title = group.title
	usedTitles = {g.title for g in ev.groups}
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
	core.init()
	fs = core.fs
	event_lib.init(fs)  # must come before ev.init
	ev.init(fs)  # must come after event_lib.init


# ----------------------------------------------------------------------


def getActiveMonthCalOptions() -> list[tuple[int, CalTypeOptionsDict]]:
	return list(
		zip(
			calTypes.active,
			conf.mcalTypeParams.v,
			strict=False,
		),
	)


# --------------------------------


def iterAllEvents() -> Iterable[EventType]:
	# dosen"t include orphan events
	for group in ev.groups:
		for event in group:
			yield event
	for event in ev.trash:
		yield event


eventUpdateQueue = EventUpdateQueue()

# -------------------
# BUILD CACHE AFTER SETTING calTypes.primary

cells: CellCacheType = DummyCellCache()
# ---------------------------
# appLogo = join(pixDir, "starcal.png")
appLogo = join(svgDir, "starcal.svg")
appIcon = join(pixDir, "starcal-48.png")
# ---------------------------

uiName = ""

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

fontDefault: Font = Font(family="Sans", size=12)
fontDefaultInit: Font = fontDefault

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

focusTime: float = 0.0
lastLiveConfChangeTime = 0.0


saveLiveConfDelay = 0.5  # seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime() -> None:
	global focusTime
	focusTime = perf_counter()


# --------------------------------------------------------

loadConf()

if updateLocalTimezoneHistory():
	saveConf()


needRestartList: list[tuple[Option[Any], Any]] = [
	(opt, opt.v) for opt in conf.needRestartList + locale_man.getNeedRestartOptions()
]

# ----------------------------------

# move to gtk_ud ? FIXME
mainWin: MainWin = None  # type: ignore[assignment]
prefWindow: Any = None
eventManDialog: Any = None
eventSearchWin: Any = None
timeLineWin: Any = None
dayCalWin: Any = None
yearWheelWin: Any = None
weekCalWin: Any = None
