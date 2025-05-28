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
		self.c = gtk.ComboBoxText.new_with_entry()
		pack(self, self.c, 1, 1)
		# gtk.ComboBoxText.__init__(self)
		self.c.set_model(model)
		self.c.set_entry_text_column(0)

		first_cell = self.c.get_cells()[0]

		# self.c.add_attribute(first_cell, "text", 0)
		# above line causes this warning:
		# Cannot connect attribute 'text' for cell renderer class
		# 'GtkCellRendererText' since 'text' is already attributed to column 0

		self.c.add_attribute(first_cell, "sensitive", 1)

		self.c.connect("changed", self.onChanged)
		child = self.c.get_child()
		child.set_text(str(locale_man.localTz))
		# self.set_text(str(locale_man.localTz)) # FIXME
		# ---
		self.get_text = child.get_text
		# self.get_text = self.c.get_active_text # FIXME
		self.set_text = child.set_text
		# -----
		recentIter = model.append(
			None,
			[
				_("Recent..."),
				False,
			],
		)
		for tz_name in conf.localTzHist.v:
			model.append(recentIter, [tz_name, True])
		# ---
		self.appendOrderedDict(
			None,
			getZoneInfoTree(),
		)

	def appendOrderedDict(self, parentIter: gtk.TreeIter, dct: dict[str, Any]) -> None:
		model = self.c.get_model()
		for key, value in dct.items():
			if isinstance(value, dict):
				itr = model.append(parentIter, [key, False])
				self.appendOrderedDict(itr, value)
			else:
				itr = model.append(parentIter, [key, True])

	def onChanged(self, _w: gtk.Widget) -> None:
		model = self.c.get_model()
		itr = self.c.get_active_iter()
		if itr is None:
			return
		path = model.get_path(itr)
		if path[0] == 0:
			self.set_text(model.get(itr, 0)[0])
			return

		self.set_text(
			"/".join(
				[
					model.get(
						model.get_iter(path[: i + 1]),
						0,
					)[0]
					for i in range(len(path))
				],
			),
		)


if __name__ == "__main__":
	diolog = gtk.Dialog()
	w = TimeZoneComboBoxEntry()
	pack(diolog.vbox, w)
	diolog.vbox.show_all()
	diolog.run()
