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

import json
from typing import TYPE_CHECKING, Self

from scal3.filesystem import null_fs
from scal3.json_utils import dataToPrettyJson
from scal3.s_object import SObjTextModel

from . import state
from .pytypes import AccountType, EventGroupType

if TYPE_CHECKING:
	from collections.abc import Iterator

	from scal3.filesystem import FileSystem


__all__ = ["ObjectsHolderTextModel"]


class ObjectsHolderTextModel[T: (EventGroupType, AccountType)](SObjTextModel):
	"""In-memory container for groups or accounts, backed by a JSON list of IDs."""

	# keeps all objects in memory
	# only for keeping groups and accounts, not events or rules
	skipLoadNoFile = True

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> Self:
		"""Load the holder and its objects from a JSON ID list file."""
		fpath = cls.getFile(ident)
		data: list[int] = []
		if fs.isfile(fpath):
			with fs.open(fpath) as fp:
				jsonStr = fp.read()
			data = json.loads(jsonStr)
		else:
			log.debug(f"ObjectsHolderTextModel: {fpath=} does not exist")

		obj = cls(ident)
		obj.fs = fs
		obj._setList(data)
		return obj

	def save(self) -> None:
		"""Write the ID list to disk as a JSON file."""
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		if not self.file:
			log.warning(
				f"save method called for object {self!r} while file is not set",
			)
			return

		jstr = dataToPrettyJson(self._getList())
		with self.fs.open(self.file, "w") as fp:
			fp.write(jstr)

	def __init__(
		self,
		ident: int | None = None,  # noqa: ARG002 # FIXME?
	) -> None:
		self.fs = null_fs
		self._clear()
		self._byId: dict[int, T] = {}
		self.idList: list[int] = []
		self._idByUuid: dict[str, int] = {}

	def _clear(self) -> None:
		"""Remove all objects from this holder."""
		self._byId = {}
		self.idList = []

	def __iter__(self) -> Iterator[T]:
		for ident in self.idList:
			yield self._byId[ident]

	def __len__(self) -> int:
		return len(self.idList)

	def __bool__(self) -> bool:
		return bool(self.idList)

	def index(self, ident: int) -> int:
		"""Return the positional index of an object ID in the list."""
		return self.idList.index(ident)
		# or get object instead of obj id? FIXME

	def __getitem__(self, ident: int) -> T:
		return self._byId[ident]

	def byIndex(self, index: int) -> T:
		"""Return the object at the given positional index."""
		return self._byId[self.idList[index]]

	def __setitem__(self, ident: int, obj: T) -> None:
		return self._byId.__setitem__(ident, obj)

	def insert(self, index: int, obj: T) -> None:
		"""Insert an object at the given position in the ID list."""
		assert obj.id is not None
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self._byId[obj.id] = obj
		self.idList.insert(index, obj.id)

	def append(self, obj: T) -> None:
		"""Append an object to the end of the ID list."""
		assert obj.id is not None
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self._byId[obj.id] = obj
		self.idList.append(obj.id)

	def delete(self, obj: T) -> None:
		"""Remove an object from the holder and delete its file from disk."""
		if obj.id not in self.idList:
			raise ValueError(f"{self} does not contains id={obj.id}, {obj=}")
		try:
			self.fs.removeFile(obj.file)
		except Exception:
			# FileNotFoundError, PermissionError, etc
			log.exception("")
		try:
			del self._byId[obj.id]
		except KeyError:
			log.exception("")
		try:
			self.idList.remove(obj.id)
		except ValueError:
			log.exception("")
		if obj.uuid in self._idByUuid:
			del self._idByUuid[obj.uuid]

	def exclude(self, obj: T) -> None:
		"""Remove an object from the holder without deleting its file."""
		if obj.id not in self.idList:
			raise ValueError(f"{self} does not contains id={obj.id}, {obj=}")
		try:
			del self._byId[obj.id]
		except KeyError:
			log.exception("")
		try:
			self.idList.remove(obj.id)
		except ValueError:
			log.exception("")
		if obj.uuid in self._idByUuid:
			del self._idByUuid[obj.uuid]

	def _pop(self, index: int) -> T:
		"""Remove and return the object at the given positional index."""
		return self._byId.pop(self.idList.pop(index))

	def moveUp(self, index: int) -> None:
		"""Move the object at the given index one position earlier in the list."""
		self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index: int) -> None:
		"""Move the object at the given index one position later in the list."""
		self.idList.insert(index + 1, self.idList.pop(index))

	@classmethod
	def getMainClass(cls) -> type[T] | None:
		"""Return the main class of the held objects; implemented by subclasses."""
		raise NotImplementedError

	def _setList(self, data: list[int]) -> None:
		"""Load objects from a list of signed IDs (negative means disabled)."""
		self._clear()
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
			self._byId[ident] = obj

	def _getList(self) -> list[int]:
		"""Return signed IDs, negating the ID of disabled objects."""
		return [ident if self._byId[ident] else -ident for ident in self.idList]
