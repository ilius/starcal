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
from scal3.color_utils import RGBA

log = logger.get()

from math import pi
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import ui
from scal3.timeline import conf
from scal3.ui import conf as uiConf
from scal3.ui_gtk.drawing import fillColor
from scal3.ui_gtk.font_utils import pfontEncode

if TYPE_CHECKING:
	from gi.repository import Gtk as gtk

	from scal3.timeline.box import Box
	from scal3.ui_gtk.drawing import ImageContext

__all__ = ["drawBoxBG", "drawBoxBorder", "drawBoxText"]


def drawBoxBG(
	cr: ImageContext,
	box: Box,
	x: float,
	y: float,
	w: float,
	h: float,
) -> None:
	d = box.lineW
	cr.rectangle(x, y, w, h)
	if d == 0:
		fillColor(cr, box.color)
		return
	if len(box.color) > 3:
		alpha = box.color[3]
	else:
		alpha = 255
	fillColor(
		cr,
		RGBA(
			box.color[0],
			box.color[1],
			box.color[2],
			int(alpha * conf.boxInnerAlpha.v),
		),
	)
	# ---
	cr.set_line_width(0)
	cr.move_to(x, y)
	cr.line_to(x + w, y)
	cr.line_to(x + w, y + h)
	cr.line_to(x, y + h)
	cr.line_to(x, y)
	cr.line_to(x + d, y)
	cr.line_to(x + d, y + h - d)
	cr.line_to(x + w - d, y + h - d)
	cr.line_to(x + w - d, y + d)
	cr.line_to(x + d, y + d)
	cr.close_path()
	fillColor(cr, box.color)


def drawBoxBorder(
	cr: ImageContext,
	box: Box,
	x: float,
	y: float,
	w: float,
	h: float,
) -> None:
	if box.hasBorder:
		if w > 2 * conf.boxEditBorderWidth.v and h > conf.boxEditBorderWidth.v:
			b = conf.boxEditBorderWidth.v
			bd = conf.boxEditInnerLineWidth.v
			# cr.set_line_width(bd)
			cr.move_to(x + b - bd, y + h)
			cr.line_to(x + b - bd, y + b - bd)
			cr.line_to(x + w - b + bd, y + b - bd)
			cr.line_to(x + w - b + bd, y + h)
			cr.line_to(x + w - b, y + h)
			cr.line_to(x + w - b, y + b)
			cr.line_to(x + b, y + b)
			cr.line_to(x + b, y + h)
			cr.close_path()
			fillColor(cr, box.color)
			# ---
			bds = 0.7 * bd
			cr.move_to(x, y)
			cr.line_to(x + bds, y)
			cr.line_to(x + b + bds, y + b)
			cr.line_to(x + b, y + b + bds)
			cr.line_to(x, y + bds)
			cr.close_path()
			fillColor(cr, box.color)
			# --
			cr.move_to(x + w, y)
			cr.line_to(x + w - bds, y)
			cr.line_to(x + w - b - bds, y + b)
			cr.line_to(x + w - b, y + b + bds)
			cr.line_to(x + w, y + bds)
			cr.close_path()
			fillColor(cr, box.color)
		else:
			box.hasBorder = False


def drawBoxText(
	cr: ImageContext,
	box: Box,
	x: float,
	y: float,
	w: float,
	h: float,
	widget: gtk.Widget,
) -> None:
	# FIXME how to find the best font size based on the box's width,
	# height, and font family?
	# possibly write in many lines? or just in one line and wrap if needed?
	if not box.text:
		return
	# log.debug(box.text)
	text = box.text
	if len(text) < 4:
		text = f" {text} "

	textW = 0.95 * w
	textH = 0.95 * h
	textLen = len(text)
	# log.debug(f"{textLen=}")
	avgCharW = (textW if conf.rotateBoxLabel.v == 0 else max(textW, textH)) / textLen

	if avgCharW < 3:  # FIXME
		return

	font = ui.getFont()
	layout = widget.create_pango_layout(text)  # a Pango.Layout object
	layout.set_font_description(pfontEncode(font))
	layoutW, layoutH = layout.get_pixel_size()
	# log.debug(f"orig font size: {font.size}")
	normRatio = min(
		textW / layoutW,
		textH / layoutH,
	)
	rotateRatio = min(
		textW / layoutH,
		textH / layoutW,
	)

	# fillColor before cr.move_to:
	fillColor(cr, conf.fgColor.v or uiConf.textColor.v)

	if conf.rotateBoxLabel.v == 0 or rotateRatio <= normRatio:
		font.size *= normRatio
		layout.set_font_description(pfontEncode(font))
		layoutW, layoutH = layout.get_pixel_size()
		cr.move_to(
			x + (w - layoutW) / 2.0,
			y + (h - layoutH) / 2.0,
		)
		show_layout(cr, layout)
		return

	font.size *= rotateRatio
	layout.set_font_description(pfontEncode(font))
	layoutW, layoutH = layout.get_pixel_size()
	cr.move_to(
		x + (w - conf.rotateBoxLabel.v * layoutH) / 2.0,
		y + (h + conf.rotateBoxLabel.v * layoutW) / 2.0,
	)
	cr.rotate(-conf.rotateBoxLabel.v * pi / 2)
	show_layout(cr, layout)
	try:
		cr.rotate(conf.rotateBoxLabel.v * pi / 2)
	except Exception:
		log.warning(
			f"could not rotate by {conf.rotateBoxLabel.v * pi / 2 = }",
		)
