"""GTK3 API compatibility shims for GTK4."""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Any

import gi
from gi.repository import Gdk, GdkPixbuf, GLib, GObject, Gtk

try:
	gi.require_version("GdkX11", "4.0")
	from gi.repository import GdkX11
except (ImportError, ValueError):
	GdkX11 = None  # type: ignore[assignment]

if not hasattr(Gtk.Widget, "_starcal_native_connect"):
	Gtk.Widget._starcal_native_connect = (  # type: ignore[attr-defined]  # noqa: SLF001
		Gtk.Widget.connect
	)
_gtk4_widget_connect = (
	Gtk.Widget._starcal_native_connect  # type: ignore[attr-defined]  # noqa: SLF001
)

if TYPE_CHECKING:
	from collections.abc import Callable

	import cairo

__all__ = [
	"CheckMenuItem",
	"Clipboard",
	"Dialog",
	"IconSize",
	"Menu",
	"MenuBar",
	"MenuItem",
	"MenuSeparator",
	"SelectionData",
	"SeparatorMenuItem",
	"begin_resize_drag",
	"connect_draw",
	"connect_widget_event",
	"events_pending",
	"getScrollValue",
	"get_children",
	"hide_all",
	"install_gtk4_patches",
	"main_iteration_do",
	"pack",
	"set_border_width",
	"show_all",
	"window_add",
]


def _get_pointer_device(window: Gtk.Window) -> Gdk.Device | None:
	display = window.get_display()
	seat = display.get_default_seat()
	if seat is None:
		return None
	return seat.get_pointer()


def begin_resize_drag(
	window: Gtk.Window,
	edge: Gdk.SurfaceEdge,
	button: int,
	x: float,
	y: float,
	timestamp: int,
) -> None:
	"""Start an interactive GTK 4 resize on a window's toplevel surface."""
	surface = window.get_surface()
	if isinstance(surface, Gdk.Toplevel):
		surface.begin_resize(
			edge,
			_get_pointer_device(window),
			button,
			x,
			y,
			timestamp,
		)


def begin_move_drag(
	window: Gtk.Window,
	button: int,
	x: float,
	y: float,
	timestamp: int,
) -> None:
	"""Start an interactive GTK 4 move on a window's toplevel surface."""
	surface = window.get_surface()
	device = _get_pointer_device(window)
	if isinstance(surface, Gdk.Toplevel) and device is not None:
		surface.begin_move(device, button, x, y, timestamp)


def window_resize(window: Gtk.Window, width: int, height: int) -> None:
	window.set_default_size(width, height)


def window_move(window: Gtk.Window, x: int, y: int) -> None:
	# GTK 4 intentionally removed programmatic toplevel positioning. Preserve
	# the requested coordinates so legacy bookkeeping remains self-consistent.
	window._compat_position = (x, y)  # type: ignore[attr-defined]  # noqa: SLF001


def window_get_position(window: Gtk.Window) -> tuple[int, int]:
	return getattr(window, "_compat_position", (0, 0))


def window_get_size(window: Gtk.Window) -> tuple[int, int]:
	width = window.get_width()
	height = window.get_height()
	default_width, default_height = window.get_default_size()
	return (
		width if width > 0 else default_width,
		height if height > 0 else default_height,
	)


def _apply_skip_taskbar_hint(window: Gtk.Window) -> None:
	if GdkX11 is None:
		return
	surface = window.get_surface()
	if isinstance(surface, GdkX11.X11Surface):
		enabled = bool(getattr(window, "_compat_skip_taskbar_hint", False))
		surface.set_skip_taskbar_hint(enabled)
		surface.set_skip_pager_hint(enabled)


def window_set_skip_taskbar_hint(window: Gtk.Window, enabled: bool) -> None:
	"""Apply GTK3's taskbar hint when GTK4 is using its X11 backend."""
	window._compat_skip_taskbar_hint = (  # type: ignore[attr-defined]  # noqa: SLF001
		enabled
	)
	if not hasattr(window, "_compat_skip_taskbar_realize_handler"):
		handler_id = _gtk4_widget_connect(
			window,
			"realize",
			_apply_skip_taskbar_hint,
		)
		window._compat_skip_taskbar_realize_handler = (  # type: ignore[attr-defined]  # noqa: SLF001
			handler_id
		)
	_apply_skip_taskbar_hint(window)


# ---------------------------------------------------------------------------
# Icon sizes (GTK3 enum values mapped to pixel sizes)
# ---------------------------------------------------------------------------


class IconSize:
	MENU = 16
	SMALL_TOOLBAR = 16
	BUTTON = 16
	LARGE_TOOLBAR = 24
	DND = 32
	DIALOG = 48


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------


def pack(
	box: Gtk.Box,
	child: Gtk.Widget,
	expand: bool | int = False,
	fill: bool | int = False,
	padding: int = 0,
) -> None:
	del fill
	if not isinstance(box, Gtk.Box):
		raise TypeError(f"pack: unknown type {type(box)}")
	if padding:
		child.set_margin_start(padding)
		child.set_margin_end(padding)
		child.set_margin_top(padding)
		child.set_margin_bottom(padding)
	child.set_hexpand(bool(expand))
	child.set_vexpand(bool(expand))
	# Call the GTK implementation directly. Compatibility subclasses such as
	# MenuBar override append(), and dispatching through the instance would
	# recurse back into pack().
	Gtk.Box.append(box, child)


def set_border_width(widget: Gtk.Widget, width: int) -> None:
	widget.set_margin_start(width)
	widget.set_margin_end(width)
	widget.set_margin_top(width)
	widget.set_margin_bottom(width)


def show_all(widget: Gtk.Widget) -> None:
	widget.set_visible(True)
	child = widget.get_first_child()
	while child is not None:
		next_child = child.get_next_sibling()
		# GTK 4 exposes implementation children that GTK 3's show_all() did
		# not.  In particular, walking into a ComboBox reveals its dropdown
		# popover before the user opens it.
		if isinstance(child, Gtk.Popover):
			child.set_visible(False)
		else:
			show_all(child)
		child = next_child


