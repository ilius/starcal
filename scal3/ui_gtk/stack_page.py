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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from gi.repository import Gtk as gtk

	from scal3.ui_gtk.pytypes import CustomizableCalObjType

__all__ = ["StackPage"]


class StackPage:
	def __init__(self) -> None:
		self.pageWidget: gtk.Box | None = None
		self.pageParent: str = ""
		self.pageName: str = ""
		self.pagePath: str = ""
		self.pageTitle: str = ""
		self.pageLabel: str = ""
		self.pageIcon: str = ""
		self.pageExpand: bool = True
		self.pageItem: CustomizableCalObjType | None = None
		self.iconSize: int = 0

	def __str__(self) -> str:
		return (
			f"StackPage(pageName={self.pageName!r}, pagePath={self.pagePath!r}, "
			f"pageParent={self.pageParent!r})"
		)

	def __repr__(self) -> str:
		return self.__str__()
