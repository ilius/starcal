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

from typing import Any, NamedTuple

__all__ = [
	"CUSTOMIZE",
	"DAYCAL_WIN_LIVE",
	"LIVE",
	"MAIN_CONF",
	"NEED_RESTART",
	"NOT_SET",
	"OptionData",
]

MAIN_CONF = 1
LIVE = 2
CUSTOMIZE = 4
NEED_RESTART = 8
DAYCAL_WIN_LIVE = 16


class NOT_SET:
	pass


class OptionData(NamedTuple):
	name: str
	v3Name: str
	flags: int
	type: str
	where: str = ""
	desc: str = ""
	default: Any = NOT_SET
	valid: str = ""
