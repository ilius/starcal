#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from time import time as now
import os
from os.path import join, isabs
from subprocess import Popen

from typing import Optional, Tuple, Union, Callable

from scal3.utils import toBytes, toStr
from scal3.json_utils import *
from scal3.color_utils import ColorType, rgbToCSS
from scal3.path import pixDir, sourceDir
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from gi.repository import GdkPixbuf
from gi.repository import Pango as pango

from scal3.ui_gtk import *
from scal3.ui_gtk.icon_mapping import (
	iconNameByImageName,
	rtlImageNameMapping,
)
from scal3.ui_gtk import pixcache
from scal3.ui_gtk.svg_utils import pixbufFromSvgFile, imageFromSvgFile
from scal3.ui_gtk.color_utils import gdkColorToRgb


def hideList(widgets):
	for w in widgets:
		w.hide()


def showList(widgets):
	for w in widgets:
		w.show()


def set_tooltip(widget, text):
	widget.set_tooltip_text(text)


def buffer_get_text(b):
	return b.get_text(
		b.get_start_iter(),
		b.get_end_iter(),
		True,
	)


def show_event(widget, gevent):
	try:
		value = gevent.get_value()
	except AttributeError:
		value = "NONE"
	log.debug(
		# f"{type(widget).__class__.__name__}, " +
		f"{widget.__class__.__name__}, " +
		f"value_name={gevent.type.value_name}, value={value}"
	)
	# gevent.send_event


def setClipboard(text, clipboard=None):
	if not clipboard:
		clipboard = gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)
	clipboard.set_text(
		toStr(text),
		len(toBytes(text)),
	)
	#clipboard.store() ## ?????? No need!


def imageFromIconName(
	iconName: str,
	size: gtk.IconSize,
) -> gtk.Image:
	# TODO: pixcache does not contain iconNames right now, maybe later
	# pixbuf = pixcache.getPixbuf(iconName, int(size))
	# if pixbuf is not None:
	#	return gtk.Image.new_from_pixbuf(pixbuf)

	# So gtk.Image.new_from_stock is deprecated
	# And the doc says we should use gtk.Image.new_from_icon_name
	# which does NOT have the same functionality!
	# because not all stock items are existing in all themes (even popular themes)
	# and new_from_icon_name does not seem to look in other (non-default) themes!
	# So for now we use new_from_stock, unless it's not a stock item
	# But we do not use either of these two outside this function
	# So that it's easy to switch
	if not iconName.startswith("gtk-"):
		return gtk.Image.new_from_icon_name(iconName, size)
	try:
		return gtk.Image.new_from_stock(iconName, size)
	except AttributeError:
		# just in case new_from_stock was removed
		return gtk.Image.new_from_icon_name(iconName, size)


# this is not working, image.get_pixbuf returns None!
def imageFromIconNameWithPixelSize(
	iconName: str,
	size: int,
) -> gtk.Image:
	image = imageFromIconName(
		iconName,
		size=gtk.IconSize.DIALOG,
	)
	pixbuf = image.get_pixbuf()
	if pixbuf is None:
		raise RuntimeError("pixbuf is None")
	pixbuf = pixbuf.scale_simple(
		size, size,
		GdkPixbuf.InterpType.BILINEAR,
	)
	image.set_from_pixbuf(pixbuf)
	return image


def imageFromFile(path, size=0):
	# the file must exist
	im = gtk.Image()
	pixbuf = pixbufFromFile(path, size=size)
	im.set_from_pixbuf(pixbuf)
	return im


def pixbufFromFile(
	path: str,
	size: Union[int, float] = 0,
) -> GdkPixbuf.Pixbuf:
	# the file may not exist
	if not path:
		return None
	pixbuf = pixcache.getPixbuf(path, size)
	if pixbuf is not None:
		return pixbuf
	if path.endswith(".svg"):
		pixbuf = pixbufFromSvgFile(path, size)
		pixcache.setPixbuf(path, size, pixbuf)
		return pixbuf
	relPath = path
	if not isabs(path):
		path = join(pixDir, path)
	try:
		pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
	except GLibError:
		log.exception(f"Error while opening image {path}")
		return None
	if pixbuf is None:
		return
	if size < 0:
		raise ValueError(f"pixbufFromFile: invalid size={size}")
	if pixbuf.get_width() != size:
		pixbuf = pixbuf.scale_simple(
			size, size,
			GdkPixbuf.InterpType.BILINEAR,
		)
		pixcache.setPixbuf(relPath, size, pixbuf)
	return pixbuf


"""
Looks like Gtk.Button.set_image is removed since Gtk 3.89.1

commit be2f19663bf9c1ead35fa69aee0292842ceada97
Author: Timm Bäder <mail@baedert.org>
Date:   Fri Oct 14 17:31:56 2016

    button: Add icon-name property

    Remove the old-style button construction that allowed to show both an
    icon and a label and change visibility based on a GtkSetting.
"""


def newButtonImageBox(label: str, image: gtk.Image, spacing=0) -> gtk.Box:
	hbox = HBox(spacing=spacing)
	labelObj = gtk.Label(label=label)
	labelObj.set_use_underline(True)
	labelObj.set_xalign(0)
	pack(hbox, image, 0, 0)
	pack(hbox, labelObj, 0, 0)
	hbox.show_all()
	return hbox


