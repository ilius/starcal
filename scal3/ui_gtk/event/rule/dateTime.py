from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.mywidgets.multi_spin.time_b import TimeButton


class WidgetClass(gtk.Box):
	def __init__(self, rule):
		self.rule = rule
		# ---
		gtk.ComboBox.__init__(self)
		# ---
		self.dateInput = DateButton()
		pack(self, self.dateInput)
		# ---
		pack(self, gtk.Label(label="   " + _("Time")))
		self.timeInput = TimeButton()
		pack(self, self.timeInput)

	def updateWidget(self):
		self.dateInput.set_value(self.rule.date)
		self.timeInput.set_value(self.rule.time)

	def updateVars(self):
		self.rule.date = self.dateInput.get_value()
		self.rule.time = self.timeInput.get_value()

	def changeCalType(self, calType):
		if calType == self.rule.getCalType():
			return
		self.updateVars()
		self.rule.changeCalType(calType)
		self.updateWidget()
