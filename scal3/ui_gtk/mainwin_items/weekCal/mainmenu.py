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

from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.toolbox import ToolBoxItem

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk

	from .pytypes import WeekCalType

__all__ = ["MainMenuToolBoxItem"]


class MainMenuToolBoxItem(ToolBoxItem):
	hasOptions = True

	def __init__(self, wcal: WeekCalType) -> None:
		ToolBoxItem.__init__(
			self,
			name="mainMenu",
			imageNameDynamic=True,
			desc=_("Main Menu"),
			enableTooltip=True,
			continuousClick=False,
			onPress=self.onButtonPress,
		)
		self._wcal = wcal

	def onConfigChange(self) -> None:
		super().onConfigChange()
		self.updateImage()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.file import IconChooserOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		optionsWidget = gtk.Box(
			orientation=gtk.Orientation.VERTICAL,
			spacing=self.optionsPageSpacing,
		)
		# ---
		option = IconChooserOptionUI(
			option=conf.wcal_toolbar_mainMenu_icon,
			label=_("Icon"),
			live=True,
			onChangeFunc=self.updateImage,
		)
		pack(optionsWidget, option.getWidget())
		# ---
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def updateImage(self) -> None:
		self.setIconFile(conf.wcal_toolbar_mainMenu_icon.v)
		self.build()
		self.showHide()

	def getMenuPos(self) -> tuple[int, int]:
		wcal = self._wcal
		alloc = self.w.get_allocation()
		w = alloc.width
		h = alloc.height
		coords = self.w.translate_coordinates(wcal.w, 0, 0)
		assert coords is not None
		x0, y0 = coords
		return (
			x0 if rtl else x0 + w,
			y0 + h // 2,
		)

	def onButtonPress(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
		x, y = self.getMenuPos()
		self._wcal.s.emit(
			"popup-main-menu",
			x,
			y,
		)
