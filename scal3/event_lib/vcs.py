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

from .vcs_base import (
	VcsBaseEventGroup,
	VcsEpochBaseEvent,
	VcsEpochBaseEventGroup,
)

log = logger.get()

from time import perf_counter
from typing import TYPE_CHECKING, Self

import mytz
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getEpochFromJd,
	getJdFromEpoch,
)
from scal3.utils import toStr

from .event_base import Event
from .occur import JdOccurSet
from .register import classes

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventContainerType, OccurSetType
	from scal3.filesystem import FileSystem

	from .pytypes import EventType

__all__ = ["VcsCommitEventGroup", "VcsTagEventGroup"]


# @classes.event.register  # FIXME
class VcsCommitEvent(VcsEpochBaseEvent):
	name = "vcs"
	desc = _("VCS Commit")
	params = VcsEpochBaseEvent.params + [
		"author",
		"shortHash",
	]

	def __init__(self, parent: EventContainerType, ident: str) -> None:
		Event.__init__(self, parent=parent)
		# commit full hash:
		self.id = ident  # type: ignore[assignment]
		# ---
		self.epoch = None
		self.author = ""
		self.shortHash = ""

	def __repr__(self) -> str:
		return f"{self.parent!r}.getEvent({self.id!r})"


class VcsTagEvent(VcsEpochBaseEvent):
	name = "vcsTag"
	desc = _("VCS Tag")
	# params = VcsEpochBaseEvent.params +

	def __init__(self, parent: EventContainerType, ident: str) -> None:
		Event.__init__(self, parent=parent)
		# tag name
		self.id = ident  # type: ignore[assignment]
		self.epoch = None
		self.author = ""


@classes.group.register
class VcsCommitEventGroup(VcsEpochBaseEventGroup):
	name = "vcs"
	desc = _("VCS Repository (Commits)")
	_myOptions = [
		"showAuthor",
		"showShortHash",
		"showStat",
	]
	params = VcsEpochBaseEventGroup.params + _myOptions
	paramsOrder = VcsEpochBaseEventGroup.paramsOrder + _myOptions

	def __init__(self, ident: str | None = None) -> None:
		VcsEpochBaseEventGroup.__init__(self, ident)  # type: ignore[arg-type]
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

	def updateEventDesc(self, event: EventType) -> None:
		assert isinstance(event, VcsCommitEvent), f"{event=}"
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
	def getEvent(
		self,
		commitId: str,  # type: ignore[override]
	) -> EventType:
		mod = self.getVcsModule()
		if mod is None:
			raise ValueError(f"VCS module {self.vcsType!r} not found")
		data = mod.getCommitInfo(self, commitId)
		if not data:
			raise ValueError(f"No commit with {commitId=}")
		data["summary"] = self.title + ": " + data["summary"]
		data["icon"] = self.icon
		event = VcsCommitEvent(self, commitId)
		event.setDict(data)
		self.updateEventDesc(event)
		return event


@classes.group.register
class VcsTagEventGroup(VcsEpochBaseEventGroup):
	name = "vcsTag"
	desc = _("VCS Repository (Tags)")
	params = VcsEpochBaseEventGroup.params + ["showStat"]
	paramsOrder = VcsEpochBaseEventGroup.paramsOrder + ["showStat"]

	def __init__(self, ident: str | None = None) -> None:
		VcsEpochBaseEventGroup.__init__(self, ident)  # type: ignore[arg-type]
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

	def updateEventDesc(self, event: EventType) -> None:
		mod = self.getVcsModule()
		if mod is None:
			raise ValueError(f"VCS module {self.vcsType!r} not found")
		assert event.id is not None
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
	def getEvent(
		self,
		tag: str,  # type: ignore[override]
	) -> EventType:
		tag = toStr(tag)
		if tag not in self.vcsIds:  # type: ignore[comparison-overlap]
			raise ValueError(f"No tag {tag!r}")
		data = {}
		data["summary"] = self.title + " " + tag
		data["icon"] = self.icon  # type: ignore[assignment]
		event = VcsTagEvent(self, tag)
		event.setDict(data)
		self.updateEventDesc(event)
		return event


class VcsDailyStatEvent(Event):
	name = "vcsDailyStat"
	desc = _("VCS Daily Stat")
	readOnly = True
	isAllDay = True
	params = Event.params + ["jd"]

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> Self:  # FIXME
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def __init__(self, parent: EventContainerType, jd: int) -> None:
		Event.__init__(self, parent=parent)
		self.id = jd  # ID is Julian Day

	def save(self) -> None:
		pass

	def afterModify(self) -> None:
		pass

	def getInfo(self) -> str:
		return self.getText()  # FIXME

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		jd = self.id
		if jd is not None and startJd <= jd < endJd:
			return JdOccurSet({jd})
		return JdOccurSet()


@classes.group.register
class VcsDailyStatEventGroup(VcsBaseEventGroup):
	name = "vcsDailyStat"
	desc = _("VCS Repository (Daily Stat)")

	def __init__(self, ident: str | None = None) -> None:
		VcsBaseEventGroup.__init__(self, ident)  # type: ignore[arg-type]
		# statByJd value: (commitsCount, lastCommitId)
		self.statByJd: dict[int, tuple[int, str]] = {}

	def clear(self) -> None:
		VcsBaseEventGroup.clear(self)
		self.statByJd = {}

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

	def getEvent(self, jd: int) -> EventType:
		# cache commit data FIXME
		from scal3.vcs_modules import encodeShortStat

		try:
			commitsCount, stat = self.statByJd[jd]
		except KeyError:
			raise ValueError(f"No commit for jd {jd}") from None
		mod = self.getVcsModule()
		if mod is None:
			raise ValueError(f"VCS module {self.vcsType!r} not found")
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
