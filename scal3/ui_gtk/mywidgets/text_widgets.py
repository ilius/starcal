from __future__ import annotations

from typing import Never

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import Menu, gdk, gtk
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import buffer_get_text, setClipboard
from scal3.utils import findWordByPos, toStr

__all__ = ["ReadOnlyTextView"]


class ReadOnlyTextWidget:
	def copyAll(self, _item: gtk.MenuItem) -> None:
		setClipboard(toStr(self.get_text()))

	def has_selection() -> Never:
		raise NotImplementedError

	# def cursorIsOnURL(self):
	# 	return False


# class ReadOnlyLabel(gtk.Label, ReadOnlyTextWidget):
# 	def get_cursor_position(self):
# 		return self.get_property("cursor-position")

# 	def get_selection_bound(self):
# 		return self.get_property("selection-bound")

# 	def has_selection(self):
# 		return self.get_cursor_position() != self.get_selection_bound()

# 	def copy(self, _item) -> None:
# 		bound = self.get_selection_bound()
# 		cursor = self.get_cursor_position()
# 		start = min(bound, cursor)
# 		end = max(bound, cursor)
# 		setClipboard(toStr(self.get_text())[start:end])

# 	def onPopup(self, _widget, menu) -> None:
# 		# instead of creating a new menu, we should remove all the
# 		# current items from current menu
# 		for item in menu.get_children():
# 			menu.remove(item)
# 		# ----
# 		menu.add(
# 			ImageMenuItem(
# 				_("Copy _All"),
# 				imageName="edit-copy.svg",
# 				func=self.copyAll,
# 			),
# 		)
# 		# ----
# 		itemCopy = ImageMenuItem(
# 			_("_Copy"),
# 			imageName="edit-copy.svg",
# 			func=self.copy,
# 		)
# 		if not self.has_selection():
# 			itemCopy.set_sensitive(False)
# 		menu.add(itemCopy)
# 		# ----
# 		menu.show_all()
# 		self.tmpMenu = menu
# 		ui.updateFocusTime()

# 	def __init__(self, **kwargs) -> None:
# 		gtk.Label.__init__(self, **kwargs)
# 		self.set_selectable(True)  # to be selectable, with visible cursor
# 		self.connect("populate-popup", self.onPopup)


class ReadOnlyTextView(gtk.TextView, ReadOnlyTextWidget):
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

	def copy(self, _item: gtk.MenuItem) -> None:
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
	def copyText(cls, _item: gtk.MenuItem, text: str) -> None:
		setClipboard(text)

	def onButtonPress(self, _widget: gtk.Widget, gevent: gdk.Event) -> bool:
		if gevent.button != 3:
			return False
		# ----
		iter_ = None
		buf_x, buf_y = self.window_to_buffer_coords(
			gtk.TextWindowType.TEXT,
			gevent.x,
			gevent.y,
		)
		if buf_x is not None and buf_y is not None:
			# overText, iter_, trailing = ...
			iter_ = self.get_iter_at_position(buf_x, buf_y)[1]
		# ----
		text = self.get_text()
		pos = iter_.get_offset()
		word = findWordByPos(text, pos)[0]
		# ----
		menu = Menu()
		# ----
		menu.add(
			ImageMenuItem(
				_("Copy _All"),
				imageName="edit-copy.svg",
				func=self.copyAll,
			),
		)
		# ----
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)
		# ----
		if "://" in word:
			menu.add(
				ImageMenuItem(
					_("Copy _URL"),
					imageName="edit-copy.svg",
					func=self.copyText,
					args=(word,),
				),
			)
		# ----
		menu.show_all()
		self.tmpMenu = menu
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

	def __init__(self, *args, **kwargs) -> None:
		gtk.TextView.__init__(self, *args, **kwargs)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.connect("button-press-event", self.onButtonPress)
