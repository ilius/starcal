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

from scal3 import logger
log = logger.get()

avgYearLen = 365.24219
springRefJd = 2456372.4597222223


def getSeasonValueFromJd(jd):
	return ((jd - springRefJd) % avgYearLen) / avgYearLen * 4.0


def getSpringJdAfter(fromJd):
	d, m = divmod(fromJd - 1 - springRefJd, avgYearLen)
	return int(fromJd + (d + 1) * avgYearLen)


"""

Spring - Above		3, 4, 5		March, April, May
Spring - Below		9, 10, 11	September, October, November

Summer - Above		6, 7, 8		June, July, August
Summer - Below		12, 1, 2	December, January, February

Autumn - Above		9, 10, 11	September, October, November
Autumn - Below		3, 4, 5		March, April, May

Winter - Above		12, 1, 2	December, January, February
Winter - Below		6, 7, 8		June, July, August

>>> monthShiftFunc = lambda month: ((month + 6) - 1) % 12 + 1


Wikipedia:
	Spring:
		in the US and UK, spring months are March, April and May,
		while in New Zealand and Australia, spring conventionally begins on
		September 1 and ends November 30
	Summer:
		The meteorological convention is to define summer as comprising the
		months of June, July, and August in the northern hemisphere and the
		months of December, January, and February in the southern hemisphere
	Autumn:
		with autumn being September, October, and November in the northern
		hemisphere, and March, April, and May in the southern hemisphere
	Winter:
		This corresponds to the months of December, January and February in
		the Northern Hemisphere, and June, July and August in the Southern
		Hemisphere

"""


def getSeasonNamePercentFromJd(jd, southernHemisphere=False):
	d, m = divmod(getSeasonValueFromJd(jd), 1)
	if southernHemisphere:
		d = (d + 2) % 4
	name = [
		"Spring",
		"Summer",
		"Autumn",
		"Winter",
	][int(d)]
	return name, m


def test():
	from scal3.cal_types.jalali import to_jd as jalali_to_jd
	for year in range(1390, 1400):
		# for month in (1, 4, 7, 10):
		for month in (1,):
			s = getSeasonFromJd(jalali_to_jd(year, month, 1))
			log.info(f"{year:04d}/{month:02d}/01\t{s:.5f}")
		# print


if __name__ == "__main__":
	test()
