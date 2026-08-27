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

from scal3.event_lib.occur import JdOccurSet
from scal3.locale_man import textNumEncode
from scal3.utils import numRangesEncode

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType

__all__ = ["AllDayEventRule", "MultiValueAllDayEventRule"]


class AllDayEventRule(EventRule):
	"""Rule for events that recur on specific days, matching all-day occurrences."""

	def jdMatches(self, jd: int) -> bool:  # noqa: ARG002, PLR6301
		"""Return True if the given Julian day matches this rule."""
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		"""Return all matching days in the range as a JdOccurSet."""
		# improve performance FIXME
		jds = set()
		for jd in range(startJd, endJd):
			if self.jdMatches(jd):
				jds.add(jd)  # benchmark FIXME
		return JdOccurSet(jds)


class MultiValueAllDayEventRule(AllDayEventRule):
	"""All-day rule that matches against a list of individual values or ranges."""

	conflict: Sequence[str] = ("date",)
	params = ["values"]
	expand = True  # FIXME

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values: list[int | tuple[int, int]] = []

	def getRuleValue(self) -> Any:
		"""Return the list of values for serialization."""
		return self.values

	def setRuleValue(self, data: Any) -> None:
		"""Set the values from serialized data, wrapping scalars in a list."""
		if not isinstance(data, tuple | list):
			data = [data]
		self.values = data

	def __str__(self) -> str:
		return textNumEncode(numRangesEncode(self.values, ", "))

	def hasValue(self, value: Any) -> bool:
		"""Return True if value falls within any of the stored values or ranges."""
		for item in self.values:
			if isinstance(item, tuple | list):
				if item[0] <= value <= item[1]:
					return True
			elif item == value:
				return True
		return False

	def changeCalType(self, _calType: int) -> bool:  # noqa: PLR6301
		"""Return False since day values cannot convert between calendars."""
		return False

	# FIXME: I think getValuesPlain was meant to be used in getServerString

	# def getValuesPlain(self) -> list[int | tuple[int, int]]:
	# 	"""Return values expanded from ranges into a flat list."""
	# 	ls: list[int | tuple[int, int]] = []
	# 	for item in self.values:
	# 		if isinstance(item, tuple | list):
	# 			ls += list(range(item[0], item[1] + 1))
	# 		else:
	# 			ls.append(item)
	# 	return ls

	# def setValuesPlain(self, values: list[int]) -> None:
	# 	"""Set values from a flat list, simplifying into ranges where possible."""
	# 	self.values = simplifyNumList(values)
