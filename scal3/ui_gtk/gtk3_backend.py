"""Public GTK compatibility surface for the GTK 3 backend."""

from __future__ import annotations

from typing import Any

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

__all__ = [
	"CursorType",
	"Dialog",
	"Menu",
	"MenuItem",
	"WindowEdge",
	"add_style_provider",
	"begin_resize_drag",
	"connect_dialog_response",
	"connect_draw",
	"connect_monitor_changes",
	"connect_window_drag_source",
	"event_hits_interactive_child",
	"events_pending",
	"getScrollValue",
	"get_monitor",
	"get_monitor_for_window",
	"get_root_window_size",
	"initialize_gtk",
	"install_backend",
	"install_default_icon",
	"main_iteration_do",
	"new_cursor",
	"pack",
	"popup_menu_at",
	"quit_application",
	"run_application",
	"set_widget_cursor",
	"should_present_main_window",
]

CursorType = gdk.CursorType
WindowEdge = gdk.WindowEdge
events_pending = gtk.events_pending
main_iteration_do = gtk.main_iteration_do


def pack(
	box: gtk.Box,
	child: gtk.Widget,
	expand: bool | int = False,
	fill: bool | int = False,
	padding: int = 0,
) -> None:
	if isinstance(box, gtk.Box):
		box.pack_start(child, bool(expand), bool(fill), padding)
	elif isinstance(box, gtk.CellLayout):
		raise TypeError("pack: use gtk.CellLayout.pack_start instead")
	else:
		raise TypeError(f"pack: unknown type {type(box)}")


class Menu(gtk.Menu):
	def __init__(self, reserve_toggle_size: bool = False) -> None:
		super().__init__()
		self.set_reserve_toggle_size(reserve_toggle_size)


class MenuItem(gtk.MenuItem):
	def __init__(self, label: str = "") -> None:
		self.text = label
		super().__init__(label=label)
		self.set_use_underline(True)


class Dialog(gtk.Dialog):
	vbox: gtk.Box  # type: ignore[assignment]

	def run(self) -> gtk.ResponseType:
		return gtk.Dialog.run(self)  # type: ignore[no-any-return, no-untyped-call]


def getScrollValue(gevent: gdk.EventScroll, last: str = "") -> str:
	value = gevent.direction.value_nick
	if value == "smooth":
		if gevent.delta_y < 0:
			value = "up"
		elif gevent.delta_y == 0 and last:
			return last
		else:
			value = "down"
	return value


def install_backend() -> None:
	pass


def connect_draw(widget: gtk.DrawingArea, callback: Any) -> None:
	widget.connect("draw", callback)


def connect_dialog_response(dialog: gtk.Dialog, callback: Any) -> None:
	dialog.connect("response", callback)


def begin_resize_drag(
	window: gtk.Window,
	edge: gdk.WindowEdge,
	button: int,
	x: float,
	y: float,
	timestamp: int,
) -> None:
	window.begin_resize_drag(edge, button, int(x), int(y), timestamp)


def new_cursor(cursor_type: gdk.CursorType) -> gdk.Cursor:
	display = gdk.Display.get_default()
	assert display is not None
	cursor = gdk.Cursor.new_for_display(display, cursor_type)
	assert cursor is not None
	return cursor


def set_widget_cursor(widget: gtk.Widget, cursor: gdk.Cursor) -> None:
	window = widget.get_window()
	if window is not None:
		window.set_cursor(cursor)


def add_style_provider(provider: gtk.CssProvider) -> None:
	screen = gdk.Screen.get_default()
	assert screen is not None
	gtk.StyleContext.add_provider_for_screen(
		screen,
		provider,
		gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
	)


def install_default_icon(icon_path: str, _source_dir: str) -> None:
	gtk.Window.set_default_icon_from_file(icon_path)


def get_monitor() -> gdk.Monitor | None:
	display = gdk.Display.get_default()
	assert display is not None
	monitor = display.get_monitor_at_point(1, 1)
	if monitor is None:
		monitor = display.get_primary_monitor()
	if monitor is None:
		monitor = display.get_monitor_at_window(gdk.get_default_root_window())
	return monitor


def get_root_window_size() -> tuple[int, int]:
	root = gdk.get_default_root_window()
	return root.get_width(), root.get_height()


def get_monitor_for_window(window: gtk.Window) -> gdk.Monitor | None:
	display = gdk.Display.get_default()
	assert display is not None
	gdk_window = window.get_window()
	if gdk_window is None:
		return None
	return display.get_monitor_at_window(gdk_window)


def connect_monitor_changes(callback: Any) -> None:
	screen = gdk.Screen.get_default()
	assert screen is not None
	screen.connect("size-changed", callback)


def initialize_gtk(argv: list[str]) -> None:
	gtk.init_check(argv)  # type: ignore[call-arg]


def run_application(_app: gtk.Application) -> None:
	gtk.main()


def quit_application(_app: gtk.Application) -> None:
	gtk.main_quit()


def should_present_main_window(
	action: str,
	has_status_icon: bool,
	_show_desktop_widget: bool,
) -> bool:
	return action == "show" or not has_status_icon


def popup_menu_at(
	menu: gtk.Menu,
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
	if position_func is not None:
		menu.popup(
			None,
			None,
			position_func,
			position_data,
			button,
			timestamp,
		)
		return
	if root is None:
		menu.popup(
			None,
			None,
			None,
			None,
			button,
			timestamp,
		)
		return
	coords = widget.translate_coordinates(root, int(x), int(y))
	if coords is None:
		raise RuntimeError("failed to translate popup-menu coordinates")
	x, y = coords
	window = root.get_window()
	assert window is not None
	_origin_ok, window_x, window_y = window.get_origin()
	x += window_x
	y += window_y
	if rtl:
		from scal3.ui_gtk.utils import get_menu_width

		x -= get_menu_width(menu)
	menu.popup(
		None,
		None,
		lambda *_args: (int(x), int(y), True),
		None,
		button,
		timestamp or gtk.get_current_event_time(),
	)


def event_hits_interactive_child(
	_widget: gtk.Widget,
	_event: Any,
) -> bool:
	return False


def connect_window_drag_source(widget: gtk.Widget, callback: Any) -> None:
	widget.connect("button-press-event", callback)
