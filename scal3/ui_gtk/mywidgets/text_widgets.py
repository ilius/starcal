from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import Menu, gtk
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import buffer_get_text, setClipboard
from scal3.utils import findWordByPos, toStr

if TYPE_CHECKING:
	from scal3.ui_gtk import gdk

__all__ = ["ReadOnlyTextView"]


class ReadOnlyTextView(gtk.TextView):
	def __init__(self) -> None:
		gtk.TextView.__init__(self)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.connect("button-press-event", self.onButtonPress)

	def copyAll(self, _w: gtk.Widget) -> None:
		setClipboard(self.get_text())

	# def cursorIsOnURL(self):
	# 	return False

	def get_text(self) -> str:
		return buffer_get_text(self.get_buffer())

	# def get_cursor_position(self):
	# 	return self.get_buffer().get_property("cursor-position")

	def has_selection(self) -> bool:
		buf = self.get_buffer()
		try:
			buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def copy(self, _w: gtk.Widget, *_args: Any) -> None:
		buf = self.get_buffer()
		bounds = buf.get_selection_bounds()
		if not bounds:
			return
		start_iter, end_iter = bounds
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	# def copyWordByIter(self, _item, gIter):
	# 	text = self.get_text()
	# 	pos = gIter.get_offset()
	# 	word = findWordByPos(text, pos)[0]
	# 	setClipboard(word)

	@classmethod
	def copyText(cls, _w: gtk.Widget, text: str, *_args: Any) -> None:
		setClipboard(text)

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		if gevent.button != 3:
			return False
		# ----
		iter_ = None
		buf_x, buf_y = self.window_to_buffer_coords(
			gtk.TextWindowType.TEXT,
			int(gevent.x),
			int(gevent.y),
		)
		if buf_x is not None and buf_y is not None:
			# overText, iter_, trailing = ...
			iter_ = self.get_iter_at_position(buf_x, buf_y)[1]
		# ----
		text = self.get_text()
		if iter_ is not None:
			word = findWordByPos(text, iter_.get_offset())[0]
		else:
			word = ""
		# ----
		menu = Menu()
		# ----
		menu.add(
			ImageMenuItem(
				_("Copy _All"),
				imageName="edit-copy.svg",
				onActivate=self.copyAll,
			),
		)
		# ----
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			onActivate=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)

		# ----

		def copyWord(w: gtk.Widget) -> None:
			self.copyText(w, word)

		if "://" in word:
			menu.add(
				ImageMenuItem(
					_("Copy _URL"),
					imageName="edit-copy.svg",
					onActivate=copyWord,
				),
			)
		# ----
		menu.show_all()
		menu.popup(
			None,
			None,
			None,
			None,
			3,
			gevent.time,
		)
		ui.updateFocusTime()
		return True
