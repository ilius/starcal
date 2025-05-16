from __future__ import annotations

from scal3 import logger

log = logger.get()

from time import time as now
from typing import TYPE_CHECKING

from scal3 import ui
from scal3.ui_gtk import gdk, gtk, pack, timeout_add
from scal3.ui_gtk.decorators import registerSignals

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["ConButton", "ConButtonBase"]


class ConButtonBase:
	def __init__(self, button: int | None = None) -> None:
		self.pressTm = 0
		self.counter = 0
		self._button = button
		# ---
		self.connect("button-press-event", self.onPress)
		self.connect("button-release-event", self.onRelease)

	def doTrigger(self) -> None:
		self.emit("con-clicked")

	def onPress(self, _widget: gtk.Widget, gevent: gdk.Event) -> bool | None:
		if self._button is not None and gevent.button != self._button:
			return
		self.pressTm = now()
		self.doTrigger()
		self.counter += 1
		timeout_add(
			ui.timeout_initial,
			self.onPressRemain,
			self.doTrigger,
			self.counter,
		)
		return True

	def onRelease(self, _widget: gtk.Widget, _gevent: gdk.Event) -> bool:
		self.counter += 1
		return True

	def onPressRemain(self, func: Callable, counter: int) -> None:
		if counter == self.counter and now() - self.pressTm >= ui.timeout_repeat / 1000:
			func()
			timeout_add(
				ui.timeout_repeat,
				self.onPressRemain,
				self.doTrigger,
				self.counter,
			)


@registerSignals
class ConButton(gtk.Button, ConButtonBase):
	signals = [
		("con-clicked", []),
	]

	def __init__(self, *args, **kwargs) -> None:
		gtk.Button.__init__(self, *args, **kwargs)
		ConButtonBase.__init__(self)


if __name__ == "__main__":
	win = gtk.Dialog()
	button = ConButton("Press")

	def con_clicked(_widget: gtk.Widget) -> None:
		log.info(f"{now():.4f}\tcon-clicked")

	button.connect("con-clicked", con_clicked)
	pack(win.vbox, button, 1, 1)
	win.vbox.show_all()
	win.resize(100, 100)
	win.run()
