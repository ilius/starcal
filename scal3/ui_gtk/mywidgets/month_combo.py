from scal3 import core
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.ui_gtk import *

class MonthComboBox(gtk.ComboBox):
	def __init__(self, includeEvery=False):
		self.includeEvery = includeEvery
		###
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, 'text', 0)
	def build(self, mode):
		active = self.get_active()
		ls = self.get_model()
		ls.clear()
		if self.includeEvery:
			ls.append([_('Every Month')])
		for m in range(1, 13):
			ls.append([locale_man.getMonthName(mode, m)])
		if active is not None:
			self.set_active(active)
	def getValue(self):
		a = self.get_active()
		if self.includeEvery:
			return a
		else:
			return a + 1
	def setValue(self, value):
		if self.includeEvery:
			self.set_active(value)
		else:
			self.set_active(value - 1)

