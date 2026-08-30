"""GTK 3 week-calendar hit testing."""

from __future__ import annotations

from typing import Any

from scal3.ui_gtk import gtk

__all__ = ["find_column_at"]


def _contains(item_widget: gtk.Widget, window: Any) -> bool:
	if window == item_widget.get_window():
		return True
	if isinstance(item_widget, gtk.Container):
		return any(_contains(child, window) for child in item_widget.get_children())
	return False


def find_column_at(
	root: gtk.Widget,
	items: list[Any],
	event: Any,
) -> tuple[Any, int, int] | None:
	column_window = event.get_window()

	def find_item(candidates: list[Any]) -> Any | None:
		for item in candidates:
			nested = find_item(getattr(item, "items", []))
			if nested is not None:
				return nested
			if _contains(item.w, column_window):
				return item
		return None

	column = find_item(items)
	if column is None:
		return None
	coords = column.w.translate_coordinates(
		root,
		int(event.x),
		int(event.y),
	)
	if coords is None:
		return None
	return column, coords[0], coords[1]
