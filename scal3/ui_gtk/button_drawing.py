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


from scal3.ui_gtk import *
from scal3.ui_gtk.utils import pixbufFromFile


class BaseButton(object):
	def __init__(
		self,
		onPress=None,
		onRelease=None,
		x=None,
		y=None,
		xalign="left",
		yalign="top",
		autoDir=True,
		opacity=1.0,
	):
		if x is None:
			raise ValueError("x is not given")
		if y is None:
			raise ValueError("y is not given")

		if x < 0 and xalign != "center":
			raise ValueError(f"invalid x={x}, xalign={xalign}")
		if y < 0 and yalign != "center":
			raise ValueError(f"invalid y={y}, yalign={yalign}")
		if xalign not in ("left", "right", "center"):
			raise ValueError(f"invalid xalign={xalign}")
		if yalign not in ("top", "buttom", "center"):
			raise ValueError(f"invalid yalign={yalign}")

		self.onPress = onPress
		self.onRelease = onRelease
		self.x = x
		self.y = y
		self.xalign = xalign
		self.yalign = yalign
		self.autoDir = autoDir
		self.opacity = opacity

		self.width = None
		self.height = None

	def setSize(self, width, height):
		self.width = width
		self.height = height

	def opposite(self, align):
		if align == "left":
			return "right"
		if align == "right":
			return "left"
		if align == "top":
			return "buttom"
		if align == "buttom":
			return "top"
		return align

	def getAbsPos(self, w, h):
		x = self.x
		y = self.y
		xalign = self.xalign
		yalign = self.yalign
		if self.autoDir and rtl:
			xalign = self.opposite(xalign)
		if xalign == "right":
			x = w - self.width - x
		elif xalign == "center":
			x = (w - self.width) / 2.0 + x
		if yalign == "buttom":
			y = h - self.height - y
		elif yalign == "center":
			y = (h - self.height) / 2.0 + y
		return (x, y)

	def contains(self, px, py, w, h):
		x, y = self.getAbsPos(w, h)
		return (
			x <= px < x + self.width
			and
			y <= py < y + self.height
		)

	def draw(self, cr, w, h, bgColor=None):
		raise NotImplementedError


class SVGButton(BaseButton):
	def __init__(
		self,
		imageName="",
		iconSize=16,
		**kwargs
	):
		BaseButton.__init__(self, **kwargs)

		if not imageName:
			raise ValueError("imageName is given")
		self.imageName = imageName
		pixbuf = pixbufFromFile(imageName, iconSize)
		if pixbuf is None:
			raise RuntimeError(f"could not get pixbuf for imageName={imageName!r}")

		# we assume that svg image is square
		self.setSize(iconSize, iconSize)

		self.iconSize = iconSize
		self.pixbuf = pixbuf

	def getImagePath(self) -> None:
		from os.path import isabs
		path = self.imageName
		if not isabs(path):
			path = join(svgDir, path)
		return path

	def draw(
		self,
		cr: "cairo.Context",
		w: float,
		h: float,
		bgColor=None,
	):
		# from gi.repository import Rsvg as rsvg
		# handle = rsvg.Handle.new_from_file(self.getImagePath())
		# dim = handle.get_dimensions()
		# cr.save()
		# try:
		# 	cr.translate(*self.getAbsPos(w, h))
		# 	cr.scale(self.width / dim.width, self.height / dim.height)
		# 	handle.render_cairo(cr)
		# finally:
		# 	cr.restore()
		# 	handle.close()
		x, y = self.getAbsPos(w, h)
		gdk.cairo_set_source_pixbuf(
			cr,
			self.pixbuf,
			x,
			y,
		)
		cr.paint_with_alpha(self.opacity)

	def __repr__(self):
		return (
			f"SVGButton({self.imageName!r}, {self.onPress.__name__!r}, " +
			f"{self.x!r}, {self.y!r}, {self.autoDir!r})"
		)


class Button(BaseButton):
	def __init__(
		self,
		imageName="",
		iconName="",
		iconSize=0,
		**kwargs
	):
		BaseButton.__init__(self, **kwargs)

		shouldResize = True

		if iconName:
			self.imageName = iconName
			if iconSize == 0:
				iconSize = 16
			# GdkPixbuf.Pixbuf.new_from_stock is removed
			# gtk.Widget.render_icon_pixbuf: Deprecated since version 3.10:
			# 		Use Gtk.IconTheme.load_icon()
			pixbuf = gtk.IconTheme.get_default().load_icon(
				iconName,
				iconSize,
				0,  # Gtk.IconLookupFlags
			)
		else:
			if not imageName:
				raise ValueError("no imageName nor iconName were given")
			self.imageName = imageName
			if imageName.endswith(".svg"):
				if iconSize == 0:
					iconSize = 16
				shouldResize = False
				pixbuf = pixbufFromFile(imageName, iconSize)
			else:
				pixbuf = GdkPixbuf.Pixbuf.new_from_file(join(pixDir, imageName))

		if shouldResize and iconSize != 0:  # need to resize
			pixbuf = pixbuf.scale_simple(
				iconSize,
				iconSize,
				GdkPixbuf.InterpType.BILINEAR,
			)

		# the actual/final width and height of pixbuf/button
		width, height = pixbuf.get_width(), pixbuf.get_height()
		# width, height = iconSize, iconSize
		self.setSize(width, height)

		self.iconSize = iconSize
		self.pixbuf = pixbuf

	def draw(self, cr, w, h, bgColor=None):
		x, y = self.getAbsPos(w, h)
		gdk.cairo_set_source_pixbuf(
			cr,
			self.pixbuf,
			x,
			y,
		)
		cr.paint_with_alpha(self.opacity)

	def __repr__(self):
		return (
			f"Button({self.imageName!r}, {self.onPress.__name__!r}, " +
			f"{self.x!r}, {self.y!r}, {self.autoDir!r})"
		)
