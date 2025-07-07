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
from typing import TYPE_CHECKING, Any

from scal3.s_object import (
	SObjBinaryModel,
	objectDirName,
)

from . import state
from .object_base import EventObjTextModel

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.filesystem import FileSystem

__all__ = ["EventObjTextModel", "HistoryEventObjBinaryModel", "iterObjectFiles"]


class HistoryEventObjBinaryModel(SObjBinaryModel):
	uuid: str | None

	def set_uuid(self) -> None:
		from uuid import uuid4

		self.uuid = uuid4().hex

	def save(
		self,
		*args: Any,  # noqa: ANN002
	) -> tuple[int, str] | None:
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return None
		if hasattr(self, "uuid") and self.uuid is None:
			self.set_uuid()
		return SObjBinaryModel.save(self, *args)


def iterObjectFiles(fs: FileSystem) -> Iterable[tuple[str, str]]:
	for dname in fs.listdir(objectDirName):
		dpath = join(objectDirName, dname)
		if not fs.isdir(dpath):
			continue
		if len(dname) != 2:
			if dname.startswith("."):
				continue
			log.error(f"Unexpected directory: {dname}")  # do not skip it!
		for fname in fs.listdir(dpath):
			fpath = join(dpath, fname)
			if not fs.isfile(fpath):
				log.error(f"Object file does not exist or not a file: {fpath}")
				continue
			hash_ = dname + fname
			if len(hash_) != 40:
				log.debug(f"Skipping non-object file {fpath}")
				continue
			try:
				int(hash_, 16)
			except ValueError:
				log.debug(f"Skipping non-object file {fpath}  (not hexadecimal)")
				continue
			yield hash_, fpath