def hide_all(widget: Gtk.Widget) -> None:
	widget.set_visible(False)
	child = widget.get_first_child()
	while child is not None:
		hide_all(child)
		child = child.get_next_sibling()


def get_children(widget: Gtk.Widget) -> list[Gtk.Widget]:
	"""Return direct children using GTK 4's sibling-based widget API."""
	children: list[Gtk.Widget] = []
	child = widget.get_first_child()
	while child is not None:
		children.append(child)
		child = child.get_next_sibling()
	return children


def window_add(window: Gtk.Window, child: Gtk.Widget) -> None:
	if isinstance(window, Gtk.ApplicationWindow) or (
		hasattr(window, "get_child") and window.get_child() is None
	):
		window.set_child(child)
	else:
		# Dialog: content area
		content = (
			window.get_content_area() if hasattr(window, "get_content_area") else None
		)
		if content is not None:
			content.append(child)
		else:
			window.set_child(child)


# ---------------------------------------------------------------------------
# Main loop helpers (replace gtk.main_iteration_do / events_pending)
# ---------------------------------------------------------------------------


def main_iteration_do(_may_block: bool) -> bool:
	ctx = GLib.MainContext.default()
	return ctx.iteration(_may_block)


def events_pending() -> bool:
	ctx = GLib.MainContext.default()
	return ctx.pending()


# ---------------------------------------------------------------------------
# Clipboard (replace Gtk.Clipboard)
# ---------------------------------------------------------------------------


class Clipboard:
	@staticmethod
	def get(_selection: object = None) -> Gdk.Clipboard:
		del _selection
		display = Gdk.Display.get_default()
		assert display is not None
		return display.get_clipboard()


# ---------------------------------------------------------------------------
# Dialog with blocking run()
# ---------------------------------------------------------------------------


class Dialog(Gtk.Dialog):
	vbox: Gtk.Box  # type: ignore[assignment]

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		self._standalone_parent: Gtk.Window | None = None
		if kwargs.get("transient_for") is None:
			self._standalone_parent = Gtk.Window()
			kwargs["transient_for"] = self._standalone_parent
		super().__init__(*args, **kwargs)
		self._run_response: Gtk.ResponseType = Gtk.ResponseType.NONE

	@property
	def vbox(self) -> Gtk.Box:  # noqa: F811
		return self.get_content_area()

	def run(self) -> Gtk.ResponseType:
		self._run_response = Gtk.ResponseType.NONE
		loop = GLib.MainLoop()

		def finish(response: Gtk.ResponseType) -> None:
			self._run_response = response
			if loop.is_running():
				loop.quit()

		def on_response(_dialog: Gtk.Dialog, response: Gtk.ResponseType) -> None:
			finish(response)

		def on_close_request(_dialog: Gtk.Dialog) -> bool:
			finish(Gtk.ResponseType.DELETE_EVENT)
			return False

		def on_visible(dialog: Gtk.Dialog, _pspec: object) -> None:
			if not dialog.get_visible():
				finish(Gtk.ResponseType.DELETE_EVENT)

		response_handler = self.connect("response", on_response)
		close_handler = self.connect("close-request", on_close_request)
		visible_handler = self.connect("notify::visible", on_visible)
		try:
			self.present()
			if self._run_response == Gtk.ResponseType.NONE:
				loop.run()
		finally:
			self.disconnect(response_handler)
			self.disconnect(close_handler)
			self.disconnect(visible_handler)
		return self._run_response


# ---------------------------------------------------------------------------
# Menu / MenuItem (GtkMenu removed in GTK4)
# ---------------------------------------------------------------------------


class MenuSeparator(Gtk.Separator):
	def __init__(self) -> None:
		super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
		self.add_css_class("menu-separator")


class SeparatorMenuItem(MenuSeparator):
	"""Alias for gtk.SeparatorMenuItem."""


class MenuItem(Gtk.Button):
	def __init__(self, label: str = "") -> None:
		super().__init__()
		self.text = label
		self.add_css_class("menuitem")
		if label:
			self.set_label(label)
			self.set_use_underline(True)
		self._submenu: Menu | None = None
		self._activate_callbacks: list[Callable[[MenuItem], None]] = []
		super().connect("clicked", self._on_clicked)

	def add(self, child: Gtk.Widget) -> None:
		self.set_child(child)

	def set_use_underline(self, use: bool) -> None:
		if use and self.text:
			self.set_label(self.text)
			super().set_use_underline(True)

	def set_label(self, label: str) -> None:
		self.text = label
		super().set_label(label)

	def get_label(self) -> str:
		return self.text

	def set_submenu(self, submenu: Menu) -> None:
		self._submenu = submenu

	def get_submenu(self) -> Menu | None:
		return self._submenu

	def _on_clicked(self, _btn: Gtk.Button) -> None:
		if self._submenu is not None:
			self._submenu._attach_widget = self  # noqa: SLF001
			self._submenu.set_parent(self)
			Gtk.Popover.popup(self._submenu)
			return
		# GtkMenu dismisses the whole menu hierarchy before emitting
		# ``activate``. GtkPopover does not do that for button children.
		parent = self.get_parent()
		while parent is not None:
			if isinstance(parent, Gtk.Popover):
				parent.popdown()
			parent = parent.get_parent()
		for callback in self._activate_callbacks:
			callback(self)

	def connect(self, signal: str, callback: Callable[..., Any]) -> int:
		if signal == "activate":
			self._activate_callbacks.append(callback)
			return len(self._activate_callbacks)
		if signal.endswith("-event"):
			connect_widget_event(self, signal, callback)
			return 1
		return super().connect(signal, callback)


