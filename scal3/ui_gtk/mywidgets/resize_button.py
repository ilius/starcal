from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.ui_gtk import WindowEdge, begin_resize_drag, gtk
from scal3.ui_gtk.utils import imageFromFile

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk

__all__ = ["ResizeButton"]


class ResizeButton(gtk.EventBox):
	def __init__(
		self,
		win: gtk.Window,
		size: int = 20,
		edge: WindowEdge = WindowEdge.SOUTH_EAST,
	) -> None:
		gtk.EventBox.__init__(self)
		self.parentWin = win
		self.edge = edge
		# ---
		self.image = imageFromFile("resize-small.svg", size)
		self.add(self.image)
		self.connect("button-press-event", self.onButtonPress)

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		begin_resize_drag(
			self.parentWin,
			self.edge,
			gevent.button,
			int(gevent.x_root),
			int(gevent.y_root),
			gevent.time,
		)
		return True
