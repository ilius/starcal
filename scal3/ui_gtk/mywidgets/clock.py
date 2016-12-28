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

from gi.repository.GObject import timeout_add
from gi.repository import GdkPixbuf

from scal3.ui_gtk import *
from scal3.ui_gtk.font_utils import *


def time_rem():
	return int(1000 * (1.01 - now() % 1))


class ClockLabel(gtk.Label):
	def __init__(self, bold=False, seconds=True, selectable=False):
		gtk.Label.__init__(self)
		self.set_use_markup(True)
		self.set_selectable(selectable)
		self.bold = bold
		self.seconds = seconds
		self.running = False
		#self.connect('button-press-event', self.button_press)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(time_rem(), self.update)
			if self.seconds:
				l = '%.2d:%.2d:%.2d' % tuple(localtime()[3:6])
			else:
				l = '%.2d:%.2d' % tuple(localtime()[3:5])
			if self.bold:
				l = '<b>%s</b>' % l
			self.set_label(l)

	def stop(self):
		self.running = False

	#def button_press(self, obj, gevent):
	#	if gevent.button == 3:


class FClockLabel(gtk.Label):
	def __init__(self, format='%T', local=True, selectable=False):
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
		#self.connect('button-press-event', self.button_press)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(time_rem(), self.update)
			if self.local:
				self.set_label(strftime(self.format))
			else:
				self.set_label(strftime(self.format, time.gmtime()))

	def stop(self):
		self.running = False


class FClockWidget(gtk.DrawingArea): ## Time is in Local
	def __init__(self, format='%T', selectable=False):
		"""
		format is a string that used in strftime(), it can contains markup
		that apears in GtkLabel for example format can be "<b>%T</b>"
		local is bool. if True, use Local time. and if False, use GMT time.
		selectable is bool that passes to GtkLabel
		"""
		gtk.DrawingArea.__init__(self)
		self.set_direction(gtk.TextDirection.LTR)
		self.format = format
		self.running = False
		#self.connect('button-press-event', self.button_press)
		self.start()#???

	def start(self):
		self.running = True
		self.update()

	def update(self):
		if self.running:
			timeout_add(time_rem(), self.update)
			self.set_label(strftime(self.format))

	def stop(self):
		self.running = False

	def set_label(self, text):
		if self.get_window() is None:
			return
		self.get_window().clear()
		cr = self.get_window().cairo_create()
		cr.set_source_color(gdk.Color(0, 0, 0))
		lay = self.create_pango_layout(text)
		show_layout(cr, lay)
		w, h = lay.get_pixel_size()
		cr.clip()
		self.set_size_request(w, h)
		"""
		textLay = self.create_pango_layout('') ## markup
		textLay.set_markup(text)
		textLay.set_font_description(Pango.FontDescription(ui.getFont()))
		w, h = textLay.get_pixel_size()
		pixbuf = GdkPixbuf.Pixbuf(GdkPixbuf.Colorspace.RGB, True, 8, w, h)
		pixbuf = pixbuf.add_alpha(True, '0','0','0')
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
