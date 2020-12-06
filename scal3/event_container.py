# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux


from scal3 import ui


class DummyEventContainer(object):
	def __init__(self, idsDict: "Dict[int, List[int]]"):
		self.idsDict = idsDict

	def __len__(self):
		return sum(
			len(eventIds)
			for eventIds in self.idsDict.values()
		)

	def __iter__(self):
		for groupId, eventIdList in self.idsDict.items():
			group = ui.eventGroups[groupId]
			for eventId in eventIdList:
				yield group[eventId]

	def iterGroups(self):
		for groupId, eventIdList in self.idsDict.items():
			yield ui.eventGroups[groupId]
