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

from scal3 import logger

log = logger.get()

from scal3.locale_man import tr as _
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox

if TYPE_CHECKING:
	from scal3.ui_gtk import gtk

__all__ = ["PreferencesPluginsToolbar"]


class PreferencesWindowType(Protocol):
	def plugTreeviewTop(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewUp(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewDown(self, _w: gtk.Widget) -> None: ...
	def plugTreeviewBottom(self, _w: gtk.Widget) -> None: ...
	def onPlugAddClick(self, _w: gtk.Widget) -> None: ...
	def onPlugDeleteClick(self, _w: gtk.Widget) -> None: ...


class PreferencesPluginsToolbar(VerticalStaticToolBox):
	def __init__(self, parent: PreferencesWindowType) -> None:
		VerticalStaticToolBox.__init__(
			self,
			parent,
			# buttonBorder=0,
			# buttonPadding=0,
		)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		self.extend(
			[
				ToolBoxItem(
					name="goto-top",
					imageName="go-top.svg",
					onClick=parent.plugTreeviewTop,
					desc=_("Move to top"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=parent.plugTreeviewUp,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=parent.plugTreeviewDown,
					desc=_("Move down"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="goto-bottom",
					imageName="go-bottom.svg",
					onClick=parent.plugTreeviewBottom,
					desc=_("Move to bottom"),
					continuousClick=False,
				),
			],
		)
		self.buttonAdd = self.append(
			ToolBoxItem(
				name="add",
				imageName="list-add.svg",
				onClick=parent.onPlugAddClick,
				desc=_("Add"),
				continuousClick=False,
			),
		)
		self.buttonAdd.w.set_sensitive(False)
		self.append(
			ToolBoxItem(
				name="delete",
				imageName="edit-delete.svg",
				onClick=parent.onPlugDeleteClick,
				desc=_("Delete"),
				continuousClick=False,
			),
		)

	def setCanAdd(self, canAdd: bool) -> None:
		self.buttonAdd.w.set_sensitive(canAdd)
