# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Saeed Rasooli <saeed.gnu@gmail.com>
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

def getSeasonValueFromJd(jd):
    jd0 = 2456372.4597222223
    yearLen = 365.24219
    return ((jd-jd0) % yearLen) / yearLen * 4.0

def getSeasonNamePercentFromJd(jd):
    d, m = divmod(getSeasonValueFromJd(jd), 1)
    name = [
        'Spring',
        'Summer',
        'Autumn',
        'Winter',
    ][int(d)]
    return name, m


def test():
    from scal2.cal_types.jalali import to_jd as jalali_to_jd
    for year in range(1390, 1400):
        #for month in (1, 4, 7, 10):
        for month in (1,):
            s = getSeasonFromJd(jalali_to_jd(year, month, 1))
            print '%.4d/%.2d/01\t%.5f'%(year, month, s)
        #print
    

if __name__=='__main__':
    test()
