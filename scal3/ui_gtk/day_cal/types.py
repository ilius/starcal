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

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.signals import SignalHandlerType
	from scal3.ui_gtk.starcal_types import OptWidget

__all__ = ["MainWinType", "ParentWindowType"]


class ParentWindowType(Protocol):
	w: gtk.Widget
	win: gtk.Window

	def customizeShow(
		self,
		_widget: gtk.Widget,
	) -> None: ...


class MainWinType(Protocol):
	def dayInfoShow(self, _sig: SignalHandlerType | None = None) -> None: ...
	def onStatusIconClick(self, _w: OptWidget = None) -> None: ...
	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]: ...
