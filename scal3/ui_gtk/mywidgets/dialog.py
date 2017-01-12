from scal3 import core
from scal3.ui_gtk import *


class MyDialog:
	def startWaiting(self):
		self.queue_draw()
		self.vbox.set_sensitive(False)
		self.get_window().set_cursor(gdk.Cursor.new(gdk.CursorType.WATCH))
		while gtk.events_pending():
			gtk.main_iteration_do(False)

	def endWaiting(self):
		gdkWin = self.get_window()
		if gdkWin:
			gdkWin.set_cursor(gdk.Cursor.new(gdk.CursorType.LEFT_PTR))
		if self.vbox:
			self.vbox.set_sensitive(True)

	def waitingDo(self, func, *args, **kwargs):
		result = None
		self.startWaiting()
		if core.debugMode:
			result = func(*args, **kwargs)
			self.endWaiting()
		else:
			try:
				result = func(*args, **kwargs)
			except Exception as e:
				raise e
			finally:
				self.endWaiting()
		return result
