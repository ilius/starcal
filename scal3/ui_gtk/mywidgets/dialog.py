from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from scal3 import logger

log = logger.get()

from scal3.ui_gtk import (
	CursorType,
	Dialog,
	events_pending,
	gtk,
	main_iteration_do,
	new_cursor,
	set_widget_cursor,
)

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.ui_gtk import gdk

__all__ = ["MyDialog", "MyWindow"]


def newCursor(cursor_type: CursorType) -> gdk.Cursor:
	return new_cursor(cursor_type)


class MyWindow(gtk.Window):
	vbox: gtk.Box

	def startWaiting(self) -> None:
		self.queue_draw()
		self.vbox.set_sensitive(False)
		set_widget_cursor(self, newCursor(CursorType.WATCH))
		while events_pending():
			main_iteration_do(False)

	def endWaiting(self) -> None:
		set_widget_cursor(self, newCursor(CursorType.LEFT_PTR))
		if self.vbox:
			self.vbox.set_sensitive(True)

	def waitingDo[*Ts, R](
		self,
		func: Callable[[*Ts], R],
		*args: *Ts,
	) -> R | None:
		result = None
		self.startWaiting()
		if log.level >= logging.DEBUG:
			try:
				result = func(*args)
			finally:
				self.endWaiting()
			return result
		try:
			result = func(*args)
		finally:
			self.endWaiting()
		return result


class MyDialog(Dialog, MyWindow):  # type: ignore[misc]
	vbox: gtk.Box  # type: ignore[assignment]
