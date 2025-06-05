from __future__ import annotations

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk

__all__ = ["DirectionComboBox"]


class DirectionComboBox(gtk.ComboBox):
	keys = ["ltr", "rtl", "auto"]
	descs = [
		_("Left to Right"),
		_("Right to Left"),
		_("Auto"),
	]

	def __init__(self) -> None:
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		# ---
		cell = gtk.CellRendererText()
		self.pack_start(cell, expand=True)
		self.add_attribute(cell, "text", 0)
		# ---
		for d in self.descs:
			ls.append([d])
		self.set_active(0)

	def getValue(self) -> str:
		return self.keys[self.get_active()]

	def setValue(self, value: str) -> None:
		self.set_active(self.keys.index(value))
