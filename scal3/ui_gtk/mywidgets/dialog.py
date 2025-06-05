from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from scal3 import logger

log = logger.get()

from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["MyDialog", "MyWindow"]


def newCursor(cursor_type: gdk.CursorType) -> gdk.Cursor:
	cur = gdk.Cursor.new_for_display(ud.display, cursor_type)
	assert cur is not None
	return cur


class MyWindow(gtk.Window):
	vbox: gtk.Box

	def startWaiting(self) -> None:
		self.queue_draw()
		self.vbox.set_sensitive(False)
		win = self.get_window()
		assert win is not None
		win.set_cursor(newCursor(gdk.CursorType.WATCH))
		while gtk.events_pending():
			gtk.main_iteration_do(False)

	def endWaiting(self) -> None:
		gdkWin = self.get_window()
		if gdkWin:
			gdkWin.set_cursor(newCursor(gdk.CursorType.LEFT_PTR))
		if self.vbox:
			self.vbox.set_sensitive(True)

	def waitingDo(self, func: Callable, *args, **kwargs) -> Any:
		result = None
		self.startWaiting()
		if log.level >= logging.DEBUG:
			try:
				result = func(*args, **kwargs)
			finally:
				self.endWaiting()
			return result
		try:
			result = func(*args, **kwargs)
		finally:
			self.endWaiting()
		return result


class MyDialog(gtk.Dialog, MyWindow):  # type: ignore[misc]
	vbox: gtk.Box  # type: ignore[assignment]
