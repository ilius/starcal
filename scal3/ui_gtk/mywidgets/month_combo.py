from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack

__all__ = ["MonthComboBox"]


class MonthComboBox(gtk.ComboBox):
	def __init__(self, includeEvery: bool = False) -> None:
		self.includeEvery = includeEvery
		# ---
		ls = gtk.ListStore(str)
		gtk.ComboBox.__init__(self)
		self.set_model(ls)
		# ---
		cell = gtk.CellRendererText()
		pack(self, cell, True)
		self.add_attribute(cell, "text", 0)

	def build(self, calType: int) -> None:
		active = self.get_active()
		ls = self.get_model()
		ls.clear()
		if self.includeEvery:
			ls.append([_("Every Month")])
		for m in range(1, 13):
			ls.append([locale_man.getMonthName(calType, m)])
		if active is not None:
			self.set_active(active)

	def getValue(self) -> int:
		a = self.get_active()
		if self.includeEvery:
			return a
		return a + 1

	def setValue(self, value: int) -> None:
		if self.includeEvery:
			self.set_active(value)
		else:
			self.set_active(value - 1)
