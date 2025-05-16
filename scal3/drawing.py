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

from scal3.locale_man import rtl

__all__ = ["getAbsPos"]


# TODO: make private
def oppositeAlign(align: str) -> str:
	if align == "left":
		return "right"
	if align == "right":
		return "left"
	if align == "top":
		return "buttom"
	if align == "buttom":
		return "top"
	return align


def getAbsPos(
	width: float,
	height: float,
	areaWidth: float,
	areaHeight: float,
	x: float,
	y: float,
	xalign: str,
	yalign: str,
	autoDir: bool = False,
) -> tuple[float, float]:
	if autoDir and rtl:
		xalign = oppositeAlign(xalign)
	if xalign == "right":
		x = areaWidth - width - x
	elif xalign == "center":
		x = (areaWidth - width) / 2.0 + x
	if yalign == "buttom":
		y = areaHeight - height - y
	elif yalign == "center":
		y = (areaHeight - height) / 2.0 + y
	return (x, y)
