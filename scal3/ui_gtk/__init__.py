from __future__ import annotations

from scal3 import logger

log = logger.get()

import gi

from scal3.ui_gtk.gtk_version import GTK_VERSION

# Gtk must be imported before Gdk and other
# in other to prevent ruff from re-ordering the following imports
# we call require_version right before importing each one

gi.require_version("Gtk", GTK_VERSION)
gi.require_version("Gdk", GTK_VERSION)
from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf

gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango as pango

# gi.require_version('Rsvg', '2.0')
# from gi.repository import Rsvg as rsvg

try:
	from gi.repository.GLib import (
		main_context_default,
		source_remove,
		timeout_add,
		timeout_add_seconds,
	)
except ImportError:
	from gi.repository.GObject import (
		main_context_default,
		source_remove,
		timeout_add,
		timeout_add_seconds,
	)

try:
	from gi.repository.GLib import Error as GLibError
except ImportError:
	from gi.repository.GObject import Error as GLibError  # type: ignore[assignment]

from scal3.ui_gtk.gtk_backend import (
	CursorType,
	Dialog,
	Menu,
	MenuItem,
	WindowEdge,
	add_style_provider,
	begin_resize_drag,
	connect_dialog_response,
	connect_draw,
	connect_monitor_changes,
	connect_window_drag_source,
	event_hits_interactive_child,
	events_pending,
	get_monitor,
	get_monitor_for_window,
	get_root_window_size,
	getScrollValue,
	initialize_gtk,
	install_backend,
	install_default_icon,
	main_iteration_do,
	new_cursor,
	pack,
	popup_menu_at,
	quit_application,
	run_application,
	set_widget_cursor,
	should_present_main_window,
)

install_backend()


__all__ = [
	"CursorType",
	"Dialog",
	"GLibError",
	"GdkPixbuf",
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
	"gdk",
	"getOrientation",
	"getScrollValue",
	"get_monitor",
	"get_monitor_for_window",
	"get_root_window_size",
	"gtk",
	"initialize_gtk",
	"install_default_icon",
	"main_context_default",
	"main_iteration_do",
	"new_cursor",
	"pack",
	"pango",
	"popup_menu_at",
	"quit_application",
	"run_application",
	"set_widget_cursor",
	"should_present_main_window",
	"source_remove",
	"timeout_add",
	"timeout_add_seconds",
	# "rsvg",
]


def getOrientation(vertical: bool) -> gtk.Orientation:
	if vertical:
		return gtk.Orientation.VERTICAL
	return gtk.Orientation.HORIZONTAL
