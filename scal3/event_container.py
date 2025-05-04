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

from scal3 import ui

__all__ = ["DummyEventContainer"]


class DummyEventContainer:
	def __init__(self, idsDict: dict[int, list[int]]) -> None:
		self.idsDict = idsDict

	def __len__(self) -> int:
		return sum(len(eventIds) for eventIds in self.idsDict.values())

	def __iter__(self):
		for groupId, eventIdList in self.idsDict.items():
			group = ui.eventGroups[groupId]
			for eventId in eventIdList:
				yield group[eventId]
