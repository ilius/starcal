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

from scal3 import ui
from scal3.locale_man import rtl  # import scal3.locale_man after core
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk.layout import WinLayoutBox, WinLayoutObj
from scal3.ui_gtk.starcal_funcs import createPluginsText
from scal3.ui_gtk.utils import x_large

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk.cal_obj_base import CustomizableCalObj

__all__ = ["makeMainWinLayout"]


def makeMainWinLayout(
	createEventDayView: Callable[[], CustomizableCalObj],
	createWindowControllers: Callable[[], CustomizableCalObj],
	createStatusBar: Callable[[], CustomizableCalObj],
	createMainVBox: Callable[[], CustomizableCalObj],
	createRightPanel: Callable[[], CustomizableCalObj],
) -> WinLayoutBox:
	footer = WinLayoutBox(
		name="footer",
		desc="Footer",  # should not be seen in GUI
		vertical=True,
		expand=False,
		itemsMovable=True,
		itemsParam=conf.mainWinFooterItems,
		buttonSpacing=2,
		items=[
			WinLayoutObj(
				name="statusBar",
				desc=_("Status Bar"),
				enableParam=conf.statusBarEnable,
				vertical=False,
				expand=False,
				movable=True,
				buttonBorder=0,
				initializer=createStatusBar,
			),
			WinLayoutObj(
				name="pluginsText",
				desc=_("Plugins Text"),
				enableParam=conf.pluginsTextEnable,
				vertical=False,
				expand=False,
				movable=True,
				buttonBorder=0,
				initializer=createPluginsText,
			),
			WinLayoutObj(
				name="eventDayView",
				desc=_("Events of Day"),
				enableParam=conf.eventDayViewEnable,
				vertical=False,
				expand=False,
				movable=True,
				buttonBorder=0,
				initializer=createEventDayView,
			),
		],
	)
	footer.setItemsOrder(conf.mainWinFooterItems)
	return WinLayoutBox(
		name="layout",
		desc=_("Main Window"),
		vertical=True,
		expand=True,
		items=[
			WinLayoutObj(
				name="layout_winContronller",
				desc=_("Window Controller"),
				enableParam=conf.winControllerEnable,
				vertical=False,
				expand=False,
				initializer=createWindowControllers,
			),
			WinLayoutBox(
				name="middleBox",
				desc="Middle Box",  # should not be seen in GUI
				vertical=False,
				expand=True,
				items=[
					WinLayoutObj(
						name="mainPanel",
						desc=x_large(_("Main Panel")),
						vertical=True,
						expand=True,
						initializer=createMainVBox,
					),
					WinLayoutObj(
						name="rightPanel",
						desc=_("Right Panel"),
						enableParam=conf.mainWinRightPanelEnable,
						vertical=True,
						expand=False,
						labelAngle=90 if rtl else -90,
						initializer=createRightPanel,
						buttonBorder=int(ui.getFont().size),
					),
				],
			),
			footer,
		],
	)
