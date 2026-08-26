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


from scal3.s_object import (
	SObjTextModel,
)

from . import state

__all__ = ["EventObjTextModel"]


class EventObjTextModel(SObjTextModel):
	"""Text-based model that respects the global read-only flag when saving."""

	def save(self) -> None:
		"""Save this object unless events are in read-only mode."""
		if state.allReadOnly:
			log.info(f"events are read-only, ignored file {self.file}")
			return
		super().save()
