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

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.toolbox import (
	CustomizableToolBox,
	ToolBoxItem,
)

from .base import ColumnBase
from .mainmenu import MainMenuToolBoxItem
from .weeknum import WeekNumToolBoxItem

if TYPE_CHECKING:
	from scal3.ui_gtk.toolbox import BaseToolBoxItem

	from .pytypes import WeekCalType

__all__ = ["ToolbarColumn"]


# FIXME: multi-inheritance
class ToolbarColumn(CustomizableToolBox, ColumnBase):
	vertical = True
	desc = _("Toolbar (Vertical)")
	autoButtonPressHandler = False
	optionsPageSpacing = 5

	def __init__(self, wcal: WeekCalType) -> None:
		CustomizableToolBox.__init__(self, wcal)
		ColumnBase.__init__(self)
		self.defaultItems: list[BaseToolBoxItem] = [
			MainMenuToolBoxItem(wcal),
			WeekNumToolBoxItem(),
			ToolBoxItem(
				name="backward4",
				imageName="go-top.svg",
				onClick=wcal.goBackward4,
				desc="Backward 4 Weeks",
			),
			ToolBoxItem(
				name="backward",
				imageName="go-up.svg",
				onClick=wcal.goBackward,
				desc="Previous Week",
			),
			ToolBoxItem(
				name="today",
				imageName="go-home.svg",
				onClick=wcal.goToday,
				desc="Today",
				continuousClick=False,
			),
			ToolBoxItem(
				name="forward",
				imageName="go-down.svg",
				onClick=wcal.goForward,
				desc="Next Week",
			),
			ToolBoxItem(
				name="forward4",
				imageName="go-bottom.svg",
				onClick=wcal.goForward4,
				desc="Forward 4 Weeks",
			),
		]
		self.defaultItemsDict = {item.objName: item for item in self.defaultItems}
		if not ud.wcalToolbarData["items"]:
			ud.wcalToolbarData["items"] = [
				(item.objName, True) for item in self.defaultItems
			]
		self.setDict(ud.wcalToolbarData)

	def updateVars(self) -> None:
		super().updateVars()
		ud.wcalToolbarData = self.getDict()
