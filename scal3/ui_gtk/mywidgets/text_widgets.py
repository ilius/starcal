#!/usr/bin/env python3
from scal3.utils import toStr
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	setClipboard,
	buffer_get_text,
)
from scal3.ui_gtk.menuitems import ImageMenuItem


class ReadOnlyTextWidget:
	def copyAll(self, item):
		return setClipboard(toStr(self.get_text()))

	def has_selection():
		raise NotImplementedError

	def onPopup(self, widget, menu):
		# instead of creating a new menu, we should remove all the
		# current items from current menu
		for item in menu.get_children():
			menu.remove(item)
		####
		menu.add(ImageMenuItem(
			_("Copy _All"),
			imageName="edit-copy.svg",
			func=self.copyAll,
		))
		####
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		if not self.has_selection():
			itemCopy.set_sensitive(False)
		menu.add(itemCopy)
		####
		menu.show_all()
		self.tmpMenu = menu
		ui.updateFocusTime()


class ReadOnlyLabel(gtk.Label, ReadOnlyTextWidget):
	def get_cursor_position(self):
		return self.get_property("cursor-position")

	def get_selection_bound(self):
		return self.get_property("selection-bound")

	def has_selection(self):
		return self.get_cursor_position() != self.get_selection_bound()

	def copy(self, item):
		bound = self.get_selection_bound()
		cursor = self.get_cursor_position()
		start = min(bound, cursor)
		end = max(bound, cursor)
		setClipboard(toStr(self.get_text())[start:end])

	def __init__(self, **kwargs):
		gtk.Label.__init__(self, **kwargs)
		self.set_selectable(True)## to be selectable, with visible cursor
		self.connect("populate-popup", self.onPopup)


class ReadOnlyTextView(gtk.TextView, ReadOnlyTextWidget):
	def get_text(self):
		return buffer_get_text(self.get_buffer())

	def get_cursor_position(self):
		return self.get_buffer().get_property("cursor-position")

	def has_selection(self):
		buf = self.get_buffer()
		try:
			start_iter, end_iter = buf.get_selection_bounds()
		except ValueError:
			return False
		else:
			return True

	def copy(self, item):
		buf = self.get_buffer()
		start_iter, end_iter = buf.get_selection_bounds()
		setClipboard(toStr(buf.get_text(start_iter, end_iter, True)))

	def __init__(self, *args, **kwargs):
		gtk.TextView.__init__(self, *args, **kwargs)
		self.set_editable(False)
		self.set_cursor_visible(False)
		self.connect("populate-popup", self.onPopup)
