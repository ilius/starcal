"""GTK3 removed widgets compatibility on GTK4."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from gi.repository import Gdk, Gtk

from scal3.ui_gtk.gtk4_compat import pack

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import RGB, RGBA, RawColor

__all__ = [
	"ColorButton",
	"EventBox",
	"FileChooserButton",
	"FontButton",
	"RadioButton",
	"install_widget_patches",
]


class EventBox(Gtk.Box):
	"""Replacement for Gtk.EventBox."""

	def add(self, child: Gtk.Widget) -> None:
		pack(self, child)


class RadioButton(Gtk.CheckButton):
	"""GTK 4 replacement using grouped check buttons."""

	def __init__(
		self,
		label: str = "",
		group: RadioButton | None = None,
	) -> None:
		super().__init__(label=label)
		if group is None:
			# Gtk.RadioButton groups always start with one active member.
			self.set_active(True)
		else:
			self.set_group(group)

	@classmethod
	def new_with_mnemonic(
		cls,
		group: RadioButton | None,
		label: str,
	) -> RadioButton:
		button = cls(label=label, group=group)
		button.set_use_underline(True)
		return button

	@classmethod
	def new_with_mnemonic_from_widget(
		cls,
		radio_group_member: RadioButton,
		label: str,
	) -> RadioButton:
		return cls.new_with_mnemonic(radio_group_member, label)

	def connect_after(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		if signal == "clicked":
			signal = "toggled"
		return super().connect_after(signal, callback, *user_data)


class FontButton(Gtk.Button):
	"""Replacement for Gtk.FontButton."""

	def __init__(self) -> None:
		super().__init__()
		self._font_name = ""
		self._font_set_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...]]] = []
		self.set_label("Font")
		self.add_css_class("font-button")

	@staticmethod
	def get_font(button: FontButton) -> str | None:
		return button._font_name or None

	@staticmethod
	def set_font(button: FontButton, font_name: str) -> None:
		button._font_name = font_name
		button.set_label(font_name or "Font")

	def get_font_name(self) -> str:
		return self._font_name

	def set_font_name(self, font_name: str) -> None:
		FontButton.set_font(self, font_name)

	def set_show_size(self, _show_size: bool) -> None:
		pass

	def set_level(self, _level: Gtk.FontChooserLevel) -> None:
		pass

	def set_preview_text(self, text: str) -> None:
		# Gtk.FontDialog does not expose GtkFontChooser's persistent preview
		# property. Keep the value for compatibility with option widgets.
		self._preview_text = text

	def set_property(self, name: str, value: Any) -> None:
		if name == "preview-text":
			self.set_preview_text(str(value))
			return
		super().set_property(name, value)

	def connect(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		if signal == "font-set":
			self._font_set_callbacks.append((callback, user_data))
			return len(self._font_set_callbacks)
		return super().connect(signal, callback, *user_data)

	def emit(self, signal: str, *args: Any) -> Any:
		if signal == "font-set":
			for callback, user_data in self._font_set_callbacks:
				callback(self, *args, *user_data)
			return None
		return super().emit(signal, *args)


class ColorButton(Gtk.Button):
	"""Replacement for Gtk.ColorButton."""

	def __init__(self) -> None:
		super().__init__()
		self._color_set_callbacks: list[tuple[Callable[..., Any], tuple[Any, ...]]] = []
		self._rgba = Gdk.RGBA()
		self._rgba.red = 1.0
		self._rgba.green = 1.0
		self._rgba.blue = 1.0
		self._rgba.alpha = 1.0
		self._use_alpha = True
		self.add_css_class("color-button")
		self.connect("clicked", self._on_clicked)

	def _on_clicked(self, _button: Gtk.Button) -> None:
		dialog = Gtk.ColorDialog()
		dialog.choose_rgba(
			cast("Gtk.Window | None", self.get_root()),
			self._rgba,
			None,
			None,
			self._on_color_chosen,
		)

	def _on_color_chosen(self, dialog: Gtk.ColorDialog, result: Any) -> None:
		try:
			self._rgba = dialog.choose_rgba_finish(result)
		except Exception:
			return
		self.emit("color-set")

	def connect(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		if signal == "color-set":
			self._color_set_callbacks.append((callback, user_data))
			return len(self._color_set_callbacks)
		return super().connect(signal, callback, *user_data)

	def emit(self, signal: str, *args: Any) -> Any:
		if signal == "color-set":
			for callback, user_data in self._color_set_callbacks:
				callback(self, *args, *user_data)
			return None
		return super().emit(signal, *args)

	@staticmethod
	def get_rgba(button: ColorButton) -> Gdk.RGBA:
		return button._rgba

	@staticmethod
	def set_rgba(button: ColorButton, rgba: Gdk.RGBA) -> None:
		button._rgba = rgba

	def getRGBA(self) -> RGBA:
		from scal3.color_utils import RGBA as RGBAClass

		return RGBAClass(
			int(self._rgba.red * 255),
			int(self._rgba.green * 255),
			int(self._rgba.blue * 255),
			int(self._rgba.alpha * 255),
		)

	def setRGBA(self, color: RGB | RGBA | RawColor) -> None:
		from scal3.ui_gtk.color_utils import rgbaToGdkRGBA

		self._rgba = rgbaToGdkRGBA(*color)


class ColorChooser:
	@staticmethod
	def set_use_alpha(widget: ColorButton, use: bool) -> None:
		widget._use_alpha = use  # noqa: SLF001 -- Gtk.ColorChooser compatibility state

	@staticmethod
	def get_use_alpha(widget: ColorButton) -> bool:
		return widget._use_alpha  # noqa: SLF001 -- Gtk.ColorChooser compatibility state


class FileChooserButton(Gtk.Button):
	"""Replacement for Gtk.FileChooserButton."""

	def __init__(self, title: str = "Select File") -> None:
		super().__init__(label=title)
		self._filename = ""
		self._title = title
		self.connect("clicked", self._on_clicked)

	def _on_clicked(self, _button: Gtk.Button) -> None:
		dialog = Gtk.FileDialog(title=self._title)
		dialog.open(
			cast("Gtk.Window | None", self.get_root()),
			None,
			self._on_file_chosen,
		)

	def _on_file_chosen(self, _dialog: Gtk.FileDialog, result: Any) -> None:
		try:
			file = result
			if file is not None:
				self._filename = file.get_path() or ""
		except Exception:
			pass

	def get_filename(self) -> str | None:
		return self._filename or None

	@staticmethod
	def new_with_dialog(_dialog: Gtk.Dialog) -> FileChooserButton:
		return FileChooserButton()


def install_widget_patches() -> None:
	Gtk.EventBox = EventBox  # type: ignore[attr-defined]
	Gtk.RadioButton = RadioButton  # type: ignore[attr-defined]
	Gtk.FontButton = FontButton  # type: ignore[attr-defined]
	Gtk.ColorButton = ColorButton  # type: ignore[attr-defined]
	Gtk.ColorChooser = ColorChooser  # type: ignore[attr-defined]
	Gtk.FileChooserButton = FileChooserButton  # type: ignore[attr-defined]

	def frame_add(self: Gtk.Frame, child: Gtk.Widget) -> None:
		self.set_child(child)

	Gtk.Frame.add = frame_add  # type: ignore[attr-defined]
	Gtk.Frame.set_shadow_type = lambda self, shadow_type: None  # type: ignore[attr-defined]  # noqa: ARG005

	def paned_add(self: Gtk.Paned, child: Gtk.Widget) -> None:
		if self.get_start_child() is None:
			self.set_start_child(child)
		elif self.get_end_child() is None:
			self.set_end_child(child)
		else:
			raise ValueError("Gtk.Paned already has two children")

	def paned_remove(self: Gtk.Paned, child: Gtk.Widget) -> None:
		if self.get_start_child() is child:
			self.set_start_child(None)
		elif self.get_end_child() is child:
			self.set_end_child(None)

	Gtk.Paned.add = paned_add  # type: ignore[attr-defined]
	Gtk.Paned.remove = paned_remove  # type: ignore[assignment]

	if not hasattr(Gtk.ScrolledWindow, "add_with_viewport"):
		Gtk.ScrolledWindow.add_with_viewport = lambda self, child: self.set_child(child)  # type: ignore[attr-defined]

	if not hasattr(Gdk, "EventMask"):

		class EventMask:
			ALL_EVENTS_MASK = 0

		Gdk.EventMask = EventMask  # type: ignore[attr-defined]

	if not hasattr(Gtk, "ShadowType"):

		class ShadowType:
			IN = 1
			ETCHED_IN = 3

		Gtk.ShadowType = ShadowType  # type: ignore[attr-defined]

	if not hasattr(Gdk, "Screen"):

		class Screen:
			@staticmethod
			def get_default() -> None:
				return None

		Gdk.Screen = Screen  # type: ignore[attr-defined]

	if not hasattr(Gdk, "get_default_root_window"):
		Gdk.get_default_root_window = lambda: None  # type: ignore[attr-defined]

	def get_for_screen(_screen: Any) -> Gtk.Settings | None:
		return Gtk.Settings.get_default()

	Gtk.Settings.get_for_screen = staticmethod(get_for_screen)  # type: ignore[attr-defined]

	if not hasattr(Gtk.Window, "move"):
		Gtk.Window.move = lambda self, x, y: None  # type: ignore[attr-defined]  # noqa: ARG005

	if not hasattr(Gtk.Window, "set_role"):
		Gtk.Window.set_role = lambda self, role: None  # type: ignore[attr-defined]  # noqa: ARG005

	if not hasattr(Gtk.Widget, "drag_source_set"):
		Gtk.Widget.drag_source_set = lambda self, *a, **k: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_dest_set = lambda self, *a, **k: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_source_add_text_targets = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_source_add_uri_targets = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_dest_add_text_targets = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_dest_add_uri_targets = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.Widget.drag_source_unset = lambda self: None  # type: ignore[attr-defined]  # noqa: ARG005
		Gtk.drag_set_icon_pixbuf = lambda *a: None  # type: ignore[attr-defined]  # noqa: ARG005

	if not hasattr(Gtk.Button, "set_always_show_image"):
		Gtk.Button.set_always_show_image = lambda self, show: None  # type: ignore[attr-defined]  # noqa: ARG005

	if not hasattr(Gtk.Dialog, "get_action_area"):
		Gtk.Dialog.get_action_area = lambda self: self  # type: ignore[attr-defined]

	if not hasattr(Gtk.Window, "set_cursor"):
		Gtk.Window.set_cursor = lambda self, cursor: None  # type: ignore[attr-defined]  # noqa: ARG005

	if not hasattr(Gtk.Widget, "remove"):

		def widget_remove(self: Gtk.Widget, child: Gtk.Widget) -> None:
			if hasattr(self, "get_child") and self.get_child() is child:
				self.set_child(None)

		Gtk.Widget.remove = widget_remove  # type: ignore[attr-defined]
