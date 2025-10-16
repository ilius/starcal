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

import logging
from copy import deepcopy

from scal3.path import APP_NAME

log = logging.getLogger(APP_NAME)

__all__ = [
	"ItemOption",
	"ListOption",
	"Option",
	"StrDictOption",
	"StringMappingProxyOption",
]


class Option[T]:
	__slots__ = ["_default", "_v"]

	def __init__(self, default: T) -> None:
		self._v = default
		self._default = deepcopy(default)

	@property
	def v(self) -> T:
		return self._v

	@v.setter
	def v(self, value: T) -> None:
		self._v = value

	@property
	def default(self) -> T:
		return self._default


class ListOption[T](Option[list[T]]):
	pass


# FIXME: broken
class DictOption[T: dict](Option[T]):  # type: ignore[type-arg]
	pass


class StrDictOption[T](Option[dict[str, T]]):
	pass


class ItemOption[T](Option[T]):
	__slots__ = ["_index", "_parent"]

	def __init__(self, parent: Option[list[T]], index: int) -> None:
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


class StringMappingProxyOption(Option[str]):
	def __init__(
		self,
		default: str,
		option: Option[str],
		mapping: dict[str, str],
	) -> None:
		super().__init__(default)
		self.mapping = mapping
		self.option = option
		option.v = mapping[default]

	@property
	def v(self) -> str:
		return self._v

	@v.setter
	def v(self, value: str) -> None:
		self._v = value
		self.option.v = self.mapping[value]
