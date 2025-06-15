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

from scal3 import core, logger

log = logger.get()

import json
from typing import TYPE_CHECKING, Self

from scal3.json_utils import dataToPrettyJson
from scal3.s_object import SObjTextModel

from . import state
from .pytypes import AccountType, EventGroupType

if TYPE_CHECKING:
	from collections.abc import Iterator

	from scal3.filesystem import FileSystem


__all__ = ["ObjectsHolderTextModel"]


class ObjectsHolderTextModel[T: (EventGroupType, AccountType)](SObjTextModel):
	# keeps all objects in memory
	# Only use to keep groups and accounts, but not events
	skipLoadNoFile = True

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> Self | None:
		fpath = cls.getFile(ident)
		data: list[int] = []
		if fs.isfile(fpath):
			try:
				with fs.open(fpath) as fp:
					jsonStr = fp.read()
				data = json.loads(jsonStr)
			except Exception:
				if not cls.skipLoadExceptions:
					raise
				return None
		else:
			log.debug(f"ObjectsHolderTextModel: {fpath=} does not exist")

		obj = cls(ident)
		obj.fs = fs
		obj.setList(data)
		return obj

	def save(self) -> None:
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		if not self.file:
			log.warning(
				f"save method called for object {self!r} while file is not set",
			)
			return

		jstr = dataToPrettyJson(self.getList())
		with self.fs.open(self.file, "w") as fp:
			fp.write(jstr)

	def __init__(
		self,
		ident: int | None = None,  # noqa: ARG002 # FIXME?
	) -> None:
		self.fs = core.fs
		self.clear()
		self.byId: dict[int, T] = {}
		self.idList: list[int] = []
		self.idByUuid: dict[str, int] = {}

	def clear(self) -> None:
		self.byId = {}
		self.idList = []

	def __iter__(self) -> Iterator[T]:
		for ident in self.idList:
			yield self.byId[ident]

	def __len__(self) -> int:
		return len(self.idList)

	def __bool__(self) -> bool:
		return bool(self.idList)

	def index(self, ident: int) -> int:
		return self.idList.index(ident)
		# or get object instead of obj id? FIXME

	def __getitem__(self, ident: int) -> T:
		return self.byId[ident]

	def byIndex(self, index: int) -> T:
		return self.byId[self.idList[index]]

	def __setitem__(self, ident: int, obj: T) -> None:
		return self.byId.__setitem__(ident, obj)

	def insert(self, index: int, obj: T) -> None:
		assert obj.id is not None
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self.byId[obj.id] = obj
		self.idList.insert(index, obj.id)

	def append(self, obj: T) -> None:
		assert obj.id is not None
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self.byId[obj.id] = obj
		self.idList.append(obj.id)

	def delete(self, obj: T) -> None:
		if obj.id not in self.idList:
			raise ValueError(f"{self} does not contains id={obj.id}, {obj=}")
		try:
			self.fs.removeFile(obj.file)
		except Exception:
			# FileNotFoundError, PermissionError, etc
			log.exception("")
		try:
			del self.byId[obj.id]
		except KeyError:
			log.exception("")
		try:
			self.idList.remove(obj.id)
		except ValueError:
			log.exception("")
		if obj.uuid in self.idByUuid:
			del self.idByUuid[obj.uuid]

	def pop(self, index: int) -> T:
		return self.byId.pop(self.idList.pop(index))

	def moveUp(self, index: int) -> None:
		self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index: int) -> None:
		self.idList.insert(index + 1, self.idList.pop(index))

	@classmethod
	def getMainClass(cls) -> type[T] | None:
		raise NotImplementedError

	def setList(self, data: list[int]) -> None:
		self.clear()
		for signed_id in data:
			if not isinstance(signed_id, int) or signed_id == 0:
				raise RuntimeError(f"unexpected {signed_id=}, {self=}")
			ident = abs(signed_id)
			cls = self.getMainClass()
			assert cls is not None
			obj = cls.load(ident, fs=self.fs)
			assert obj is not None
			assert obj.id == ident
			obj.enable = signed_id > 0
			self.idList.append(ident)
			self.byId[ident] = obj

	def getList(self) -> list[int]:
		return [ident if self.byId[ident] else -ident for ident in self.idList]
