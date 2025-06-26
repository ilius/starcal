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

from __future__ import annotations

import time
from time import localtime, strftime

from gi.repository.PangoCairo import show_layout

from scal3.time_utils import clockWaitMilliseconds
from scal3.ui import conf
from scal3.ui_gtk import Dialog, gdk, gtk, pack, timeout_add
from scal3.ui_gtk.drawing import ImageContext, fillColor, setColor


class ClockLabel(gtk.Label):
	def __init__(
		self,
		bold: bool = False,
		seconds: bool = True,
		selectable: bool = False,
	) -> None:
		gtk.Label.__init__(self)
		self.set_use_markup(True)
		self.set_selectable(selectable)
		self.bold = bold
		self.seconds = seconds
		self.running = False
		self.start()  # ???

	def start(self) -> None:
		self.running = True
		self.update()

	def update(self) -> None:
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

	def stop(self) -> None:
		self.running = False

	# 	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
	# 	if gevent.button == 3:


class FClockLabel(gtk.Label):
	def __init__(
		self,
		clockFormat: str = "%T",
		local: bool = True,
		selectable: bool = False,
	) -> None:
		"""
		ClockFormat is a string that used in strftime(), it can contains markup
		that apears in GtkLabel for example format can be "<b>%T</b>"
		local is bool. if True, use Local time. and if False, use GMT time.
		selectable is bool that passes to GtkLabel.
		"""
		gtk.Label.__init__(self)
		self.set_use_markup(True)
		self.set_selectable(selectable)
		self.set_direction(gtk.TextDirection.LTR)
		self.format = clockFormat
		self.local = local
		self.running = False
		self.start()  # ???

	def start(self) -> None:
		self.running = True
		self.update()

	def update(self) -> None:
		if self.running:
			timeout_add(clockWaitMilliseconds(), self.update)
			if self.local:
				self.set_label(strftime(self.format))
			else:
				self.set_label(strftime(self.format, time.gmtime()))

	def stop(self) -> None:
		self.running = False


class FClockWidget(gtk.DrawingArea):  # Time is in Local
	def __init__(
		self,
		clockFormat: str = "%T",
		selectable: bool = False,  # noqa: ARG002
	) -> None:
		"""
		ClockFormat is a string that used in strftime(), it can contains markup
		that apears in GtkLabel for example format can be "<b>%T</b>"
		local is bool. if True, use Local time. and if False, use GMT time.
		selectable is bool that passes to GtkLabel.
		"""
		gtk.DrawingArea.__init__(self)
		self.set_direction(gtk.TextDirection.LTR)
		self.format = clockFormat
		self.text = ""
		self.running = False
		self.connect("draw", self.onDraw)
		self.start()  # ???

	def start(self) -> None:
		self.running = True
		self.update()

	def update(self) -> None:
		if self.running:
			timeout_add(clockWaitMilliseconds(), self.update)
			self.set_label(strftime(self.format))

	def stop(self) -> None:
		self.running = False

	def set_label(self, text: str) -> None:
		self.text = text
		self.queue_draw()

	def onDraw(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
	) -> None:
		win = self.get_window()
		assert win is not None
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

	def drawWithContext(self, cr: ImageContext) -> None:
		text = self.text
		fillColor(cr, conf.bgColor.v)
		setColor(cr, conf.textColor.v)
		lay = self.create_pango_layout(text)
		show_layout(cr, lay)
		w, h = lay.get_pixel_size()
		self.set_size_request(w, h)
		"""
		textLay = self.create_pango_layout("") # markup
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
	d = Dialog()
	widget = FClockWidget()
	# widget = ClockLabel()
	pack(d.vbox, widget, 1, 1)  # type: ignore[arg-type]
	d.vbox.show_all()  # type: ignore[attr-defined]
	d.run()
