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

import typing
from typing import Any

if typing.TYPE_CHECKING:
	from scal3.option import Option
	from scal3.ui_gtk import gtk

__all__ = ["OptionUI"]


class OptionUI:
	option: Option[Any]
	# def __new__(cls, *args, **kwargs):
	# print("OptionUI:", args, kwargs)
	# obj = object.__new__(cls)
	# return obj

	def get(self) -> Any:
		raise NotImplementedError

	def set(self, value: Any) -> None:
		raise NotImplementedError

	def updateVar(self) -> None:
		self.option.v = self.get()

	def updateWidget(self) -> None:
		self.set(self.option.v)

	def getWidget(self) -> gtk.Widget:
		raise NotImplementedError
