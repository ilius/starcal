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

from scal3.ui import conf
from scal3.ui_gtk.day_cal import DayCal

if TYPE_CHECKING:
	from scal3.ui_gtk import gtk

__all__ = ["CalObj"]


class CalObj(DayCal):
	expand = True

	dayOptions = conf.dcalDayParams
	monthOptions = conf.dcalMonthParams
	weekdayOptions = conf.dcalWeekdayParams

	widgetButtonsEnable = conf.dcalWidgetButtonsEnable
	widgetButtons = conf.dcalWidgetButtons

	navButtonsEnable = conf.dcalNavButtonsEnable
	navButtonsGeo = conf.dcalNavButtonsGeo
	navButtonsOpacity = conf.dcalNavButtonsOpacity

	eventIconSize = conf.dcalEventIconSize
	eventTotalSizeRatio = conf.dcalEventTotalSizeRatio
	weekdayLocalize = conf.dcalWeekdayLocalize
	weekdayAbbreviate = conf.dcalWeekdayAbbreviate
	weekdayUppercase = conf.dcalWeekdayUppercase

	def do_get_preferred_height(self) -> tuple[int, int]:  # noqa: PLR6301
		return 0, int(conf.winHeight.v // 3)

	def getWindow(self) -> gtk.Window:
		return self.parentWin.win
