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

import re
from math import cos, pi, sin
from os.path import join
from typing import TYPE_CHECKING

from scal3 import ui
from scal3.color_utils import RGB, RGBA, ColorType, RawColor, rgbToHtmlColor
from scal3.font import Font
from scal3.locale_man import cutText
from scal3.path import sourceDir
from scal3.ui_gtk import GdkPixbuf, gtk
from scal3.ui_gtk.font_utils import pfontEncode
from scal3.utils import toBytes

if TYPE_CHECKING:
	import cairo
	from gi.repository import Pango as pango


__all__ = [
	"ImageContext",
	"calcTextPixelSize",
	"calcTextPixelWidth",
	"drawArcOutline",
	"drawCircle",
	"drawCircleOutline",
	"drawLineLengthAngle",
	"drawOutlineRoundedRect",
	"drawPieOutline",
	"drawRoundedRect",
	"fillColor",
	"goAngle",
	"newColorCheckPixbuf",
	"newDndDatePixbuf",
	"newDndFontNamePixbuf",
	"newTextLayout",
	"setColor",
]

type ImageContext = cairo.Context[cairo.ImageSurface]
type BothContext = cairo.Context[cairo.ImageSurface] | cairo.Context[cairo.SVGSurface]


with open(join(sourceDir, "svg", "special", "color-check.svg"), encoding="utf-8") as fp:
	colorCheckSvgTextChecked = fp.read()
colorCheckSvgTextUnchecked = re.sub(
	r'<path[^<>]*?id="check"[^<>]*?/>',
	"",
	colorCheckSvgTextChecked,
	flags=re.MULTILINE | re.DOTALL,
)


def setColor(cr: BothContext, color: RGB | RGBA | RawColor) -> None:
	# arguments to set_source_rgb and set_source_rgba must be between 0 and 1
	if len(color) == 3:
		cr.set_source_rgb(
			color[0] / 255.0,
			color[1] / 255.0,
			color[2] / 255.0,
		)
	elif len(color) == 4:
		cr.set_source_rgba(
			color[0] / 255.0,
			color[1] / 255.0,
			color[2] / 255.0,
			color[3] / 255.0,
		)
	else:
		raise ValueError(f"bad color {color}")


def fillColor(cr: BothContext, color: ColorType) -> None:
	setColor(cr, color)
	cr.fill()


