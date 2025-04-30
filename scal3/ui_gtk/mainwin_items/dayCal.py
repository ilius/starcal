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
from scal3.ui import conf
from scal3.ui_gtk.day_cal import DayCal
from scal3.ui_gtk.day_cal_config import ConfigHandlerBase
from scal3.ui_gtk.decorators import registerSignals

__all__ = ["CalObj"]


class ConfigHandler(ConfigHandlerBase):
	@property
	def dayParams(self):
		return conf.dcalDayParams

	@dayParams.setter
	def dayParams(self, value):
		conf.dcalDayParams = value

	@property
	def monthParams(self) -> list[dict] | None:
		return conf.dcalMonthParams

	@monthParams.setter
	def monthParams(self, value: list[dict]):
		conf.dcalMonthParams = value

	@property
	def weekdayParams(self) -> list[dict] | None:
		return conf.dcalWeekdayParams

	@weekdayParams.setter
	def weekdayParams(self, value: list[dict]) -> None:
		conf.dcalWeekdayParams = value

	@property
	def widgetButtonsEnable(self) -> bool | None:
		return conf.dcalWidgetButtonsEnable

	@widgetButtonsEnable.setter
	def widgetButtonsEnable(self, value: bool) -> None:
		conf.dcalWidgetButtonsEnable = value

	@property
	def widgetButtons(self) -> list[dict] | None:
		return conf.dcalWidgetButtons

	@widgetButtons.setter
	def widgetButtons(self, value: list[dict]) -> None:
		conf.dcalWidgetButtons = value

	@property
	def navButtonsEnable(self) -> bool | None:
		return conf.dcalNavButtonsEnable

	@navButtonsEnable.setter
	def navButtonsEnable(self, value: bool) -> None:
		conf.dcalNavButtonsEnable = value

	@property
	def navButtonsGeo(self) -> list[dict] | None:
		return conf.dcalNavButtonsGeo

	@navButtonsGeo.setter
	def navButtonsGeo(self, value: list[dict]) -> None:
		conf.dcalNavButtonsGeo = value

	@property
	def navButtonsOpacity(self) -> float | None:
		return conf.dcalNavButtonsOpacity

	@navButtonsOpacity.setter
	def navButtonsOpacity(self, value: bool) -> None:
		conf.dcalNavButtonsOpacity = value

	@property
	def eventIconSize(self) -> float | None:
		return conf.dcalEventIconSize

	@eventIconSize.setter
	def eventIconSize(self, value: float) -> None:
		conf.dcalEventIconSize = value

	@property
	def eventTotalSizeRatio(self) -> float | None:
		return conf.dcalEventTotalSizeRatio

	@eventTotalSizeRatio.setter
	def eventTotalSizeRatio(self, value: float) -> None:
		conf.dcalEventTotalSizeRatio = value

	@property
	def weekdayLocalize(self) -> bool | None:
		return conf.dcalWeekdayLocalize

	@weekdayLocalize.setter
	def weekdayLocalize(self, value: bool) -> None:
		conf.dcalWeekdayLocalize = value

	@property
	def weekdayAbbreviate(self) -> bool | None:
		return conf.dcalWeekdayAbbreviate

	@weekdayAbbreviate.setter
	def weekdayAbbreviate(self, value: bool) -> None:
		conf.dcalWeekdayAbbreviate = value

	@property
	def weekdayUppercase(self) -> bool | None:
		return conf.dcalWeekdayUppercase

	@weekdayUppercase.setter
	def weekdayUppercase(self, value: bool) -> None:
		conf.dcalWeekdayUppercase = value


@registerSignals
class CalObj(DayCal):
	expand = True

	def __init__(self, win, config: ConfigHandlerBase) -> None:
		DayCal.__init__(self, win, config=ConfigHandler())

	def do_get_preferred_height(self):  # noqa: PLR6301
		return 0, conf.winHeight / 3

	def getWindow(self):
		return self.win
