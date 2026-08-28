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
from scal3.cal_types import (
	convert,
	getSysDate,
	jd_to,
)
from scal3.event_lib.register import classes
from scal3.locale_man import textNumEncode
from scal3.locale_man import tr as _
from scal3.utils import numRangesEncode

from .rule_allday import AllDayEventRule, MultiValueAllDayEventRule

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.event_lib.pytypes import RuleContainerType


log = logger.get()

__all__ = ["DayOfMonthEventRule", "MonthEventRule", "YearEventRule"]


@classes.rule.register
class YearEventRule(MultiValueAllDayEventRule):
	"""Rule that matches specific years or year ranges."""

	name = "year"
	desc = _("Year")
	params = ["values"]

	def getServerString(self) -> str:
		"""Return the year values as a space-separated string."""
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values = [getSysDate(self.getCalType())[0]]

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day's year is selected."""
		return self._hasValue(jd_to(jd, self.getCalType())[0])

	def _newCalTypeValues(
		self,
		newCalType: int,
	) -> list[int | tuple[int, int]]:
		"""Convert the stored year values to a different calendar type."""

		def yearConv(year: int) -> int:
			return convert(year, 7, 1, curCalType, newCalType)[0]

		curCalType = self.getCalType()
		values2: list[int | tuple[int, int]] = []
		for item in self.values:
			if isinstance(item, tuple | list):
				values2.append(
					(
						yearConv(item[0]),
						yearConv(item[1]),
					),
				)
			else:
				values2.append(yearConv(item))
		return values2

	def changeCalType(self, calType: int) -> bool:
		"""Convert the year values to a new calendar type."""
		self.values = self._newCalTypeValues(calType)
		return True


@classes.rule.register
class MonthEventRule(AllDayEventRule):
	"""Rule that matches specific months of the year."""

	name = "month"
	desc = _("Month")
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["values"]
	expand = True  # FIXME

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values: list[int] = [1]

	def getRuleValue(self) -> Any:
		"""Return the list of matching months."""
		return self.values

	def setRuleValue(self, data: Any) -> None:
		"""Set the month values, wrapping a scalar in a list."""
		if not isinstance(data, tuple | list):
			data = [data]
		self.values = data

	def __str__(self) -> str:
		return textNumEncode(", ".join(str(x) for x in self.values))

	def changeCalType(self, _calType: int) -> bool:  # noqa: PLR6301
		"""Return False since month numbers cannot be converted between calendars."""
		return False

	def getServerString(self) -> str:
		"""Return the month values as a space-separated string."""
		return " ".join(str(n) for n in self.values)

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day's month is selected."""
		return jd_to(jd, self.getCalType())[1] in self.values


@classes.rule.register
class DayOfMonthEventRule(MultiValueAllDayEventRule):
	"""Rule that matches specific days of the month, with optional ranges."""

	name = "day"
	desc = _("Day of Month")
	params = ["values"]

	def getServerString(self) -> str:
		"""Return the day values as a space-separated string."""
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values = [1]

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day of month is selected."""
		return self._hasValue(jd_to(jd, self.getCalType())[2])


@classes.rule.register
class ExYearEventRule(YearEventRule):
	"""Exception rule that excludes specific years from matching."""

	name = "ex_year"
	desc = "[" + _("Exception") + "] " + _("Year")

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day's year is not selected."""
		return not YearEventRule.jdMatches(self, jd)


@classes.rule.register
class ExMonthEventRule(MonthEventRule):
	"""Exception rule that excludes specific months from matching."""

	name = "ex_month"
	desc = "[" + _("Exception") + "] " + _("Month")
	conflict: Sequence[str] = (
		"date",
		"month",
		"weekMonth",
	)

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day's month is not selected."""
		return not MonthEventRule.jdMatches(self, jd)


@classes.rule.register
class ExDayOfMonthEventRule(DayOfMonthEventRule):
	"""Exception rule that excludes specific days of the month from matching."""

	name = "ex_day"
	desc = "[" + _("Exception") + "] " + _("Day of Month")

	def jdMatches(self, jd: int) -> bool:
		"""Return True if the day of month is not selected."""
		return not DayOfMonthEventRule.jdMatches(self, jd)
