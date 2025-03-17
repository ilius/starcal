from __future__ import annotations

import sys
from os.path import abspath, dirname, isabs, join

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk as gtk

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf

gi.require_version("PangoCairo", "1.0")

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable

_ = str

scalDir = dirname(dirname(__file__))
sourceDir = abspath(dirname(scalDir))
pixDir = join(sourceDir, "pixmaps")
svgDir = join(sourceDir, "svg")


def HBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


def pack(
	box: gtk.Box | gtk.CellLayout,
	child: gtk.Widget | gtk.CellRenderer,
	expand: bool = False,
	fill: bool = False,  # noqa: ARG001
	padding: int = 0,
) -> None:  # noqa: ARG001
	if padding > 0:
		print(f"pack: padding={padding} ignored")
	if isinstance(box, gtk.Box):
		box.append(child)
		if expand:
			if box.get_orientation() == gtk.Orientation.VERTICAL:
				child.set_vexpand(True)
			else:
				child.set_hexpand(True)
		# FIXME: what to do with: fill, padding
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError(f"pack: unknown type {type(box)}")


def imageFromIconName(iconName: str, size: int, nonStock: bool = False) -> gtk.Image:
	# So gtk.Image.new_from_stock is deprecated
	# And the doc says we should use gtk.Image.new_from_icon_name
	# which does NOT have the same functionality!
	# because not all stock items are existing in all themes (even popular themes)
	# and new_from_icon_name does not seem to look in other (non-default) themes!
	# So for now we use new_from_stock, unless it's not a stock item
	# But we do not use either of these two outside this function
	# So that it's easy to switch
	if nonStock:
		return gtk.Image.new_from_icon_name(iconName)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except Exception:
		return gtk.Image.new_from_icon_name(iconName)


def dialog_add_button(
	dialog: gtk.Dialog,
	_iconName: str,  # TODO: remove
	label: str,
	resId: int,
	onClicked: Callable | None = None,
	tooltip: str = "",
) -> None:
	button = gtk.Button(
		label=label,
		use_underline=True,
		# icon_name=iconName,
	)
	# fixed bug: used to ignore resId and pass gtk.ResponseType.OK
	dialog.add_action_widget(
		button,
		resId,
	)
	if onClicked:
		label.connect("clicked", onClicked)
	if tooltip:
		label.set_tooltip_text(tooltip)

def imageFromFile(path, size=0):
	if not isabs(path):
		if path.endswith(".svg"):
			path = join(svgDir, path)
		else:
			path = join(pixDir, path)
	if path.endswith(".svg"):
		return gtk.Image.new_from_pixbuf(pixbufFromSvgFile(path, size))
	if size <= 0:
		raise ValueError(f"invalid {size=}")
	return gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(path))


def pixbufFromSvgFile(path: str, size: int):
	if size <= 0:
		raise ValueError(f"invalid {size=} for svg file {path}")
	if not isabs(path):
		path = join(svgDir, path)
	with open(path, "rb") as fp:
		data = fp.read()
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	loader.set_size(size, size)
	try:
		loader.write(data)
	finally:
		loader.close()
	return loader.get_pixbuf()


def showMsg(  # noqa: PLR0913
	msg: str,
	iconName: str = "",
	transient_for: gtk.Widget | None = None,
	title: str = "",
	borderWidth: int = 10,  # noqa: ARG001
	iconSize: gtk.IconSize = gtk.IconSize.LARGE,
	selectable: bool = False,
) -> None:
	win = gtk.Dialog(
		transient_for=transient_for,
	)
	# flags=0 makes it skip task bar
	if title:
		win.set_title(title)
	hbox = HBox(spacing=10)
	# hbox.set_border_width(borderWidth)
	if iconName:
		# win.set_icon(...)
		pack(hbox, imageFromIconName(iconName, iconSize))
	label = gtk.Label(label=msg)
	# set_line_wrap(True) makes the window go crazy tall (taller than screen)
	# and that's the reason for label.set_size_request and win.resize
	# label.set_line_wrap(True)
	# label.set_line_wrap_mode(pango.WrapMode.WORD)
	label.set_size_request(500, 1)
	if selectable:
		label.set_selectable(True)
	pack(hbox, label)
	hbox.show()
	content_area = win.get_content_area()
	pack(content_area, hbox)
	dialog_add_button(
		win,
		"gtk-close",
		"_Close",
		gtk.ResponseType.OK,
	)

	def onResponse(_w, _response_id: int) -> None:
		win.destroy()

	win.connect("response", onResponse)

	# win.resize(600, 1)
	win.show()


def showError(msg, **kwargs):
	showMsg(msg, iconName="gtk-dialog-error", **kwargs)


def error_exit(resCode, text, **kwargs):
	d = gtk.MessageDialog(
		destroy_with_parent=True,
		message_type=gtk.MessageType.ERROR,
		buttons=gtk.ButtonsType.OK,
		text=text.strip(),
		**kwargs,
	)
	d.set_title("Error")
	d.run()
	sys.exit(resCode)


if sys.version_info[0] < 3:  # noqa: UP036
	error_exit(1, "Run this script with Python 3.x")

try:
	from scal3.ui_gtk.starcal import main

	sys.exit(main())
except Exception as e:
	msg = str(e).strip()
	log.error(msg)
	showError(msg)
	sys.exit(1)
