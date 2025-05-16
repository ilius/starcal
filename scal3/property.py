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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence

__all__ = ["ItemProperty", "Property"]


class Property[T]:
	__slots__ = ["_default", "_v"]

	def __init__(self, default: T) -> None:
		self._default = default
		if hasattr(default, "copy"):
			self._v = default.copy()
		else:
			self._v = default

	@property
	def v(self) -> T:
		return self._v

	@v.setter
	def v(self, value: T) -> None:
		self._v = value

	@property
	def default(self) -> T:
		return self._default


class ItemProperty[T](Property[T]):
	__slots__ = ["_index", "_parent"]

	def __init__(self, parent: Property[Sequence[T]], index: int) -> None:
		self._parent = parent
		self._index = index

	@property
	def v(self) -> T:
		return self._parent.v[self._index]

	@v.setter
	def v(self, value: T) -> None:
		self._parent.v[self._index] = value

	@property
	def default(self) -> T:
		return self._parent.default[self._index]
