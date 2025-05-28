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
from scal3.color_utils import RGB
from scal3.event_lib.notifier_base import EventNotifier

log = logger.get()

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _

from .register import classes

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import ColorType
	from scal3.event_lib.pytypes import EventType


__all__ = ["AlarmNotifier", "FloatingMsgNotifier"]

classes.notifier.setMain(EventNotifier)


@classes.notifier.register
class AlarmNotifier(EventNotifier):
	name = "alarm"
	desc = _("Alarm")
	params = [
		"alarmSound",
		"playerCmd",
	]

	def __init__(self, event: EventType) -> None:
		EventNotifier.__init__(self, event)
		self.alarmSound = ""  # FIXME
		self.playerCmd = "mplayer"

	def notify(self, finishFunc: Callable) -> None:
		from scal3.ui_gtk.event.notifier.alarm import notify

		notify(self, finishFunc)


@classes.notifier.register
class FloatingMsgNotifier(EventNotifier):
	name = "floatingMsg"
	desc = _("Floating Message")
	params = [
		"fillWidth",
		"speed",
		"bgColor",
		"textColor",
	]

	def __init__(self, event: EventType) -> None:
		EventNotifier.__init__(self, event)
		# ---
		self.fillWidth = False
		self.speed = 100
		self.bgColor: ColorType = RGB(255, 255, 0)
		self.textColor: ColorType = RGB(0, 0, 0)

	def notify(self, finishFunc: Callable) -> None:
		from scal3.ui_gtk.event.notifier.floatingMsg import notify

		notify(self, finishFunc)


@classes.notifier.register
class WindowMsgNotifier(EventNotifier):
	name = "windowMsg"
	desc = _("Message Window")  # FIXME
	params = ["extraMessage"]

	def __init__(self, event: EventType) -> None:
		EventNotifier.__init__(self, event)
		# window icon, FIXME

	def notify(self, finishFunc: Callable) -> None:
		from scal3.ui_gtk.event.notifier.windowMsg import notify

		notify(self, finishFunc)


# @classes.notifier.register  # FIXME
class CommandNotifier(EventNotifier):
	name = "command"
	desc = _("Run a Command")
	params = [
		"command",
		"pyEval",
	]

	def __init__(self, event: EventType) -> None:
		EventNotifier.__init__(self, event)
		self.command = ""
		self.pyEval = False

	def notify(self, finishFunc: Callable) -> None:
		raise NotImplementedError
		# from scal3.ui_gtk.event.command.alarm import notify

		# notify(self, finishFunc)
