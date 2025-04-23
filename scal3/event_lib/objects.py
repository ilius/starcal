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


from scal3.event_lib import state
from scal3.s_object import (
	SObjBinaryModel,
	SObjTextModel,
)

__all__ = ["EventObjTextModel", "HistoryEventObjBinaryModel"]


class EventObjTextModel(SObjTextModel):
	def save(self) -> None:
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		SObjTextModel.save(self)


class HistoryEventObjBinaryModel(SObjBinaryModel):
	def set_uuid(self) -> None:
		from uuid import uuid4

		self.uuid = uuid4().hex

	def save(self, *args) -> None:
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		if hasattr(self, "uuid") and self.uuid is None:
			self.set_uuid()
		return SObjBinaryModel.save(self, *args)
