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

from typing import IO, TYPE_CHECKING

from scal3 import ics

from .occur import (
	IntervalOccurSet,
	JdOccurSet,
	TimeListOccurSet,
)

if TYPE_CHECKING:
	from .pytypes import EventType

__all__ = ["exportEventToIcsFileObj"]


def exportEventToIcsFileObj(
	fp: IO[str],
	event: EventType,
	currentTimeStamp: str,
) -> None:
	# log.debug("exportToIcsFp", event.id)

	commonText = (
		"\n".join(
			[
				"BEGIN:VEVENT",
				"CREATED:" + currentTimeStamp,
				"DTSTAMP:" + currentTimeStamp,  # FIXME
				"LAST-MODIFIED:" + currentTimeStamp,
				"SUMMARY:" + event.getSummary().replace("\n", "\\n"),
				"DESCRIPTION:" + event.getDescription().replace("\n", "\\n"),
				# "CATEGORIES:" + self.title,  # FIXME
				"CATEGORIES:" + event.name,  # FIXME
				"LOCATION:",
				"SEQUENCE:0",
				"STATUS:CONFIRMED",
				"UID:" + event.icsUID(),
			],
		)
		+ "\n"
	)

	icsData = event.getIcsData()
	if icsData is not None:
		vevent = commonText
		for key, value in icsData:
			vevent += key + ":" + value + "\n"
		vevent += "END:VEVENT\n"
		fp.write(vevent)
		return

	occur = event.calcEventOccurrence()
	if not occur:
		return
	if isinstance(occur, JdOccurSet):
		# for sectionStartJd in occur.getDaysJdList():
		# 	sectionEndJd = sectionStartJd + 1
		for sectionStartJd, sectionEndJd in occur.calcJdRanges():
			vevent = commonText
			vevent += "\n".join(
				[
					"DTSTART;VALUE=DATE:" + ics.getIcsDateByJd(sectionStartJd),
					"DTEND;VALUE=DATE:" + ics.getIcsDateByJd(sectionEndJd),
					"TRANSP:TRANSPARENT",
					# http://www.kanzaki.com/docs/ical/transp.html
					"END:VEVENT\n",
				],
			)
			fp.write(vevent)
	elif isinstance(occur, IntervalOccurSet | TimeListOccurSet):
		for startEpoch, endEpoch in occur.getTimeRangeList():
			vevent = commonText
			parts = [
				"DTSTART:" + ics.getIcsTimeByEpoch(startEpoch),
			]
			if endEpoch is not None and endEpoch - startEpoch > 1:
				# FIXME why is endEpoch sometimes float?
				parts.append("DTEND:" + ics.getIcsTimeByEpoch(int(endEpoch)))
			parts += [
				"TRANSP:OPAQUE",  # FIXME
				# http://www.kanzaki.com/docs/ical/transp.html
				"END:VEVENT\n",
			]
			vevent += "\n".join(parts)
			fp.write(vevent)
	else:
		raise TypeError(f"invalid type {type(occur)} for occur")
