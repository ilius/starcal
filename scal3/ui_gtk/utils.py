#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
from __future__ import annotations

from scal3 import logger

log = logger.get()

from os.path import isabs, join
from typing import TYPE_CHECKING, Any

from scal3.color_utils import rgbToCSS
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.path import pixDir, svgDir
from scal3.ui import conf
from scal3.ui_gtk import (
	Dialog,
	GdkPixbuf,
	GLibError,
	MenuItem,
	gdk,
	gtk,
	pack,
	pango,
	pixcache,
)
from scal3.ui_gtk.color_utils import gdkColorToRgb
from scal3.ui_gtk.icon_mapping import (
	iconNameByImageName,
	rtlImageNameMapping,
)
from scal3.ui_gtk.svg_utils import pixbufFromSvgFile
from scal3.utils import toBytes

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import ColorType
	from scal3.font import Font

__all__ = [
	"CopyLabelMenuItem",
	"GLibError",
	"IdComboBox",
	"buffer_get_text",
	"confirm",
	"cssTextStyle",
	"dialog_add_button",
	"getGtkWindow",
	"get_menu_height",
	"get_menu_width",
	"get_pixbuf_hash",
	"imageClassButton",
	"imageFromFile",
	"imageFromIconName",
	"labelImageButton",
	"newAlignLabel",
	"newHSep",
	"openWindow",
	"pixbufFromFile",
	"pixbufFromFileMust",
	"pixbufFromIconName",
	"rectangleContainsPoint",
	"resolveImagePath",
	"setClipboard",
	"setImageClassButton",
	"set_tooltip",
	"showError",
	"showInfo",
	"showMsg",
	"trimMenuItemLabel",
	"widgetActionCallback",
	"window_set_size_aspect",
	"x_large",
]


def widgetActionCallback[*Ts](
	func: Callable[[*Ts], None],
) -> Callable[[*Ts], Callable[[gtk.Widget], None]]:
	def func2(*args: *Ts) -> Callable[[gtk.Widget], None]:
		def func3(_w: gtk.Widget) -> None:
			func(*args)

		return func3

	return func2


def set_tooltip(widget: gtk.Widget, text: str) -> None:
	widget.set_tooltip_text(text)


def buffer_get_text(b: gtk.TextBuffer) -> str:
	return b.get_text(
		b.get_start_iter(),
		b.get_end_iter(),
		True,
	)


# def show_event(widget: gtk.Widget, gevent: gdk.Event) -> None:
# 	# try:
# 	# 	value = gevent.get_value()
# 	# except AttributeError:
# 	# 	value = "NONE"
# 	log.debug(
# 		# f"{type(widget).__class__.__name__}, " +
# 		f"{widget.__class__.__name__}, {gevent.type.value_name=}",
# 	)
# 	# gevent.send_event


def setClipboard(text: str, clipboard: gtk.Clipboard | None = None) -> None:
	if not clipboard:
		clipboard = gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)
	clipboard.set_text(
		text,
		len(toBytes(text)),
	)
	# clipboard.store() # ?????? No need!


def imageFromIconName(
	iconName: str,
	size: gtk.IconSize,
) -> gtk.Image:
	# TODO: pixcache does not contain iconNames right now, maybe later
	# pixbuf = pixcache.getPixbuf(iconName, int(size))
	# if pixbuf is not None:
	# 	return gtk.Image.new_from_pixbuf(pixbuf)

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


def imageFromFile(path: str, size: int = 0) -> gtk.Image:
	# the file must exist
	im = gtk.Image()
	pixbuf = pixbufFromFile(path, size=size)
	im.set_from_pixbuf(pixbuf)
	return im


def resolveImagePath(path: str) -> str:
	if isabs(path):
		return path
	if path.endswith(".svg"):
		return join(svgDir, path)
	return join(pixDir, path)


def pixbufFromFileMust(
	path: str | None,
	size: int = 0,
) -> GdkPixbuf.Pixbuf:
	pixbuf = pixbufFromFile(path, size)
	assert pixbuf is not None
	return pixbuf


