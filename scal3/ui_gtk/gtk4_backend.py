"""Public GTK compatibility surface for the GTK 4 backend."""

from __future__ import annotations

from enum import StrEnum
from os.path import join
from typing import Any

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from scal3.ui_gtk.gtk4_compat import (
	Dialog,
	Menu,
	MenuItem,
	begin_resize_drag,
	connect_draw,
	events_pending,
	getScrollValue,
	install_gtk4_patches,
	main_iteration_do,
	pack,
)
from scal3.ui_gtk.gtk4_tree import install_tree_patches
from scal3.ui_gtk.gtk4_widgets import install_widget_patches

__all__ = [
	"Dialog",
	"Menu",
	"MenuItem",
	"begin_resize_drag",
	"connect_dialog_response",
	"connect_draw",
	"events_pending",
	"getScrollValue",
	"main_iteration_do",
	"pack",
	"should_present_main_window",
]

WindowEdge = gdk.SurfaceEdge


class CursorType(StrEnum):
	FLEUR = "move"
	LEFT_PTR = "default"
	LEFT_SIDE = "w-resize"
	RIGHT_SIDE = "e-resize"
	WATCH = "wait"


def install_backend() -> None:
	install_gtk4_patches()
	install_tree_patches()
	install_widget_patches()


def connect_dialog_response(_dialog: gtk.Widget, _callback: Any) -> None:
	# Gtk4.AboutDialog is a Window and has no response signal.
	pass


def new_cursor(cursor_type: CursorType) -> gdk.Cursor:
	cursor = gdk.Cursor.new_from_name(cursor_type.value)
	if cursor is None:
		cursor = gdk.Cursor.new_from_name("default")
	assert cursor is not None
	return cursor


def set_widget_cursor(widget: gtk.Widget, cursor: gdk.Cursor) -> None:
	widget.set_cursor(cursor)


def add_style_provider(provider: gtk.CssProvider) -> None:
	display = gdk.Display.get_default()
	assert display is not None
	gtk.StyleContext.add_provider_for_display(
		display,
		provider,
		gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
	)


def install_default_icon(_icon_path: str, source_dir: str) -> None:
	display = gdk.Display.get_default()
	assert display is not None
	icon_theme = gtk.IconTheme.get_for_display(display)
	icon_theme.add_search_path(join(source_dir, "icons"))
	icon_theme.add_search_path(join(source_dir, "images"))
	gtk.Window.set_default_icon_name("starcal")


def get_monitor() -> gdk.Monitor | None:
	display = gdk.Display.get_default()
	assert display is not None
	monitor = display.get_monitors().get_item(0)
	return monitor if isinstance(monitor, gdk.Monitor) else None


def get_root_window_size() -> tuple[int, int]:
	return 1920, 1080


def get_monitor_for_window(window: gtk.Window) -> gdk.Monitor | None:
	display = gdk.Display.get_default()
	assert display is not None
	surface = window.get_surface()
	if surface is None:
		return None
	return display.get_monitor_at_surface(surface)


def connect_monitor_changes(callback: Any) -> None:
	display = gdk.Display.get_default()
	assert display is not None
	monitors = display.get_monitors()
	for index in range(monitors.get_n_items()):
		monitor = monitors.get_item(index)
		if isinstance(monitor, gdk.Monitor):
			monitor.connect("notify::geometry", callback)


def initialize_gtk(_argv: list[str]) -> None:
	pass


def run_application(app: gtk.Application) -> None:
	handler_id = app.connect("activate", lambda _app: None)
	try:
		app.run(None)
	finally:
		app.disconnect(handler_id)


def quit_application(app: gtk.Application) -> None:
	app.quit()


def should_present_main_window(
	action: str,
	has_status_icon: bool,
	show_desktop_widget: bool,
) -> bool:
	return action == "show" or (not has_status_icon and not show_desktop_widget)


def popup_menu_at(
	menu: Menu,
	widget: gtk.Widget,
	x: float,
	y: float,
	*,
	button: int = 3,
	timestamp: int = 0,
	position_func: Any = None,
	position_data: Any = None,
	root: gtk.Widget | None = None,
	rtl: bool = False,
) -> None:
	del button, timestamp, position_func, position_data, root, rtl
	rect = gdk.Rectangle()
	rect.x = int(x)
	rect.y = int(y)
	rect.width = 1
	rect.height = 1
	menu.popup_at_widget(widget, rect)


def event_hits_interactive_child(
	widget: gtk.Widget,
	event: Any,
) -> bool:
	picked = widget.pick(event.x, event.y, gtk.PickFlags.DEFAULT)
	while picked is not None and picked is not widget:
		if (
			isinstance(picked, (gtk.Button, gtk.DrawingArea))
			or picked.get_focusable()
			or getattr(picked, "_starcal_click_controller", None) is not None
		):
			return True
		picked = picked.get_parent()
	return False


def connect_window_drag_source(
	_widget: gtk.Widget,
	_callback: Any,
) -> None:
	pass
