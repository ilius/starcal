#
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

import json
from os.path import join
from time import perf_counter

from scal3.cal_types import (
	GREGORIAN,
	calTypes,
	convert,
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.core import (
	getAbsWeekNumberFromJd,
	jd_to_primary,
)
from scal3.date_utils import (
	checkDate,
	dateDecode,
	dateEncode,
	getJdRangeForMonth,
	jwday,
)
from scal3.dict_utils import makeOrderedData
from scal3.event_lib.objects import iterObjectFiles
from scal3.filesystem import DefaultFileSystem, FileSystem
from scal3.interval_utils import (
	intersectionOfTwoIntervalList,
	simplifyNumList,
)
from scal3.locale_man import getMonthName, textNumEncode
from scal3.locale_man import tr as _
from scal3.path import confDir, pixDir, svgDir
from scal3.s_object import (
	SObj,
	SObjBinaryModel,
	SObjTextModel,
	objectDirName,
)
from scal3.time_utils import (
	HMS,
	durationDecode,
	durationEncode,
	getEpochFromJd,
	getEpochFromJhms,
	getFloatJdFromEpoch,
	getJdFromEpoch,
	getJdListFromEpochRange,
	getJhmsFromEpoch,
	getSecondsFromHms,
	hmDecode,
	hmEncode,
	jsonTimeFromEpoch,
	roundEpochToDay,
	simpleTimeEncode,
	timeDecode,
	timeEncode,
	timeToFloatHour,
)
from scal3.utils import (
	findNearestIndex,
	iceil,
	ifloor,
	numRangesEncode,
	s_join,
	toStr,
)

from . import (
	events,  # noqa: F401
	state,
	vcs,  # noqa: F401
)
from .accounts import Account, accountsDir
from .accounts_holder import EventAccountsHolder
from .event_base import Event, eventsDir
from .groups import EventGroup, LargeScaleGroup, NoteBook, groupsDir
from .groups_holder import EventGroupsHolder
from .icon import WithIcon
from .occur import JdOccurSet
from .occur_data import getDayOccurrenceData, getWeekOccurrenceData
from .register import classes
from .state import InfoWrapper, LastIdsWrapper
from .trash import EventTrash

__all__ = [
	"GREGORIAN",
	"HMS",
	"Account",
	"DefaultFileSystem",
	"Event",
	"EventAccountsHolder",
	"EventGroup",
	"EventGroupsHolder",
	"EventTrash",
	"JdOccurSet",
	"LargeScaleGroup",
	"NoteBook",
	"SObj",
	"SObjBinaryModel",
	"SObjTextModel",
	"WithIcon",
	"_",
	"allReadOnly",
	"calTypes",
	"checkDate",
	"classes",
	"convert",
	"dateDecode",
	"dateEncode",
	"defaultGroupTypeIndex",
	"durationDecode",
	"durationEncode",
	"findNearestIndex",
	"getAbsWeekNumberFromJd",
	"getDayOccurrenceData",
	"getEpochFromJd",
	"getEpochFromJhms",
	"getFloatJdFromEpoch",
	"getJdFromEpoch",
	"getJdListFromEpochRange",
	"getJdRangeForMonth",
	"getJhmsFromEpoch",
	"getMonthName",
	"getSecondsFromHms",
	"getSysDate",
	"getWeekOccurrenceData",
	"hmDecode",
	"hmEncode",
	"iceil",
	"ifloor",
	"init",
	"intersectionOfTwoIntervalList",
	"jd_to",
	"jd_to_primary",
	"jsonTimeFromEpoch",
	"jwday",
	"makeOrderedData",
	"numRangesEncode",
	"pixDir",
	"removeUnusedObjects",
	"roundEpochToDay",
	"s_join",
	"simpleTimeEncode",
	"simplifyNumList",
	"svgDir",
	"textNumEncode",
	"timeDecode",
	"timeEncode",
	"timeToFloatHour",
	"toStr",
	"to_jd",
]

# --------------------------


lockPath = join(confDir, "event", "lock.json")

# ---------------------------------------------------


def init(fs: FileSystem) -> None:
	fs.makeDir(objectDirName)
	fs.makeDir(eventsDir)
	fs.makeDir(groupsDir)
	fs.makeDir(accountsDir)

	from scal3.lockfile import checkAndSaveJsonLockFile

	state.allReadOnly = checkAndSaveJsonLockFile(lockPath)
	if state.allReadOnly:
		log.info(f"Event lock file {lockPath} exists, EVENT DATA IS READ-ONLY")

	state.info = InfoWrapper.load(fs)
	state.lastIds = LastIdsWrapper.load(fs)
	state.lastIds.scan()


# ---------------------------------------------------------------------------


def removeUnusedObjects(fs: FileSystem) -> None:
	global allReadOnly
	if allReadOnly:
		raise RuntimeError("removeUnusedObjects: EVENTS ARE READ-ONLY")

	def do_removeUnusedObjects() -> None:
		hashSet = set()
		for cls in (Account, EventTrash, EventGroup, Event):
			for fpath in cls.iterFiles(fs):
				with fs.open(fpath) as fp:
					jsonStr = fp.read()
				data = json.loads(jsonStr)
				history = data.get("history")
				if not history:
					log.error(f"No history in file: {fpath}")
					continue
				hashSet.update({revHash for _revTime, revHash in history})

		log.info(f"Found {len(hashSet)} used objects")
		removedCount = 0
		for _hash, fpath in iterObjectFiles(fs):
			if _hash not in hashSet:
				log.debug(f"Removing file: {fpath}")
				removedCount += 1
				fs.removeFile(fpath)
		log.info(f"Removed {removedCount} objects")

	allReadOnly = True
	try:
		tm0 = perf_counter()
		do_removeUnusedObjects()
		log.info(f"removeUnusedObjects: took {perf_counter() - tm0}")
	finally:
		allReadOnly = False


# ---------------------------------------------------------------------------


defaultGroupTypeIndex = 0  # FIXME

__plugin_api_get__ = [
	"classes",
	"defaultGroupTypeIndex",
	"EventRule",
	"EventNotifier",
	"Event",
	"EventGroup",
	"Account",
]


# ---------------------------------------------------------------------------


# TODO
# @classes.rule.register
# class HolidayEventRule(EventRule):
# 	name = "holiday"
# 	desc = _("Holiday")
# 	conflict = ("date",)


# TODO
# @classes.rule.register
# class ShowInMCalEventRule(EventRule):
# 	name = "show_cal"
# 	desc = _("Show in Calendar")

# TODO
# @classes.rule.register
# class SunTimeRule(EventRule):
# ... minutes before Sun Rise      eval("sunRise-x")
# ... minutes after Sun Rise       eval("sunRise+x")
# ... minutes before Sun Set       eval("sunSet-x")
# ... minutes after Sun Set        eval("sunSet+x")

# ---------------------------------------------------------------------------
