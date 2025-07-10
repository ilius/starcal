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


import os
import os.path
from os.path import join
from typing import TYPE_CHECKING

from scal3.locale_man import tr as _

from .event_base import Event
from .event_container import EventContainer
from .icon import WithIcon

if TYPE_CHECKING:
	from collections.abc import Iterable
	from typing import Any

	from scal3.filesystem import FileSystem


__all__ = ["EventTrash"]


class EventTrash(EventContainer, WithIcon):
	name = "trash"
	desc = _("Trash")
	file = join("event", "trash.json")
	skipLoadNoFile = True
	id = -1  # FIXME
	defaultIcon = "./user-trash.svg"

	@classmethod
	def iterFiles(cls, fs: FileSystem) -> Iterable[str]:
		if fs.isfile(cls.file):
			yield cls.file

	def __init__(self, ident: int) -> None:  # noqa: ARG002
		EventContainer.__init__(self, title=_("Trash"))
		self.icon = self.defaultIcon
		self.enable = False
		self.addEventsToBeginning = True

	def setDict(self, data: dict[str, Any]) -> None:
		EventContainer.setDict(self, data)
		if not self.icon or not os.path.isfile(self.icon):
			log.info(f"Trash icon {self.icon} does not exist, using {self.defaultIcon}")
			self.icon = self.defaultIcon

	def delete(self, eid: int) -> None:
		# different from EventContainer.remove
		# remove() only removes event from this group,
		# but event file and data still available
		# and probably will be added to another event container
		# but after delete(), there is no event file, and not event data
		if not isinstance(eid, int):
			raise TypeError("delete takes event ID that is integer")
		assert eid in self.idList, f"{eid=}, {self.idList=}"
		try:
			self.fs.removeFile(Event.getFile(eid))
		except Exception:
			log.exception("")
		else:
			self.idList.remove(eid)

	def empty(self) -> None:
		idList2 = self.idList.copy()
		for eid in self.idList:
			try:
				self.fs.removeFile(Event.getFile(eid))
			except Exception:
				log.exception("")
			idList2.remove(eid)
		self.idList = idList2
		self.save()
