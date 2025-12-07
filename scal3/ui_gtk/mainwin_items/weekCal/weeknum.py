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
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk
from scal3.ui_gtk.toolbox import LabelToolBoxItem

if TYPE_CHECKING:
	from gi.repository import GObject

__all__ = ["WeekNumToolBoxItem"]


class WeekNumToolBoxItem(LabelToolBoxItem):
	def __init__(self) -> None:
		LabelToolBoxItem.__init__(
			self,
			name="weekNum",
			onClick=self.onClick,
			desc=("Week Number"),
			continuousClick=False,
		)
		self.label.set_direction(gtk.TextDirection.LTR)

	def updateLabel(self) -> None:
		if conf.wcal_toolbar_weekNum_negative.v:
			n = ui.cells.current.weekNumNeg
		else:
			n = ui.cells.current.weekNum
		self.label.set_label(_(n))

	def onDateChange(self) -> None:
		super().onDateChange()
		self.updateLabel()

	def onClick(self, _obj: GObject.Object) -> None:
		conf.wcal_toolbar_weekNum_negative.v = not conf.wcal_toolbar_weekNum_negative.v
		self.updateLabel()
		ui.saveLiveConf()