def pixbufFromFile(
	path: str | None,
	size: int = 0,
) -> GdkPixbuf.Pixbuf | None:
	# the file may not exist
	if not path:
		return None
	pixbuf = pixcache.getPixbuf(path, size)
	if pixbuf is not None:
		return pixbuf
	if path.endswith(".svg"):
		pixbuf = pixbufFromSvgFile(path, size)
		if pixbuf is not None:
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
		return None
	if size < 0:
		raise ValueError(f"pixbufFromFile: invalid {size=}")
	if pixbuf.get_width() != size:
		pixbuf = pixbuf.scale_simple(
			size,
			size,
			GdkPixbuf.InterpType.BILINEAR,
		)
		if pixbuf is not None:
			pixcache.setPixbuf(relPath, size, pixbuf)
	return pixbuf


def pixbufFromIconName(iconName: str, iconSize: int) -> GdkPixbuf.Pixbuf:
	pixbuf = gtk.IconTheme.get_default().load_icon(
		iconName,
		iconSize,
		0,  # type: ignore[arg-type] # Gtk.IconLookupFlags
	)
	assert pixbuf is not None
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


def newButtonImageBox(label: str, image: gtk.Image, spacing: int = 0) -> gtk.Box:
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=spacing)
	pack(hbox, image, 0, 0)
	if label:
		labelObj = gtk.Label(label=label)
		labelObj.set_use_underline(True)
		labelObj.set_xalign(0)
		pack(hbox, labelObj, 0, 0)
	hbox.show_all()
	return hbox


def labelImageButton(
	label: str = "",
	imageName: str = "",
	size: int = 0,
	func: Callable[[gtk.Button], None] | None = None,
	tooltip: str = "",
	spacing: int = 10,
) -> gtk.Button:
	button = gtk.Button()
	if conf.buttonIconEnable.v or not label:
		if size == 0:
			size = int(conf.buttonIconSize.v)
		button.add(
			newButtonImageBox(
				label,
				imageFromFile(imageName, size=size),
				spacing=spacing,
			),
		)
		# TODO: the child(HBox) is not centered in the Button
		# problem can be seen in Preferences window: Apply and OK buttons
		# button.set_alignment(0.5, 0.5)
	else:
		button.set_label(label)
		button.set_use_underline(True)
	if func is not None:
		button.connect("clicked", func)
	if tooltip:
		set_tooltip(button, tooltip)
	return button


def imageClassButton(iconName: str, styleClass: str, size: gtk.IconSize) -> gtk.Button:
	button = gtk.Button()
	button.add(
		imageFromIconName(
			iconName,
			size,
		),
	)
	button.get_style_context().add_class("image-button")
	button.set_can_focus(False)
	if styleClass:
		button.get_style_context().add_class(styleClass)
	return button


def setImageClassButton(
	button: gtk.Button,
	iconName: str,
	styleClass: str,
	size: gtk.IconSize,
) -> gtk.Button:
	child = button.get_child()
	if child is not None:
		button.remove(child)
	image = imageFromIconName(
		iconName,
		size,
	)
	image.show()
	button.add(image)
	button.get_style_context().add_class("image-button")
	button.set_can_focus(False)
	if styleClass:
		button.get_style_context().add_class(styleClass)
	return button


# def getStyleColor(widget: gtk.Widget, state:gtk.StateType=gtk.StateType.NORMAL):
# 	return widget.get_style_context().get_color(state)


def rectangleContainsPoint(r: gdk.Rectangle, x: float, y: float) -> bool:
	return r.x <= x < r.x + r.width and r.y <= y < r.y + r.height


"""
>>> sorted(gtk.ResponseType.__enum_values__.items()) == [
	(-11, <enum GTK_RESPONSE_HELP of type Gtk.ResponseType>),
	(-10, <enum GTK_RESPONSE_APPLY of type Gtk.ResponseType>),
	(-9, <enum GTK_RESPONSE_NO of type Gtk.ResponseType>),
	(-8, <enum GTK_RESPONSE_YES of type Gtk.ResponseType>),
	(-7, <enum GTK_RESPONSE_CLOSE of type Gtk.ResponseType>),
	(-6, <enum GTK_RESPONSE_CANCEL of type Gtk.ResponseType>),
	(-5, <enum GTK_RESPONSE_OK of type Gtk.ResponseType>),
	(-4, <enum GTK_RESPONSE_DELETE_EVENT of type Gtk.ResponseType>),
	(-3, <enum GTK_RESPONSE_ACCEPT of type Gtk.ResponseType>),
	(-2, <enum GTK_RESPONSE_REJECT of type Gtk.ResponseType>),
	(-1, <enum GTK_RESPONSE_NONE of type Gtk.ResponseType>)
]
"""


