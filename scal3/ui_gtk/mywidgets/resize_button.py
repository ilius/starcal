from __future__ import annotations

from scal3.ui_gtk import gdk, gtk
from scal3.ui_gtk.utils import imageFromFile

__all__ = ["ResizeButton"]


class ResizeButton(gtk.EventBox):
	def __init__(
		self,
		win: gtk.Window,
		size: int = 20,
		edge: gdk.WindowEdge = gdk.WindowEdge.SOUTH_EAST,
	) -> None:
		gtk.EventBox.__init__(self)
		self.parentWin = win
		self.edge = edge
		# ---
		self.image = imageFromFile("resize-small.svg", size)
		self.add(self.image)
		self.connect("button-press-event", self.onButtonPress)

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		self.parentWin.begin_resize_drag(
			self.edge,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
		return True
