#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

from scal3 import ui
from scal3.ui_gtk.day_cal import DayCal
from scal3.ui_gtk.decorators import *


@registerSignals
class CalObj(DayCal):
	expand = True

	dayParamsParam = "dcalDayParams"
	monthParamsParam = "dcalMonthParams"
	weekdayParamsParam = "dcalWeekdayParams"

	widgetButtonsEnableParam = "dcalWidgetButtonsEnable"
	widgetButtonsParam = "dcalWidgetButtons"

	navButtonsEnableParam = "dcalNavButtonsEnable"
	navButtonsGeoParam = "dcalNavButtonsGeo"
	navButtonsOpacityParam = "dcalNavButtonsOpacity"

	eventIconSizeParam = "dcalEventIconSize"
	eventTotalSizeRatioParam = "dcalEventTotalSizeRatio"
	weekdayLocalizeParam = "dcalWeekdayLocalize"
	weekdayAbbreviateParam = "dcalWeekdayAbbreviate"
	weekdayUppercaseParam = "dcalWeekdayUppercase"

	def do_get_preferred_height(self):
		return 0, ui.winHeight / 3

	def getWindow(self):
		return self.win
