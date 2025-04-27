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


from os.path import join
from typing import TYPE_CHECKING

# from scal3.interval_utils import
from scal3.event_lib import state
from scal3.locale_man import tr as _

from .objects import HistoryEventObjBinaryModel
from .register import classes

if TYPE_CHECKING:
	from collections.abc import Iterator
	from typing import Any

	from scal3.s_object import FileSystem

	from .groups import EventGroup


__all__ = ["Account", "DummyAccount", "accountsDir"]
accountsDir = join("event", "accounts")


class DummyAccount:
	loaded = False
	enable = False
	params = ()
	paramsOrder = ()
	accountsDesc = {
		"google": _("Google"),
	}

	def __init__(self, _type: str, _id: int, title: str) -> None:
		self.name = _type
		self.desc = self.accountsDesc[_type]
		self.id = _id
		self.title = title

	def save(self) -> None:
		pass

	def load(
		cls,
		fs: FileSystem,
		*args,  # noqa: ANN002
	) -> None:
		pass

	def getLoadedObj(self) -> None:
		pass


# Should not be registered, or instantiate directly
@classes.account.setMain
class Account(HistoryEventObjBinaryModel):
	loaded = True
	name = ""
	desc = ""
	basicParams = (  # FIXME
		# "enable",
		"type",
	)
	params = (
		# "enable",
		"title",
		"remoteGroups",
	)
	paramsOrder = (
		# "enable",
		"type",
		"title",
		"remoteGroups",
	)

	@classmethod
	def getFile(cls, _id: int) -> str:
		return join(accountsDir, f"{_id}.json")

	@classmethod
	def iterFiles(cls, fs: FileSystem) -> Iterator[str]:
		for _id in range(1, state.lastIds.account + 1):
			fpath = cls.getFile(_id)
			if not fs.isfile(fpath):
				continue
			yield fpath

	@classmethod
	def getSubclass(cls, _type: str) -> type:
		return classes.account.byName[_type]

	def __bool__(self) -> bool:
		return True

	def __init__(self, _id: int | None = None) -> None:
		if _id is None:
			self.id = None
		else:
			self.setId(_id)
		self.enable = True
		self.title = "Account"

		# a list of dictionarise {"id":..., "title":...}
		self.remoteGroups = []

		# example for status: {"action": "pull", "done": 10, "total": 20}
		# action values: "fetchGroups", "pull", "push"
		self.status = None

	def save(self) -> None:
		if self.id is None:
			self.setId()
		HistoryEventObjBinaryModel.save(self)

	def setId(self, id_: int | None = None) -> None:
		if id_ is None or id_ < 0:
			id_ = state.lastIds.account + 1  # FIXME
			state.lastIds.account = id_
		elif id_ > state.lastIds.account:
			state.lastIds.account = id_
		self.id = id_
		self.file = self.getFile(self.id)

	def stop(self) -> None:
		self.status = None

	def fetchGroups(self) -> None:
		raise NotImplementedError

	def fetchAllEventsInGroup(self, _remoteGroupId: Any) -> list[dict]:
		raise NotImplementedError

	def sync(self, _group: EventGroup, _remoteGroupId: Any) -> None:
		raise NotImplementedError

	def getData(self) -> dict:
		data = HistoryEventObjBinaryModel.getData(self)
		data["type"] = self.name
		return data