def newTextLayout(
	widget: gtk.Widget,
	text: str = "",
	font: Font | None = None,
	maxSize: tuple[float, float] | None = None,
	maximizeScale: float = 0.6,
	truncate: bool = False,
) -> pango.Layout | None:
	"""None return value should be expected and handled, only if maxSize is given."""
	layout = widget.create_pango_layout("")  # a Pango.Layout object
	if font:
		assert isinstance(font, Font)
		assert isinstance(font.family, str), font
		# should we copy the font? font = font.copy()
	else:
		font = ui.getFont()
	layout.set_font_description(pfontEncode(font))
	if not text:
		return layout
	layout.set_markup(text=text, length=-1)  # type: ignore[no-untyped-call]
	if maxSize is None:
		return layout
	layoutW, layoutH = layout.get_pixel_size()
	# --
	maxW, maxH = maxSize
	if maxW <= 0:
		return None
	if maxH <= 0:
		minRat = 1.0
	else:
		minRat = 1.01 * layoutH / maxH  # FIXME
	if not truncate:
		if maximizeScale > 0:
			minRat /= maximizeScale
		minRat = max(minRat, layoutW / maxW)
		if minRat > 1:
			font.size /= minRat
		layout.set_font_description(pfontEncode(font))
		return layout

	if minRat > 1:
		font.size /= minRat
	layout.set_font_description(pfontEncode(font))
	layoutW, layoutH = layout.get_pixel_size()
	if layoutW > 0:
		char_w = layoutW / len(text)
		char_num = int(maxW // char_w)
		while layoutW > maxW:
			text = cutText(text, char_num)
			if not text:
				break
			layout = widget.create_pango_layout(text)
			layout.set_font_description(pfontEncode(font))
			layoutW, layoutH = layout.get_pixel_size()
			char_num -= max(
				int((layoutW - maxW) // char_w),
				1,
			)
			if char_num < 0:
				log.error(f"newTextLayout: {char_num=}, {text=}, {maxSize=}")
				return None
	return layout


"""
def newLimitedWidthTextLayout(
	widget,
	text,
	width,
	font=None,
	truncate=True,
	markup=True,
):
	if not font:
		font = ui.getFont()
	layout = widget.create_pango_layout("")
	if markup:
		layout.set_markup(text=text, length=-1)
	else:
		layout.set_text(text=text, length=-1)
	layout.set_font_description(pfontEncode(font))
	if not layout:
		return None
	layoutW, layoutH = layout.get_pixel_size()
	if layoutW > width:
		if truncate:
			char_w = layoutW/len(text)
			char_num = int(width//char_w)
			while layoutW > width:
				text = cutText(text, char_num)
				layout = widget.create_pango_layout(text)
				layout.set_font_description(pfontEncode(font))
				layoutW, layoutH = layout.get_pixel_size()
				char_num -= max(int((layoutW-width)//char_w), 1)
				if char_num<0:
					layout = None
					break
		else:-- use smaller font
			font2 = list(font)
			while layoutW > width:
				font2[3] = 0.9*font2[3]*width/layoutW
				layout.set_font_description(pfontEncode(font2))
				layoutW, layoutH = layout.get_pixel_size()
				# log.debug(layoutW, width)
			#print
	return layout
"""


def calcTextPixelSize(
	widget: gtk.Widget,
	text: str,
	font: Font | None = None,
) -> tuple[float, float]:
	layout = widget.create_pango_layout(text)  # a Pango.Layout object
	if font is not None:
		layout.set_font_description(pfontEncode(font))
	width, height = layout.get_pixel_size()
	return width, height


def calcTextPixelWidth(
	widget: gtk.Widget,
	text: str,
	font: Font | None = None,
) -> float:
	width, _height = calcTextPixelSize(widget, text, font=font)
	return width


def newColorCheckPixbuf(
	color: RGB,
	size: int,
	checked: bool,
) -> GdkPixbuf.Pixbuf:
	if checked:
		data = colorCheckSvgTextChecked
	else:
		data = colorCheckSvgTextUnchecked
	data = data.replace(
		"fill:#000000;",
		f"fill:{rgbToHtmlColor(color)};",
	)
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	loader.set_size(size, size)
	try:
		loader.write(toBytes(data))
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	assert pixbuf is not None
	return pixbuf


def newDndDatePixbuf(ymd: tuple[int, int, int]) -> GdkPixbuf.Pixbuf:
	imagePath = join(sourceDir, "svg", "special", "dnd-date.svg")
	with open(imagePath, encoding="utf-8") as fp:
		data = fp.read()
	data = data.replace("YYYY", f"{ymd[0]:04d}")
	data = data.replace("MM", f"{ymd[1]:02d}")
	data = data.replace("DD", f"{ymd[2]:02d}")
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	try:
		loader.write(toBytes(data))
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	assert pixbuf is not None
	return pixbuf


def newDndFontNamePixbuf(name: str) -> GdkPixbuf.Pixbuf:
	imagePath = join(sourceDir, "svg", "special", "dnd-font.svg")
	with open(imagePath, encoding="utf-8") as fp:
		data = fp.read()
	data = data.replace("FONTNAME", name)
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	try:
		loader.write(toBytes(data))
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	assert pixbuf is not None
	return pixbuf


def drawRoundedRect(
	cr: ImageContext,
	cx0: float,
	cy0: float,
	cw: float,
	ch: float,
	ro: float,
) -> None:
	ro = min(ro, cw / 2.0, ch / 2.0)
	cr.move_to(
		cx0 + ro,
		cy0,
	)
	# up side:
	cr.line_to(
		cx0 + cw - ro,
		cy0,
	)
	# up right corner:
	cr.arc(
		cx0 + cw - ro,
		cy0 + ro,
		ro,
		3 * pi / 2,
		2 * pi,
	)
	# right side:
	cr.line_to(
		cx0 + cw,
		cy0 + ch - ro,
	)
	# down right corner:
	cr.arc(
		cx0 + cw - ro,
		cy0 + ch - ro,
		ro,
		0,
		pi / 2,
	)
	# down side:
	cr.line_to(
		cx0 + ro,
		cy0 + ch,
	)
	# down left corner:
	cr.arc(
		cx0 + ro,
		cy0 + ch - ro,
		ro,
		pi / 2,
		pi,
	)
	# left side:
	cr.line_to(
		cx0,
		cy0 + ro,
	)
	# up left corner:
	cr.arc(
		cx0 + ro,
		cy0 + ro,
		ro,
		pi,
		3 * pi / 2,
	)
	# done
	cr.close_path()


def drawOutlineRoundedRect(
	cr: ImageContext,
	cx0: float,
	cy0: float,
	cw: float,
	ch: float,
	ro: float,
	d: float,
) -> None:
	ro = min(ro, cw / 2.0, ch / 2.0)
	# a = min(cw, ch); ri = ro*(a-2*d)/a
	ri = max(0, ro - d)
	# log.debug(ro, ri)
	# ------- Outline:
	cr.move_to(
		cx0 + ro,
		cy0,
	)
	cr.line_to(
		cx0 + cw - ro,
		cy0,
	)
	# up right corner:
	cr.arc(
		cx0 + cw - ro,
		cy0 + ro,
		ro,
		3 * pi / 2,
		2 * pi,
	)
	cr.line_to(
		cx0 + cw,
		cy0 + ch - ro,
	)
	# down right corner:
	cr.arc(
		cx0 + cw - ro,
		cy0 + ch - ro,
		ro,
		0,
		pi / 2,
	)
	cr.line_to(
		cx0 + ro,
		cy0 + ch,
	)
	# down left corner:
	cr.arc(
		cx0 + ro,
		cy0 + ch - ro,
		ro,
		pi / 2,
		pi,
	)
	cr.line_to(
		cx0,
		cy0 + ro,
	)
	# up left corner:
	cr.arc(
		cx0 + ro,
		cy0 + ro,
		ro,
		pi,
		3 * pi / 2,
	)
	# Inline:
	if ri == 0:
		cr.move_to(
			cx0 + d,
			cy0 + d,
		)
		cr.line_to(
			cx0 + d,
			cy0 + ch - d,
		)
		cr.line_to(
			cx0 + cw - d,
			cy0 + ch - d,
		)
		cr.line_to(
			cx0 + cw - d,
			cy0 + d,
		)
		cr.line_to(
			cx0 + d,
			cy0 + d,
		)
	else:
		cr.move_to(  # or line_to
			cy0 + d,
			cx0 + ro,
		)
		# up left corner:
		cr.arc_negative(
			cx0 + ro,
			cy0 + ro,
			ri,
			3 * pi / 2,
			pi,
		)
		cr.line_to(
			cx0 + d,
			cy0 + ch - ro,
		)
		# down left:
		cr.arc_negative(
			cx0 + ro,
			cy0 + ch - ro,
			ri,
			pi,
			pi / 2,
		)
		cr.line_to(
			cx0 + cw - ro,
			cy0 + ch - d,
		)
		# down right:
		cr.arc_negative(
			cx0 + cw - ro,
			cy0 + ch - ro,
			ri,
			pi / 2,
			0,
		)
		cr.line_to(
			cx0 + cw - d,
			cy0 + ro,
		)
		# up right:
		cr.arc_negative(
			cx0 + cw - ro,
			cy0 + ro,
			ri,
			2 * pi,
			3 * pi / 2,
		)
		cr.line_to(
			cx0 + ro,
			cy0 + d,
		)
	cr.close_path()


def drawCircle(cr: ImageContext, cx: float, cy: float, radius: float) -> None:
	cr.arc(cx, cy, radius, 0, 2 * pi)


def drawCircleOutline(
	cr: ImageContext,
	cx: float,
	cy: float,
	r: float,
	d: float,
) -> None:
	cr.arc(cx, cy, r, 0, 2 * pi)
	cr.close_path()
	cr.arc_negative(cx, cy, r - d, 2 * pi, 0)
	cr.close_path()


def drawPieOutline(
	cr: ImageContext,
	cx: float,
	cy: float,
	r: float,
	d: float,
	start: float,
	end: float,
) -> None:
	# start and end are angles
	# 0 <= start <= 1
	# 0 <= end <= 1
	start_radian = 2 * pi * start
	end_radian = 2 * pi * end
	cr.move_to(cx, cy)
	cr.arc(
		cx,
		cy,
		r,
		start_radian,
		end_radian,
	)
	cr.arc_negative(
		cx,
		cy,
		r - d,
		end_radian,
		start_radian,
	)
	cr.close_path()


def goAngle(x0: float, y0: float, angle: float, length: float) -> tuple[float, float]:
	return x0 + cos(angle) * length, y0 + sin(angle) * length


def drawLineLengthAngle(
	cr: ImageContext,
	xs: float,
	ys: float,
	length: float,
	angle: float,
	d: float,
) -> None:
	xe, ye = goAngle(xs, ys, angle, length)
	# --
	x1, y1 = goAngle(xs, ys, angle - pi / 2.0, d / 2.0)
	x2, y2 = goAngle(xs, ys, angle + pi / 2.0, d / 2.0)
	x3, y3 = goAngle(xe, ye, angle + pi / 2.0, d / 2.0)
	x4, y4 = goAngle(xe, ye, angle - pi / 2.0, d / 2.0)
	# --
	cr.move_to(x1, y1)
	cr.line_to(x2, y2)
	cr.line_to(x3, y3)
	cr.line_to(x4, y4)
	cr.close_path()


def drawArcOutline(
	cr: ImageContext,
	xc: float,
	yc: float,
	r: float,
	d: float,
	a0: float,
	a1: float,
) -> None:
	"""
	cr: cairo context
	xc, yc: coordinates of center
	r: outer radius
	d: outline width (r - ri)
	a0: start angle (radians)
	a1: end angle (radians).
	"""
	x1, y1 = goAngle(xc, yc, a0, r - d)
	# x2, y2 = goAngle(xc, yc, a1, r - d)
	x3, y3 = goAngle(xc, yc, a1, r)
	# x4, y4 = goAngle(xc, yc, a0, r)
	# ----
	cr.move_to(x1, y1)
	cr.arc(xc, yc, r - d, a0, a1)
	# cr.move_to(x2, y2)
	cr.line_to(x3, y3)
	cr.arc_negative(xc, yc, r, a1, a0)
	# cr.move_to(x4, y4)
	# cr.line_to(x1, y1)

	cr.close_path()
