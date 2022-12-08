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

from os.path import join
from math import pi
from math import sin, cos
import re

from typing import Optional, Tuple

from scal3.path import *
from scal3.utils import toBytes
from scal3 import core
from scal3.locale_man import cutText, rtl
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import *
from scal3.ui_gtk.color_utils import *

from gi.repository.PangoCairo import show_layout

if not ui.fontCustom:
	ui.fontCustom = ui.fontDefault.copy()

with open(join(sourceDir, "svg", "special", "color-check.svg")) as fp:  # noqa: FURB101
	colorCheckSvgTextChecked = fp.read()
colorCheckSvgTextUnchecked = re.sub(
	"<path[^<>]*?id=\"check\"[^<>]*?/>",
	"",
	colorCheckSvgTextChecked,
	flags=re.M | re.S,
)


def setColor(cr, color):
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


def fillColor(cr, color):
	setColor(cr, color)
	cr.fill()


def newTextLayout(
	widget,
	text="",
	font=None,
	maxSize=None,
	maximizeScale=0.6,
	truncate=False,
):
	"""
	None return value should be expected and handled, only if maxSize is given
	"""
	layout = widget.create_pango_layout("")  # a Pango.Layout object
	if font:
		assert isinstance(font, ui.Font)
		# should we copy the font? font = font.copy()
	else:
		font = ui.getFont()
	layout.set_font_description(pfontEncode(font))
	if text:
		layout.set_markup(text=text, length=-1)
		if maxSize:
			layoutW, layoutH = layout.get_pixel_size()
			##
			maxW, maxH = maxSize
			maxW = float(maxW)
			maxH = float(maxH)
			if maxW <= 0:
				return
			if maxH <= 0:
				minRat = 1.0
			else:
				minRat = 1.01 * layoutH / maxH  # FIXME
			if truncate:
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
							layout = None
							break
			else:
				if maximizeScale > 0:
					minRat = minRat / maximizeScale
				if minRat < layoutW / maxW:
					minRat = layoutW / maxW
				if minRat > 1:
					font.size /= minRat
				layout.set_font_description(pfontEncode(font))
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
		else:## use smaller font
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
	font: "Optional[Font]" = None,
) -> Tuple[float, float]:
	layout = widget.create_pango_layout(text)  # a Pango.Layout object
	if font is not None:
		layout.set_font_description(pfontEncode(font))
	width, height = layout.get_pixel_size()
	return width, height


def calcTextPixelWidth(
	widget: gtk.Widget,
	text: str,
	font: "Optional[Font]" = None,
) -> float:
	width, height = calcTextPixelSize(widget, text, font=font)
	return width


def newColorCheckPixbuf(color, size, checked):
	if checked:
		data = colorCheckSvgTextChecked
	else:
		data = colorCheckSvgTextUnchecked
	data = data.replace(
		f"fill:#000000;",
		f"fill:{rgbToHtmlColor(color[:3])};",
	)
	data = toBytes(data)
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	loader.set_size(size, size)
	try:
		loader.write(data)
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	return pixbuf


def newDndDatePixbuf(ymd):
	imagePath = join(sourceDir, "svg", "special", "dnd-date.svg")
	with open(imagePath) as fp:  # noqa: FURB101
		data = fp.read()
	data = data.replace("YYYY", f"{ymd[0]:04d}")
	data = data.replace("MM", f"{ymd[1]:02d}")
	data = data.replace("DD", f"{ymd[2]:02d}")
	data = toBytes(data)
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	try:
		loader.write(data)
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	return pixbuf


def newDndFontNamePixbuf(name):
	imagePath = join(sourceDir, "svg", "special", "dnd-font.svg")
	with open(imagePath) as fp:  # noqa: FURB101
		data = fp.read()
	data = data.replace("FONTNAME", name)
	data = toBytes(data)
	loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
	try:
		loader.write(data)
	finally:
		loader.close()
	pixbuf = loader.get_pixbuf()
	return pixbuf


def drawRoundedRect(cr, cx0, cy0, cw, ch, ro):
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
		cy0 + ro, ro,
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


def drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, ro, d):
	ro = min(ro, cw / 2.0, ch / 2.0)
	# a = min(cw, ch); ri = ro*(a-2*d)/a
	ri = max(0, ro - d)
	# log.debug(ro, ri)
	# ####### Outline:
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
	# ## Inline:
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


def drawCircle(cr, cx, cy, r):
	cr.arc(cx, cy, r, 0, 2 * pi)


def drawCircleOutline(cr, cx, cy, r, d):
	cr.arc(cx, cy, r, 0, 2 * pi)
	cr.close_path()
	cr.arc_negative(cx, cy, r - d, 2 * pi, 0)
	cr.close_path()

def drawPieOutline(cr, cx, cy, r, d, start, end):
	# start and end are angles
	# 0 <= start <= 1
	# 0 <= end <= 1
	start_radian = 2 * pi * start
	end_radian = 2 * pi * end
	cr.move_to(cx, cy)
	cr.arc(
		cx, cy,
		r,
		start_radian,
		end_radian,
	)
	cr.arc_negative(
		cx, cy,
		r - d,
		end_radian,
		start_radian,
	)
	cr.close_path()


def goAngle(x0, y0, angle, length):
	return x0 + cos(angle) * length, y0 + sin(angle) * length


def drawLineLengthAngle(cr, xs, ys, length, angle, d):
	xe, ye = goAngle(xs, ys, angle, length)
	##
	x1, y1 = goAngle(xs, ys, angle - pi / 2.0, d / 2.0)
	x2, y2 = goAngle(xs, ys, angle + pi / 2.0, d / 2.0)
	x3, y3 = goAngle(xe, ye, angle + pi / 2.0, d / 2.0)
	x4, y4 = goAngle(xe, ye, angle - pi / 2.0, d / 2.0)
	##
	cr.move_to(x1, y1)
	cr.line_to(x2, y2)
	cr.line_to(x3, y3)
	cr.line_to(x4, y4)
	cr.close_path()


def drawArcOutline(cr, xc, yc, r, d, a0, a1):
	"""
		cr: cairo context
		xc, yc: coordinates of center
		r: outer radius
		d: outline width (r - ri)
		a0: start angle (radians)
		a1: end angle (radians)
	"""
	x1, y1 = goAngle(xc, yc, a0, r - d)
	x2, y2 = goAngle(xc, yc, a1, r - d)
	x3, y3 = goAngle(xc, yc, a1, r)
	x4, y4 = goAngle(xc, yc, a0, r)
	####
	cr.move_to(x1, y1)
	cr.arc(xc, yc, r - d, a0, a1)
	# cr.move_to(x2, y2)
	cr.line_to(x3, y3)
	cr.arc_negative(xc, yc, r, a1, a0)
	# cr.move_to(x4, y4)
	# cr.line_to(x1, y1)

	cr.close_path()