def dialog_add_button(
	dialog: gtk.Dialog,
	res: int,
	iconName: str = "",
	label: str = "",
	onClick: Callable[[gtk.Widget], None] | None = None,
	tooltip: str = "",
	imageName: str = "",
) -> gtk.Button:
	b: gtk.Button = dialog.add_button(button_text=label, response_id=res)  # type: ignore[assignment]
	# if label:
	# 	b.set_label(label)
	if conf.buttonIconEnable.v:
		b.set_always_show_image(True)
		# FIXME: how to get rid of set_image calls?
		useIconName = bool(iconName)
		if conf.useSystemIcons.v and imageName and not iconName:
			iconName = iconNameByImageName.get(imageName, "")
			useIconName = bool(iconName)
		if useIconName:
			b.set_image(imageFromIconName(iconName, gtk.IconSize.BUTTON))
		elif imageName:
			if rtl:
				imageName = rtlImageNameMapping.get(imageName, imageName)
			b.set_image(
				imageFromFile(
					imageName,
					size=conf.buttonIconSize.v,
				),
			)
	if onClick:
		b.connect("clicked", onClick)
	if tooltip:
		set_tooltip(b, tooltip)
	return b


def confirm(
	msg: str,
	title: str = "Confirmation",
	border_width: int = 15,
	transient_for: gtk.Window | None = None,
	use_markup: bool = False,
) -> bool:
	win = gtk.MessageDialog(
		message_type=gtk.MessageType.INFO,
		buttons=gtk.ButtonsType.NONE,
		text=msg,
		title=_(title),
		transient_for=transient_for,
		use_markup=use_markup,
	)
	button = dialog_add_button(
		win,
		res=gtk.ResponseType.CANCEL,
		imageName="dialog-cancel.svg",
		label=_("Cancel"),
	)
	button.set_border_width(border_width)
	button.get_style_context().add_class("bigger")
	button = dialog_add_button(
		win,
		res=gtk.ResponseType.OK,
		imageName="dialog-ok.svg",
		label=_("_Confirm"),
	)
	button.set_border_width(border_width)
	button.get_style_context().add_class("bigger")
	ok: bool = win.run() == gtk.ResponseType.OK  # type: ignore[no-untyped-call]
	win.destroy()
	return ok


def showMsg(
	msg: str,
	imageName: str = "",
	transient_for: gtk.Window | None = None,
	title: str = "",
	borderWidth: int = 10,
	selectable: bool = False,
) -> None:
	win = Dialog(
		transient_for=transient_for,
	)
	# flags=0 makes it skip task bar
	if title:
		win.set_title(title)
	hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=10)
	hbox.set_border_width(borderWidth)
	# win.set_icon(...)
	if imageName:
		pack(
			hbox,
			imageFromFile(
				imageName,
				size=conf.messageDialogIconSize.v,
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
		res=gtk.ResponseType.OK,
		imageName="window-close.svg",
		label=_("_Close"),
	)
	win.resize(600, 1)
	win.run()
	win.destroy()


def showError(
	msg: str,
	transient_for: gtk.Window | None = None,
	title: str = "",
	borderWidth: int = 10,
	selectable: bool = False,
) -> None:
	showMsg(
		msg,
		imageName="dialog-error.svg",
		transient_for=transient_for,
		title=title,
		borderWidth=borderWidth,
		selectable=selectable,
	)


def showInfo(
	msg: str,
	transient_for: gtk.Window | None = None,
	title: str = "",
	borderWidth: int = 10,
	selectable: bool = False,
) -> None:
	showMsg(
		msg,
		imageName="dialog-information.svg",
		transient_for=transient_for,
		title=title,
		borderWidth=borderWidth,
		selectable=selectable,
	)


def openWindow(win: gtk.Window) -> None:
	# win.set_keep_above(conf.winKeepAbove.v)
	win.set_keep_above(True)
	win.present()


def get_menu_width(menu: gtk.Menu) -> int:
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
	).
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
		return mw + conf.cellMenuXOffset.v
	return 0


