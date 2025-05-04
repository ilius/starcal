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

from time import perf_counter
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3.ui_gtk import gdk, gtk, timeout_add
from scal3.ui_gtk.decorators import registerType
from scal3.ui_gtk.drawing import (
	newTextLayout,
	setColor,
)

if TYPE_CHECKING:
	import cairo

__all__ = [
	"FloatingMsg",
	"MyLabel",
	"NoFillFloatingMsgWindow",
]

rootWin = gdk.get_default_root_window()
screenWidth = rootWin.get_width()
# FIXME: use ud.workAreaW from gtk_ud.py


@registerType
class FloatingMsg(gtk.DrawingArea):
	def on_realize(self, _widget) -> None:
		self.animateStart()

	def __init__(
		self,
		text,
		speed=100,
		bgColor=(255, 255, 0),
		textColor=(0, 0, 0),
		refreshTime=10,
		finishFunc=None,
		finishOnClick=True,
		createWindow=True,
	) -> None:
		gtk.DrawingArea.__init__(self)
		# speed: pixels per second
		self.speed = speed
		self.bgColor = bgColor
		self.textColor = textColor
		self.refreshTime = refreshTime
		self.finishFunc = finishFunc
		self.isFinished = False
		if finishOnClick:
			self.connect("button-press-event", self.finish)
		# --------
		if isinstance(bytes, str):
			text = text.decode("utf8")
		lines = []
		for line in text.split("\n"):
			line = line.strip()  # noqa: PLW2901
			if line:
				lines.append(line)
		self.linesNum = len(lines)
		self.layoutList = [newTextLayout(self, line) for line in lines]
		self.rtlList = [
			self.isRtl(lines[i], self.layoutList[i]) for i in range(self.linesNum)
		]
		self.index = 0
		self.height = 30
		# --------
		self.connect("draw", self.onExposeEvent)
		self.connect("realize", self.on_realize)
		# --------
		if createWindow:
			self.win = gtk.Window(gtk.WindowType.POPUP)
			# ^ gtk.WindowType.POPUP ?
			self.win.add(self)
			self.win.set_decorated(False)
			self.win.set_property("skip-taskbar-hint", True)
			self.win.set_keep_above(True)
		else:
			self.win = False

	@staticmethod
	def isRtl(line, layout):
		for i in range(len(line)):
			y = layout.index_to_pos(i).y
			if y != 0:
				return y < 0
		return False

	def updateLine(self) -> None:
		self.layout = self.layoutList[self.index]
		self.rtl = self.rtlList[self.index]
		self.rtlSign = 1 if self.rtl else -1
		size = self.layout.get_pixel_size()
		self.height = size[1]
		self.set_size_request(screenWidth, self.height)
		if self.win is not None:
			self.win.resize(screenWidth, self.height)
		self.textWidth = size[0]
		self.startXpos = -self.textWidth if self.rtl else screenWidth
		self.xpos = self.startXpos

	def finish(self, _w=None, _e=None) -> None:
		self.isFinished = True
		self.win.destroy()
		self.destroy()
		if self.finishFunc:
			self.finishFunc()

	def onExposeEvent(self, _widget, _gevent) -> None:
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

	def drawWithContext(self, cr: cairo.Context) -> None:
		cr.rectangle(0, 0, screenWidth, self.height)
		setColor(cr, self.bgColor)
		cr.fill()
		# -------
		cr.move_to(self.xpos, 0)
		setColor(cr, self.textColor)
		show_layout(cr, self.layout)

	def animateStart(self) -> None:
		self.updateLine()
		self.startTime = perf_counter()
		self.animateUpdate()

	def animateUpdate(self) -> None:
		if self.isFinished:
			return
		timeout_add(self.refreshTime, self.animateUpdate)
		self.xpos = self.startXpos + (
			(perf_counter() - self.startTime) * self.speed * self.rtlSign
		)
		if self.xpos > screenWidth or self.xpos < -self.textWidth:
			if self.index >= self.linesNum - 1:
				self.finish()
				return
			self.index += 1
			self.updateLine()
		self.queue_draw()

	def show(self) -> None:
		gtk.DrawingArea.show(self)
		self.win.show()


