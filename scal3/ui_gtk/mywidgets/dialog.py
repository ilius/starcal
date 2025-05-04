import logging

from scal3 import logger

log = logger.get()

from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk import gtk_ud as ud

__all__ = ["MyDialog"]


def newCursor(cursor_type: gdk.CursorType) -> gdk.Cursor:
	return gdk.Cursor.new_for_display(ud.display, cursor_type)


class MyDialog:
	def startWaiting(self) -> None:
		self.queue_draw()
		self.vbox.set_sensitive(False)
		self.get_window().set_cursor(newCursor(gdk.CursorType.WATCH))
		while gtk.events_pending():
			gtk.main_iteration_do(False)

	def endWaiting(self) -> None:
		gdkWin = self.get_window()
		if gdkWin:
			gdkWin.set_cursor(newCursor(gdk.CursorType.LEFT_PTR))
		if self.vbox:
			self.vbox.set_sensitive(True)

	def waitingDo(self, func, *args, **kwargs):
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