def labelIconButton(
	label: str = "",
	iconName: str = "",
	size: gtk.IconSize = gtk.IconSize.BUTTON,
):
	button = gtk.Button()
	if ui.buttonIconEnable:
		button.add(newButtonImageBox(
			label,
			imageFromIconName(iconName, size),
			spacing=size/2,
		))
		return button
	button.set_label(label)
	button.set_use_underline(True)
	return button


def labelImageButton(
	label: str = "",
	imageName: str = "",
	size: int = 0,
):
	button = gtk.Button()
	if ui.buttonIconEnable:
		if size == 0:
			size = ui.buttonIconSize
		button.add(newButtonImageBox(
			label,
			imageFromFile(imageName, size=size),
			spacing=10,
		))
		# TODO: the child(HBox) is not centered in the Button
		# problem can be seen in Preferences window: Apply and OK buttons
		# button.set_alignment(0.5, 0.5)
		return button
	button.set_label(label)
	button.set_use_underline(True)
	return button


def imageClassButton(iconName: str, styleClass: str, size: int):
	button = gtk.Button()
	button.add(imageFromIconName(
		iconName,
		size,
	))
	button.get_style_context().add_class("image-button")
	button.set_can_focus(False)
	if styleClass:
		button.get_style_context().add_class(styleClass)
	return button


def getStyleColor(widget, state=gtk.StateType.NORMAL):
	return widget.get_style_context().get_color(state)


def modify_bg_all(widget, state, gcolor):
	log.info(widget.__class__.__name__)
	widget.modify_bg(state, gcolor)
	try:
		children = widget.get_children()
	except AttributeError:
		pass
	else:
		for child in children:
			modify_bg_all(child, state, gcolor)


def rectangleContainsPoint(r, x, y):
	return (
		r.x <= x < r.x + r.width and
		r.y <= y < r.y + r.height
	)


"""
>>> sorted(gtk.ResponseType.__enum_values__.items())
[(-11, <enum GTK_RESPONSE_HELP of type Gtk.ResponseType>), (-10, <enum GTK_RESPONSE_APPLY of type Gtk.ResponseType>), (-9, <enum GTK_RESPONSE_NO of type Gtk.ResponseType>), (-8, <enum GTK_RESPONSE_YES of type Gtk.ResponseType>), (-7, <enum GTK_RESPONSE_CLOSE of type Gtk.ResponseType>), (-6, <enum GTK_RESPONSE_CANCEL of type Gtk.ResponseType>), (-5, <enum GTK_RESPONSE_OK of type Gtk.ResponseType>), (-4, <enum GTK_RESPONSE_DELETE_EVENT of type Gtk.ResponseType>), (-3, <enum GTK_RESPONSE_ACCEPT of type Gtk.ResponseType>), (-2, <enum GTK_RESPONSE_REJECT of type Gtk.ResponseType>), (-1, <enum GTK_RESPONSE_NONE of type Gtk.ResponseType>)]
"""

def dialog_add_button(
	dialog,
	iconName: str = "",
	label: str = "",
	res: Optional[gtk.ResponseType] = None,
	onClick: Optional[Callable] = None,
	tooltip: str = "",
	imageName: str = "",
):
	b = dialog.add_button(label, res)
	if label:
		b.set_label(label)
	if ui.buttonIconEnable:
		b.set_always_show_image(True)
		# FIXME: how to get rid of set_image calls?
		useIconName = bool(iconName)
		if ui.useSystemIcons:
			if imageName and not iconName:
				iconName = iconNameByImageName.get(imageName, "")
				useIconName = bool(iconName)
		if useIconName:
			b.set_image(imageFromIconName(iconName, gtk.IconSize.BUTTON))
		elif imageName:
			if rtl:
				imageName = rtlImageNameMapping.get(imageName, imageName)
			b.set_image(imageFromFile(
				imageName,
				size=ui.buttonIconSize,
			))
	if onClick:
		b.connect("clicked", onClick)
	if tooltip:
		set_tooltip(b, tooltip)
	return b


def confirm(msg, **kwargs):
	win = gtk.MessageDialog(
		flags=0,
		message_type=gtk.MessageType.INFO,
		buttons=gtk.ButtonsType.NONE,
		text=msg,
		**kwargs
	)
	dialog_add_button(
		win,
		imageName="dialog-cancel.svg",
		label=_("_Cancel"),
		res=gtk.ResponseType.CANCEL,
	)
	dialog_add_button(
		win,
		imageName="dialog-ok.svg",
		label=_("_OK"),
		res=gtk.ResponseType.OK,
	)
	ok = win.run() == gtk.ResponseType.OK
	win.destroy()
	return ok


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
			size=ui.messageDialogIconSize,
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
		imageName="dialog-close.svg",
		label=_("_Close"),
		res=gtk.ResponseType.OK,
	)
	win.resize(600, 1)
	win.run()
	win.destroy()


