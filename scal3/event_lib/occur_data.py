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


import operator
from typing import TYPE_CHECKING, NamedTuple

from scal3 import core
from scal3.cal_types import calTypes
from scal3.core import jd_to_primary
from scal3.date_utils import getJdRangeForMonth
from scal3.time_utils import (
	HMS,
	getEpochFromJd,
	getJhmsFromEpoch,
)

from .occur import IntervalOccurSet, JdOccurSet, TimeListOccurSet

if TYPE_CHECKING:
	from collections.abc import Iterable

	from .event_base import Event
	from .groups import EventGroup

__all__ = ["getDayOccurrenceData", "getWeekOccurrenceData"]
dayLen = 24 * 3600
hms_zero = HMS()
hms_24 = HMS(24)
keyFuncIndex0 = operator.itemgetter(0)


class DayOccurData(NamedTuple):
	time: str
	time_epoch: tuple[int, int]
	is_allday: bool
	text: str
	icon: str
	color: tuple[int, int, int]
	ids: tuple[int, int]
	show: tuple[bool, bool, bool]  # (showInDCal, showInWCal, showInMCal)
	showInStatusIcon: bool


class WeekOccurData(NamedTuple):
	weekDay: int
	time: str
	text: str
	icon: str


class MonthOccurData(NamedTuple):
	day: int
	time: str
	text: str
	icon: str
	ids: tuple[int, int]


def getDayOccurrenceData(
	curJd: int,
	groups: Iterable[EventGroup],
	tfmt: str = "HM$",
) -> list[DayOccurData]:
	data = []
	for groupIndex, group in enumerate(groups):
		if not group.enable:
			continue
		if not group.showInCal():
			continue
		# log.debug("\nupdateData: checking event", event.summary)
		gid = group.id
		color = group.color
		for item in group.occur.search(
			getEpochFromJd(curJd),
			getEpochFromJd(curJd + 1),
		):
			eid = item.eid
			epoch0 = item.start
			epoch1 = item.end
			event = group[eid]
			# ---
			text = event.getTextParts()
			# ---
			timeStr = ""
			if epoch1 - epoch0 < dayLen:
				jd0, hms0 = getJhmsFromEpoch(epoch0)
				if jd0 < curJd:
					hms0 = hms_zero
				if epoch1 - epoch0 < 1:
					timeStr = f"{hms0:{tfmt}}"
				else:
					jd1, hms1 = getJhmsFromEpoch(epoch1)
					if jd1 > curJd:
						hms1 = hms_24
					timeStr = f"{hms0:{tfmt}} - {hms1:{tfmt}}"
			# ---
			try:
				eventIndex = group.index(eid)
			except ValueError:
				eventIndex = event.modified  # FIXME
			data.append(
				(
					(epoch0, epoch1, groupIndex, eventIndex),  # FIXME for sorting
					DayOccurData(
						time=timeStr,
						time_epoch=(epoch0, epoch1),
						is_allday=epoch0 % dayLen + epoch1 % dayLen == 0,
						text=text,
						icon=event.getIconRel(),
						color=color,
						ids=(gid, eid),
						show=(
							group.showInDCal,
							group.showInWCal,
							group.showInMCal,
						),
						showInStatusIcon=group.showInStatusIcon,
					),
				),
			)
	data.sort(key=keyFuncIndex0)
	return [item[1] for item in data]


