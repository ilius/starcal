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

from scal3 import locale_man, logger
from scal3.datetime_utils import epochDateTimeEncode
from scal3.event_lib import ev
from scal3.event_lib.trash import EventTrash
from scal3.locale_man import tr as _
from scal3.ui_gtk.event.manager.conf import archivedGroupsRowId

if TYPE_CHECKING:
	from scal3.ui_gtk import gtk
	from scal3.ui_gtk.event.manager.dialog import EventManagerDialog

log = logger.get()


class StatusBar:
	"""Shows info about the selected tree row in the dialog status bar."""

	def __init__(self, dialog: EventManagerDialog) -> None:
		self.dialog = dialog

	def cursorChanged(self, _selection: gtk.TreeSelection | None = None) -> bool:
		path = self.dialog.tree.getSelectedPath()

		if not self.dialog.syncing:
			if path:
				self.cursorChangedPath(path)
			elif hasattr(self.dialog, "sbar"):
				self.dialog.sbar.push(0, "")

		self.dialog.toolbar.w.set_sensitive(bool(path))

		return True

	def cursorChangedPath(self, path: list[int]) -> None:
		text = ""
		modified: int | float | None = None
		if len(path) == 1:
			groupId = self.dialog.tree.getRowId(self.dialog.tree.iterFromPath(path))
			if groupId == archivedGroupsRowId:
				text = _("contains {groupCount} archived groups").format(
					groupCount=_(len(ev.archivedGroups)),
				)
				if hasattr(self.dialog, "sbar"):
					self.dialog.sbar.push(0, text)
				return
			group = self.dialog.tree.getGroupOrTrashByPath(path)
			assert group.id is not None
			if isinstance(group, EventTrash):
				text = _("contains {eventCount} events").format(
					eventCount=_(len(group)),
				)
			else:
				text = (
					_(
						"contains {eventCount} events and {occurCount} occurrences",
					).format(
						eventCount=_(len(group)),
						occurCount=_(group.occurCount),
					)
					+ _(",")
					+ " "
					+ _("Group ID: {groupId}").format(
						groupId=_(group.id),
					)
				)
			modified = group.modified
			# log.info(f"group, id = {group.id}, uuid = {group.uuid}")
		elif len(path) == 2:
			if self.dialog.tree.isArchivedGroupRow(path):
				group = ev.archivedGroups[
					self.dialog.tree.getRowId(self.dialog.tree.iterFromPath(path))
				]
				assert group.id is not None
				text = (
					_("contains {eventCount} events").format(
						eventCount=_(len(group)),
					)
					+ _(",")
					+ " "
					+ _("Group ID: {groupId}").format(
						groupId=_(group.id),
					)
				)
				modified = group.modified
			else:
				group, event = self.dialog.tree.getEventAndParentByPath(path)
				assert event.id is not None
				text = _("Event ID: {eventId}").format(eventId=_(event.id))
				modified = event.modified
				# log.info(f"event, id = {event.id}, uuid = {event.uuid}")
				for rule in event.rulesDict.values():
					log.debug(f"Rule {rule.name}: '{rule}', info='{rule.getInfo()}'")

		if modified is None:
			raise RuntimeError("modified is None")

		comma = _(",")
		modifiedLabel = _("Last Modified")
		modifiedTime = locale_man.textNumEncode(
			epochDateTimeEncode(modified),
		)
		text += f"{comma} {modifiedLabel}: {modifiedTime}"
		if hasattr(self.dialog, "sbar"):
			self.dialog.sbar.push(0, text)
