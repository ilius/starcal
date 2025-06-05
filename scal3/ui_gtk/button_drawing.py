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
from typing import TYPE_CHECKING

from scal3.drawing import getAbsPos
from scal3.path import svgDir
from scal3.ui_gtk import GdkPixbuf, gdk
from scal3.ui_gtk.drawing import drawOutlineRoundedRect
from scal3.ui_gtk.utils import pixbufFromFile, pixbufFromFileMust, pixbufFromIconName

if TYPE_CHECKING:
	from collections.abc import Callable

	import cairo

	from scal3.color_utils import ColorType

__all__ = ["BaseButton", "Button", "SVGButton"]


class BaseButton:
	def __init__(
		self,
		onPress: Callable,
		onRelease: Callable | None = None,
		x: float | None = None,
		y: float | None = None,
		xalign: str = "left",
		yalign: str = "top",
		autoDir: bool = True,
		opacity: float = 1.0,
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

		self.width = 0.0
		self.height = 0.0

	def setSize(self, width: float, height: float) -> None:
		self.width = width
		self.height = height

	def getAbsPos(self, w: float, h: float) -> tuple[float, float]:
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

	def contains(self, px: float, py: float, w: float, h: float) -> bool:
		x, y = self.getAbsPos(w, h)
		return x <= px < x + self.width and y <= py < y + self.height

	def draw(self, cr: cairo.Context, w: float, h: float) -> None:
		raise NotImplementedError


class SVGButton(BaseButton):
	def __init__(
		self,
		onPress: Callable,
		imageName: str = "",
		iconSize: int = 16,
		rectangleColor: ColorType | None = None,
		**kwargs,
	) -> None:
		BaseButton.__init__(self, onPress=onPress, **kwargs)

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

	def getImagePath(self) -> str:
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
				opacity = color[3] / 255.0
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
		onPress: Callable,
		imageName: str = "",
		iconName: str = "",
		iconSize: int = 0,
		**kwargs,
	) -> None:
		BaseButton.__init__(self, onPress=onPress, **kwargs)

		pixbuf: GdkPixbuf.Pixbuf
		if iconName:
			self.imageName = iconName
			pixbuf = pixbufFromIconName(iconName, iconSize or 16)
		else:
			if not imageName:
				raise ValueError("no imageName nor iconName were given")
			self.imageName = imageName
			pixbuf = pixbufFromFileMust(imageName, iconSize or 16)

		# the actual/final width and height of pixbuf/button
		width, height = pixbuf.get_width(), pixbuf.get_height()
		# width, height = iconSize, iconSize
		self.setSize(width, height)

		self.iconSize = iconSize
		self.pixbuf = pixbuf

	def draw(self, cr: cairo.Context, w: float, h: float) -> None:
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
