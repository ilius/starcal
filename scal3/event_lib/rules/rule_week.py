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

import json
from typing import TYPE_CHECKING

from scal3 import locale_man, logger
from scal3.cal_types import jd_to, to_jd
from scal3.date_utils import jwday
from scal3.event_lib.common import (
	firstWeekDay,
	getAbsWeekNumberFromJd,
	weekDayName,
	weekDayNameEnglish,
)
from scal3.event_lib.exceptions import BadEventFile
from scal3.event_lib.occur import JdOccurSet
from scal3.event_lib.register import classes
from scal3.locale_man import tr as _
from scal3.utils import s_join

from .rule_allday import AllDayEventRule
from .rule_base import EventRule

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

	from scal3.event_lib.pytypes import EventType, OccurSetType, RuleContainerType


log = logger.get()

__all__ = ["WeekDayEventRule", "WeekMonthEventRule", "WeekNumberModeEventRule"]


@classes.rule.register
class WeekNumberModeEventRule(EventRule):
	name = "weekNumMode"
	desc = _("Week Number")
	need: Sequence[str] = ("start",)  # FIXME
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["weekNumMode"]
	EVERY_WEEK, ODD_WEEKS, EVEN_WEEKS = list(range(3))
	# remove EVERY_WEEK? FIXME
	weekNumModeNames = ("any", "odd", "even")

	def getServerString(self) -> str:
		return self.weekNumModeNames[self.weekNumMode]

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.weekNumMode = self.EVERY_WEEK

	def getRuleValue(self) -> Any:
		return self.weekNumModeNames[self.weekNumMode]

	def setRuleValue(self, wnModeName: str) -> None:
		if wnModeName not in self.weekNumModeNames:
			raise BadEventFile(
				f"bad rule value {wnModeName=}, "
				"the value for weekNumMode must be "
				f"one of {self.weekNumModeNames!r}",
			)
		self.weekNumMode = self.weekNumModeNames.index(wnModeName)

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSetType:
		# improve performance FIXME
		startAbsWeekNum = getAbsWeekNumberFromJd(event.getStartJd()) - 1
		# 1st week # FIXME
		if self.weekNumMode == self.EVERY_WEEK:
			return JdOccurSet(
				set(range(startJd, endJd)),
			)
		if self.weekNumMode == self.ODD_WEEKS:
			return JdOccurSet(
				{
					jd
					for jd in range(startJd, endJd)
					if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 1
				},
			)
		if self.weekNumMode == self.EVEN_WEEKS:
			return JdOccurSet(
				{
					jd
					for jd in range(startJd, endJd)
					if (getAbsWeekNumberFromJd(jd) - startAbsWeekNum) % 2 == 0
				},
			)
		log.error(f"calcOccurrence: invalid weekNumMode={self.weekNumMode}")
		return JdOccurSet()

	def __str__(self) -> str:
		return self.weekNumModeNames[self.weekNumMode]

	def getInfo(self) -> str:
		if self.weekNumMode == self.EVERY_WEEK:
			return ""
		if self.weekNumMode == self.ODD_WEEKS:
			return _("Odd Weeks")
		if self.weekNumMode == self.EVEN_WEEKS:
			return _("Even Weeks")
		log.error(f"getInfo: invalid weekNumMode={self.weekNumMode}")
		return ""


