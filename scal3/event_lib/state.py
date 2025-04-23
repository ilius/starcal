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


from os.path import join, splitext
from time import perf_counter
from time import time as now

from scal3 import core

from .objects import EventObjTextModel

__all__ = ["InfoWrapper", "LastIdsWrapper", "allReadOnly", "info", "lastIds"]


class InfoWrapper(EventObjTextModel):
	file = join("event", "info.json")
	skipLoadNoFile = True
	params = (
		"version",
		"last_run",
	)
	paramsOrder = (
		"version",
		"last_run",
	)

	def __init__(self) -> None:
		self.version = ""
		self.last_run = 0

	def update(self) -> None:
		self.version = core.VERSION
		self.last_run = int(now())

	def updateAndSave(self) -> None:
		self.update()
		self.save()


class LastIdsWrapper(EventObjTextModel):
	skipLoadNoFile = True
	file = join("event", "last_ids.json")
	params = (
		"event",
		"group",
		"account",
	)
	paramsOrder = (
		"event",
		"group",
		"account",
	)

	def __init__(self) -> None:
		self.event = 0
		self.group = 0
		self.account = 0

	def __str__(self) -> str:
		return (
			f"LastIds(event={self.event}, group={self.group}, account={self.account})"
		)

	def scanDir(self, dpath: str) -> int:
		lastId = 0
		for fname in self.fs.listdir(dpath):
			idStr, ext = splitext(fname)
			if ext != ".json":
				continue
			try:
				id_ = int(idStr)
			except ValueError:
				log.error(f"invalid file name: {dpath}")
				continue
			lastId = max(id_, lastId)
		return lastId

	def scan(self) -> None:
		t0 = perf_counter()
		self.event = self.scanDir("event/events")
		self.group = self.scanDir("event/groups")
		self.account = self.scanDir("event/accounts")
		self.save()
		log.info(
			f"Scanning last_ids took {int((perf_counter() - t0) * 1000)} ms, {self}",
		)


info = None  # type: InfoWrapper
lastIds = None  # type: LastIdsWrappe
allReadOnly = False
