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

from scal3.locale_man import tr as _
from scal3.ui_gtk.toolbox import ToolBoxItem, VerticalStaticToolBox

if TYPE_CHECKING:
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog


class EventManagerToolbar(VerticalStaticToolBox):
	def __init__(self, dialog: EventManagerDialog) -> None:
		VerticalStaticToolBox.__init__(self, dialog)
		# with iconSize < 20, the button would not become smaller
		# so 20 is the best size
		# self.append(ToolBoxItem(
		# 	name="goto-top",
		# 	imageName="go-top.svg",
		# 	onClick="",
		# 	desc=_("Move to top"),
		# 	continuousClick=False,
		# ))
		self.extend(
			[
				ToolBoxItem(
					name="go-up",
					imageName="go-up.svg",
					onClick=dialog.ops.moveUpByButton,
					desc=_("Move up"),
					continuousClick=False,
				),
				ToolBoxItem(
					name="go-down",
					imageName="go-down.svg",
					onClick=dialog.ops.moveDownByButton,
					desc=_("Move down"),
					continuousClick=False,
				),
				# ToolBoxItem(
				# 	name="goto-bottom",
				# 	imageName="go-bottom.svg",
				# 	onClick=dialog.,
				# 	desc=_("Move to bottom"),
				# 	continuousClick=False,
				# ),
				ToolBoxItem(
					name="duplicate",
					imageName="edit-copy.svg",
					onClick=dialog.ops.duplicateSelectedObj,
					desc=_("Duplicate"),
					continuousClick=False,
				),
			],
		)
