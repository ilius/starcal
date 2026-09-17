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

from scal3.plugin_man.base import BaseJsonPlugin

# importing these registers the built-in plugin classes
from scal3.plugin_man.holiday import HolidayPlugin  # noqa: F401
from scal3.plugin_man.ics import IcsTextPlugin  # noqa: F401
from scal3.plugin_man.loader import loadPlugin
from scal3.plugin_man.yearly_text import YearlyTextPlugin  # noqa: F401

__all__ = [
	"BaseJsonPlugin",
	"loadPlugin",
]
