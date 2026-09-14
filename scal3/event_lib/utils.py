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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any


def listToDict(value: Any) -> dict[Any, Any]:
	"""Convert a list of (key, value) pairs into a dict, passing dicts through."""
	if not isinstance(value, list):
		assert isinstance(value, dict)
		return value
	valueDict = {}
	for item in value:
		if len(item) != 2:
			continue
		if not isinstance(item[0], tuple | list):
			continue
		valueDict[tuple(item[0])] = item[1]
	return valueDict
