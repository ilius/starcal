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

from scal3 import logger
from scal3.locale_man import numDecode

__all__ = ["parseDroppedDate"]

log = logger.get()


def parseDroppedDate(text: str) -> tuple[int, int, int] | None:
	part = text.split("/")
	if len(part) != 3:
		return None
	try:
		num0 = numDecode(part[0])
		num1 = numDecode(part[1])
		num2 = numDecode(part[2])
	except ValueError:
		log.exception("")
		return None
	del part
	maxPart = max(num0, num1, num2)
	if maxPart <= 999:
		valid = 0 <= num0 <= 99 and 1 <= num1 <= 12 and 1 <= num2 <= 31
		if not valid:
			return None
		return (
			2000 + num0,
			num1,
			num2,
		)

	minMax = (
		(1000, 2100),
		(1, 12),
		(1, 31),
	)
	formats = (
		[0, 1, 2],
		[1, 2, 0],
		[2, 1, 0],
	)
	# "format" must be list because we use method "index"

	nums = [num0, num1, num2]

	def formatIsValid(fmt: list[int]) -> bool:
		for i, num in enumerate(nums):
			f = fmt[i]
			if not (minMax[f][0] <= num <= minMax[f][1]):
				return False
		return True

	for fmt in formats:
		if formatIsValid(fmt):
			return (
				nums[fmt.index(0)],
				nums[fmt.index(1)],
				nums[fmt.index(2)],
			)
	return None

	# FIXME: when drag from a persian GtkCalendar with format %y/%m/%d
	# if year < 100:
	# 	year += 2000
