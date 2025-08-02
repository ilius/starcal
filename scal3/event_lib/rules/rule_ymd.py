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

from typing import TYPE_CHECKING

from scal3 import logger
from scal3.cal_types import (
	convert,
	getSysDate,
	jd_to,
)
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _
from scal3.utils import numRangesEncode

from .rule_allday import MultiValueAllDayEventRule

if TYPE_CHECKING:
	from collections.abc import Sequence

	from scal3.event_lib.pytypes import RuleContainerType


log = logger.get()

__all__ = ["DayOfMonthEventRule", "MonthEventRule", "YearEventRule"]


@classes.rule.register
class YearEventRule(MultiValueAllDayEventRule):
	name = "year"
	desc = _("Year")
	params = ["values"]

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values = [getSysDate(self.getCalType())[0]]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[0])

	def newCalTypeValues(
		self,
		newCalType: int,
	) -> list[int | tuple[int, int]]:
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
		self.values = self.newCalTypeValues(calType)
		return True


# FIXME: directly inherit from AllDayEventRule
@classes.rule.register
class MonthEventRule(MultiValueAllDayEventRule):
	name = "month"
	desc = _("Month")
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["values"]

	def getServerString(self) -> str:
		# return numRangesEncode(self.values, " ")  # no comma
		return " ".join(str(n) for n in self.values)

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values: list[int] = [1]  # type: ignore[assignment]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[1])


@classes.rule.register
class DayOfMonthEventRule(MultiValueAllDayEventRule):
	name = "day"
	desc = _("Day of Month")
	params = ["values"]

	def getServerString(self) -> str:
		return numRangesEncode(self.values, " ")  # no comma

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.values = [1]

	def jdMatches(self, jd: int) -> bool:
		return self.hasValue(jd_to(jd, self.getCalType())[2])


@classes.rule.register
class ExYearEventRule(YearEventRule):
	name = "ex_year"
	desc = "[" + _("Exception") + "] " + _("Year")

	def jdMatches(self, jd: int) -> bool:
		return not YearEventRule.jdMatches(self, jd)


@classes.rule.register
class ExMonthEventRule(MonthEventRule):
	name = "ex_month"
	desc = "[" + _("Exception") + "] " + _("Month")
	conflict: Sequence[str] = (
		"date",
		"month",
		"weekMonth",
	)

	def jdMatches(self, jd: int) -> bool:
		return not MonthEventRule.jdMatches(self, jd)


@classes.rule.register
class ExDayOfMonthEventRule(DayOfMonthEventRule):
	name = "ex_day"
	desc = "[" + _("Exception") + "] " + _("Day of Month")

	def jdMatches(self, jd: int) -> bool:
		return not DayOfMonthEventRule.jdMatches(self, jd)
