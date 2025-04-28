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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any

	from scal3.filesystem import FileSystem

	from .event_container import EventContainer

from time import perf_counter

import mytz
from scal3.locale_man import tr as _

# from scal3.interval_utils import
from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
)
from scal3.utils import toStr

from .event_base import Event
from .groups import EventGroup
from .occur import JdOccurSet, OccurSet, TimeListOccurSet
from .register import classes


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


# @classes.event.register  # FIXME
class VcsCommitEvent(VcsEpochBaseEvent):
	name = "vcs"
	desc = _("VCS Commit")
	params = VcsEpochBaseEvent.params + (
		"author",
		"shortHash",
	)

	def __init__(self, parent: EventContainer, ident: str) -> None:
		Event.__init__(self, parent=parent)
		self.id = ident  # commit full hash
		# ---
		self.epoch = None
		self.author = ""
		self.shortHash = ""

	def __repr__(self) -> str:
		return f"{self.parent!r}.getEvent({self.id!r})"


class VcsTagEvent(VcsEpochBaseEvent):
	name = "vcsTag"
	desc = _("VCS Tag")
	params = VcsEpochBaseEvent.params + ()

	def __init__(self, parent: EventContainer, ident: str) -> None:
		Event.__init__(self, parent=parent)
		self.id = ident  # tag name
		self.epoch = None
		self.author = ""


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


@classes.group.register
class VcsCommitEventGroup(VcsEpochBaseEventGroup):
	name = "vcs"
	desc = _("VCS Repository (Commits)")
	myParams = VcsEpochBaseEventGroup.myParams + (
		"showAuthor",
		"showShortHash",
		"showStat",
	)
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, ident: str | None = None) -> None:
		VcsEpochBaseEventGroup.__init__(self, ident)
		self.showAuthor = True
		self.showShortHash = True
		self.showStat = True

	def updateOccurrence(self) -> None:
		stm0 = perf_counter()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		try:
			commitsData = mod.getCommitList(
				self,
				startJd=self.startJd,
				endJd=self.endJd,
				branch=self.vcsBranch,
			)
		except Exception:
			log.error(
				f"Error while fetching commit list of {self.vcsType} "
				f"repository in {self.vcsDir}",
			)
			log.exception("")
			return
		for epoch, commitId in commitsData:
			if not self.showSeconds:
				epoch -= epoch % 60  # noqa: PLW2901
			self.addOccur(epoch, epoch, commitId)
		# ---
		self.updateOccurrenceLog(perf_counter() - stm0)

	def updateEventDesc(self, event: Event) -> None:
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		lines = []
		if event.description:
			lines.append(event.description)
		if self.showStat:
			statLine = mod.getCommitShortStatLine(self, event.id)
			if statLine:
				lines.append(statLine)  # TODO: translation
		if self.showAuthor and event.author:
			lines.append(_("Author") + ": " + event.author)
		if self.showShortHash and event.shortHash:
			lines.append(_("Hash") + ": " + event.shortHash)
		event.description = "\n".join(lines)

	# TODO: cache commit data
	def getEvent(self, commitId: str) -> Event:
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		data = mod.getCommitInfo(self, commitId)
		if not data:
			raise ValueError(f"No commit with {commitId=}")
		data["summary"] = self.title + ": " + data["summary"]
		data["icon"] = self.icon
		event = VcsCommitEvent(self, commitId)
		event.setData(data)
		self.updateEventDesc(event)
		return event


@classes.group.register
class VcsTagEventGroup(VcsEpochBaseEventGroup):
	name = "vcsTag"
	desc = _("VCS Repository (Tags)")
	myParams = VcsEpochBaseEventGroup.myParams + ("showStat",)
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, ident: str | None = None) -> None:
		VcsEpochBaseEventGroup.__init__(self, ident)
		self.showStat = True

	def updateOccurrence(self) -> None:
		stm0 = perf_counter()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		try:
			tagsData = mod.getTagList(self, self.startJd, self.endJd)
			# TOO SLOW, FIXME
		except Exception:
			log.error(
				f"Error while fetching tag list of {self.vcsType} "
				f"repository in {self.vcsDir}",
			)
			log.exception("")
			return
		# self.updateOccurrenceLog(perf_counter() - stm0)
		for epoch, tag in tagsData:
			if not self.showSeconds:
				epoch -= epoch % 60  # noqa: PLW2901
			self.addOccur(epoch, epoch, tag)
		# ---
		self.updateOccurrenceLog(perf_counter() - stm0)

	def updateEventDesc(self, event: Event) -> None:
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		tag = event.id
		lines = []
		if self.showStat:
			tagIndex = self.vcsIds.index(tag)
			if tagIndex > 0:
				prevTag = self.vcsIds[tagIndex - 1]
			else:
				prevTag = None
			statLine = mod.getTagShortStatLine(self, prevTag, tag)
			if statLine:
				lines.append(statLine)  # TODO: translation
		event.description = "\n".join(lines)

	# TODO: cache commit data
	def getEvent(self, tag: str) -> Event:
		tag = toStr(tag)
		if tag not in self.vcsIds:
			raise ValueError(f"No tag {tag!r}")
		data = {}
		data["summary"] = self.title + " " + tag
		data["icon"] = self.icon
		event = VcsTagEvent(self, tag)
		event.setData(data)
		self.updateEventDesc(event)
		return event