@classes.rule.register
class WeekDayEventRule(AllDayEventRule):
	name = "weekDay"
	desc = _("Day of Week")
	conflict: Sequence[str] = (
		"date",
		"weekMonth",
	)
	params = ["weekDayList"]

	def getServerString(self) -> str:
		return s_join(self.weekDayList)

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.weekDayList = list(range(7))  # or [] FIXME

	def getRuleValue(self) -> Any:
		return self.weekDayList

	def setRuleValue(self, data: int | list[int]) -> None:
		if isinstance(data, int):
			self.weekDayList = [data]
		elif isinstance(data, tuple | list):
			self.weekDayList = data
		else:
			raise BadEventFile(
				f"bad rule weekDayList={data}, "
				"value for weekDayList must be a list of integers"
				" (0 for sunday)",
			)

	def jdMatches(self, jd: int) -> bool:
		return jwday(jd) in self.weekDayList

	def __str__(self) -> str:
		if self.weekDayList == list(range(7)):
			return ""
		return ", ".join([weekDayNameEnglish[wd] for wd in self.weekDayList])

	def getInfo(self) -> str:
		if self.weekDayList == list(range(7)):
			return ""
		sep = _(",") + " "
		sep2 = " " + _("or") + " "
		return (
			_("Day of Week")
			+ ": "
			+ sep.join([weekDayName[wd] for wd in self.weekDayList[:-1]])
			+ sep2
			+ weekDayName[self.weekDayList[-1]]
		)


@classes.rule.register
class WeekMonthEventRule(EventRule):
	name = "weekMonth"
	desc = _("Week-Month")
	conflict: Sequence[str] = (
		"date",
		"month",
		"ex_month",
		"weekNumMode",
		"weekday",
		"cycleDays",
		"cycleWeeks",
		"cycleLen",
	)
	params = [
		"month",  # 0..12   0 means every month
		"wmIndex",  # 0..4
		"weekDay",  # 0..6
	]
	"""
	paramsValidators = {
		"month": lambda m: 0 <= m <= 12,
		"wmIndex": lambda m: 0 <= m <= 4,
		"weekDay": lambda m: 0 <= m <= 6,
	}
	"""
	wmIndexNamesEn = (
		"First",  # 0
		"Second",  # 1
		"Third",  # 2
		"Fourth",  # 3
		"Last",  # 4
	)
	wmIndexNames = (
		_("First"),  # 0
		_("Second"),  # 1
		_("Third"),  # 2
		_("Fourth"),  # 3
		_("Last"),  # 4
	)

	def __str__(self) -> str:
		calType = self.getCalType()
		if self.month == 0:
			monthDesc = "every month"
		else:
			monthDesc = locale_man.getMonthName(calType, self.month)
		return " ".join(
			[
				self.wmIndexNamesEn[self.wmIndex],
				weekDayNameEnglish[self.weekDay],
				"of",
				monthDesc,
			],
		)

	def __init__(self, parent: RuleContainerType) -> None:
		super().__init__(parent)
		self.month = 1
		self.wmIndex = 4
		self.weekDay = firstWeekDay.v

	def getRuleValue(self) -> Any:
		return {
			"month": self.month,
			"wmIndex": self.wmIndex,
			"weekDay": self.weekDay,
		}

	def setRuleValue(self, data: Any) -> None:
		assert isinstance(data, dict), f"{data=}"
		self.month = data["month"]
		self.wmIndex = data["wmIndex"]
		self.weekDay = data["weekDay"]

	def getServerString(self) -> str:
		return json.dumps(
			{
				"weekIndex": self.wmIndex,
				"weekDay": self.weekDay,
				"month": self.month,
			},
		)

	# usefull? FIXME
	# def setJd(self, jd) -> None:
	# 	self.month, self.wmIndex, self.weekDay = getMonthWeekNth(
	# 	jd,
	# 	self.getCalType(),
	# )

	# def getJd(self) -> int:

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,  # noqa: ARG002
	) -> OccurSetType:
		calType = self.getCalType()
		startYear, _startMonth, _startDay = jd_to(startJd, calType)
		endYear, _endMonth, _endDay = jd_to(endJd, calType)
		jds = set()
		monthList = range(1, 13) if self.month == 0 else [self.month]
		for year in range(startYear, endYear):
			for month in monthList:
				jd = to_jd(
					year,
					month,
					7 * self.wmIndex + 1,
					calType,
				)
				jd += (self.weekDay - jwday(jd)) % 7
				# Last (Fouth or Fifth)
				if self.wmIndex == 4 and jd_to(jd, calType)[1] != month:
					jd -= 7
				if startJd <= jd < endJd:
					jds.add(jd)
		return JdOccurSet(jds)
