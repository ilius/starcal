#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import ui

fontFamily = ui.getFont()[0]

dayLen = 24 * 3600
minYearLenSec = 365 * dayLen
avgMonthLen = 30 * dayLen

unitSteps = (
	(3600, 12),
	(3600, 6),
	(3600, 3),
	(3600, 1),
	(60, 30),
	(60, 15),
	(60, 5),
	(60, 1),
	(1, 30),
	(1, 15),
	(1, 5),
	(1, 1),
)

