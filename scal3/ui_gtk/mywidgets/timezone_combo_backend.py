"""GTK 4 timezone selector implementation."""

from __future__ import annotations

from scal3 import locale_man
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack


class TimeZoneComboBoxEntry(gtk.Box):
	def __init__(self) -> None:
		from mytz.tree import getZoneInfoTree

		super().__init__(orientation=gtk.Orientation.HORIZONTAL)
		entry = gtk.Entry()
		entry.set_text(str(locale_man.localTz))
		pack(self, entry, 1, 1)
		self.get_text = entry.get_text
		self.set_text = entry.set_text

		def flatten(data: dict[str, object], prefix: str = "") -> list[str]:
			result: list[str] = []
			for key, value in data.items():
				name = f"{prefix}/{key}" if prefix else key
				if isinstance(value, dict):
					result.extend(flatten(value, name))
				else:
					result.append(name)
			return result

		zone_names = list(
			dict.fromkeys(
				[
					*conf.localTzHist.v,
					*flatten(getZoneInfoTree()),
				]
			),
		)
		dropdown = gtk.DropDown.new_from_strings(zone_names)
		dropdown.set_selected(gtk.INVALID_LIST_POSITION)

		def on_selected(combo: gtk.DropDown, _pspec: object) -> None:
			selected = combo.get_selected()
			if selected != gtk.INVALID_LIST_POSITION:
				entry.set_text(zone_names[selected])

		dropdown.connect("notify::selected", on_selected)
		pack(self, dropdown)
