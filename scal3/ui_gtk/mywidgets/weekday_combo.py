from scal3 import core
from scal3.ui_gtk import gtk, pack

__all__ = ["WeekDayComboBox"]


class WeekDayComboBox(gtk.ComboBox):
	def __init__(self) -> None:
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		self.firstWeekDay = core.firstWeekDay.v
		# ---
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 0)
		# ---
		for i in range(7):
			ls.append([core.weekDayName[(i + self.firstWeekDay) % 7]])
		self.set_active(0)

	def getValue(self):
		return (self.firstWeekDay + self.get_active()) % 7

	def setValue(self, value) -> None:
		self.set_active((value - self.firstWeekDay) % 7)
