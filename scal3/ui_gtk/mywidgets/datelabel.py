from scal3.utils import toStr
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3 import ui
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import setClipboard

class DateLabel(gtk.Label):
	def __init__(self, text=None):
		gtk.Label.__init__(self, text)
		self.set_selectable(True)
		#self.set_cursor_visible(False)## FIXME
		self.set_can_focus(False)
		self.set_use_markup(True)
		self.connect('populate-popup', self.popupPopulate)
	def popupPopulate(self, label, menu):
		itemCopyAll = ImageMenuItem(_('Copy _All'))
		itemCopyAll.set_image(gtk.Image.new_from_stock(gtk.STOCK_COPY, gtk.IconSize.MENU))
		itemCopyAll.connect('activate', self.copyAll)
		##
		itemCopy = ImageMenuItem(_('_Copy'))
		itemCopy.set_image(gtk.Image.new_from_stock(gtk.STOCK_COPY, gtk.IconSize.MENU))
		itemCopy.connect('activate', self.copy)
		itemCopy.set_sensitive(self.get_property('cursor-position') > self.get_property('selection-bound'))## FIXME
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
		start = self.get_property('selection-bound')
		end = self.get_property('cursor-position')
		setClipboard(toStr(self.get_text())[start:end])
	copyAll = lambda self, label: setClipboard(self.get_text())

