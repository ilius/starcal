#!/usr/bin/env python3
__all__ = [
	"gtk",
	"gdk",
	"GdkPixbuf",
	"pango",
	# "rsvg",
	"pack",
	"Box",
	"VBox",
	"HBox",
	"Menu",
	"TWO_BUTTON_PRESS",
	"MenuItem",
	"getScrollValue",
	"getOrientation",
	"timeout_add",
	"timeout_add_seconds",
	"source_remove",
	"GLibError",
]

from scal3 import logger
log = logger.get()

from typing import Optional

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("PangoCairo", "1.0")
# gi.require_version('Rsvg', '2.0')

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf
from gi.repository import Pango as pango
# from gi.repository import Rsvg as rsvg

try:
	from gi.repository.GLib import (
		timeout_add,
		timeout_add_seconds,
		source_remove,
	)
except ImportError:
	from gi.repository.GObject import (
		timeout_add,
		timeout_add_seconds,
		source_remove,
	)

try:
	from gi.repository.GLib import Error as GLibError
except ImportError:
	from gi.repository.GObject import Error as GLibError


TWO_BUTTON_PRESS = getattr(gdk.EventType, "2BUTTON_PRESS")


def pack(box, child, expand=False, fill=False, padding=0):
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand=expand, fill=fill, padding=padding)
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError(f"pack: unkown type {type(box)}")


def Box(vertical: Optional[bool] = None, **kwargs):
	if vertical is None:
		raise ValueError("vertical argument is missing")
	if vertical:
		orientation = gtk.Orientation.VERTICAL
	else:
		orientation = gtk.Orientation.HORIZONTAL
	return gtk.Box(orientation=orientation, **kwargs)


def VBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.VERTICAL, **kwargs)


def HBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


class Menu(gtk.Menu):
	def __init__(self, **kwargs):
		gtk.Menu.__init__(self, **kwargs)
		self.set_reserve_toggle_size(0)
		# self.imageSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)

	# def add(self, item):
	# 	gtk.Menu.add(self, item)
	# 	self.imageSizeGroup.add_widget(item.get_image())


"""
dir(gevent) == ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__gtype__', '__hash__', '__info__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_get_angle', '_get_center', '_get_distance', 'copy', 'delta_x', 'delta_y', 'device', 'direction', 'free', 'get', 'get_axis', 'get_button', 'get_click_count', 'get_coords', 'get_device', 'get_device_tool', 'get_event_sequence', 'get_event_type', 'get_keycode', 'get_keyval', 'get_pointer_emulated', 'get_root_coords', 'get_scancode', 'get_screen', 'get_scroll_deltas', 'get_scroll_direction', 'get_seat', 'get_source_device', 'get_state', 'get_time', 'get_window', 'handler_set', 'is_scroll_stop_event', 'is_stop', 'new', 'peek', 'put', 'request_motions', 'send_event', 'set_device', 'set_device_tool', 'set_screen', 'set_source_device', 'state', 'time', 'triggers_context_menu', 'type', 'window', 'x', 'x_root', 'y', 'y_root']
"""
def getScrollValue(gevent, last=""):
	"""
	return value is either "up" or "down"
	"""
	value = gevent.direction.value_nick
	# gevent.delta_x is always 0
	# gevent.get_keycode() is always (False, keycode=0)
	# gevent.get_scroll_deltas() is (True, delta_x={delta_x}, delta_y={delta_y})
	# gevent.is_scroll_stop_event() == (gevent.is_stop == 1)
	# is_scroll_stop_event is new in version 3.20.
	if value == "smooth":  # happens *sometimes* in PyGI (Gtk3)
		# log.debug(
		#	f"Scroll: value={value}, delta_y={gevent.delta_y}, " +
		#	f"is_stop={gevent.is_stop}={gevent.is_scroll_stop_event()}"
		#)
		if gevent.delta_y < 0:  # -1.0 (up)
			value = "up"
		elif gevent.delta_y == 0 and last:
			return last
		else:
			# most of the time delta_y=1.0, but sometimes 0.0, why?!
			# both mean "down" though
			value = "down"
	return value

def getOrientation(vertical: bool):
	if vertical:
		return gtk.Orientation.VERTICAL
	return gtk.Orientation.HORIZONTAL

class MenuItem(gtk.MenuItem):
	def __init__(self, label=""):
		gtk.MenuItem.__init__(self, label=label)
		self.set_use_underline(True)
