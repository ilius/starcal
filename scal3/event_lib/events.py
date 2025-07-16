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

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _

from .event_base import Event
from .register import classes

if TYPE_CHECKING:
	from typing import Any


__all__ = [
	"Event",
]


@classes.event.register
class CustomEvent(Event):
	name = "custom"
	desc = _("Custom Event")
	isAllDay = False

	def getV4Dict(self) -> dict[str, Any]:
		data = Event.getV4Dict(self)
		data.update(
			{
				"rules": [
					{
						"type": ruleName,
						"value": rule.getServerString(),
					}
					for ruleName, rule in self.rulesDict.items()
				],
			},
		)
		return data
