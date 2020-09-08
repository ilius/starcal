#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/lgpl.txt>.
# Also avalable in /usr/share/common-licenses/LGPL on Debian systems
# or /usr/share/licenses/common/LGPL/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

import sys
import os
from time import time as now
from time import localtime
from typing import Tuple

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import *
from scal3.ui_gtk.color_utils import *
from scal3.ui_gtk.utils import buffer_get_text
from scal3.ui_gtk.drawing import newDndFontNamePixbuf

from scal3.locale_man import tr as _


def show_event(widget, gevent):
	log.info(f"{type(widget)}, {gevent.type.value_name}")
	#, gevent.send_event


class MyFontButton(gtk.FontButton):
	def __init__(self, dragAndDrop=True):
		gtk.FontButton.__init__(self)
		if dragAndDrop:
			self.setupDragAndDrop()

	def setupDragAndDrop(self):
		self.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_source_add_text_targets()
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag-begin", self.dragBegin)
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_dest_add_text_targets()
		self.connect("drag-data-received", self.dragDataRec)

	def dragDataGet(
		self,
		fontb: gtk.FontButton,
		context: gdk.DragContext,
		selection: gtk.SelectionData,
		info: int,
		etime: int,
	):
		# log.debug("fontButtonDragDataGet")
		valueStr = gfontEncode(fontb.get_font())
		valueBytes = valueStr.encode("utf-8")
		selection.set_text(valueStr, len(valueBytes))
		return True

	def dragDataRec(self, fontb, context, x, y, selection, target_id, etime):
		#dtype = selection.get_data_type()
		# log.debug(dtype ## UTF8_STRING)
		text = selection.get_text()
		log.debug(f"fontButtonDragDataRec    text={text}")
		if text:
			pfont = pango.FontDescription(text)
			if pfont.get_family() and pfont.get_size() > 0:
				gtk.FontButton.set_font(fontb, text)
				self.emit("font-set")
		return True

	def dragBegin(self, fontb, context):
		# log.debug("fontBottonDragBegin"## caled before dragCalDataGet)
		fontName = gtk.FontButton.get_font(self)
		pbuf = newDndFontNamePixbuf(fontName)
		w = pbuf.get_width()
		h = pbuf.get_height()
		gtk.drag_set_icon_pixbuf(
			context,
			pbuf,
			w / 2,
			-10,
		)
		return True

	def get_font(self) -> Tuple[str, bool, bool, float]:
		return gfontDecode(gtk.FontButton.get_font(self))

	def set_font(self, font: Tuple[str, bool, bool, float]):
		gtk.FontButton.set_font(self, gfontEncode(font))


class MyColorButton(gtk.ColorButton):
	# for tooltip text
	def __init__(self):
		gtk.ColorButton.__init__(self)
		gtk.ColorChooser.set_use_alpha(self, True)
		self.connect("color-set", self.update_tooltip)

	def update_tooltip(self, colorb=None):
		r, g, b, a = self.get_rgba()
		if gtk.ColorChooser.get_use_alpha(self):
			text = f"{_('Red')}: {_(r)}\n{_('Green')}: {_(g)}\n{_('Blue')}: {_(b)}\n{_('Opacity')}: {_(a)}"
		else:
			text = f"{_('Red')}: {_(r)}\n{_('Green')}: {_(g)}\n{_('Blue')}: {_(b)}"
		##self.get_tooltip_window().set_direction(gtk.TextDirection.LTR)
		## log.debug(self.get_tooltip_window())
		self.set_tooltip_text(text) ##???????????????? Right to left
		#self.tt_label.set_label(text)##???????????? Dosent work
		##self.set_tooltip_window(self.tt_win)

	# color is a tuple of (r, g, b) or (r, g, b, a)
	def set_rgba(self, color):
		gtk.ColorButton.set_rgba(self, rgbaToGdkRGBA(*color))
		self.update_tooltip()

	def get_rgba(self):
		color = gtk.ColorButton.get_rgba(self)
		return (
			int(color.red * 255),
			int(color.green * 255),
			int(color.blue * 255),
			int(color.alpha * 255),
		)


class TextFrame(gtk.Frame):
	def __init__(self, onTextChange=None):
		gtk.Frame.__init__(self)
		self.set_border_width(4)
		####
		self.textview = gtk.TextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.add(self.textview)
		####
		self.buff = self.textview.get_buffer()
		if onTextChange is not None:
			self.buff.connect("changed", onTextChange)

	def set_text(self, text):
		self.buff.set_text(text)

	def get_text(self):
		return buffer_get_text(self.buff)


if __name__ == "__main__":
	d = gtk.Dialog()
	clock = FClockLabel()
	clock.start()
	pack(d.vbox, clock, 1, 1)
	d.connect("delete-event", lambda widget, event: gtk.main_quit())
	d.show_all()
	gtk.main()
