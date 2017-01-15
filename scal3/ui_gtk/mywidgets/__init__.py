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

import sys
import os
from time import time as now
from time import localtime

from gi.repository import GObject
from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import *
from scal3.ui_gtk.color_utils import *
from scal3.ui_gtk.utils import buffer_get_text
from scal3.ui_gtk.drawing import newDndFontNamePixbuf


def myRaise():
	i = sys.exc_info()
	try:
		print("line %s: %s: %s" % (
			i[2].tb_lineno,
			i[0].__name__, i[1],
		))
	except:
		print(i)


def show_event(widget, gevent):
	print(type(widget), gevent.type.value_name)#, gevent.send_event


def time_rem():
	return int(1000 * (1.01 - now() % 1))


class MyFontButton(gtk.FontButton):
	def __init__(self, parent):
		gtk.FontButton.__init__(self)
		##########
		self.drag_source_set(
			gdk.ModifierType.MODIFIER_MASK,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_source_add_text_targets()
		self.connect("drag-data-get", self.dragDataGet)
		self.connect("drag-begin", self.dragBegin, parent)
		self.drag_dest_set(
			gtk.DestDefaults.ALL,
			(),
			gdk.DragAction.COPY,
		)
		self.drag_dest_add_text_targets()
		self.connect("drag-data-received", self.dragDataRec)

	def dragDataGet(self, fontb, context, selection, target_id, etime):
		#print("fontButtonDragDataGet")
		selection.set_text(gfontEncode(fontb.get_font_name()))
		return True

	def dragDataRec(self, fontb, context, x, y, selection, target_id, etime):
		#dtype = selection.get_data_type()
		#print(dtype ## UTF8_STRING)
		text = selection.get_text()
		#\print("fontButtonDragDataRec    text=", text)
		if text:
			pfont = Pango.FontDescription(text)
			if pfont.get_family() and pfont.get_size() > 0:
				gtk.FontButton.set_font_name(fontb, text)
		return True

	def dragBegin(self, fontb, context, parent):
		#print("fontBottonDragBegin"## caled before dragCalDataGet)
		fontName = gtk.FontButton.get_font_name(self)
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

	def get_font_name(self):
		return gfontDecode(gtk.FontButton.get_font_name(self))

	def set_font_name(self, font):
		if isinstance(font, str):## For compatibility
			gtk.FontButton.set_font_name(self, font)
		else:
			gtk.FontButton.set_font_name(self, gfontEncode(font))


class MyColorButton(gtk.ColorButton):
	# for tooltip text
	def __init__(self):
		gtk.ColorButton.__init__(self)
		self.connect("color-set", self.update_tooltip)

	def update_tooltip(self, colorb=None):
		r, g, b = self.get_color()
		a = self.get_alpha()
		if self.get_use_alpha():
			text = "%s\n%s\n%s\n%s" % (r, g, b, a)
		else:
			text = "%s\n%s\n%s" % (r, g, b)
		##self.get_tooltip_window().set_direction(gtk.TextDirection.LTR)
		##print(self.get_tooltip_window())
		self.set_tooltip_text(text) ##???????????????? Right to left
		#self.tt_label.set_label(text)##???????????? Dosent work
		##self.set_tooltip_window(self.tt_win)

	def set_color(self, color):## color is a tuple of (r, g, b)
		if len(color) == 3:
			r, g, b = color
			gtk.ColorButton.set_color(self, rgbToGdkColor(*color))
			self.set_alpha(255)
		elif len(color) == 4:
			gtk.ColorButton.set_color(self, rgbToGdkColor(*color[:3]))
			gtk.ColorButton.set_alpha(self, color[3] * 257)
		else:
			raise ValueError
		self.update_tooltip()

	def set_alpha(self, alpha):  # alpha is in range(256)
		if alpha is None:
			alpha = 255
		gtk.ColorButton.set_alpha(self, alpha * 257)
		self.update_tooltip()

	def get_color(self):
		color = gtk.ColorButton.get_color(self)
		return (
			int(color.red / 257),
			int(color.green / 257),
			int(color.blue / 257),
		)

	def get_alpha(self):
		return int(gtk.ColorButton.get_alpha(self) / 257)


class TextFrame(gtk.Frame):
	def __init__(self):
		gtk.Frame.__init__(self)
		self.set_border_width(4)
		####
		self.textview = gtk.TextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.add(self.textview)
		####
		self.buff = self.textview.get_buffer()

	def set_text(self, text):
		self.buff.set_text(text)

	def get_text(self):
		return buffer_get_text(self.buff)


if __name__ == "__main__":
	d = gtk.Dialog(parent=None)
	clock = FClockLabel()
	clock.start()
	pack(d.vbox, clock, 1, 1)
	d.connect("delete-event", lambda widget, event: gtk.main_quit())
	d.show_all()
	gtk.main()
