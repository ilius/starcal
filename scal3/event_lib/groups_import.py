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
	"IMPORT_MODE_APPEND",
	"IMPORT_MODE_OVERRIDE_MODIFIED",
	"IMPORT_MODE_SKIP_MODIFIED",
	"EventGroupsImportResult",
]


(
	IMPORT_MODE_APPEND,
	IMPORT_MODE_SKIP_MODIFIED,
	IMPORT_MODE_OVERRIDE_MODIFIED,
) = range(3)


class EventGroupsImportResult:
	def __init__(self):
		self.newGroupIds = set()  # type: Set[int]
		self.newEventIds = set()  # type: Set[Tuple[int, int]]
		self.modifiedEventIds = set()  # type: Set[Tuple[int, int]]

	def __add__(
		self,
		other: EventGroupsImportResult,
	) -> EventGroupsImportResult:
		r = EventGroupsImportResult()
		r.newGroupIds = self.newGroupIds | other.newGroupIds
		r.newEventIds = self.newEventIds | other.newEventIds
		r.modifiedEventIds = self.modifiedEventIds | other.modifiedEventIds
		return r
