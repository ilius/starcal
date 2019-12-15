#!/usr/bin/env python3
from scal3.utils import toStr
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	setClipboard,
)
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)



class SLabel(gtk.Label):
	"""
		Selectable Label with custom, localized and minimal menu
		for right-click, with only 2 menu items: Copy All, Copy
	"""

	def __init__(self, label=None):
		gtk.Label.__init__(self, label=label)
		self.set_selectable(True)
		#self.set_cursor_visible(False)## FIXME
		self.set_can_focus(False)
		self.set_use_markup(True)
		self.connect("populate-popup", self.popupPopulate)

	def popupPopulate(self, label, menu):
		itemCopyAll = ImageMenuItem(
			_("Copy _All"),
			imageName="edit-copy.svg",
			func=self.copyAll
		)
		##
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		itemCopy.set_sensitive(
			self.get_property("cursor-position") >
			self.get_property("selection-bound")
		)  # FIXME
		##
		for item in menu.get_children():
			menu.remove(item)
		##
		menu.add(itemCopyAll)
		menu.add(itemCopy)
		menu.show_all()
		##
		ui.updateFocusTime()

	def copy(self, item):
		start = self.get_property("selection-bound")
		end = self.get_property("cursor-position")
		setClipboard(toStr(self.get_text())[start:end])

	def copyAll(self, label):
		setClipboard(self.get_text())
