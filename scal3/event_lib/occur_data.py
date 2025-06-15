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

from scal3.time_utils import (
	HMS,
	getEpochFromJd,
	getJhmsFromEpoch,
)

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.color_utils import ColorType

	from .pytypes import EventGroupType

__all__ = ["DayOccurData", "getDayOccurrenceData"]

dayLen = 86400
hms_zero = HMS()
hms_24 = HMS(24)
keyFuncIndex0 = operator.itemgetter(0)


class DayOccurData(NamedTuple):
	time: str
	time_epoch: tuple[int, int]
	is_allday: bool
	text: list[str]
	icon: str | None
	color: ColorType
	ids: tuple[int, int]
	show: tuple[bool, bool, bool]  # (showInDCal, showInWCal, showInMCal)
	showInStatusIcon: bool


class WeekOccurData(NamedTuple):
	weekDay: int
	time: str
	text: str
	icon: str
	ids: tuple[int, int]


class MonthOccurData(NamedTuple):
	day: int
	time: str
	text: str
	icon: str
	ids: tuple[int, int]


def getDayOccurrenceData(
	curJd: int,
	groups: Iterable[EventGroupType],
	tfmt: str = "HM$",
) -> list[DayOccurData]:
	data = []
	for groupIndex, group in enumerate(groups):
		if not group.enable:
			continue
		if not group.showInCal():
			continue
		assert group.occur is not None
		# log.debug("\nupdateData: checking event", event.summary)
		gid = group.id
		assert gid is not None
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
			eventSortValue: float
			try:
				eventSortValue = group.index(eid)
			except ValueError:
				eventSortValue = event.modified
			data.append(
				(
					(epoch0, epoch1, groupIndex, eventSortValue),  # FIXME for sorting
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