class CheckMenuItem(MenuItem):
	def __init__(self, label: str = "") -> None:
		super().__init__()
		self.text = label
		self._check = Gtk.CheckButton(label=label)
		self._check.set_use_underline(True)
		self.set_child(self._check)
		self._active = False
		self._toggled_callbacks: list[Callable[[CheckMenuItem], None]] = []

	def set_active(self, active: bool) -> None:
		self._active = active
		self._check.set_active(active)

	def get_active(self) -> bool:
		return self._check.get_active()

	def connect(self, signal: str, callback: Callable[..., Any]) -> int:
		if signal == "toggled":
			self._toggled_callbacks.append(callback)

			def on_toggled(_check: Gtk.CheckButton) -> None:
				self._active = self._check.get_active()
				callback(self)

			return self._check.connect("toggled", on_toggled)
		return super().connect(signal, callback)


class MenuBar(Gtk.Box):
	def __init__(self) -> None:
		super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
		self._items: list[MenuItem] = []

	def append(self, item: MenuItem) -> None:
		self._items.append(item)
		pack(self, item)

	def select_item(self, item: MenuItem) -> None:  # noqa: PLR6301
		item._on_clicked(item)  # noqa: SLF001

	def show_all(self) -> None:
		show_all(self)


class Menu(Gtk.Popover):
	def __init__(self, reserve_toggle_size: bool = False) -> None:
		del reserve_toggle_size
		super().__init__()
		self._box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
		self._box.add_css_class("menu")
		self.set_child(self._box)
		self._attach_widget: Gtk.Widget | None = None
		self.set_has_arrow(False)
		self.lastLeaveNotify = 0.0

	def set_reserve_toggle_size(self, _reserve: bool) -> None:
		pass

	def append(self, item: Gtk.Widget) -> None:
		self._box.append(item)

	def add(self, item: Gtk.Widget) -> None:
		self.append(item)

	def remove(self, item: Gtk.Widget) -> None:
		self._box.remove(item)

	def get_children(self) -> list[Gtk.Widget]:
		return get_children(self._box)

	def reorder_child(self, item: Gtk.Widget, position: int) -> None:
		children = [child for child in self.get_children() if child is not item]
		position = max(0, min(position, len(children)))
		sibling = children[position - 1] if position > 0 else None
		self._box.reorder_child_after(item, sibling)

	def hide(self) -> None:
		self.popdown()

	def show_all(self) -> None:
		show_all(self._box)

	def connect(self, signal: str, callback: Callable[..., Any]) -> int:
		if signal == "show":

			def on_visible(_menu: Menu, _pspec: object) -> None:
				if self.get_visible():
					callback(self)

			return super().connect("notify::visible", on_visible)
		if signal == "leave-notify-event":

			def on_leave(_box: Gtk.Widget, event: _CompatMotionEvent) -> Any:
				return callback(self, event)

			connect_widget_event(self._box, signal, on_leave)
			return 1
		return super().connect(signal, callback)

	def popup(
		self,
		_parent_shell: Gtk.Widget | None = None,
		_parent_item: Gtk.Widget | None = None,
		func: Callable[..., tuple[int, int]] | None = None,
		data: Any = None,
		button: int = 0,
		activate_time: int = 0,
	) -> None:
		del button, activate_time
		if func is not None and self._attach_widget is not None:
			position = func(data)
			x, y = position[:2]
			rect = Gdk.Rectangle()
			rect.x = x
			rect.y = y
			rect.width = 1
			rect.height = 1
			self.set_pointing_to(rect)
		elif self._attach_widget is not None:
			parent = self.get_parent()
			if parent is not self._attach_widget:
				if parent is not None:
					self.unparent()
				self.set_parent(self._attach_widget)
		Gtk.Popover.popup(self)

	def popup_at_widget(
		self,
		widget: Gtk.Widget,
		rect: Gdk.Rectangle | None = None,
	) -> None:
		self._attach_widget = widget
		parent = self.get_parent()
		if parent is not widget:
			if parent is not None:
				self.unparent()
			self.set_parent(widget)
		if rect is not None:
			self.set_pointing_to(rect)
		self.popup()

	def attach_to_widget(self, widget: Gtk.Widget, _destroy_func: Any = None) -> None:
		self._attach_widget = widget


# ---------------------------------------------------------------------------
# Scroll event helper
# ---------------------------------------------------------------------------


_double_button_press = object()
_no_modifier = Gdk.ModifierType(0)


class _CompatEvent:
	def __init__(
		self,
		widget: Gtk.Widget,
		*,
		state: Gdk.ModifierType = _no_modifier,
		timestamp: int = Gdk.CURRENT_TIME,
	) -> None:
		self._widget = widget
		self.state = state
		self.time = timestamp

	def get_state(self) -> Gdk.ModifierType:
		return self.state

	def get_window(self) -> Any:
		return self._widget.get_window()


class _CompatButtonEvent(_CompatEvent):
	def __init__(
		self,
		widget: Gtk.Widget,
		x: float,
		y: float,
		event_type: object,
		*,
		button: int = 1,
		state: Gdk.ModifierType = _no_modifier,
		timestamp: int = Gdk.CURRENT_TIME,
		x_root: float | None = None,
		y_root: float | None = None,
	) -> None:
		super().__init__(widget, state=state, timestamp=timestamp)
		self.type = event_type
		self.button = button
		self.x = x
		self.y = y
		# GTK 4 does not expose global pointer coordinates on every backend.
		self.x_root = x if x_root is None else x_root
		self.y_root = y if y_root is None else y_root

	def get_coords(self) -> tuple[float, float]:
		return self.x, self.y


class _CompatMotionEvent(_CompatButtonEvent):
	pass


