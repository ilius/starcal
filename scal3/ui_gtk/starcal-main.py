from __future__ import annotations

import sys
from os.path import abspath, dirname, isabs, join

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk as gtk

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf

gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango as pango

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3.ui_gtk.utils import set_tooltip

if TYPE_CHECKING:
	from collections.abc import Callable

_ = str

scalDir = dirname(dirname(__file__))
sourceDir = abspath(dirname(scalDir))
pixDir = join(sourceDir, "pixmaps")
svgDir = join(sourceDir, "svg")


def HBox(**kwargs) -> gtk.Box:
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


def pack(
	box: gtk.Box | gtk.CellLayout,
	child: gtk.Widget,
	expand: bool | int = False,
	fill: bool | int = False,
	padding: int = 0,
) -> None:
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand=expand, fill=fill, padding=padding)
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError(f"pack: unkown type {type(box)}")


def imageFromIconName(
	iconName: str,
	size: gtk.IconSize,
) -> gtk.Image:
	if not iconName.startswith("gtk-"):
		return gtk.Image.new_from_icon_name(iconName, size)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except AttributeError:
		# just in case new_from_stock was removed
		return gtk.Image.new_from_icon_name(iconName, size)


def dialog_add_button(
	dialog: gtk.Dialog,
	imageName: str = "",
	label: str = "",
	res: gtk.ResponseType | None = None,
	onClick: Callable | None = None,
	tooltip: str = "",
) -> gtk.Button:
	b = dialog.add_button(label, res)
	if label:
		b.set_label(label)
	# FIXME: how to get rid of set_image calls?
	if imageName:
		b.set_image(imageFromFile(imageName, size=22))
	if onClick:
		b.connect("clicked", onClick)
	if tooltip:
		set_tooltip(b, tooltip)
	return b


def imageFromFile(path: str, size: float = 0) -> gtk.Image:
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


def pixbufFromSvgFile(path: str, size: int) -> GdkPixbuf.Pixbuf:
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


def showMsg(
	msg: str,
	imageName: str = "",
	parent: gtk.Window | None = None,
	transient_for: gtk.Window | None = None,
	title: str = "",
	borderWidth: int = 10,
	selectable: bool = False,
) -> None:
	win = gtk.Dialog(
		parent=parent,
		transient_for=transient_for,
	)
	# flags=0 makes it skip task bar
	if title:
		win.set_title(title)
	hbox = HBox(spacing=10)
	hbox.set_border_width(borderWidth)
	# win.set_icon(...)
	if imageName:
		pack(
			hbox,
			imageFromFile(
				imageName,
				size=48,
			),
		)
	label = gtk.Label(label=msg)
	# set_line_wrap(True) makes the window go crazy tall (taller than screen)
	# and that's the reason for label.set_size_request and win.resize
	label.set_line_wrap(True)
	label.set_line_wrap_mode(pango.WrapMode.WORD)
	label.set_size_request(500, 1)
	if selectable:
		label.set_selectable(True)
	pack(hbox, label)
	hbox.show_all()
	pack(win.vbox, hbox)
	dialog_add_button(
		win,
		imageName="window-close.svg",
		label=_("_Close"),
		res=gtk.ResponseType.OK,
	)
	win.resize(600, 1)
	win.run()
	win.destroy()


def showError(msg: str, **kwargs) -> None:
	showMsg(msg, imageName="dialog-error.svg", **kwargs)


def error_exit(resCode: int, text: str, **kwargs) -> None:
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


try:
	from scal3.ui_gtk.starcal import main

	sys.exit(main())
except Exception as e:
	msg = str(e).strip()
	log.error(msg)
	showError(msg)
	sys.exit(1)
