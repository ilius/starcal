from __future__ import annotations

from scal3 import logger

log = logger.get()

import gi

# Gtk must be imported before Gdk and other
# in other to prevent ruff from re-ordering the following imports
# we call require_version right before importing each one

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
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


__all__ = [
	"TWO_BUTTON_PRESS",
	"Box",
	"Dialog",
	"GLibError",
	"GdkPixbuf",
	"HBox",
	"Menu",
	"MenuItem",
	"VBox",
	"gdk",
	"getOrientation",
	"getScrollValue",
	"gtk",
	"main_context_default",
	"pack",
	"pango",
	"source_remove",
	"timeout_add",
	"timeout_add_seconds",
	# "rsvg",
]

TWO_BUTTON_PRESS = getattr(gdk.EventType, "2BUTTON_PRESS")


def pack(
	box: gtk.Box | gtk.CellLayout,
	child: gtk.Widget,
	expand: bool | int = False,
	fill: bool | int = False,
	padding: int = 0,
) -> None:
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand=bool(expand), fill=bool(fill), padding=padding)
	elif isinstance(box, gtk.CellLayout):
		raise TypeError("pack: use gtk.CellLayout.pack_start instead")
	else:
		raise TypeError(f"pack: unkown type {type(box)}")


def Box(vertical: bool | None = None, **kwargs) -> gtk.Box:
	if vertical is None:
		raise ValueError("vertical argument is missing")
	if vertical:
		orientation = gtk.Orientation.VERTICAL
	else:
		orientation = gtk.Orientation.HORIZONTAL
	return gtk.Box(orientation=orientation, **kwargs)


def VBox(**kwargs) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.VERTICAL, **kwargs)


def HBox(**kwargs) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


class Menu(gtk.Menu):
	def __init__(self, **kwargs) -> None:
		gtk.Menu.__init__(self, **kwargs)
		self.set_reserve_toggle_size(False)
		# self.imageSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)

	# def add(self, item):
	# 	gtk.Menu.add(self, item)
	# 	self.imageSizeGroup.add_widget(item.get_image())


def getScrollValue(gevent: gdk.EventScroll, last: str = "") -> str:
	"""Return value is either "up" or "down"."""
	value = gevent.direction.value_nick
	# gevent.delta_x is always 0
	# gevent.get_keycode() is always (False, keycode=0)
	# gevent.get_scroll_deltas() is (True, delta_x={delta_x}, delta_y={delta_y})
	# gevent.is_scroll_stop_event() == (gevent.is_stop == 1)
	# is_scroll_stop_event is new in version 3.20.
	if value == "smooth":  # happens *sometimes* in PyGI (Gtk3)
		# log.debug(
		# 	f"Scroll: {value=}, {gevent.delta_y=}, " +
		# 	f"{gevent.is_stop=}={gevent.is_scroll_stop_event()}"
		# )
		if gevent.delta_y < 0:  # -1.0 (up)
			value = "up"
		elif gevent.delta_y == 0 and last:
			return last
		else:
			# most of the time delta_y=1.0, but sometimes 0.0, why?!
			# both mean "down" though
			value = "down"
	return value


def getOrientation(vertical: bool) -> gtk.Orientation:
	if vertical:
		return gtk.Orientation.VERTICAL
	return gtk.Orientation.HORIZONTAL


class MenuItem(gtk.MenuItem):
	def __init__(self, label: str = "") -> None:
		self.text = label
		gtk.MenuItem.__init__(self, label=label)
		self.set_use_underline(True)


class Dialog(gtk.Dialog):
	vbox: gtk.Box  # type: ignore[assignment]
