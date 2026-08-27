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
	from collections.abc import Callable, Sequence

	from scal3.event_lib.pytypes import EventType, OccurSetType
	from scal3.filesystem import FileSystem

	from .pytypes import EventGroupType

__all__ = ["VcsBaseEventGroup", "VcsEpochBaseEvent", "VcsEpochBaseEventGroup"]


def _load_module_git() -> Any:
	try:
		from scal3.vcs_modules import git
	except ImportError:
		log.exception("")
		return None
	return git


def _load_module_hg() -> Any:
	try:
		from scal3.vcs_modules import hg
	except ImportError:
		log.exception("")
		return

	return hg


_vcsModuleByName: dict[str, Callable[[], Any]] = {
	"git": _load_module_git,
	"hg": _load_module_hg,
}


class VcsBaseEventGroup(EventGroup):
	"""Base group for events sourced from a version control system."""

	acceptsEventTypes: Sequence[str] = ()
	myParams: list[str] = [
		"vcsType",
		"vcsDir",
		"vcsBranch",
	]
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

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
		"""Set default group properties."""
		self.eventTextSep = "\n"
		self.showInTimeLine = False

	def getRulesHash(self) -> int:
		"""Return a hash of the group's configuration attributes."""
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

	def __getitem__(self, key: str) -> EventType:  # type: ignore
		return self.getEvent(key)  # type: ignore

	# FIXME: remove
	# def __getitem__(self, key: str) -> EventType:
	# 	if key in classes.rule.names:
	# 		return EventGroup.__getitem__(self, key)
	# 	# len(commitId)==40 for git
	# 	return self.getEvent(key)

	def _getVcsModule(self) -> Any:
		"""Return the VCS module (git or hg) for this group."""
		name = toStr(self.vcsType)
		# if not isinstance(name, str):
		# 	raise TypeError(f"getVcsModule({name!r}): bad type {type(name)}")
		try:
			mod = _vcsModuleByName[name]()
		except KeyError:
			log.exception("")
			return None
		if mod is None:
			return None
		return mod

	def _updateVcsModuleObj(self) -> None:
		"""Initialize or clear the VCS module object for this group."""
		mod = self._getVcsModule()
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
		"""Refresh the VCS module object after a group change."""
		self._updateVcsModuleObj()
		super().afterModify()

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the group from a dictionary and refresh the VCS module."""
		super().setDict(data)
		self._updateVcsModuleObj()


class VcsEpochBaseEventGroup(VcsBaseEventGroup):
	"""Base group for VCS events identified by epoch timestamps."""

	myParams = VcsBaseEventGroup.myParams + ["showSeconds"]
	canConvertTo: list[str] = VcsBaseEventGroup.canConvertTo + ["taskList"]

	def __init__(self, ident: int | None = None) -> None:
		self.showSeconds = True
		self.vcsIds: list[int] = []
		super().__init__(ident)

	def clear(self) -> None:
		"""Clear all occurrences and VCS IDs."""
		super().clear()
		self.vcsIds = []

	def _addOccur(self, t0: float, t1: float, eid: int) -> None:
		"""Add an occurrence and track its VCS ID."""
		super()._addOccur(t0, t1, eid)
		self.vcsIds.append(eid)

	def getRulesHash(self) -> int:
		"""Return a hash of the group's configuration attributes."""
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
		"""Convert this group to another type, creating events from VCS data."""
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
	"""Base event for VCS commits/tags identified by an epoch timestamp."""

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
		"""VCS events are virtual and are never loaded from disk."""
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def save(self) -> None:
		"""VCS events are virtual and are never saved to disk."""

	def afterModify(self) -> None:
		"""VCS events are virtual and are never modified."""

	def getInfo(self) -> str:
		"""Return the event text as its info."""
		return self.getText()  # FIXME

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Return the event's epoch as an occurrence if it falls within the range."""
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
