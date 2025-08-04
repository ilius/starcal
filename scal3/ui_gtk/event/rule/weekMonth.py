from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.mywidgets.month_combo import MonthComboBox
from scal3.ui_gtk.mywidgets.weekday_combo import WeekDayComboBox

__all__ = ["WidgetClass"]


class WidgetClass(gtk.Box):
	def __init__(self, rule):
		self.rule = rule
		# -----
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		# ---
		combo = gtk.ComboBoxText()
		for item in rule.wmIndexNames:
			combo.append_text(item)
		pack(self, combo)
		self.nthCombo = combo
		# ---
		combo = WeekDayComboBox()
		pack(self, combo)
		self.weekDayCombo = combo
		# ---
		pack(self, gtk.Label(label=_(" of ")))
		# ---
		combo = MonthComboBox(True)
		combo.build(rule.getCalType())
		pack(self, combo)
		self.monthCombo = combo

	def updateVars(self):
		self.rule.wmIndex = self.nthCombo.get_active()
		self.rule.weekDay = self.weekDayCombo.getValue()
		self.rule.month = self.monthCombo.getValue()

	def updateWidget(self):
		self.nthCombo.set_active(self.rule.wmIndex)
		self.weekDayCombo.setValue(self.rule.weekDay)
		self.monthCombo.setValue(self.rule.month)

	def changeCalType(self, calType):
		if calType == self.rule.getCalType():
			return
		self.monthCombo.build(calType)
