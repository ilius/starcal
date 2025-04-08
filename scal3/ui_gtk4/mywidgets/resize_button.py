from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk.utils import imageFromFile


class ResizeButton(gtk.EventBox):
	def __init__(self, win, size=20, edge=gdk.WindowEdge.SOUTH_EAST):
		gtk.EventBox.__init__(self)
		self.win = win
		self.edge = edge
		# ---
		self.image = imageFromFile("resize-small.svg", size)
		self.add(self.image)
		self.connect("button-press-event", self.onButtonPress)

	def onButtonPress(self, _obj, gevent):
		self.win.begin_resize_drag(
			self.edge,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
		return True
