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

from typing import TYPE_CHECKING, Self

from scal3.event_lib.register import classes
from scal3.filesystem import null_fs
from scal3.s_object import SObjBase, copyParams
from scal3.time_utils import getEpochFromJd

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType

__all__ = ["EventRule"]


# Should not be registered, or instantiate directly
@classes.rule.setMain
class EventRule(SObjBase):
	"""Base class for all event rules that define how events recur or appear."""

	name = ""
	tname = ""
	nameAlias = ""
	desc = ""
	provide: Sequence[str] = ()
	need: Sequence[str] = ()
	conflict: Sequence[str] = ()
	sgroup = -1
	expand = False
	params: list[str] = []
	WidgetClass: Any

	def getServerString(self) -> str:
		"""Return a server-compatible string representation of this rule."""
		raise NotImplementedError

	def __bool__(self) -> bool:
		return True

	def __init__(self, parent: RuleContainerType) -> None:
		"""Parent can be an event for now (maybe later a group too)."""
		self.parent = parent
		self.fs = null_fs

	def getRuleValue(self) -> Any:
		"""Return the rule's value for serialization."""
		log.warning(f"No implementation for {self.__class__.__name__}.getRuleValue")
		return None

	def setRuleValue(self, data: Any) -> None:  # noqa: ARG002
		"""Set the rule's value from serialized data."""
		log.warning(f"No implementation for {self.__class__.__name__}.setRuleValue")

	def __copy__(self) -> Self:
		newRule = self.__class__(self.parent)
		newRule.fs = self.fs
		copyParams(newRule, self)
		return newRule

	def getCalType(self) -> int:
		"""Return the calendar type of the parent container."""
		return self.parent.calType

	def changeCalType(self, calType: int) -> bool:  # noqa: ARG002, PLR6301
		"""Convert dates to a new calendar type. Return True if changed."""
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSetType:
		"""Calculate the set of occurrences within the given Julian day range."""
		raise NotImplementedError

	def getInfo(self) -> str:
		"""Return a human-readable description of this rule."""
		return self.desc + f": {self}"

	def getEpochFromJd(self, jd: int) -> int:
		"""Convert a Julian day to an epoch in the parent's time zone."""
		return getEpochFromJd(
			jd,
			tz=self.parent.getTimeZoneObj(),
		)

	def getEpoch(self) -> int:
		"""Return the epoch timestamp for this rule's primary time point."""
		raise NotImplementedError

	def getJd(self) -> int:
		"""Return the Julian day number for this rule's date."""
		raise NotImplementedError

	@classmethod
	def getFrom(cls, container: RuleContainerType) -> Self | None:
		"""Return the rule of this type from the container, or None if absent."""
		rule = container.rulesDict.get(cls.name)
		assert isinstance(rule, cls | None), f"{rule=}, {cls=}"
		return rule

	@classmethod
	def addOrGetFrom(cls, container: RuleContainerType) -> Self:
		"""Return the rule of this type from the container, creating it if absent."""
		rule = container.getAddRule(cls.name)
		assert isinstance(rule, cls), f"{rule=}, {cls=}"
		return rule
