#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from os.path import dirname, abspath, join, isabs
from typing import Optional, Callable


import gi

gi.require_version("Gtk", "3.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gtk as gtk
from gi.repository import Pango as pango
from gi.repository import GdkPixbuf


sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal3 import logger


log = logger.get()

_ = str

scalDir = dirname(dirname(__file__))
sourceDir = abspath(dirname(scalDir))
pixDir = join(sourceDir, "pixmaps")
svgDir = join(sourceDir, "svg")


def HBox(**kwargs):
	return gtk.Box(orientation=gtk.Orientation.HORIZONTAL, **kwargs)


def pack(box, child, expand=False, fill=False, padding=0):
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
	dialog,
	imageName: str = "",
	label: str = "",
	res: Optional[gtk.ResponseType] = None,
	onClick: Optional[Callable] = None,
	tooltip: str = "",
):
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


def imageFromFile(path, size=0):
	if not isabs(path):
		if path.endswith(".svg"):
			path = join(svgDir, path)
		else:
			path = join(pixDir, path)
	if path.endswith(".svg"):
		return gtk.Image.new_from_pixbuf(pixbufFromSvgFile(path, size))
	if size <= 0:
		raise ValueError(f"invalid size={size}")
	return gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(path))


def pixbufFromSvgFile(path: str, size: int):
	if size <= 0:
		raise ValueError(f"invalid size={size} for svg file {path}")
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
	pixbuf = loader.get_pixbuf()
	return pixbuf


def showMsg(
	msg,
	imageName="",
	parent=None,
	transient_for=None,
	title="",
	borderWidth=10,
	selectable=False,
):
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
		pack(hbox, imageFromFile(
			imageName,
			size=48,
		))
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


def showError(msg, **kwargs):
	showMsg(msg, imageName="dialog-error.svg", **kwargs)


if sys.version_info[0] != 3:
	error_exit(1, "Run this script with Python 3.x")

try:
	from scal3.ui_gtk.starcal import main
	sys.exit(main())
except Exception as e:
	msg = str(e).strip()
	log.error(msg)
	showError(msg)
	sys.exit(1)