@registerType
class MyLabel(gtk.DrawingArea):
	def __init__(self, bgColor, textColor) -> None:
		gtk.DrawingArea.__init__(self)
		self.bgColor = bgColor
		self.textColor = textColor
		self.connect("draw", self.onExposeEvent)

	def set_label(self, text) -> None:
		self.text = text
		self.layout = newTextLayout(self, text)
		size = self.layout.get_pixel_size()
		self.height = size[1]
		self.width = size[0]
		self.set_size_request(self.width, self.height)
		self.rtl = self.isRtl()
		self.rtlSign = 1 if self.rtl else -1

	def onExposeEvent(self, _widget, _gevent) -> None:
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

	def drawWithContext(self, cr: cairo.Context) -> None:
		cr.rectangle(0, 0, self.width, self.height)
		setColor(cr, self.bgColor)
		cr.fill()
		# -------
		cr.move_to(0, 0)
		setColor(cr, self.textColor)
		show_layout(cr, self.layout)

	def isRtl(self):
		for i in range(len(self.text)):
			y = self.layout.index_to_pos(i).y
			if y != 0:
				return y < 0
		return False


@registerType
class NoFillFloatingMsgWindow(gtk.Window):
	def __init__(
		self,
		text,
		speed=100,
		bgColor=(255, 255, 0),
		textColor=(0, 0, 0),
		refreshTime=10,
		finishFunc=None,
		finishOnClick=True,
	) -> None:
		gtk.Window.__init__(self)
		self.set_type_hint(gtk.WindowType.POPUP)
		# ^ OR gtk.WindowType.POPUP ?
		self.set_decorated(False)
		self.set_property("skip-taskbar-hint", True)
		self.set_keep_above(True)
		self.label = MyLabel(bgColor, textColor)
		self.add(self.label)
		self.label.show()
		# speed: pixels per second
		self.speed = speed
		self.refreshTime = refreshTime
		self.finishFunc = finishFunc
		self.isFinished = False
		if finishOnClick:
			self.connect("button-press-event", self.finish)
		# --------
		if isinstance(text, bytes):
			text = text.decode("utf8")
		text = text.replace("\\n", "\n").replace("\\t", "\t")
		lines = []
		for line in text.split("\n"):
			line = line.strip()  # noqa: PLW2901
			if line:
				lines.append(line)
		self.linesNum = len(lines)
		self.lines = lines
		self.index = 0
		# --------
		self.connect("realize", lambda _w: self.animateStart())

	def updateLine(self) -> None:
		self.label.set_label(self.lines[self.index])
		self.startXpos = -self.label.width if self.label.rtl else screenWidth
		self.startTime = perf_counter()

	def finish(self, _w=None, _e=None) -> None:
		self.isFinished = True
		self.destroy()
		if self.finishFunc:
			self.finishFunc()

	def animateStart(self) -> None:
		self.updateLine()
		self.animateUpdate()

	def animateUpdate(self) -> None:
		if self.isFinished:
			return
		timeout_add(self.refreshTime, self.animateUpdate)
		xpos = int(
			self.startXpos  # TODO: time.perf_counter()
			+ ((perf_counter() - self.startTime) * self.speed * self.label.rtlSign),
		)
		self.move(xpos, 0)
		self.resize(1, 1)
		if xpos > screenWidth or xpos < -self.label.width:
			if self.index >= self.linesNum - 1:
				self.finish()
				return
			self.index += 1
			self.updateLine()


if __name__ == "__main__":
	import sys

	if len(sys.argv) < 2:
		sys.exit(1)
	text = " ".join(sys.argv[1:])
	# msg = FloatingMsg(
	msg = NoFillFloatingMsgWindow(
		text,
		speed=200,
		finishFunc=gtk.main_quit,
	)
	msg.show()
	gtk.main()