class _CompatScrollEvent(_CompatEvent):
	def __init__(
		self,
		widget: Gtk.Widget,
		delta_x: float,
		delta_y: float,
		*,
		x: float = 0.0,
		y: float = 0.0,
		state: Gdk.ModifierType = _no_modifier,
		timestamp: int = Gdk.CURRENT_TIME,
	) -> None:
		super().__init__(widget, state=state, timestamp=timestamp)
		self.direction = Gdk.ScrollDirection.SMOOTH
		self.delta_x = delta_x
		self.delta_y = delta_y
		self.x = x
		self.y = y

	def is_scroll_stop_event(self) -> bool:  # noqa: PLR6301
		# The GTK4 ``scroll`` signal carries deltas only; deceleration ending
		# is a separate signal, so adapted scroll events are not stop events.
		return False


class _CompatKeyEvent(_CompatEvent):
	def __init__(
		self,
		widget: Gtk.Widget,
		keyval: int,
		hardware_keycode: int,
		state: Gdk.ModifierType,
		*,
		timestamp: int = Gdk.CURRENT_TIME,
	) -> None:
		super().__init__(widget, state=state, timestamp=timestamp)
		self.keyval = keyval
		self.hardware_keycode = hardware_keycode


def getScrollValue(gevent: _CompatScrollEvent, last: str = "") -> str:
	value = gevent.direction.value_nick
	if value == "smooth":
		if gevent.delta_y < 0:
			value = "up"
		elif gevent.delta_y == 0 and last:
			return last
		else:
			value = "down"
	return value


# ---------------------------------------------------------------------------
# DrawingArea: replace "draw" signal with set_draw_func
# ---------------------------------------------------------------------------


def connect_draw(
	widget: Gtk.DrawingArea,
	callback: Callable[..., Any],
) -> None:
	def draw_func(
		area: Gtk.DrawingArea,
		cr: cairo.Context,
		width: int,
		height: int,
		_data: Any,
	) -> None:
		del width, height
		# Adapt GTK3 draw callbacks: (widget, cr) or (widget, event)
		try:
			callback(area, cr)
		except TypeError:
			callback(area)

	widget.set_draw_func(draw_func, None)


# ---------------------------------------------------------------------------
# Event controllers (replace widget event signals)
# ---------------------------------------------------------------------------


def _get_click_controller(
	widget: Gtk.Widget,
) -> tuple[
	Gtk.GestureClick,
	list[Callable[..., Any]],
	list[Callable[..., Any]],
]:
	stored = getattr(widget, "_starcal_click_controller", None)
	if stored is not None:
		return stored

	press_callbacks: list[Callable[..., Any]] = []
	release_callbacks: list[Callable[..., Any]] = []
	controller = Gtk.GestureClick.new()
	controller.set_button(0)

	def get_surface_position(
		ctrl: Gtk.GestureClick,
		x: float,
		y: float,
	) -> tuple[float, float]:
		current_event = ctrl.get_current_event()
		if current_event is None:
			return x, y
		position = current_event.get_position()
		if not position[0]:
			return x, y
		return position[1], position[2]

	def on_pressed(
		ctrl: Gtk.GestureClick,
		n_press: int,
		x: float,
		y: float,
	) -> None:
		event_type = _double_button_press if n_press > 1 else Gdk.EventType.BUTTON_PRESS
		x_root, y_root = get_surface_position(ctrl, x, y)
		event = _make_button_event(
			widget,
			x,
			y,
			event_type,
			button=ctrl.get_current_button(),
			state=ctrl.get_current_event_state(),
			timestamp=ctrl.get_current_event_time(),
			x_root=x_root,
			y_root=y_root,
		)
		for press_callback in press_callbacks:
			if press_callback(widget, event):
				ctrl.set_state(Gtk.EventSequenceState.CLAIMED)
				break

	def on_released(
		ctrl: Gtk.GestureClick,
		_n_press: int,
		x: float,
		y: float,
	) -> None:
		x_root, y_root = get_surface_position(ctrl, x, y)
		event = _make_button_event(
			widget,
			x,
			y,
			Gdk.EventType.BUTTON_RELEASE,
			button=ctrl.get_current_button(),
			state=ctrl.get_current_event_state(),
			timestamp=ctrl.get_current_event_time(),
			x_root=x_root,
			y_root=y_root,
		)
		for release_callback in release_callbacks:
			if release_callback(widget, event):
				ctrl.set_state(Gtk.EventSequenceState.CLAIMED)
				break

	controller.connect("pressed", on_pressed)
	controller.connect("released", on_released)
	widget.add_controller(controller)
	stored = controller, press_callbacks, release_callbacks
	widget._starcal_click_controller = (  # type: ignore[attr-defined]  # noqa: SLF001
		stored
	)
	return stored


