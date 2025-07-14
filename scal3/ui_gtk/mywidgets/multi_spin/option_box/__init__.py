from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from scal3.ui_gtk import Menu, MenuItem, gdk, gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin import MultiSpinButton
from scal3.ui_gtk.signals import registerSignals
from scal3.ui_gtk.utils import imageClassButton

if TYPE_CHECKING:
	from scal3.mywidgets.multi_spin import Field

__all__ = ["MultiSpinOptionBox"]


@registerSignals
class MultiSpinOptionBox[F: Field[Any], V](gtk.Box):
	signals: ClassVar[list[tuple[str, list[Any]]]] = [
		("activate", []),
	]

	def _entry_activate(self, _w: gtk.Widget) -> bool:
		# self.spin.update() #?????
		# self.add_history()
		self.emit("activate")
		return False

	def __init__(
		self,
		field: F,
		spacing: int = 0,
		hist_size: int = 10,
	) -> None:
		gtk.Box.__init__(
			self,
			orientation=gtk.Orientation.HORIZONTAL,
			spacing=spacing,
		)
		self.spin: MultiSpinButton[F, V] = MultiSpinButton(
			field=field,
		)
		pack(self, self.spin, 1, 1)
		self.hist_size = hist_size
		self.option = imageClassButton(
			"pan-down-symbolic",
			"down",  # FIXME: same class as decrease button?
			MultiSpinButton.buttonSize,
		)
		pack(self, self.option, 1, 1)
		self.menu = Menu()
		# self.menu.show()
		self.option.connect("button-press-event", self.option_pressed)
		self.menuItems: list[MenuItem] = []
		# self.option.set_sensitive(False) #???????
		# self.spin._entry_activate = self._entry_activate
		self.spin.connect("activate", self._entry_activate)
		self.get_value = self.spin.get_value
		self.set_value = self.spin.set_value

	def option_pressed(self, _w: gtk.Widget, gevent: gdk.EventButton) -> None:
		# x, y, w, h = self.option.
		self.menu.popup(
			None,
			None,
			None,
			None,
			gevent.button,
			gevent.time,
		)

	def find_text(self, text: str) -> int:
		for index, item in enumerate(self.menuItems):
			if item.text == text:
				return index
		return -1

	def add_history(self) -> None:
		self.spin.update()
		text = self.spin.get_text()
		index = self.find_text(text)
		if index == 0:
			return
		if index > 0:
			self.menu.remove(self.menuItems.pop(index))
		# m.prepend([text]) # self.combo.prepend_text(text)
		item = MenuItem(text)
		item.connect("activate", lambda _obj: self.spin.set_text(text))
		item.text = text
		self.menu.add(item)
		self.menu.reorder_child(item, 0)
		self.menuItems.insert(0, item)
		if len(self.menuItems) > self.hist_size:
			self.menu.remove(self.menuItems.pop(-1))
		self.menu.show_all()
		# self.option.set_sensitive(True) #???????

	def clear_history(self) -> None:
		for item in self.menu.get_children():
			self.menu.remove(item)