class VcsDailyStatEvent(Event):
	name = "vcsDailyStat"
	desc = _("VCS Daily Stat")
	readOnly = True
	isAllDay = True
	params = Event.params + ("jd",)

	@classmethod
	def load(
		cls,
		fs: FileSystem,
		*args,  # noqa: ANN002
	) -> None:  # FIXME
		pass

	def __bool__(self) -> bool:
		return True

	def __init__(self, parent: EventContainer, jd: int) -> None:
		Event.__init__(self, parent=parent)
		self.id = jd  # ID is Julian Day

	def save(self) -> None:
		pass

	def afterModify(self) -> None:
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSet:
		jd = self.jd
		if jd is not None and startJd <= jd < endJd:
			return JdOccurSet({jd})
		return JdOccurSet()


@classes.group.register
class VcsDailyStatEventGroup(VcsBaseEventGroup):
	name = "vcsDailyStat"
	desc = _("VCS Repository (Daily Stat)")
	myParams = VcsBaseEventGroup.myParams + ()
	params = EventGroup.params + myParams
	paramsOrder = EventGroup.paramsOrder + myParams

	def __init__(self, ident: str | None = None) -> None:
		VcsBaseEventGroup.__init__(self, ident)
		self.statByJd = {}

	def clear(self) -> None:
		VcsBaseEventGroup.clear(self)
		self.statByJd = {}  # a dict of (commintsCount, lastCommitId)s

	def updateOccurrence(self) -> None:
		stm0 = perf_counter()
		self.clear()
		if not self.vcsDir:
			return
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		# ----
		try:
			utc = mytz.gettz("UTC")
			self.vcsMinJd = getJdFromEpoch(mod.getFirstCommitEpoch(self), tz=utc)
			self.vcsMaxJd = getJdFromEpoch(mod.getLastCommitEpoch(self), tz=utc) + 1
		except Exception:
			log.exception("")
			return
		# ---
		startJd = max(self.startJd, self.vcsMinJd)
		endJd = min(self.endJd, self.vcsMaxJd)
		# ---
		commitsByJd: dict[int, list[str]] = {}
		for epoch, commitId in mod.getCommitList(
			self,
			startJd=startJd,
			endJd=endJd + 1,
			branch=self.vcsBranch,
		):
			jd = getJdFromEpoch(epoch)
			if jd in commitsByJd:
				commitsByJd[jd].append(commitId)
			else:
				commitsByJd[jd] = [commitId]
		for jd in range(startJd, endJd + 1):
			if jd not in commitsByJd:
				continue
			epoch = getEpochFromJd(jd)
			commitIds = commitsByJd[jd]
			newCommitId = commitIds[-1]
			oldCommitId = mod.getLatestParentBefore(self, newCommitId, epoch)
			if not oldCommitId:
				log.info(f"oldCommitId is empty, {jd=}, {newCommitId=}")
				continue
			stat = mod.getShortStat(self, oldCommitId, newCommitId)
			self.statByJd[jd] = (len(commitIds), stat)
			self.addOccur(
				getEpochFromJd(jd),
				getEpochFromJd(jd + 1),
				jd,
			)
		# ---
		self.updateOccurrenceLog(perf_counter() - stm0)

	def getEvent(self, jd: int) -> Event:
		# cache commit data FIXME
		from scal3.vcs_modules import encodeShortStat

		try:
			commitsCount, stat = self.statByJd[jd]
		except KeyError:
			raise ValueError(f"No commit for jd {jd}") from None
		mod = self.getVcsModule()
		if mod is None:
			log.info(f"VCS module {self.vcsType!r} not found")
			return
		event = VcsDailyStatEvent(self, jd)
		# ---
		event.icon = self.icon
		# --
		statLine = encodeShortStat(*stat)
		event.summary = (
			self.title
			+ ": "
			+ _("{commitsCount} commits").format(commitsCount=commitsCount)
		)
		event.summary += ", " + statLine
		# event.description = statLine
		# ---
		return event