def connect_widget_event(
	widget: Gtk.Widget,
	signal_name: str,
	callback: Callable[..., Any],
) -> None:
	if signal_name == "button-press-event":
		_get_click_controller(widget)[1].append(callback)
	elif signal_name == "button-release-event":
		_get_click_controller(widget)[2].append(callback)
	elif signal_name == "scroll-event":

		def on_scroll(
			ctrl: Gtk.EventControllerScroll,
			dx: float,
			dy: float,
		) -> bool:
			x = y = 0.0
			current_event = ctrl.get_current_event()
			if current_event is not None:
				position = current_event.get_position()
				if position[0]:
					_, x, y = position
			event = _CompatScrollEvent(
				widget,
				dx,
				dy,
				x=x,
				y=y,
				state=ctrl.get_current_event_state(),
				timestamp=ctrl.get_current_event_time(),
			)
			result = callback(widget, event)
			return bool(result) if result is not None else False

		scroll_controller = Gtk.EventControllerScroll.new(
			Gtk.EventControllerScrollFlags.VERTICAL,
		)
		scroll_controller.connect("scroll", on_scroll)
		widget.add_controller(scroll_controller)
	elif signal_name == "key-press-event":

		def on_key(
			ctrl: Gtk.EventControllerKey,
			keyval: int,
			keycode: int,
			state: Gdk.ModifierType,
		) -> bool:
			event = _CompatKeyEvent(
				widget,
				keyval,
				keycode,
				state,
				timestamp=ctrl.get_current_event_time(),
			)
			result = callback(widget, event)
			return bool(result) if result is not None else False

		key_controller = Gtk.EventControllerKey.new()
		key_controller.connect("key-pressed", on_key)
		widget.add_controller(key_controller)
	elif signal_name == "motion-notify-event":

		def on_motion(ctrl: Gtk.EventControllerMotion, x: float, y: float) -> None:
			event = _make_motion_event(
				widget,
				x,
				y,
				state=ctrl.get_current_event_state(),
				timestamp=ctrl.get_current_event_time(),
			)
			callback(widget, event)

		motion_controller = Gtk.EventControllerMotion.new()
		motion_controller.connect("motion", on_motion)
		widget.add_controller(motion_controller)
	elif signal_name == "enter-notify-event":

		def on_enter(
			ctrl: Gtk.EventControllerMotion,
			x: float,
			y: float,
		) -> None:
			callback(
				widget,
				_make_motion_event(
					widget,
					x,
					y,
					state=ctrl.get_current_event_state(),
					timestamp=ctrl.get_current_event_time(),
				),
			)

		enter_controller = Gtk.EventControllerMotion.new()
		enter_controller.connect("enter", on_enter)
		widget.add_controller(enter_controller)
	elif signal_name == "leave-notify-event":

		def on_leave(ctrl: Gtk.EventControllerMotion) -> None:
			callback(
				widget,
				_make_motion_event(
					widget,
					0.0,
					0.0,
					state=ctrl.get_current_event_state(),
					timestamp=ctrl.get_current_event_time(),
				),
			)

		leave_controller = Gtk.EventControllerMotion.new()
		leave_controller.connect("leave", on_leave)
		widget.add_controller(leave_controller)
	elif signal_name in {"focus-in-event", "focus-out-event"}:

		def on_focus(_ctrl: Gtk.EventControllerFocus) -> None:
			callback(widget, None)

		focus_controller = Gtk.EventControllerFocus.new()
		focus_signal = "enter" if signal_name == "focus-in-event" else "leave"
		focus_controller.connect(focus_signal, on_focus)
		widget.add_controller(focus_controller)
	elif signal_name == "configure-event":
		if isinstance(widget, Gtk.Window):
			_gtk4_widget_connect(
				widget,
				"notify::default-width",
				lambda w, _p: callback(w, None),
			)
			_gtk4_widget_connect(
				widget,
				"notify::default-height",
				lambda w, _p: callback(w, None),
			)
		else:
			_gtk4_widget_connect(widget, "map", lambda w: callback(w, None))
	else:
		_gtk4_widget_connect(widget, signal_name, callback)


def _make_button_event(
	widget: Gtk.Widget,
	x: float,
	y: float,
	event_type: object,
	*,
	button: int = 1,
	state: Gdk.ModifierType = _no_modifier,
	timestamp: int = Gdk.CURRENT_TIME,
	x_root: float | None = None,
	y_root: float | None = None,
) -> _CompatButtonEvent:
	return _CompatButtonEvent(
		widget,
		x,
		y,
		event_type,
		button=button,
		state=state,
		timestamp=timestamp,
		x_root=x_root,
		y_root=y_root,
	)


def _make_motion_event(
	widget: Gtk.Widget,
	x: float,
	y: float,
	*,
	state: Gdk.ModifierType = _no_modifier,
	timestamp: int = Gdk.CURRENT_TIME,
) -> _CompatMotionEvent:
	return _CompatMotionEvent(
		widget,
		x,
		y,
		Gdk.EventType.MOTION_NOTIFY,
		state=state,
		timestamp=timestamp,
	)


# ---------------------------------------------------------------------------
# Drag-and-drop stubs (SelectionData removed in GTK4)
# ---------------------------------------------------------------------------


class SelectionData:
	def __init__(self) -> None:
		self._text = ""

	def set_text(self, text: str, _length: int) -> None:
		self._text = text

	def get_text(self) -> str | None:
		return self._text


class DestDefaults:
	ALL = 0


# ---------------------------------------------------------------------------
# CssProvider.load_from_data compat
# ---------------------------------------------------------------------------


def css_provider_load_from_data(provider: Gtk.CssProvider, data: bytes) -> None:
	provider.load_from_string(data.decode("utf-8"))


# ---------------------------------------------------------------------------
# StyleContext.get_color compat (StateFlags removed)
# ---------------------------------------------------------------------------


if not hasattr(Gtk.StyleContext, "_starcal_native_get_color"):
	Gtk.StyleContext._starcal_native_get_color = (  # type: ignore[attr-defined]  # noqa: SLF001
		Gtk.StyleContext.get_color
	)
	Gtk.StyleContext._starcal_native_get_property = (  # type: ignore[attr-defined]  # noqa: SLF001
		Gtk.StyleContext.get_property
	)
_gtk4_style_context_get_color = (
	Gtk.StyleContext._starcal_native_get_color  # type: ignore[attr-defined]  # noqa: SLF001
)
_gtk4_style_context_get_property = (
	Gtk.StyleContext._starcal_native_get_property  # type: ignore[attr-defined]  # noqa: SLF001
)


def style_context_get_color(style_ctx: Gtk.StyleContext) -> Gdk.RGBA:
	return _gtk4_style_context_get_color(style_ctx)


def style_context_get_background_color(
	style_ctx: Gtk.StyleContext,
	_state: Gtk.StateFlags | None = None,
) -> Gdk.RGBA:
	del _state
	found, color = style_ctx.lookup_color("theme_bg_color")
	if found:
		return color
	return Gdk.RGBA()


# ---------------------------------------------------------------------------
# Install monkey-patches on Gtk/Gdk classes
# ---------------------------------------------------------------------------


