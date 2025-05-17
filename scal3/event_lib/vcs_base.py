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

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.event_lib.occur import OccurSet, TimeListOccurSet
from scal3.event_lib.register import classes
from scal3.utils import toStr

log = logger.get()


from .event_base import Event
from .groups import EventGroup

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem


class VcsBaseEventGroup(EventGroup):
	acceptsEventTypes = ()
	myParams = (
		"vcsType",
		"vcsDir",
		"vcsBranch",
	)

	def __init__(self, ident: str | None = None) -> None:
		self.vcsType = "git"
		self.vcsDir = ""
		self.vcsBranch = "main"
		EventGroup.__init__(self, ident)

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

	def __getitem__(self, key: str) -> Event:
		if key in classes.rule.names:
			return EventGroup.__getitem__(self, key)
		# len(commitId)==40 for git
		return self.getEvent(key)

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
		EventGroup.afterModify(self)

	def setData(self, data: dict[str, Any]) -> None:
		EventGroup.setData(self, data)
		self.updateVcsModuleObj()


class VcsEpochBaseEventGroup(VcsBaseEventGroup):
	myParams = VcsBaseEventGroup.myParams + ("showSeconds",)
	canConvertTo = VcsBaseEventGroup.canConvertTo + ("taskList",)

	def __init__(self, ident: str | None = None) -> None:
		self.showSeconds = True
		self.vcsIds = []
		VcsBaseEventGroup.__init__(self, ident)

	def clear(self) -> None:
		EventGroup.clear(self)
		self.vcsIds = []

	def addOccur(self, t0: float, t1: float, eid: int) -> None:
		EventGroup.addOccur(self, t0, t1, eid)
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

	def deepConvertTo(self, newGroupType: str) -> EventGroup:
		newGroup = self.copyAs(newGroupType)
		if newGroupType == "taskList":
			newEventType = "task"
			newGroup.enable = False  # to prevent per-event node update
			for vcsId in self.vcsIds:
				event = self.getEvent(vcsId)
				newEvent = newGroup.create(newEventType)
				newEvent.changeCalType(event.calType)  # FIXME needed?
				newEvent.copyFrom(event, True)
				newEvent.setStartEpoch(event.epoch)
				newEvent.setEnd("duration", 0, 1)
				newEvent.save()
				newGroup.append(newEvent)
			newGroup.enable = self.enable
		return newGroup


class VcsEpochBaseEvent(Event):
	readOnly = True
	params = Event.params + ("epoch",)

	# FIXME
	@classmethod
	def load(
		cls,
		fs: FileSystem,
		*args,  # noqa: ANN002
	) -> type:
		pass

	def __bool__(self) -> bool:
		return True

	def save(self) -> None:
		pass

	def afterModify(self) -> None:
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		epoch = self.epoch
		if epoch is not None and self.getEpochFromJd(
			startJd,
		) <= epoch < self.getEpochFromJd(endJd):
			if not self.parent.showSeconds:
				log.info("-------- showSeconds = False")
				epoch -= epoch % 60
			return TimeListOccurSet(epoch)
		return TimeListOccurSet()