def showError(msg, **kwargs):
	showMsg(msg, imageName="dialog-error.svg", **kwargs)


def showWarning(msg, **kwargs):
	showMsg(msg, imageName="dialog-warning.svg", **kwargs)


def showInfo(msg, **kwargs):
	showMsg(msg, imageName="dialog-information.svg", **kwargs)


def openWindow(win):
	win.set_keep_above(ui.winKeepAbove)
	win.present()


def get_menu_width(menu):
	"""
	# log.debug(menu.has_screen())
	#menu.show_all()
	#menu.realize()
	log.info(
		menu.get_border_width(),
		max_item_width,
		menu.get_allocation().width,
		menu.get_preferred_size()[1].width,
		menu.get_preferred_size()[0],
		menu.get_preferred_width(),
		#menu.do_get_preferred_width(),
		menu.get_preferred_size()[0].width,
		menu.get_preferred_size()[1].width,
		)
	"""
	w = menu.get_allocation().width
	# get_preferred_size() returns (minimum_size: Gtk.Requisition,
	# 		natural_size: Gtk.Requisition)
	if w > 1:
		# log.debug(w - max(
		# 	item.get_preferred_size()[1].width for item in menu.get_children()
		# ))
		return w
	items = menu.get_children()
	if items:
		mw = max(item.get_preferred_size()[1].width for item in items)
		return mw + ui.cellMenuXOffset
	return 0


def get_menu_height(menu):
	h = menu.get_allocation().height
	if h > 1:
		# log.debug("menu height from before:", h)
		return h
	items = menu.get_children()
	if not items:
		return 0
	# get_preferred_size() returns (minimum_size: Gtk.Requisition,
	#		natural_size: Gtk.Requisition)
	h = sum(item.get_preferred_size()[1].height for item in items)
	# FIXME: does not work, all items are zero
	# log.debug("menu height from sum:", h)
	# log.debug([item.get_preferred_size()[1].height for item in items])
	return h


def get_pixbuf_hash(pbuf):
	import hashlib
	md5 = hashlib.md5()

	def save_func(chunkBytes, size, unknown):
		# len(chunkBytes) == size
		md5.update(chunkBytes)
		return True

	pbuf.save_to_callbackv(
		save_func,
		None,  # user_data
		"bmp",  # type, name of file format
		[],  # option_keys
		[],  # option_values
	)
	return md5.hexdigest()


def window_set_size_aspect(win, min_aspect, max_aspect=None):
	if max_aspect is None:
		max_aspect = min_aspect
	geom = gdk.Geometry()
	geom.min_aspect = min_aspect
	geom.max_aspect = max_aspect
	win.set_geometry_hints(
		None,  # widget, ignored since Gtk 3.20
		geom,  # geometry
		gdk.WindowHints.ASPECT,  # geom_mask
	)
	win.resize(1, 1)


def newHSep():
	return gtk.Separator(orientation=gtk.Orientation.HORIZONTAL)


def newAlignLabel(sgroup=None, label=""):
	label = gtk.Label(label=label)
	label.set_xalign(0)
	if sgroup:
		sgroup.add_widget(label)
	return label


class IdComboBox(gtk.ComboBox):
	def set_active(self, _id):
		ls = self.get_model()
		for i in range(len(ls)):
			if ls[i][0] == _id:
				gtk.ComboBox.set_active(self, i)
				return

	def get_active(self):
		i = gtk.ComboBox.get_active(self)
		if i is None:
			return
		model = self.get_model()
		if model is None:
			log.info("IdComboBox.get_active: model is None")
		try:
			return model[i][0]
		except IndexError:
			return


class CopyLabelMenuItem(MenuItem):
	def __init__(self, label):
		MenuItem.__init__(self)
		self.set_label(label)
		self.connect("activate", self.on_activate)

	def on_activate(self, item):
		setClipboard(self.get_property("label"))


def cssTextStyle(
	font: Optional[Tuple[str, bool, bool, float]] = None,
	fgColor: Optional[ColorType] = None,
	bgColor: Optional[ColorType] = None,
) -> str:
	lines = []
	if font:
		lines += [
			f"\tfont-family: {font[0]};",
			f"\tfont-size: {font[3]}pt;",
			f"\tfont-weight: {'bold' if font[1] else 'normal'};",
			f"\tfont-style: {'italic' if font[2] else 'normal'};",
		]
	if fgColor:
		lines.append(f"\tcolor: {rgbToCSS(fgColor)};")
	if bgColor:
		lines.append(f"\tbackground-color: {rgbToCSS(bgColor)};")

	return "{\n" + "\n".join(lines) + "\n}"


def getBackgroundColor(widget: gtk.Widget):
	return gdkColorToRgb(
		widget.get_style_context().
		get_background_color(gtk.StateFlags.NORMAL)
	)

def getBackgroundColorCSS(widget: gtk.Widget):
	from scal3.color_utils import rgbToCSS
	return rgbToCSS(getBackgroundColor(widget))


if __name__ == "__main__":
	diolog = gtk.Dialog()
	w = TimeZoneComboBoxEntry()
	pack(diolog.vbox, w)
	diolog.vbox.show_all()
	diolog.run()
