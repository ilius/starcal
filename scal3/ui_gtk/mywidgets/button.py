from __future__ import annotations

from scal3 import logger
from scal3.ui_gtk.signals import registerSignals

log = logger.get()

from time import time as now
from typing import TYPE_CHECKING, Any

from scal3 import ui
from scal3.ui_gtk import Dialog, gdk, gtk, pack, timeout_add

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["ConButton"]


@registerSignals
class ConButton(gtk.Button):
	signals: list[tuple[str, list[Any]]] = [
		("con-clicked", []),
	]

	def __init__(self, continuousClick: bool, button: int = 1) -> None:
		gtk.Button.__init__(self)
		self.pressTm = 0.0
		self.counter = 0
		self._button = button
		# ---
		if continuousClick:
			self.connect("button-press-event", self._onConPress)
			self.connect("button-release-event", self._onRelease)

	def _doTrigger(self) -> None:
		self.emit("con-clicked")

	def _onConPress(self, _w: gtk.Widget, gevent: gdk.Event) -> bool:
		if self._button is not None and gevent.button != self._button:
			return False
		self.pressTm = now()
		self._doTrigger()
		self.counter += 1
		timeout_add(
			ui.timeout_initial,
			self._onPressRemain,
			self._doTrigger,
			self.counter,
		)
		return True

	def _onRelease(self, _w: gtk.Widget, _ge: gdk.Event) -> bool:
		self.counter += 1
		return True

	def _onPressRemain(self, func: Callable[[], None], counter: int) -> None:
		if counter == self.counter and now() - self.pressTm >= ui.timeout_repeat / 1000:
			func()
			timeout_add(
				ui.timeout_repeat,
				self._onPressRemain,
				self._doTrigger,
				self.counter,
			)


if __name__ == "__main__":
	win = Dialog()
	button = ConButton(True)
	button.set_label("Press")

	def con_clicked(_widget: gtk.Widget) -> None:
		log.info(f"{now():.4f}\tcon-clicked")

	button.connect("con-clicked", con_clicked)
	pack(win.vbox, button, 1, 1)  # type: ignore[arg-type]
	win.vbox.show_all()  # type: ignore[attr-defined]
	win.resize(100, 100)
	win.run()
