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

import time
from time import localtime, strftime
from time import time as now

from scal3.time_utils import clockWaitMilliseconds
from scal3 import ui

from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import *
from scal3.ui_gtk.drawing import setColor, fillColor, show_layout


class ClockLabel(gtk.Label):
	def __init__(self, bold=False, seconds=True, selectable=False):
		gtk.Label.__init__(self)
		self.set_use_markup(True)
		self.set_selectable(selectable)
		self.bold = bold
		self.seconds = seconds
		self.running = False
		#self.connect("button-press-event", self.onButtonPress)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(clockWaitMilliseconds(), self.update)
			H, M, S = localtime()[3:6]
			if self.seconds:
				label = f"{H:02}:{M:02}:{S:02}"
			else:
				label = f"{H:02}:{M:02}"
			if self.bold:
				label = f"<b>{label}</b>"
			self.set_label(label)

	def stop(self):
		self.running = False

	#def onButtonPress(self, obj, gevent):
	#	if gevent.button == 3:


class FClockLabel(gtk.Label):
	def __init__(self, format="%T", local=True, selectable=False):
		"""
		format is a string that used in strftime(), it can contains markup
		that apears in GtkLabel for example format can be "<b>%T</b>"
		local is bool. if True, use Local time. and if False, use GMT time.
		selectable is bool that passes to GtkLabel
		"""
		gtk.Label.__init__(self)
		self.set_use_markup(True)
		self.set_selectable(selectable)
		self.set_direction(gtk.TextDirection.LTR)
		self.format = format
		self.local = local
		self.running = False
		#self.connect("button-press-event", self.onButtonPress)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(clockWaitMilliseconds(), self.update)
			if self.local:
				self.set_label(strftime(self.format))
			else:
				self.set_label(strftime(self.format, time.gmtime()))

	def stop(self):
		self.running = False


class FClockWidget(gtk.DrawingArea): ## Time is in Local
	def __init__(self, format="%T", selectable=False):
		"""
		format is a string that used in strftime(), it can contains markup
		that apears in GtkLabel for example format can be "<b>%T</b>"
		local is bool. if True, use Local time. and if False, use GMT time.
		selectable is bool that passes to GtkLabel
		"""
		gtk.DrawingArea.__init__(self)
		self.set_direction(gtk.TextDirection.LTR)
		self.format = format
		self.text = ""
		self.running = False
		self.connect("draw", self.onDraw)
		#self.connect("button-press-event", self.onButtonPress)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(clockWaitMilliseconds(), self.update)
			self.set_label(strftime(self.format))

	def stop(self):
		self.running = False

	def set_label(self, text):
		self.text = text
		self.queue_draw()

	def onDraw(self, widget=None, event=None):
		win = self.get_window()
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr)
		finally:
			win.end_draw_frame(dctx)

	def drawWithContext(self, cr: "cairo.Context"):
		text = self.text
		fillColor(cr, ui.bgColor)
		setColor(cr, ui.textColor)
		lay = self.create_pango_layout(text)
		show_layout(cr, lay)
		w, h = lay.get_pixel_size()
		self.set_size_request(w, h)
		"""
		textLay = self.create_pango_layout("") ## markup
		textLay.set_markup(text=text, length=-1)
		textLay.set_font_description(Pango.FontDescription(ui.getFont()))
		w, h = textLay.get_pixel_size()
		pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, w, h)
		pixbuf = pixbuf.add_alpha(True, "0","0","0")
		pmap, mask = pixbuf.render_pixmap_and_mask(alpha_threshold=127)
		# pixmap is also a drawable
		pmap.draw_layout(
			pmap.new_gc(),
			0,
			0,
			textLay,
			statusIconTextColor,
		)  #, statusIconBgColor)
		self.clear()
		#self.set_from_image(pmap.get_image(0, 0, w, h), mask)
		self.set_from_pixmap(pmap, mask)
		"""


if __name__ == "__main__":
	d = gtk.Dialog()
	widget = FClockWidget()
	# widget = ClockLabel()
	pack(d.vbox, widget, 1, 1)
	d.vbox.show_all()
	d.run()
