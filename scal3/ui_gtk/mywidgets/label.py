from __future__ import annotations

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import setClipboard
from scal3.utils import toStr

__all__ = ["SLabel"]


class SLabel(gtk.Label):

	"""
	Selectable Label with custom, localized and minimal menu
	for right-click, with only 2 menu items: Copy All, Copy.
	"""

	def __init__(self, label: str | None = None) -> None:
		gtk.Label.__init__(self, label=label)
		self.set_selectable(True)
		# self.set_cursor_visible(False)-- FIXME
		self.set_can_focus(False)
		self.set_use_markup(True)
		self.connect("populate-popup", self.popupPopulate)

	def popupPopulate(self, _label: gtk.Label, menu: gtk.Menu) -> None:
		itemCopyAll = ImageMenuItem(
			_("Copy _All"),
			imageName="edit-copy.svg",
			func=self.copyAll,
		)
		# --
		itemCopy = ImageMenuItem(
			_("_Copy"),
			imageName="edit-copy.svg",
			func=self.copy,
		)
		itemCopy.set_sensitive(
			self.get_property("cursor-position") > self.get_property("selection-bound"),
		)  # FIXME
		# --
		for item in menu.get_children():
			menu.remove(item)
		# --
		menu.add(itemCopyAll)
		menu.add(itemCopy)
		menu.show_all()
		# --
		ui.updateFocusTime()

	def copy(self, _item: gtk.MenuItem) -> None:
		start = self.get_property("selection-bound")
		end = self.get_property("cursor-position")
		setClipboard(toStr(self.get_text())[start:end])

	def copyAll(self, _label: gtk.Label) -> None:
		setClipboard(self.get_text())
