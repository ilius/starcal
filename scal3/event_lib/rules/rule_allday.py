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
from scal3.interval_utils import simplifyNumList
from scal3.locale_man import textNumEncode
from scal3.utils import numRangesEncode

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType

__all__ = ["AllDayEventRule", "MultiValueAllDayEventRule"]


class AllDayEventRule(EventRule):
	def jdMatches(self, jd: int) -> bool:  # noqa: ARG002, PLR6301
		return True

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		# improve performance FIXME
		jds = set()
		for jd in range(startJd, endJd):
			if self.jdMatches(jd):
				jds.add(jd)  # benchmark FIXME
		return JdOccurSet(jds)


# Should not be registered, or instantiate directly
class MultiValueAllDayEventRule(AllDayEventRule):
	conflict: Sequence[str] = ("date",)
	params = ["values"]
	expand = True  # FIXME

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values: list[int | tuple[int, int]] = []

	def getRuleValue(self) -> Any:
		return self.values

	def setRuleValue(self, data: Any) -> None:
		if not isinstance(data, tuple | list):
			data = [data]
		self.values = data

	def __str__(self) -> str:
		return textNumEncode(numRangesEncode(self.values, ", "))

	def hasValue(self, value: Any) -> bool:
		for item in self.values:
			if isinstance(item, tuple | list):
				if item[0] <= value <= item[1]:
					return True
			elif item == value:
				return True
		return False

	def getValuesPlain(self) -> list[int | tuple[int, int]]:
		ls: list[int | tuple[int, int]] = []
		for item in self.values:
			if isinstance(item, tuple | list):
				ls += list(range(item[0], item[1] + 1))
			else:
				ls.append(item)
		return ls

	def setValuesPlain(self, values: list[int]) -> None:
		self.values = simplifyNumList(values)

	def changeCalType(self, _calType: int) -> bool:  # noqa: PLR6301
		return False