def getWeekOccurrenceData(
	curAbsWeekNumber: int,
	groups: Iterable[EventGroup],
	tfmt: str = "HM$",
) -> list[DayOccurData]:
	startJd = core.getStartJdOfAbsWeekNumber(curAbsWeekNumber)
	endJd = startJd + 7
	data = []

	def add(group: EventGroup, event: Event, eData: dict) -> None:
		eData["show"] = (
			group.showInDCal,
			group.showInWCal,
			group.showInMCal,
		)
		eData["ids"] = (group.id, event.id)
		data.append(eData)

	def handleEvent(event: Event, group: EventGroup) -> None:
		occur = event.calcEventOccurrenceIn(startJd, endJd)
		if not occur:
			return
		text = event.getText()
		icon = event.getIconRel()
		if isinstance(occur, JdOccurSet):
			for jd in occur.getDaysJdList():
				wnum, weekDay = core.getWeekDateFromJd(jd)
				if wnum != curAbsWeekNumber:
					continue
				add(
					group,
					event,
					WeekOccurData(
						weekDay=weekDay,
						time="",
						text=text,
						icon=icon,
					),
				)
		elif isinstance(occur, IntervalOccurSet):
			for startEpoch, endEpoch in occur.getTimeRangeList():
				jd1, hms1 = getJhmsFromEpoch(startEpoch)
				jd2, hms2 = getJhmsFromEpoch(endEpoch)
				wnum, weekDay = core.getWeekDateFromJd(jd1)
				if wnum != curAbsWeekNumber:
					continue
				if jd1 == jd2:
					add(
						group,
						event,
						WeekOccurData(
							weekDay=weekDay,
							time=f"{hms1:{tfmt}} - {hms2:{tfmt}}",
							text=text,
							icon=icon,
						),
					)
					continue
				# FIXME
				add(
					group,
					event,
					WeekOccurData(
						weekDay=weekDay,
						time=f"{hms1:{tfmt}} - {hms_24:{tfmt}}",
						text=text,
						icon=icon,
					),
				)
				for jd in range(jd1 + 1, jd2):
					wnum, weekDay = core.getWeekDateFromJd(jd)
					if wnum != curAbsWeekNumber:
						break
					add(
						group,
						event,
						WeekOccurData(
							weekDay=weekDay,
							time="",
							text=text,
							icon=icon,
						),
					)

				wnum, weekDay = core.getWeekDateFromJd(jd2)
				if wnum != curAbsWeekNumber:
					continue
				add(
					group,
					event,
					WeekOccurData(
						weekDay=weekDay,
						time=f"{hms_zero:{tfmt}} - {hms2:{tfmt}}",
						text=text,
						icon=icon,
					),
				)
		elif isinstance(occur, TimeListOccurSet):
			for epoch in occur.epochList:
				jd, hms = getJhmsFromEpoch(epoch)
				wnum, weekDay = core.getWeekDateFromJd(jd)
				if wnum != curAbsWeekNumber:
					continue
				add(
					group,
					event,
					WeekOccurData(
						weekDay=weekDay,
						time=f"{hms:{tfmt}}",
						text=text,
						icon=icon,
					),
				)
		else:
			raise TypeError

	for group in groups:
		if not group.enable:
			continue
		for event in group:
			if not event:
				continue
			handleEvent(event, group)

	return data


def getMonthOccurrenceData(
	curYear: int,
	curMonth: int,
	groups: Iterable[EventGroup],
	tfmt: str = "HM$",
) -> list[DayOccurData]:
	startJd, endJd = getJdRangeForMonth(curYear, curMonth, calTypes.primary)
	data = []

	def handleEvent(event: Event, group: EventGroup) -> None:
		occur = event.calcEventOccurrenceIn(startJd, endJd)
		if not occur:
			return
		text = event.getText()
		icon = event.getIconRel()
		ids = (group.id, event.id)
		if isinstance(occur, JdOccurSet):
			for jd in occur.getDaysJdList():
				y, m, d = jd_to_primary(jd)
				if y == curYear and m == curMonth:
					data.append(
						MonthOccurData(
							day=d,
							time="",
							text=text,
							icon=icon,
							ids=ids,
						),
					)
		elif isinstance(occur, IntervalOccurSet):
			for startEpoch, endEpoch in occur.getTimeRangeList():
				jd1, hms1 = getJhmsFromEpoch(startEpoch)
				jd2, hms2 = getJhmsFromEpoch(endEpoch)
				y, m, d = jd_to_primary(jd1)
				if not (y == curYear and m == curMonth):
					continue
				if jd1 == jd2:
					data.append(
						MonthOccurData(
							day=d,
							time=f"{hms1:{tfmt}} - {hms2:{tfmt}}",
							text=text,
							icon=icon,
							ids=ids,
						),
					)
					continue
				# FIXME
				data.append(
					MonthOccurData(
						day=d,
						time=f"{hms1:{tfmt}} - {hms_24:{tfmt}}",
						text=text,
						icon=icon,
						ids=ids,
					),
				)
				for jd in range(jd1 + 1, jd2):
					y, m, d = jd_to_primary(jd)
					if y == curYear and m == curMonth:
						data.append(
							MonthOccurData(
								day=d,
								time="",
								text=text,
								icon=icon,
								ids=ids,
							),
						)
					else:
						break
				y, m, d = jd_to_primary(jd2)
				if y == curYear and m == curMonth:
					data.append(
						MonthOccurData(
							day=d,
							time=f"{hms_zero:{tfmt}} - {hms2:{tfmt}}",
							text=text,
							icon=icon,
							ids=ids,
						),
					)
		elif isinstance(occur, TimeListOccurSet):
			for epoch in occur.epochList:
				jd, hms = getJhmsFromEpoch(epoch)
				y, m, d = jd_to_primary(jd1)
				if y == curYear and m == curMonth:
					data.append(
						MonthOccurData(
							day=d,
							time=f"{hms:{tfmt}}",
							text=text,
							icon=icon,
							ids=ids,
						),
					)
		else:
			raise TypeError

	for group in groups:
		if not group.enable:
			continue
		for event in group:
			if not event:
				continue
			handleEvent(event, group)
	return data
