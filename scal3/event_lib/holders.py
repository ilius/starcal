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
	from collections.abc import Iterator
	from typing import Any


from .objects import EventObjTextModel
from .register import classes

__all__ = ["ObjectsHolderTextModel"]


class ObjectsHolderTextModel(EventObjTextModel):
	# keeps all objects in memory
	# Only use to keep groups and accounts, but not events
	skipLoadNoFile = True

	def __init__(self, _id: int | None = None) -> None:
		self.fs = None
		self.clear()

	def clear(self) -> None:
		self.byId = {}
		self.idList = []

	def __iter__(self) -> Iterator[Any]:
		for _id in self.idList:
			yield self.byId[_id]

	def __len__(self) -> int:
		return len(self.idList)

	def __bool__(self) -> bool:
		return bool(self.idList)

	def index(self, _id: int) -> Any:
		return self.idList.index(_id)
		# or get object instead of obj_id? FIXME

	def __getitem__(self, _id: int) -> Any:
		return self.byId.__getitem__(_id)

	def byIndex(self, index: int) -> Any:
		return self.byId[self.idList[index]]

	def __setitem__(self, _id: int, obj: Any) -> None:
		return self.byId.__setitem__(_id, obj)

	def insert(self, index: int, obj: Any) -> None:
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self.byId[obj.id] = obj
		self.idList.insert(index, obj.id)

	def append(self, obj: Any) -> None:
		if obj.id in self.idList:
			raise ValueError(f"{self} already contains id={obj.id}, {obj=}")
		self.byId[obj.id] = obj
		self.idList.append(obj.id)

	def delete(self, obj: Any) -> None:
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
		if obj.id in self.idByUuid:
			del self.idByUuid[obj.id]

	def pop(self, index: int) -> Any:
		return self.byId.pop(self.idList.pop(index))

	def moveUp(self, index: int) -> Any:
		return self.idList.insert(index - 1, self.idList.pop(index))

	def moveDown(self, index: int) -> Any:
		return self.idList.insert(index + 1, self.idList.pop(index))

	def setData(self, data: list[int]) -> None:
		self.clear()
		for sid in data:
			if not isinstance(sid, int) or sid == 0:
				raise RuntimeError(f"unexpected {sid=}, {self=}")
			id_ = sid
			id_ = abs(sid)
			try:
				cls = getattr(classes, self.childName).main
				obj = cls.load(self.fs, id_)
			except Exception:
				log.error(f"error loading {self.childName}")
				log.exception("")
				continue
			obj.parent = self
			obj.enable = sid > 0
			self.idList.append(id_)
			self.byId[obj.id] = obj

	def getData(self) -> list[int]:
		return [_id if self.byId[_id] else -_id for _id in self.idList]
