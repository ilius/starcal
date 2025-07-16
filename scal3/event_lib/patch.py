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

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType


__all__ = ["createPatchListFromGroup"]

def createPatchListFromGroup(
	group: EventGroupType,
    sinceEpoch: int,
) -> list[dict[str, Any]]:
	patchList = []

	for event in group:
		# if not event.remoteIds:  # FIXME
		eventHist = event.loadHistory()
		if not eventHist:
			log.info(f"{eventHist = }")
			continue
		# assert event.modified == eventHist[0][0]
		if eventHist[0][0] > sinceEpoch:
			creationEpoch = eventHist[-1][0]
			if creationEpoch > sinceEpoch:
				patchList.append(
					{
						"eventId": event.id,
						"eventType": event.name,
						"action": "add",
						"newEventData": event.getV4Dict(),
					},
				)
			else:
				sinceHash = None
				for tmpEpoch, tmpHash in eventHist:
					sinceHash = tmpHash
					if tmpEpoch <= sinceEpoch:
						break
				assert sinceHash is not None  # FIXME?
				patchList.append(
					event.createPatchByHash(sinceHash),
				)

	return patchList
