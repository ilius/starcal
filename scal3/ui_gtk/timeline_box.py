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

from scal3 import logger

log = logger.get()

from math import pi

from gi.repository.PangoCairo import show_layout

from scal3 import ui
from scal3.timeline import conf
from scal3.ui_gtk.drawing import fillColor
from scal3.ui_gtk.font_utils import pfontEncode

__all__ = ["drawBoxBG", "drawBoxBorder", "drawBoxText"]


def drawBoxBG(cr, box, x, y, w, h):
	d = box.lineW
	cr.rectangle(x, y, w, h)
	if d == 0:
		fillColor(cr, box.color)
		return
	try:
		alpha = box.color[3]
	except IndexError:
		alpha = 255
	fillColor(
		cr,
		(
			box.color[0],
			box.color[1],
			box.color[2],
			int(alpha * conf.boxInnerAlpha),
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


def drawBoxBorder(cr, box, x, y, w, h):
	if box.hasBorder:
		if w > 2 * conf.boxEditBorderWidth and h > conf.boxEditBorderWidth:
			b = conf.boxEditBorderWidth
			bd = conf.boxEditInnerLineWidth
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


def drawBoxText(cr, box, x, y, w, h, widget):
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
	avgCharW = (textW if conf.rotateBoxLabel == 0 else max(textW, textH)) / textLen

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

	fillColor(cr, conf.fgColor)  # before cr.move_to

	if conf.rotateBoxLabel == 0 or rotateRatio <= normRatio:
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
		x + (w - conf.rotateBoxLabel * layoutH) / 2.0,
		y + (h + conf.rotateBoxLabel * layoutW) / 2.0,
	)
	cr.rotate(-conf.rotateBoxLabel * pi / 2)
	show_layout(cr, layout)
	try:
		cr.rotate(conf.rotateBoxLabel * pi / 2)
	except Exception:
		log.warning(
			f"could not rotate by {conf.rotateBoxLabel * pi / 2 = }",
		)
