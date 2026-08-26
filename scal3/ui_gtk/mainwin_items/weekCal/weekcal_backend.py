"""GTK 4 week-calendar hit testing."""

from __future__ import annotations

from typing import Any

from scal3.ui_gtk import gtk


def find_column_at(
	root: gtk.Widget,
	items: list[Any],
	event: Any,
) -> tuple[Any, int, int] | None:
	picked = root.pick(event.x, event.y, gtk.PickFlags.DEFAULT)
	if picked is None:
		return None

	def find_item(candidates: list[Any]) -> Any | None:
		for item in candidates:
			item_widget = getattr(item, "w", None)
			widget = picked
			while widget is not None:
				if widget is item_widget:
					nested = find_item(getattr(item, "items", []))
					return nested or item
				widget = widget.get_parent()
		return None

	column = find_item(items)
	if column is None:
		return None
	return column, int(event.x), int(event.y)
