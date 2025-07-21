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

from scal3 import logger
from scal3.color_utils import RGBA

log = logger.get()

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk, pango
from scal3.ui_gtk.color_utils import rgbaToGdkRGBA
from scal3.ui_gtk.drawing import newDndFontNamePixbuf
from scal3.ui_gtk.font_utils import gfontDecode, gfontEncode
from scal3.ui_gtk.utils import buffer_get_text

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.color_utils import RGB, RawColor
	from scal3.font import Font

__all__ = ["MyColorButton", "MyFontButton", "TextFrame"]


class MyFontButton(gtk.FontButton):
	def __init__(self, dragAndDrop: bool = True) -> None:
		gtk.FontButton.__init__(self)
		if dragAndDrop:
			self.setupDragAndDrop()

	def setupDragAndDrop(self) -> None:
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

	@staticmethod
	def dragDataGet(
		fontb: MyFontButton,
		_context: gdk.DragContext,
		selection: gtk.SelectionData,
		_info: int,  # or _target_id?
		_etime: int,
	) -> bool:
		# print(f"fontButtonDragDataGet: {fontb=}, {fontb.getFont()=}")
		valueStr = gfontEncode(fontb.getFont())
		valueBytes = valueStr.encode("utf-8")
		selection.set_text(valueStr, len(valueBytes))
		return True

	def dragDataRec(
		self,
		fontb: gtk.FontButton,
		_context: gdk.DragContext,
		_x: int,
		_y: int,
		selection: gtk.SelectionData,
		_target_id: int,
		_etime: int,
	) -> bool:
		# dtype = selection.get_data_type()
		# log.debug(dtype # UTF8_STRING)
		text = selection.get_text()
		log.debug(f"fontButtonDragDataRec    {text=}")
		if text:
			pfont = pango.FontDescription.from_string(text)
			if pfont.get_family() and pfont.get_size() > 0:
				gtk.FontButton.set_font(fontb, text)
				self.emit("font-set")
		return True

	def dragBegin(self, _fontb: gtk.FontButton, context: gdk.DragContext) -> bool:
		# log.debug("fontBottonDragBegin"-- caled before dragCalDataGet)
		fontName = gtk.FontButton.get_font(self)
		if fontName is None:
			return True
		pbuf = newDndFontNamePixbuf(fontName)
		w = pbuf.get_width()
		# h = pbuf.get_height()
		gtk.drag_set_icon_pixbuf(
			context,
			pbuf,
			int(w // 2),
			-10,
		)
		return True

	def getFont(self) -> Font:
		return gfontDecode(gtk.FontButton.get_font(self) or "")

	def setFont(self, font: Font) -> None:
		# assert isinstance(font, Font), f"{font=}"
		gtk.FontButton.set_font(self, gfontEncode(font))


class MyColorButton(gtk.ColorButton):
	# for tooltip text
	def __init__(self) -> None:
		gtk.ColorButton.__init__(self)
		gtk.ColorChooser.set_use_alpha(self, True)
		self.connect("color-set", self.update_tooltip)

	def update_tooltip(self, _colorb: gtk.Widget | None = None) -> None:
		r, g, b, a = self.getRGBA()
		if gtk.ColorChooser.get_use_alpha(self):
			text = (
				f"{_('Red')}: {_(r)}\n{_('Green')}: "
				f"{_(g)}\n{_('Blue')}: {_(b)}\n{_('Opacity')}: {_(a)}"
			)
		else:
			text = f"{_('Red')}: {_(r)}\n{_('Green')}: {_(g)}\n{_('Blue')}: {_(b)}"
		# self.get_tooltip_window().set_direction(gtk.TextDirection.LTR)
		# log.debug(self.get_tooltip_window())
		self.set_tooltip_text(text)  # ???????????????? Right to left
		# self.tt_label.set_label(text)--???????????? Dosent work
		# self.set_tooltip_window(self.tt_win)

	# color is a tuple of (r, g, b) or (r, g, b, a)
	def setRGBA(self, color: RGB | RGBA | RawColor) -> None:
		gtk.ColorButton.set_rgba(self, rgbaToGdkRGBA(*color))
		self.update_tooltip()

	def getRGBA(self) -> RGBA:
		color = gtk.ColorButton.get_rgba(self)
		return RGBA(
			int(color.red * 255),
			int(color.green * 255),
			int(color.blue * 255),
			int(color.alpha * 255),
		)


class TextFrame(gtk.Frame):
	def __init__(
		self, onTextChange: Callable[[gtk.Widget], None] | None = None
	) -> None:
		gtk.Frame.__init__(self)
		self.set_border_width(4)
		# ----
		self.textview = gtk.TextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.add(self.textview)
		# ----
		self.buff = self.textview.get_buffer()
		if onTextChange is not None:
			self.buff.connect("changed", onTextChange)

	def set_text(self, text: str) -> None:
		self.buff.set_text(text)

	def get_text(self) -> str:
		return buffer_get_text(self.buff)
