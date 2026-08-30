"""GTK 3 timezone selector implementation."""

from __future__ import annotations

from typing import Any

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack

__all__ = ["TimeZoneComboBoxEntry"]


class TimeZoneComboBoxEntry(gtk.Box):
	def __init__(self) -> None:
		from mytz.tree import getZoneInfoTree

		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		model = gtk.TreeStore(str, bool)
		self._listStore = model
		self.c = gtk.ComboBoxText.new_with_entry()
		pack(self, self.c, 1, 1)
		self.c.set_model(model)
		self.c.set_entry_text_column(0)

		first_cell = self.c.get_cells()[0]
		self.c.add_attribute(first_cell, "sensitive", 1)

		child = self.c.get_child()
		assert isinstance(child, gtk.Entry), f"{child=}"
		child.set_text(str(locale_man.localTz))
		self.get_text = child.get_text
		self.set_text = child.set_text

		recent_iter = model.append(None, [_("Recent..."), False])
		for tz_name in conf.localTzHist.v:
			model.append(recent_iter, [tz_name, True])
		self.appendOrderedDict(None, getZoneInfoTree())

	def appendOrderedDict(
		self,
		parent_iter: gtk.TreeIter | None,
		data: dict[str, Any],
	) -> None:
		model = self._listStore
		for key, value in data.items():
			if isinstance(value, dict):
				itr = model.append(parent_iter, [key, False])
				self.appendOrderedDict(itr, value)
			else:
				model.append(parent_iter, [key, True])
