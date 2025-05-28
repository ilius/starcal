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
from scal3.event_lib.pytypes import AccountType
from scal3.s_object import SObjBinaryModel

log = logger.get()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any


import json
from os.path import join

# from scal3.interval_utils import
from .accounts import accountsDir
from .holders import ObjectsHolderTextModel
from .register import classes

__all__ = ["EventAccountsHolder"]


class EventAccountsHolder(ObjectsHolderTextModel[AccountType]):
	file = join("event", "account_list.json")

	@classmethod
	def getMainClass(cls) -> type[AccountType] | None:
		return classes.account.main  # type: ignore[return-value]

	def __init__(self, ident: int | None = None) -> None:
		ObjectsHolderTextModel.__init__(self)
		self.id = ident
		self.parent = None
		self.idByUuid: dict[str, int] = {}

	@staticmethod
	def loadClass(name: str) -> type[AccountType] | None:
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

	def loadData(self, ident: int) -> dict[str, Any] | None:
		objFile = join(accountsDir, f"{ident}.json")
		if not self.fs.isfile(objFile):
			log.error(
				f"error while loading account file {objFile!r}: file not found",
			)
			return None
			# FIXME: or raise FileNotFoundError?
		with self.fs.open(objFile) as fp:
			data = json.loads(fp.read())
		SObjBinaryModel.updateBasicData(data, objFile, "account", self.fs)
		# if data["id"] != ident:
		# 	log.error(
		# 		"attribute 'id' in json file " +
		# 		f"does not match the file name: {objFile}"
		# 	)
		# del data["id"]
		return data

	# FIXME: types
	def getLoadedObj(self, obj: AccountType) -> AccountType | None:
		ident = obj.id
		data = self.loadData(ident)
		assert data is not None
		name = data["type"]
		cls = self.loadClass(name)
		if cls is None:
			return None
		objNew = cls(ident)
		objNew.fs = self.fs
		objNew.setDict(data)
		return objNew

	def replaceDummyObj(self, obj: AccountType) -> AccountType:
		ident = obj.id
		objNew = self.getLoadedObj(obj)
		assert objNew is not None
		self.byId[ident] = objNew
		return objNew
