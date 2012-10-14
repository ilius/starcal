# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License,    or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux


overlaps = lambda a0, a1, b0, b1: \
    a0 <= b0 <  a1 or \
    a0 <  b1 <= a1 or \
    b0 <= a0 <  b1 or \
    b0 <  a1 <= b1

def simplifyNumList(nums, minCount=3):## nums must be sorted, minCount >= 2
    ranges = []
    tmp = []
    for n in nums:
        if tmp and n - tmp[-1] != 1:
            if len(tmp)>minCount:
                ranges.append((tmp[0], tmp[-1]))
            else:
                ranges += tmp
            tmp = []
        tmp.append(n)
    if tmp:
        if len(tmp)>minCount:
            ranges.append((tmp[0], tmp[-1]))
        else:
            ranges += tmp
    return ranges

def cleanTimeRangeList(timeRangeList):
    num = len(timeRangeList)
    i = 0
    while i<num-1:
        if timeRangeList[i][1] == timeRangeList[i+1][0]:
            timeRangeList[i] = (timeRangeList[i][0], timeRangeList[i+1][1])
            timeRangeList.pop(i+1)
            num -= 1
        else:
            i += 1

def intersectionOfTwoTimeRangeList(rList1, rList2):
    #frontiers = []
    frontiers = set()
    for (start, end) in rList1 + rList2:
        frontiers.add(start)
        frontiers.add(end)
    frontiers = sorted(frontiers)
    partsNum = len(frontiers)-1
    partsContained = [[False, False] for i in range(partsNum)]
    for (start, end) in rList1:
        startIndex = frontiers.index(start)
        endIndex = frontiers.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][0] = True
    for (start, end) in rList2:
        startIndex = frontiers.index(start)
        endIndex = frontiers.index(end)
        for i in range(startIndex, endIndex):
            partsContained[i][1] = True
    result = []
    for i in range(partsNum):
        if partsContained[i][0] and partsContained[i][1]:
            result.append((frontiers[i], frontiers[i+1]))
    #cleanTimeRangeList(result)## not needed when both timeRangeList are clean!
    return result

