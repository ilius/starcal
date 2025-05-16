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

from scal3.s_object import SObj

if TYPE_CHECKING:
	from collections.abc import Callable

	from .event_base import Event

__all__ = ["EventNotifier"]


# Should not be registered, or instantiate directly
class EventNotifier(SObj):
	name = ""
	tname = ""
	nameAlias = ""
	desc = ""
	params = ()

	def __init__(self, event: Event) -> None:
		self.event = event

	def getCalType(self) -> str:
		return self.event.calType

	def notify(self, finishFunc: Callable) -> None:
		pass
