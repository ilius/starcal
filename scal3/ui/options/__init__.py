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

from scal3.ui.options._base import (
	CUSTOMIZE,
	DAYCAL_WIN_LIVE,
	LIVE,
	MAIN_CONF,
	NEED_RESTART,
	NOT_SET,
	OptionData,
)
from scal3.ui.options.advanced import confOptionsData as _advancedData
from scal3.ui.options.appearance import confOptionsData as _appearanceData
from scal3.ui.options.day_cal import confOptionsData as _day_calData
from scal3.ui.options.main_panel import confOptionsData as _main_panelData
from scal3.ui.options.mainwin import confOptionsData as _mainwinData
from scal3.ui.options.misc import confOptionsData as _miscData
from scal3.ui.options.month_cal import confOptionsData as _month_calData
from scal3.ui.options.status_icon import confOptionsData as _status_iconData
from scal3.ui.options.week_cal import confOptionsData as _week_calData
from scal3.ui.options.win_controller import confOptionsData as _win_controllerData

__all__ = [
	"CUSTOMIZE",
	"DAYCAL_WIN_LIVE",
	"LIVE",
	"MAIN_CONF",
	"NEED_RESTART",
	"NOT_SET",
	"OptionData",
	"confOptionsData",
	"getParamNamesWithFlag",
]

confOptionsData: list[OptionData] = [
	*_mainwinData,
	*_appearanceData,
	*_status_iconData,
	*_advancedData,
	*_win_controllerData,
	*_month_calData,
	*_week_calData,
	*_day_calData,
	*_main_panelData,
	*_miscData,
]

_v3Names = [p.v3Name for p in confOptionsData]
assert len(_v3Names) == len(set(_v3Names))


def getParamNamesWithFlag(flag: int) -> list[str]:
	return [p.v3Name for p in confOptionsData if p.flags & flag > 0]
