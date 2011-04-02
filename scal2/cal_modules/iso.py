# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2010 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# Copyright (C) 2007 Mehdi Bayazee <Bayazee@Gmail.com>
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

import gregorian

## Return Julian day of given ISO year, week, and day
def to_jd(year, week, day):
    #assert week>0 and day>0 and day<=7
    jd0 = gregorian.to_jd(year-1, 12, 28)
    return day + 7*week + jd0 - jd0%7 - 1


## Return array of ISO (year, week, day) for Julian day
def jd_to(jd):
    year = gregorian.jd_to(jd - 3)[0]
    if jd>=to_jd(year+1, 1, 1):
        year += 1
    return (year, 
                    (jd - to_jd(year, 1, 1)) // 7 + 1, 
                    jd%7 + 1)


## Return Julian day of given ISO year, and day of year
iso_day_to_jd = lambda year, day: (day - 1) + gregorian.to_jd(year, 1, 1)

## Return array of ISO (year, day_of_year) for Julian day
def jd_to_iso_day(jd):
    year = gregorian.jd_to(jd)[0]
    day = jd - gregorian.to_jd(year, 1, 1) + 1
    return (year, day)