_gtk4_patches_installed = False
_gtk_main_loops: list[GLib.MainLoop] = []


def install_gtk4_patches() -> None:
	global _gtk4_patches_installed
	if _gtk4_patches_installed:
		return
	_gtk4_patches_installed = True

	# Retain names used by GTK3 callers. Toplevel placement and type hints are
	# compositor-managed in GTK4, so their corresponding methods are no-ops.
	if not hasattr(Gtk, "WindowPosition"):

		class WindowPosition(IntEnum):
			NONE = 0
			CENTER = 1

		Gtk.WindowPosition = WindowPosition  # type: ignore[attr-defined]
	if not hasattr(Gtk, "WindowType"):

		class WindowType(IntEnum):
			TOPLEVEL = 0
			POPUP = 1

		Gtk.WindowType = WindowType  # type: ignore[attr-defined]
		window_init = Gtk.Window.__init__

		def window_init_compat(
			window: Gtk.Window,
			*args: Any,
			**kwargs: Any,
		) -> None:
			kwargs.pop("type", None)
			window_init(window, *args, **kwargs)

		Gtk.Window.__init__ = window_init_compat  # type: ignore[assignment]
	if not hasattr(Gdk, "WindowTypeHint"):

		class WindowTypeHint(IntEnum):
			NORMAL = 0
			DIALOG = 1

		Gdk.WindowTypeHint = WindowTypeHint  # type: ignore[attr-defined]
	if not hasattr(Gdk.Monitor, "get_workarea"):
		Gdk.Monitor.get_workarea = Gdk.Monitor.get_geometry  # type: ignore[attr-defined]

	# Container.get_children() was removed in GTK 4. Most GTK widgets expose
	# their direct children through the first-child/next-sibling API instead.
	if not hasattr(Gtk.Widget, "get_children"):
		Gtk.Widget.get_children = get_children  # type: ignore[attr-defined]

	# Translate removed GTK 3 widget-event signals into GTK 4 controllers.
	# Keep the original GObject signal connector for all native GTK 4 signals.
	legacy_event_signals = {
		"button-press-event",
		"button-release-event",
		"configure-event",
		"enter-notify-event",
		"focus-in-event",
		"focus-out-event",
		"key-press-event",
		"leave-notify-event",
		"motion-notify-event",
		"scroll-event",
	}

	def connect_compat(
		self: Gtk.Widget,
		signal_name: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		if signal_name in {"drag-begin", "drag-data-get", "drag-data-received"}:
			# Legacy DnD setup is currently a no-op under the GTK 4 bridge.
			return 0
		if signal_name == "populate-popup":

			def on_popup(
				ctrl: Gtk.GestureClick,
				_n_press: int,
				x: float,
				y: float,
			) -> None:
				del ctrl
				menu = Menu()
				callback(self, menu, *user_data)
				rect = Gdk.Rectangle()
				rect.x = int(x)
				rect.y = int(y)
				rect.width = 1
				rect.height = 1
				menu.popup_at_widget(self, rect)

			popup_controller = Gtk.GestureClick.new()
			popup_controller.set_button(3)
			popup_controller.connect("pressed", on_popup)
			self.add_controller(popup_controller)
			return 0
		if signal_name == "delete-event":

			def on_close_request(_window: Gtk.Window) -> bool:
				return bool(callback(self, None, *user_data))

			return _gtk4_widget_connect(self, "close-request", on_close_request)
		if signal_name == "size-allocate":

			def on_size_allocate(widget: Gtk.Widget, *_args: Any) -> Any:
				return callback(widget, widget.get_allocation(), *user_data)

			handler_id = _gtk4_widget_connect(self, "map", on_size_allocate)
			if isinstance(self, Gtk.Paned):
				_gtk4_widget_connect(
					self,
					"notify::max-position",
					on_size_allocate,
				)
			return handler_id
		if signal_name == "clicked" and isinstance(self, Gtk.CheckButton):
			return _gtk4_widget_connect(self, "toggled", callback, *user_data)
		if signal_name in legacy_event_signals:

			def callback_with_data(*args: Any) -> Any:
				return callback(*args, *user_data)

			connect_widget_event(self, signal_name, callback_with_data)
			# Legacy callers in this project do not disconnect these handlers.
			return 0
		return _gtk4_widget_connect(self, signal_name, callback, *user_data)

	Gtk.Widget.connect = connect_compat  # type: ignore[assignment]

	# Widget visibility
	if not hasattr(Gtk.Widget, "show_all"):
		Gtk.Widget.show_all = show_all  # type: ignore[attr-defined]
	if not hasattr(Gtk.Widget, "hide_all"):
		Gtk.Widget.hide_all = hide_all  # type: ignore[attr-defined]
	if not hasattr(Gtk.Widget, "show"):
		pass  # show() still exists as set_visible(True)
	else:
		_orig_show = Gtk.Widget.show

		def show(self: Gtk.Widget) -> None:
			self.set_visible(True)

		Gtk.Widget.show = show  # type: ignore[assignment]

	# Border width -> margins
	if not hasattr(Gtk.Widget, "set_border_width"):
		Gtk.Widget.set_border_width = set_border_width  # type: ignore[attr-defined]
	if not hasattr(Gtk.Widget, "destroy"):

		def widget_destroy(self: Gtk.Widget) -> None:
			self.set_visible(False)
			if self.get_parent() is not None:
				self.unparent()

		Gtk.Widget.destroy = widget_destroy  # type: ignore[attr-defined]

	# GTK 3 label and button spelling retained by the application code.
	Gtk.Label.set_line_wrap = Gtk.Label.set_wrap  # type: ignore[attr-defined]
	Gtk.Label.set_line_wrap_mode = Gtk.Label.set_wrap_mode  # type: ignore[attr-defined]
	if not hasattr(Gtk.Label, "set_angle"):
		Gtk.Label.set_angle = lambda _label, _angle: None  # type: ignore[attr-defined]
	if not hasattr(Gtk, "ReliefStyle"):

		class ReliefStyle(IntEnum):
			NONE = 2

		Gtk.ReliefStyle = ReliefStyle  # type: ignore[attr-defined]

	def button_set_relief(button: Gtk.Button, relief: object) -> None:
		if relief == Gtk.ReliefStyle.NONE:  # type: ignore[attr-defined]
			button.add_css_class("flat")

	Gtk.Button.set_relief = button_set_relief  # type: ignore[attr-defined]

	# GTK 4 delegates toplevel placement and several window-manager hints to
	# the compositor. Keep the GTK 3 methods callable for existing UI code.
	Gtk.Window.resize = window_resize  # type: ignore[attr-defined]
	Gtk.Window.move = window_move  # type: ignore[attr-defined]
	Gtk.Window.get_position = window_get_position  # type: ignore[attr-defined]
	Gtk.Window.set_position = (  # type: ignore[attr-defined]
		lambda _window, _position: None
	)
	Gtk.Window.get_size = window_get_size  # type: ignore[assignment]
	Gtk.Window.begin_move_drag = begin_move_drag  # type: ignore[attr-defined]
	Gtk.Window.begin_resize_drag = begin_resize_drag  # type: ignore[attr-defined]
	Gtk.Window.iconify = Gtk.Window.minimize  # type: ignore[attr-defined]
	Gtk.Window.deiconify = Gtk.Window.unminimize  # type: ignore[attr-defined]
	Gtk.Window.set_keep_above = (  # type: ignore[attr-defined]
		lambda _window, _enabled: None
	)
	Gtk.Window.set_keep_below = (  # type: ignore[attr-defined]
		lambda _window, _enabled: None
	)
	Gtk.Window.set_skip_taskbar_hint = window_set_skip_taskbar_hint  # type: ignore[attr-defined]
	Gtk.Window.set_type_hint = (  # type: ignore[attr-defined]
		lambda _window, _hint: None
	)
	Gtk.Window.stick = lambda _window: None  # type: ignore[attr-defined]
	Gtk.Window.unstick = lambda _window: None  # type: ignore[attr-defined]
	Gtk.Window.set_icon_from_file = (  # type: ignore[attr-defined]
		lambda _window, _path: None
	)
	Gtk.Window.set_default_icon_from_file = staticmethod(  # type: ignore[attr-defined]
		lambda _path: None,
	)

	# Box pack_start/pack_end -> append
	def pack_start(
		self: Gtk.Box,
		child: Gtk.Widget,
		expand: bool = False,
		fill: bool = False,
		padding: int = 0,
	) -> None:
		pack(self, child, expand, fill, padding)

	def pack_end(
		self: Gtk.Box,
		child: Gtk.Widget,
		expand: bool = False,
		fill: bool = False,
		padding: int = 0,
	) -> None:
		del fill
		if padding:
			child.set_margin_start(padding)
			child.set_margin_end(padding)
			child.set_margin_top(padding)
			child.set_margin_bottom(padding)
		child.set_hexpand(bool(expand))
		child.set_vexpand(bool(expand))
		self.prepend(child)

	def set_child_packing(
		self: Gtk.Box,
		child: Gtk.Widget,
		expand: bool,
		fill: bool,
		padding: int,
		pack_type: Gtk.PackType,
	) -> None:
		del self, fill, pack_type
		child.set_hexpand(expand)
		child.set_vexpand(expand)
		child.set_margin_start(padding)
		child.set_margin_end(padding)
		child.set_margin_top(padding)
		child.set_margin_bottom(padding)

	Gtk.Box.pack_start = pack_start  # type: ignore[attr-defined]
	Gtk.Box.pack_end = pack_end  # type: ignore[attr-defined]
	Gtk.Box.set_child_packing = set_child_packing  # type: ignore[attr-defined]

	# Window.add -> set_child / append
	def window_add_method(self: Gtk.Window, child: Gtk.Widget) -> None:
		window_add(self, child)

	Gtk.Window.add = window_add_method  # type: ignore[attr-defined]

	# Button.set_image compat
	def button_set_image(self: Gtk.Button, image: Gtk.Widget) -> None:
		label = self.get_label() or ""
		use_underline = self.get_use_underline()
		old = self.get_child()
		if old is not None:
			self.remove(old)
		if not label:
			self.set_child(image)
			return
		box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
		Gtk.Box.append(box, image)
		label_widget = Gtk.Label(label=label, use_underline=use_underline)
		Gtk.Box.append(box, label_widget)
		self.set_child(box)

	Gtk.Button.set_image = button_set_image  # type: ignore[attr-defined]
	Gtk.Button.add = Gtk.Button.set_child  # type: ignore[attr-defined]
	Gtk.ScrolledWindow.add = Gtk.ScrolledWindow.set_child  # type: ignore[attr-defined]

	# Image.set_from_pixbuf
	def image_set_from_pixbuf(self: Gtk.Image, pixbuf: Any) -> None:
		self.set_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))

	Gtk.Image.set_from_pixbuf = image_set_from_pixbuf  # type: ignore[attr-defined]

	image_set_from_icon_name_native = Gtk.Image.set_from_icon_name
	image_new_from_icon_name_native = Gtk.Image.new_from_icon_name

	def image_set_from_icon_name(
		image: Gtk.Image,
		icon_name: str,
		size: int | None = None,
	) -> None:
		image_set_from_icon_name_native(image, icon_name)
		if size is not None:
			image.set_pixel_size(int(size))

	def image_new_from_icon_name(
		icon_name: str,
		size: int | None = None,
	) -> Gtk.Image:
		image = image_new_from_icon_name_native(icon_name)
		if size is not None:
			image.set_pixel_size(int(size))
		return image

	Gtk.Image.set_from_icon_name = image_set_from_icon_name  # type: ignore[assignment]
	Gtk.Image.new_from_icon_name = staticmethod(  # type: ignore[assignment]
		image_new_from_icon_name,
	)
	Gtk.Image.new_from_stock = staticmethod(  # type: ignore[attr-defined]
		image_new_from_icon_name,
	)

	about_set_logo_native = Gtk.AboutDialog.set_logo

	def about_set_logo(
		dialog: Gtk.AboutDialog,
		logo: Gdk.Paintable | GdkPixbuf.Pixbuf,
	) -> None:
		if isinstance(logo, GdkPixbuf.Pixbuf):
			logo = Gdk.Texture.new_for_pixbuf(logo)
		about_set_logo_native(dialog, logo)

	Gtk.AboutDialog.set_logo = about_set_logo  # type: ignore[assignment]

	# CssProvider
	if not hasattr(Gtk.CssProvider, "load_from_data"):
		Gtk.CssProvider.load_from_data = css_provider_load_from_data  # type: ignore[attr-defined]

	# StyleContext
	def get_color_compat(
		self: Gtk.StyleContext,
		_state: Gtk.StateFlags | None = None,
	) -> Gdk.RGBA:
		del _state
		return style_context_get_color(self)

	Gtk.StyleContext.get_color = get_color_compat  # type: ignore[assignment]
	Gtk.StyleContext.get_background_color = (  # type: ignore[attr-defined]
		style_context_get_background_color
	)

	def get_property_compat(
		self: Gtk.StyleContext,
		name: str,
		_state: Gtk.StateFlags | None = None,
	) -> Any:
		del _state
		if name == "background-color":
			return style_context_get_background_color(self)
		return _gtk4_style_context_get_property(self, name)

	Gtk.StyleContext.get_property = get_property_compat  # type: ignore[assignment]

	# Event subclasses were removed in GDK 4, but they remain useful as public
	# type names throughout the GTK 3-era application code.
	Gdk.EventButton = _CompatButtonEvent  # type: ignore[attr-defined]
	Gdk.EventKey = _CompatKeyEvent  # type: ignore[attr-defined]
	Gdk.EventMotion = _CompatMotionEvent  # type: ignore[attr-defined]
	Gdk.EventScroll = _CompatScrollEvent  # type: ignore[attr-defined]
	Gdk.EventType.DOUBLE_BUTTON_PRESS = _double_button_press  # type: ignore[attr-defined]
	Gdk.ModifierType.MODIFIER_MASK = (  # type: ignore[attr-defined]
		Gdk.ModifierType.SHIFT_MASK
		| Gdk.ModifierType.LOCK_MASK
		| Gdk.ModifierType.CONTROL_MASK
		| Gdk.ModifierType.ALT_MASK
		| Gdk.ModifierType.BUTTON1_MASK
		| Gdk.ModifierType.BUTTON2_MASK
		| Gdk.ModifierType.BUTTON3_MASK
		| Gdk.ModifierType.BUTTON4_MASK
		| Gdk.ModifierType.BUTTON5_MASK
		| Gdk.ModifierType.SUPER_MASK
		| Gdk.ModifierType.HYPER_MASK
		| Gdk.ModifierType.META_MASK
	)

	# Clipboard on Gtk namespace
	if not hasattr(Gdk.Clipboard, "set_text"):

		def clipboard_set_text(
			self: Gdk.Clipboard,
			text: str,
			_length: int = -1,
		) -> None:
			self.set(GObject.Value(str, text))

		Gdk.Clipboard.set_text = clipboard_set_text  # type: ignore[attr-defined]

	Gtk.Clipboard = Clipboard  # type: ignore[attr-defined]

	# Gdk.Atom was removed in Gdk 4; keep a sentinel for the legacy
	# gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD) call.
	if not hasattr(Gdk, "SELECTION_CLIPBOARD"):
		Gdk.SELECTION_CLIPBOARD = 0  # type: ignore[attr-defined]

	# IconSize
	Gtk.IconSize = IconSize  # type: ignore[attr-defined]

	# Main loop
	Gtk.main_iteration_do = staticmethod(main_iteration_do)  # type: ignore[attr-defined]
	Gtk.events_pending = staticmethod(events_pending)  # type: ignore[attr-defined]

	def gtk_main() -> None:
		loop = GLib.MainLoop()
		_gtk_main_loops.append(loop)
		try:
			loop.run()
		finally:
			_gtk_main_loops.remove(loop)

	def gtk_main_quit() -> None:
		if _gtk_main_loops:
			_gtk_main_loops[-1].quit()

	Gtk.main = staticmethod(gtk_main)  # type: ignore[attr-defined]
	Gtk.main_quit = staticmethod(gtk_main_quit)  # type: ignore[attr-defined]

	# DestDefaults for DnD
	Gtk.DestDefaults = DestDefaults  # type: ignore[attr-defined]

	# SelectionData for DnD
	Gtk.SelectionData = SelectionData  # type: ignore[attr-defined]

	# GtkMenu removed in GTK4
	Gtk.Menu = Menu  # type: ignore[attr-defined]
	Gtk.MenuItem = MenuItem  # type: ignore[attr-defined]
	Gtk.MenuBar = MenuBar  # type: ignore[attr-defined]
	Gtk.CheckMenuItem = CheckMenuItem  # type: ignore[attr-defined]
	Gtk.SeparatorMenuItem = SeparatorMenuItem  # type: ignore[attr-defined]

	# add_events is a no-op (use event controllers)
	if not hasattr(Gtk.Widget, "add_events"):
		Gtk.Widget.add_events = lambda self, _mask: None  # type: ignore[attr-defined]  # noqa: ARG005

	# get_window stub for widgets that still call it during transition
	if not hasattr(Gtk.Widget, "get_window"):
		Gtk.Widget.get_window = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005

	# ComboBox.pack_start for cell renderers (handled in gtk4_widgets)
	# TreeView types installed from gtk4_tree module
