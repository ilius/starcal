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
from scal3.ui import conf

log = logger.get()

from collections.abc import Callable
from typing import TYPE_CHECKING

from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.icon_mapping import iconNameByImageName
from scal3.ui_gtk.utils import (
	imageFromFile,
	imageFromIconName,
	pixbufFromFile,
)

if TYPE_CHECKING:
	from gi.repository import GdkPixbuf

__all__ = ["CheckMenuItem", "ImageMenuItem", "ItemCallback", "ResizeMenuItem"]

"""
Documentation says:
	Gtk.ImageMenuItem has been deprecated since GTK+ 3.10. If you want to
	display an icon in a menu item, you should use Gtk.MenuItem and pack a
	Gtk.Box with a Gtk.Image and a Gtk.Label instead. You should also consider
	using Gtk.Builder and the XML Gio.Menu description for creating menus, by
	following the ‘GMenu guide [https://developer.gnome.org/GMenu/]’.
	You should consider using icons in menu items only sparingly, and for
	“objects” (or “nouns”) elements only, like bookmarks, files, and links;
	“actions” (or “verbs”) should not have icons.
"""

type ItemCallback = Callable[[gtk.Widget], None]

type ButtonPressCallable = Callable[[gtk.Widget, gdk.EventButton], bool]


class ImageMenuItem(gtk.MenuItem):
	def __init__(
		self,
		label: str = "",
		onActivate: ItemCallback | None = None,  # "activate" signal callback
		imageName: str | None = None,
		pixbuf: GdkPixbuf.Pixbuf | None = None,
		onButtonPress: ButtonPressCallable | None = None,
	) -> None:
		gtk.MenuItem.__init__(self)
		image = None
		if imageName:
			iconName = ""
			try:
				if conf.useSystemIcons.v:
					iconName = iconNameByImageName.get(imageName, "")
				if iconName:
					image = imageFromIconName(iconName, gtk.IconSize.MENU)
				else:
					image = imageFromFile(
						imageName,
						size=conf.menuIconSize.v,
					)
			except Exception:
				log.exception("")
		elif pixbuf:
			image = gtk.Image.new_from_pixbuf(pixbuf)

		if image is None:
			# just an empty image, to occupy the space
			image = gtk.Image()
			image.set_pixel_size(conf.menuIconSize.v)

		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
		pack(hbox, image, padding=conf.menuIconEdgePadding.v)
		labelWidget = gtk.Label(label=label)
		labelWidget.set_xalign(0)
		labelWidget.set_use_underline(True)
		pack(
			hbox,
			labelWidget,
			expand=True,
			fill=True,
			padding=conf.menuIconPadding.v,
		)
		self.add(hbox)
		self._image = image
		if onActivate:
			self.connect("activate", onActivate)
		if onButtonPress:
			self.connect("button-press-event", onButtonPress)

	def get_image(self) -> gtk.Image:
		return self._image


class ResizeMenuItem(ImageMenuItem):
	def __init__(
		self,
		label: str = "",
		onButtonPress: ButtonPressCallable | None = None,
	) -> None:
		super().__init__(
			label=label,
			imageName="resize.svg",
			onButtonPress=onButtonPress,
		)


class CheckMenuItem(gtk.MenuItem):
	def __init__(
		self,
		label: str = "",
		onActivate: ItemCallback | None = None,
		active: bool = False,
	) -> None:
		gtk.MenuItem.__init__(self)
		self._check = gtk.CheckButton(label=" " + label)
		self._check.set_use_underline(True)
		# self._check.set_border_width(
		# (conf.menuCheckSize.v - conf.menuIconSize.v) // 2)
		self._box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
		edgePadding = 0
		# edgePadding = conf.menuIconEdgePadding.v
		#   - conf.menuCheckSize.v + conf.menuIconSize.v
		# log.debug(f"CheckMenuItem: {edgePadding=}")
		# edgePadding += 2  # FIXME: why is this needed?
		# edgePadding = max(0, edgePadding)
		pack(self._box, self._check, padding=edgePadding)
		self._box.show_all()
		self.add(self._box)
		# ---
		self.set_active(active)
		# ---
		self._func = onActivate
		self.connect("activate", self._onActivate)

	def _onActivate(self, menuItem: gtk.MenuItem) -> None:
		assert self._func is not None
		self.set_active(not self._active)
		self._func(menuItem)

	def set_active(self, active: bool) -> None:
		self._active = active
		self._check.set_active(active)

	def get_active(self) -> bool:
		return self._active


class CustomCheckMenuItem(gtk.MenuItem):
	def __init__(
		self,
		label: str = "",
		onActivate: ItemCallback | None = None,
		active: bool = False,
	) -> None:
		gtk.MenuItem.__init__(self)
		self._image = gtk.Image()
		self._box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
		edgePadding = int(
			conf.menuIconEdgePadding.v - conf.menuCheckSize.v + conf.menuIconSize.v,
		)
		# log.debug(f"CheckMenuItem: {edgePadding=}")
		edgePadding += 2  # FIXME: why is this needed?
		edgePadding = max(0, edgePadding)
		pack(self._box, self._image, padding=edgePadding)
		labelWidget = gtk.Label(label=label)
		labelWidget.set_xalign(0)
		labelWidget.set_use_underline(True)
		pack(
			self._box,
			labelWidget,
			expand=True,
			fill=True,
			padding=conf.menuIconPadding.v,
		)
		self._box.show_all()
		self.add(self._box)
		# ---
		self.set_active(active)
		# ---
		self._func = onActivate
		self.connect("activate", self._onActivate)

	def _onActivate(self, menuItem: gtk.MenuItem) -> None:
		assert self._func is not None
		self.set_active(not self._active)
		self._func(menuItem)

	def set_active(self, active: bool) -> None:
		self._active = active
		imageName = "check-true.svg" if active else "check-false.svg"
		self._image.set_from_pixbuf(
			pixbufFromFile(
				imageName,
				conf.menuCheckSize.v,
			),
		)

	def get_active(self) -> bool:
		return self._active
