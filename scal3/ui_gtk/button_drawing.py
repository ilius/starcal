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

from os.path import join
from typing import TYPE_CHECKING, Never

from scal3.drawing import getAbsPos
from scal3.path import pixDir, svgDir
from scal3.ui_gtk import GdkPixbuf, gdk, gtk
from scal3.ui_gtk.drawing import drawOutlineRoundedRect
from scal3.ui_gtk.utils import pixbufFromFile

if TYPE_CHECKING:
	import cairo

__all__ = ["Button", "SVGButton"]


class BaseButton:
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
	) -> None:
		if x is None:
			raise ValueError("x is not given")
		if y is None:
			raise ValueError("y is not given")

		if x < 0 and xalign != "center":
			raise ValueError(f"invalid {x=}, {xalign=}")
		if y < 0 and yalign != "center":
			raise ValueError(f"invalid {y=}, {yalign=}")
		if xalign not in {"left", "right", "center"}:
			raise ValueError(f"invalid {xalign=}")
		if yalign not in {"top", "buttom", "center"}:
			raise ValueError(f"invalid {yalign=}")

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

	def setSize(self, width, height) -> None:
		self.width = width
		self.height = height

	def getAbsPos(self, w, h):
		return getAbsPos(
			self.width,
			self.height,
			w,
			h,
			self.x,
			self.y,
			self.xalign,
			self.yalign,
			autoDir=self.autoDir,
		)

	def contains(self, px, py, w, h):
		x, y = self.getAbsPos(w, h)
		return x <= px < x + self.width and y <= py < y + self.height

	def draw(self, cr, w, h) -> Never:
		raise NotImplementedError


class SVGButton(BaseButton):
	def __init__(
		self,
		imageName="",
		iconSize=16,
		rectangleColor=None,
		**kwargs,
	) -> None:
		BaseButton.__init__(self, **kwargs)

		if not imageName:
			raise ValueError("imageName is given")
		self.imageName = imageName
		pixbuf = pixbufFromFile(imageName, iconSize)
		if pixbuf is None:
			raise RuntimeError(f"could not get pixbuf for {imageName=}")

		# we assume that svg image is square
		self.setSize(iconSize, iconSize)

		self.iconSize = iconSize
		self.pixbuf = pixbuf

		self.rectangleColor = rectangleColor

	def getImagePath(self) -> None:
		from os.path import isabs

		path = self.imageName
		if not isabs(path):
			path = join(svgDir, path)
		return path

	def draw(
		self,
		cr: cairo.Context,
		w: float,
		h: float,
	) -> None:
		x, y = self.getAbsPos(w, h)

		if self.rectangleColor:
			color = self.rectangleColor
			size = self.iconSize
			red, green, blue = color[:3]
			if len(color) > 3:
				opacity = color[3]
			else:
				opacity = self.opacity
			lineWidth = 1
			cr.set_source_rgba(
				red / 255.0,
				green / 255.0,
				blue / 255.0,
				opacity,
			)
			drawOutlineRoundedRect(
				cr,
				x - lineWidth,
				y - lineWidth,
				size + 2 * lineWidth,
				size + 2 * lineWidth,
				size * 0.2,
				lineWidth,
			)
			cr.fill()

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
		gdk.cairo_set_source_pixbuf(
			cr,
			self.pixbuf,
			x,
			y,
		)
		cr.paint_with_alpha(self.opacity)

	def __repr__(self) -> str:
		return (
			f"SVGButton({self.imageName!r}, {self.onPress.__name__!r}, "
			f"{self.x!r}, {self.y!r}, {self.autoDir!r})"
		)


class Button(BaseButton):
	def __init__(
		self,
		imageName="",
		iconName="",
		iconSize=0,
		**kwargs,
	) -> None:
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

	def draw(self, cr, w, h) -> None:
		x, y = self.getAbsPos(w, h)
		gdk.cairo_set_source_pixbuf(
			cr,
			self.pixbuf,
			x,
			y,
		)
		cr.paint_with_alpha(self.opacity)

	def __repr__(self) -> str:
		return (
			f"Button({self.imageName!r}, {self.onPress.__name__!r}, "
			f"{self.x!r}, {self.y!r}, {self.autoDir!r})"
		)
