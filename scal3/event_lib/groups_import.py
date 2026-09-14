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

__all__ = [
	"EventGroupsImportResult",
	"ImportMode",
	"importGroupEvents",
]


from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any

	from .group import EventGroup


class ImportMode(IntEnum):
	"""Strategy for handling events that already exist during import."""

	APPEND = 0
	SKIP_MODIFIED = 1
	OVERRIDE_MODIFIED = 2


class EventGroupsImportResult:
	"""Accumulates IDs of new and modified entities created during import."""

	def __init__(self) -> None:
		self.newGroupIds: set[int] = set()
		self.newEventIds: set[tuple[int, int]] = set()
		self.modifiedEventIds: set[tuple[int, int]] = set()

	def __add__(
		self,
		other: EventGroupsImportResult,
	) -> EventGroupsImportResult:
		r = EventGroupsImportResult()
		r.newGroupIds = self.newGroupIds | other.newGroupIds
		r.newEventIds = self.newEventIds | other.newEventIds
		r.modifiedEventIds = self.modifiedEventIds | other.modifiedEventIds
		return r


def importGroupEvents(
	group: EventGroup,
	events: list[dict[str, Any]],
	importMode: int,
) -> EventGroupsImportResult:
	"""Import event data dicts into a group, reporting new and modified event IDs."""
	res = EventGroupsImportResult()
	gid = group.id
	assert gid is not None

	if importMode == ImportMode.APPEND:
		for eventData in events:
			event = group.appendByData(eventData)
			assert event.id is not None
			res.newEventIds.add((gid, event.id))
		return res

	idByUuid = group.updateIdByUuid()

	for eventData in events:
		modified = eventData.get("modified")
		uuid = eventData.get("uuid")
		if modified is None or uuid is None:
			event = group.appendByData(eventData)
			assert event.id is not None
			res.newEventIds.add((gid, event.id))
			continue

		eid = idByUuid.get(uuid)
		if eid is None:
			log.debug(f"appending event uuid = {uuid}")
			event = group.appendByData(eventData)
			assert event.id is not None
			res.newEventIds.add((gid, event.id))
			continue

		if importMode != ImportMode.OVERRIDE_MODIFIED:
			# assumed ImportMode.SKIP_MODIFIED
			log.debug(f"skipping to override existing uuid={uuid!r}, eid={eid!r}")
			continue

		event = group.getEvent(eid)
		event.setDictOverride(eventData)
		event.save()
		res.modifiedEventIds.add((gid, eid))
		log.debug(f"overridden existing uuid={uuid!r}, eid={eid!r}")

	return res
