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

log = logger.init()

import json
from os.path import join
from time import perf_counter
from typing import TYPE_CHECKING

from scal3.path import confDir
from scal3.s_object import objectDirName

from . import (
	events,  # noqa: F401
	large_scale,  # noqa: F401
	lifetime,  # noqa: F401
	monthly,  # noqa: F401
	note,  # noqa: F401
	notifiers,  # noqa: F401
	state,
	task,  # noqa: F401
	university,  # noqa: F401
	vcs,  # noqa: F401
	weekly,  # noqa: F401
	yearly,  # noqa: F401
)
from .accounts import Account, accountsDir
from .event_base import Event, eventsDir
from .group import EventGroup, groupsDir
from .groups_holder import EventGroupsHolder
from .handler import Handler
from .note import NoteBook
from .objects import iterObjectFiles
from .occur import JdOccurSet
from .occur_data import getDayOccurrenceData
from .register import classes
from .state import InfoWrapper, LastIdsWrapper
from .trash import EventTrash

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem

__all__ = [
	"Account",
	"Event",
	"EventGroup",
	"EventGroupsHolder",
	"EventTrash",
	"JdOccurSet",
	"NoteBook",
	"classes",
	"defaultGroupTypeIndex",
	"ev",
	"getDayOccurrenceData",
	"init",
	"removeUnusedObjects",
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

	state.info = InfoWrapper.s_load(0, fs=fs)
	state.lastIds = LastIdsWrapper.s_load(0, fs=fs)
	assert state.lastIds is not None
	state.lastIds.scan()


# ---------------------------------------------------------------------------


def removeUnusedObjects(fs: FileSystem) -> None:
	if state.allReadOnly:
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

	state.allReadOnly = True
	try:
		tm0 = perf_counter()
		do_removeUnusedObjects()
		log.info(f"removeUnusedObjects: took {perf_counter() - tm0}")
	finally:
		state.allReadOnly = False


# ---------------------------------------------------------------------------

ev = Handler()

assert classes.notifier
assert classes.group
assert classes.event
assert classes.rule

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
# 	conflict: Sequence[str] =("date",)


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