def get_menu_height(menu: gtk.Menu) -> int:
	h = menu.get_allocation().height
	if h > 1:
		# log.debug("menu height from before:", h)
		return h
	items = menu.get_children()
	if not items:
		return 0
	# get_preferred_size() returns (minimum_size: Gtk.Requisition,
	# 		natural_size: Gtk.Requisition)
	return sum(item.get_preferred_size()[1].height for item in items)
	# FIXME: does not work, all items are zero
	# log.debug("menu height from sum:", h)
	# log.debug([item.get_preferred_size()[1].height for item in items])


def get_pixbuf_hash(pbuf: GdkPixbuf.Pixbuf) -> str:
	import hashlib

	md5 = hashlib.md5()

	def save_func(chunkBytes: bytes, _size: int, _unknown: Any) -> bool:
		# len(chunkBytes) == size
		md5.update(chunkBytes)
		return True

	# stub has many bugs
	pbuf.save_to_callbackv(
		save_func,  # type: ignore[arg-type]
		None,  # type: ignore[arg-type] # user_data
		"png",  # type, name of file format
		[],  # option_keys
		[],  # option_values
	)
	return md5.hexdigest()


def window_set_size_aspect(
	win: gtk.Window,
	min_aspect: float,
	max_aspect: float | None = None,
) -> None:
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


def newHSep() -> gtk.Separator:
	return gtk.Separator(orientation=gtk.Orientation.HORIZONTAL)


def newAlignLabel(sgroup: gtk.SizeGroup | None = None, label: str = "") -> gtk.Label:
	glabel = gtk.Label(label=label)
	glabel.set_xalign(0)
	if sgroup:
		sgroup.add_widget(glabel)
	return glabel


# class TextComboBox(gtk.ComboBox):
# 	def setActive(self, ident: int | None) -> None:


class IdComboBox(gtk.ComboBox):
	def setActive(self, ident: int | None) -> None:
		if ident is None:
			gtk.ComboBox.set_active(self, -1)
			return
		ls = self.get_model()
		for i in range(len(ls)):
			if ls[i][0] == ident:
				gtk.ComboBox.set_active(self, i)
				return

	def getActive(self) -> int | None:
		i = gtk.ComboBox.get_active(self)
		if i == -1 or i is None:
			return None
		model = self.get_model()
		if model is None:
			log.info("IdComboBox.get_active: model is None")
		try:
			return model[i][0]  # type: ignore[no-any-return]
		except IndexError:
			return None


class CopyLabelMenuItem(MenuItem):
	def __init__(self, label: str) -> None:
		MenuItem.__init__(self)
		self.set_label(label)
		self.connect("activate", self.on_activate)

	def on_activate(self, _item: gtk.MenuItem) -> None:
		setClipboard(self.get_property("label"))


def cssTextStyle(
	font: Font | None = None,
	fgColor: ColorType | None = None,
	bgColor: ColorType | None = None,
	extra: dict[str, str] | None = None,
) -> str:
	lines = []
	if font:
		lines += [
			f"\tfont-family: {font.family};",
			f"\tfont-size: {font.size}pt;",
			f"\tfont-weight: {'bold' if font.bold else 'normal'};",
			f"\tfont-style: {'italic' if font.italic else 'normal'};",
		]
	if fgColor:
		lines.append(f"\tcolor: {rgbToCSS(fgColor)};")
	if bgColor:
		lines.append(f"\tbackground-color: {rgbToCSS(bgColor)};")

	if extra:
		for key, value in extra.items():
			lines.append(f"\t{key}: {value};")

	return "{\n" + "\n".join(lines) + "\n}"


def getBackgroundColor(widget: gtk.Widget) -> ColorType:
	return gdkColorToRgb(
		widget.get_style_context().get_background_color(gtk.StateFlags.NORMAL),
	)


def getBackgroundColorCSS(widget: gtk.Widget) -> str:
	from scal3.color_utils import rgbToCSS

	return rgbToCSS(getBackgroundColor(widget))


def getGtkWindow(widget: gtk.Widget) -> gtk.Window | None:
	top = widget.get_toplevel()
	if isinstance(top, gtk.Window):
		return top
	return None


def x_large(text: str) -> str:
	return "<span size='x-large'>" + text + "</span>"


def trimMenuItemLabel(s: str, maxLen: int) -> str:
	if len(s) > maxLen - 3:
		s = s[: maxLen - 3].rstrip(" ") + "..."
	return s
