from __future__ import annotations

from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk import gtk_ud as ud

__all__ = ["JustificationComboBox"]


class JustificationComboBox(gtk.ComboBox):
	keys = [name for name, desc, value in ud.justificationList]
	descs = [desc for name, desc, value in ud.justificationList]

	def __init__(self) -> None:
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		# ---
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 0)
		# ---
		for d in self.descs:
			ls.append([d])
		self.set_active(0)

	def getValue(self) -> str:
		return self.keys[self.get_active()]

	def setValue(self, value: str) -> None:
		self.set_active(self.keys.index(value))
