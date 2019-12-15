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

from typing import Optional, Tuple, Union, Callable

from gi.repository import GdkPixbuf

from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk import pixcache
from scal3.ui_gtk.icon_mapping import iconNameByImageName
from scal3.ui_gtk.utils import (
	pixbufFromFile,
	imageFromFile,
	imageFromIconName,
)


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



class ImageMenuItem(gtk.MenuItem):
	def __init__(
		self,
		label: str = "",
		imageName: str = "",
		pixbuf: Optional[GdkPixbuf.Pixbuf] = None,
		func: Optional[Callable] = None,
		args: Optional[Tuple] = None,
	):
		gtk.MenuItem.__init__(self)
		if args is not None and not isinstance(args, tuple):
			raise TypeError("args must be None or tuple")
		image = None
		if imageName:
			iconName = ""
			if ui.useSystemIcons:
				iconName = iconNameByImageName.get(imageName, "")
			if iconName:
				image = imageFromIconName(iconName, gtk.IconSize.MENU)
			else:
				image = imageFromFile(
					imageName,
					size=ui.menuIconSize,
				)
		elif pixbuf:
			image = gtk.Image.new_from_pixbuf(pixbuf)

		if image is None:
			# just an empty image, to occupy the space
			image = gtk.Image()
			image.set_pixel_size(ui.menuIconSize)

		hbox = HBox(spacing=0)
		pack(hbox, image, padding=ui.menuIconEdgePadding)
		labelWidget = gtk.Label(label=label)
		labelWidget.set_xalign(0)
		labelWidget.set_use_underline(True)
		pack(
			hbox,
			labelWidget,
			expand=True,
			fill=True,
			padding=ui.menuIconPadding,
		)
		self.add(hbox)
		self._image = image
		if func:
			if args is None:
				args = ()
			self.connect("activate", func, *args)

	def get_image(self):
		return self._image


class CheckMenuItem(gtk.MenuItem):
	def __init__(
		self,
		label="",
		active=False,
		func=None,
		args=None,
	):
		gtk.MenuItem.__init__(self)
		self._image = gtk.Image()
		self._box = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=0)
		edgePadding = ui.menuIconEdgePadding - ui.menuCheckSize + ui.menuIconSize
		# print(f"CheckMenuItem: edgePadding={edgePadding}")
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
			padding=ui.menuIconPadding,
		)
		self._box.show_all()
		self.add(self._box)
		###
		self.set_active(active)
		###
		self._func = func
		if args is None:
			args = ()
		self._args = args
		self.connect("activate", self._onActivate)

	def _onActivate(self, menuItem):
		self.set_active(not self._active)
		self._func(menuItem, *self._args)

	def set_active(self, active: bool) -> None:
		self._active = active
		imageName = "check-true.svg" if active else "check-false.svg"
		self._image.set_from_pixbuf(pixbufFromFile(
			imageName,
			ui.menuCheckSize,
		))

	def get_active(self) -> bool:
		return self._active

	def get_image(self):
		return self._image


