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

from typing import TYPE_CHECKING, Any, Self

from scal3 import logger
from scal3.utils import toStr

from .occur import TimeListOccurSet
from .task import TaskEvent

log = logger.get()


from .event_base import Event
from .group import EventGroup

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.event_lib.pytypes import OccurSetType
	from scal3.filesystem import FileSystem

	from .pytypes import EventGroupType

__all__ = ["VcsBaseEventGroup", "VcsEpochBaseEvent", "VcsEpochBaseEventGroup"]


class VcsBaseEventGroup(EventGroup):
	acceptsEventTypes: Sequence[str] = ()
	myOptions: list[str] = [
		"vcsType",
		"vcsDir",
		"vcsBranch",
	]

	def __init__(self, ident: int | None = None) -> None:
		self.vcsType = "git"
		self.vcsDir = ""
		self.vcsBranch = "main"
		super().__init__(ident)

	def __str__(self) -> str:
		return (
			f"{self.__class__.__name__}(ident={self.id!r}, "
			f"title='{self.title}', vcsType={self.vcsType!r}, "
			f"vcsDir={self.vcsDir!r}, vcsBranch={self.vcsBranch!r})"
		)

	def setDefaults(self) -> None:
		self.eventTextSep = "\n"
		self.showInTimeLine = False

	def getRulesHash(self) -> int:
		return hash(
			str(
				(
					self.name,
					self.vcsType,
					self.vcsDir,
					self.vcsBranch,
				),
			),
		)  # FIXME

	# FIXME: remove
	# def __getitem__(self, key: str) -> EventType:
	# 	if key in classes.rule.names:
	# 		return EventGroup.__getitem__(self, key)
	# 	# len(commitId)==40 for git
	# 	return self.getEvent(key)

	def getVcsModule(self) -> Any:
		name = toStr(self.vcsType)
		# if not isinstance(name, str):
		# 	raise TypeError(f"getVcsModule({name!r}): bad type {type(name)}")
		try:
			mod = __import__("scal3.vcs_modules", fromlist=[name])
		except ImportError:
			log.exception("")
			return
		return getattr(mod, name)

	def updateVcsModuleObj(self) -> None:
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		mod.clearObj(self)
		if self.enable and self.vcsDir:
			try:
				mod.prepareObj(self)
			except Exception:
				log.exception("")

	def afterModify(self) -> None:
		self.updateVcsModuleObj()
		super().afterModify()

	def setDict(self, data: dict[str, Any]) -> None:
		super().setDict(data)
		self.updateVcsModuleObj()


class VcsEpochBaseEventGroup(VcsBaseEventGroup):
	myOptions = VcsBaseEventGroup.myOptions + ["showSeconds"]
	canConvertTo: list[str] = VcsBaseEventGroup.canConvertTo + ["taskList"]

	def __init__(self, ident: int | None = None) -> None:
		self.showSeconds = True
		self.vcsIds: list[int] = []
		super().__init__(ident)

	def clear(self) -> None:
		super().clear()
		self.vcsIds = []

	def addOccur(self, t0: float, t1: float, eid: int) -> None:
		super().addOccur(t0, t1, eid)
		self.vcsIds.append(eid)

	def getRulesHash(self) -> int:
		return hash(
			str(
				(
					self.name,
					self.vcsType,
					self.vcsDir,
					self.vcsBranch,
					self.showSeconds,
				),
			),
		)

	def deepConvertTo(self, newGroupType: str) -> EventGroupType:
		newGroup = self.copyAs(newGroupType)
		if newGroupType == "taskList":
			newGroup.enable = False  # to prevent per-event node update
			for vcsId in self.vcsIds:
				event = self.getEvent(vcsId)
				assert isinstance(event, VcsEpochBaseEvent), f"{event=}"
				assert event.epoch is not None
				newEvent = newGroup.create("task")
				assert isinstance(newEvent, TaskEvent), f"{newEvent=}"
				newEvent.changeCalType(event.calType)  # FIXME needed?
				newEvent.copyFromExact(event)
				newEvent.setStartEpoch(event.epoch)
				newEvent.setEndDuration(0, 1)
				newEvent.save()
				newGroup.append(newEvent)
			newGroup.enable = self.enable
		return newGroup


class VcsEpochBaseEvent(Event):
	readOnly = True
	params = Event.params + ["epoch"]
	epoch: int | None = None

	# FIXME
	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> Self:
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def save(self) -> None:
		pass

	def afterModify(self) -> None:
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		assert isinstance(self.parent, VcsEpochBaseEventGroup), f"{self.parent=}"
		epoch = self.epoch
		if epoch is not None and self.getEpochFromJd(
			startJd,
		) <= epoch < self.getEpochFromJd(endJd):
			if not self.parent.showSeconds:
				log.info("-------- showSeconds = False")
				epoch -= epoch % 60
			return TimeListOccurSet([epoch])
		return TimeListOccurSet()
