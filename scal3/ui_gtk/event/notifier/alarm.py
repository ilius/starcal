from __future__ import annotations

from subprocess import PIPE, Popen
from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.event_lib.notifier_base import EventNotifier

# from scal3.ui_gtk import player

__all__ = ["WidgetClass", "notify"]


# class WidgetClass(player.PlayerBox):
# 	def __init__(self, notifier):
# 		self.notifier = notifier
# 		player.PlayerBox.__init__(self)
# 	def updateWidget(self):
# 		if self.notifier.alarmSound:
# 			self.openFile(self.notifier.alarmSound)
# 	def updateVars(self):
# 		self.notifier.alarmSound = self.getFile()


class WidgetClass(gtk.FileChooserButton):
	def __init__(self, notifier: EventNotifier) -> None:
		self.notifier = notifier
		gtk.FileChooserButton.__init__(self)
		self.set_title(_("Select Sound"))
		self.set_local_only(True)

	def updateWidget(self) -> None:
		if self.notifier.alarmSound:
			self.set_filename(self.notifier.alarmSound)

	def updateVars(self) -> None:
		self.notifier.alarmSound = self.get_filename()


# def notifyWait(notifier, finishFunc):
# 	if notifier.alarmSound and notifier.playerCmd:
# 		Popen(
# 			[
# 				notifier.playerCmd,
# 				notifier.alarmSound,
# 			],
# 			stdout=PIPE,
# 			stderr=PIPE,
# 		).communicate()
# 	# finishFunc()


def notify(notifier: EventNotifier, finishFunc: Callable[[], None]) -> None:
	# import thread
	# thread.start_new_thread(notifyWait, (notifier, finishFunc))
	finishFunc()
	Popen([notifier.playerCmd, notifier.alarmSound], stdout=PIPE, stderr=PIPE)


# event_lib.AlarmNotifier.WidgetClass = AlarmWidgetClass
# event_lib.AlarmNotifier.notify = notify
