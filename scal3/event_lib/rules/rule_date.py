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
	getSysDate,
	jd_to,
	to_jd,
)
from scal3.date_utils import (
	checkDate,
	dateDecode,
	dateEncode,
)
from scal3.event_lib.occur import JdOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _

from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType


log = logger.get()

__all__ = ["DateEventRule", "ExDatesEventRule"]


@classes.rule.register
class DateEventRule(EventRule):
	name = "date"
	desc = _("Date")
	need: Sequence[str] = ()
	conflict: Sequence[str] = (
		"year",
		"month",
		"day",
		"weekNumMode",
		"weekDay",
		"start",
		"end",
		"cycleDays",
		"duration",
		"cycleLen",
	)
	params = ["date"]

	# conflicts with all rules except for dayTime and dayTimeRange
	# (and possibly hourList, minuteList, secondList)
	# also conflict with "holiday" # FIXME

	def getServerString(self) -> str:
		y, m, d = self.date
		return f"{y:04d}/{m:02d}/{d:02d}"

	def __str__(self) -> str:
		return dateEncode(self.date)

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.date = getSysDate(self.getCalType())

	def getRuleValue(self) -> Any:
		return str(self)

	def setRuleValue(self, data: str) -> None:
		try:
			self.date = dateDecode(data)
		except ValueError:
			log.exception("")

	def getJd(self) -> int:
		year, month, day = self.date
		return to_jd(year, month, day, self.getCalType())

	def getEpoch(self) -> int:
		return self.getEpochFromJd(self.getJd())

	def setJd(self, jd: int) -> None:
		self.date = jd_to(jd, self.getCalType())

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		myJd = self.getJd()
		if startJd <= myJd < endJd:
			return JdOccurSet({myJd})
		return JdOccurSet()

	def changeCalType(self, calType: int) -> bool:
		self.date = jd_to(self.getJd(), calType)
		return True


@classes.rule.register
class ExDatesEventRule(EventRule):
	name = "ex_dates"
	desc = "[" + _("Exception") + "] " + _("Date")
	# conflict: Sequence[str] =("date",)  # FIXME
	params = ["dates"]

	def getServerString(self) -> str:
		return " ".join(f"{y:04d}/{m:02d}/{d:02d}" for y, m, d in self.dates)

	def __str__(self) -> str:
		return " ".join(f"{y:04d}/{m:02d}/{d:02d}" for y, m, d in self.dates)

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.setDates([])

	def setDates(self, dates: list[tuple[int, int, int]]) -> None:
		self.dates = dates
		self.jdList = [to_jd(y, m, d, self.getCalType()) for y, m, d in dates]

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		# improve performance # FIXME
		return JdOccurSet(
			set(range(startJd, endJd)).difference(self.jdList),
		)

	def getRuleValue(self) -> Any:
		return [dateEncode(date) for date in self.dates]

	def setRuleValue(
		self,
		datesConf: str | list[str | tuple[int, int, int] | list[int]],
	) -> None:
		dates: list[tuple[int, int, int]] = []
		try:
			if isinstance(datesConf, str):
				dates = [dateDecode(date.strip()) for date in datesConf.split(",")]
			else:
				for date in datesConf:
					if isinstance(date, str):
						dates.append(dateDecode(date))
					elif isinstance(date, tuple | list):
						y, m, d = date
						checkDate((y, m, d))
						dates.append((y, m, d))
					else:
						log.error(f"ExDatesEventRule: setRuleValue: invalid {date=}")
			self.setDates(dates)
		except ValueError:
			log.exception("")

	def changeCalType(self, calType: int) -> bool:
		self.dates = [jd_to(jd, calType) for jd in self.jdList]
		return True
