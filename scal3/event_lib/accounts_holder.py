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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any


from os.path import join

from scal3.json_utils import jsonToData

# from scal3.interval_utils import
from scal3.s_object import (
	updateBasicDataFromBson,
)

from .accounts import Account, DummyAccount, accountsDir
from .holders import ObjectsHolderTextModel
from .register import classes

__all__ = ["EventAccountsHolder"]


class EventAccountsHolder(ObjectsHolderTextModel):
	file = join("event", "account_list.json")
	childName = "account"

	def __init__(self, _id: int | None = None) -> None:
		ObjectsHolderTextModel.__init__(self)
		self.id = None
		self.parent = None
		self.idByUuid = {}

	@staticmethod
	def loadClass(name: str) -> type:
		cls = classes.account.byName.get(name)
		if cls is not None:
			return cls
		try:
			__import__(f"scal3.account.{name}")
		except ImportError:
			log.exception("")
		else:
			cls = classes.account.byName.get(name)
			if cls is not None:
				return cls
		log.error(
			f'error while loading account: no account type "{name}"',
		)
		return None

	def loadData(self, _id: int) -> dict[str, Any]:
		objFile = join(accountsDir, f"{_id}.json")
		if not self.fs.isfile(objFile):
			log.error(
				f"error while loading account file {objFile!r}: file not found",
			)
			return
			# FIXME: or raise FileNotFoundError?
		with self.fs.open(objFile) as fp:
			data = jsonToData(fp.read())
		updateBasicDataFromBson(data, objFile, "account", self.fs)
		# if data["id"] != _id:
		# 	log.error(
		# 		"attribute 'id' in json file " +
		# 		f"does not match the file name: {objFile}"
		# 	)
		# del data["id"]
		return data

	# FIXME: types
	def getLoadedObj(self, obj: DummyAccount) -> Account:
		id_ = obj.id
		data = self.loadData(id_)
		name = data["type"]
		cls = self.loadClass(name)
		if cls is None:
			return
		obj = cls(id_)
		obj.fs = self.fs
		data = self.loadData(id_)
		obj.setData(data)
		return obj

	def replaceDummyObj(self, obj: DummyAccount) -> Account:
		id_ = obj.id
		obj = self.getLoadedObj(obj)
		self.byId[id_] = obj
		return obj
