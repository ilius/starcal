import gtk
from gtk import gdk

class MyDialog:
    def startWaiting(self):
        self.queue_draw()
        self.vbox.set_sensitive(False)
        self.get_window().set_cursor(gdk.Cursor(gdk.WATCH))
        while gtk.events_pending():
            gtk.main_iteration_do(False)
    def endWaiting(self):
        self.get_window().set_cursor(gdk.Cursor(gdk.LEFT_PTR))
        self.vbox.set_sensitive(True)
    def waitingDo(self, func, *args, **kwargs):
        self.startWaiting()
        try:
            func(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            self.endWaiting()



