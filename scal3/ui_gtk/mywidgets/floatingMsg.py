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
from typing import TYPE_CHECKING, Any

from gi.repository.PangoCairo import show_layout

from scal3.color_utils import black, yellow
from scal3.ui_gtk import gdk, gtk, timeout_add
from scal3.ui_gtk.drawing import ImageContext, newTextLayout, setColor

if TYPE_CHECKING:
	from collections.abc import Callable

	from gi.repository import Pango as pango

	from scal3.color_utils import ColorType

__all__ = [
	"FloatingMsg",
	"MyLabel",
	"NoFillFloatingMsgWindow",
]

rootWin = gdk.get_default_root_window()
screenWidth = rootWin.get_width()
# FIXME: use ud.workAreaW from gtk_ud.py


class FloatingMsg(gtk.DrawingArea):
	signals: list[tuple[str, list[Any]]] = []

	def on_realize(self, _w: gtk.Widget) -> None:
		self.animateStart()

	def __init__(
		self,
		text: str,
		speed: float = 100,
		bgColor: ColorType = yellow,
		textColor: ColorType = black,
		refreshTime: int = 10,  # in milliseconds
		finishFunc: Callable[[], None] | None = None,
		finishOnClick: bool = True,
		createWindow: bool = True,
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
		self.win: gtk.Window | None = None
		if createWindow:
			self.win = gtk.Window(type=gtk.WindowType.POPUP)
			# ^ gtk.WindowType.POPUP ?
			self.win.add(self)
			self.win.set_decorated(False)
			self.win.set_property("skip-taskbar-hint", True)
			self.win.set_keep_above(True)

	@staticmethod
	def isRtl(line: str, layout: pango.Layout | None) -> bool:
		if layout is None:
			return False
		for i in range(len(line)):
			y = layout.index_to_pos(i).y
			if y != 0:
				return y < 0
		return False

	def updateLine(self) -> None:
		self.layout = self.layoutList[self.index]
		if self.layout is None:
			print(f"self.layout = None, {self.index=}")
			return
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

	def finish(
		self,
		_widget: gtk.Widget | None = None,
		_genvent: gdk.Event | None = None,
	) -> None:
		self.isFinished = True
		if self.win is not None:
			self.win.destroy()
			self.win = None
		self.destroy()
		if self.finishFunc:
			self.finishFunc()

	def onExposeEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> None:
		win = self.get_window()
		if win is None:
			return
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
		if self.layout is None:
			return
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
		self.xpos = self.startXpos + int(
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
		if self.win is not None:
			self.win.show()


class MyLabel(gtk.DrawingArea):
	signals: list[tuple[str, list[Any]]] = []

	def __init__(self, bgColor: ColorType, textColor: ColorType) -> None:
		gtk.DrawingArea.__init__(self)
		self.bgColor = bgColor
		self.textColor = textColor
		self.connect("draw", self.onExposeEvent)

	def set_label(self, text: str) -> None:
		self.text = text
		self.layout = newTextLayout(self, text)
		if self.layout is None:
			return
		size = self.layout.get_pixel_size()
		self.height = size[1]
		self.width = size[0]
		self.set_size_request(self.width, self.height)
		self.rtl = self.isRtl()
		self.rtlSign = 1 if self.rtl else -1

	def onExposeEvent(self, _w: gtk.Widget, _ge: gdk.Event) -> None:
		win = self.get_window()
		if win is None:
			return
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
		if self.layout is None:
			return
		cr.rectangle(0, 0, self.width, self.height)
		setColor(cr, self.bgColor)
		cr.fill()
		# -------
		cr.move_to(0, 0)
		setColor(cr, self.textColor)
		show_layout(cr, self.layout)

	def isRtl(self) -> bool:
		if self.layout is None:
			return False
		for i in range(len(self.text)):
			y = self.layout.index_to_pos(i).y
			if y != 0:
				return y < 0
		return False


class NoFillFloatingMsgWindow(gtk.Window):
	signals: list[tuple[str, list[Any]]] = []

	def __init__(
		self,
		text: str,
		speed: float = 100,
		bgColor: ColorType = yellow,
		textColor: ColorType = black,
		refreshTime: int = 10,  # in milliseconds
		finishFunc: Callable[[], None] | None = None,
		finishOnClick: bool = True,
	) -> None:
		gtk.Window.__init__(self, type=gtk.WindowType.POPUP)
		# self.set_type_hint(gdk.WindowTypeHint.)
		# https://docs.gtk.org/gdk3/enum.WindowTypeHint.html
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

	def finish(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None:
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
		timeout_add(int(self.refreshTime), self.animateUpdate)
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
