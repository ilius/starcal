from scal3 import core
from scal3.locale_man import tr as _
from scal3.ui_gtk import *


class WeekDayComboBox(gtk.ComboBox):
	def __init__(self):
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		self.firstWeekDay = core.firstWeekDay
		###
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, 'text', 0)
		###
		for i in range(7):
			ls.append([core.weekDayName[(i + self.firstWeekDay) % 7]])
		self.set_active(0)

	def getValue(self):
		return (self.firstWeekDay + self.get_active()) % 7

	def setValue(self, value):
		self.set_active((value - self.firstWeekDay) % 7)
