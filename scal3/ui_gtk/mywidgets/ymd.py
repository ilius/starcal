from scal3.cal_types import calTypes
from scal3 import core
from scal3.core import getMonthLen
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.year import YearSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton

class YearMonthDayBox(gtk.HBox):
	def __init__(self):
		gtk.HBox.__init__(self, spacing=4)
		self.mode = calTypes.primary
		####
		pack(self, gtk.Label(_('Year')))
		self.spinY = YearSpinButton()
		pack(self, self.spinY)
		####
		pack(self, gtk.Label(_('Month')))
		comboMonth = gtk.ComboBoxText()
		module = calTypes[self.mode]
		for i in range(12):
			comboMonth.append_text(_(module.getMonthName(i+1, None)))## year=None means all months
		comboMonth.set_active(0)
		pack(self, comboMonth)
		self.comboMonth = comboMonth
		####
		pack(self, gtk.Label(_('Day')))
		self.spinD = DaySpinButton()
		pack(self, self.spinD)
		self.comboMonthConn = comboMonth.connect('changed', self.comboMonthChanged)
		self.spinY.connect('changed', self.comboMonthChanged)
	def set_mode(self, mode):
		self.comboMonth.disconnect(self.comboMonthConn)
		self.mode = mode
		module = calTypes[mode]
		combo = self.comboMonth
		combo.remove_all()
		for i in range(12):
			combo.append_text(_(module.getMonthName(i+1)))
		self.spinD.set_range(1, module.maxMonthLen)
		self.comboMonthConn = self.comboMonth.connect('changed', self.comboMonthChanged)
	def changeMode(self, mode, newMode):## FIXME naming standard?
		self.set_mode(newMode)
	def set_value(self, date):
		y, m, d = date
		self.spinY.set_value(y)
		self.comboMonth.set_active(m-1)
		self.spinD.set_value(d)
	get_value = lambda self: (
		self.spinY.get_value(),
		self.comboMonth.get_active() + 1,
		self.spinD.get_value(),
	)
	def comboMonthChanged(self, widget=None):
		monthIndex = self.comboMonth.get_active()
		if monthIndex == -1:
			return
		self.spinD.set_range(1, getMonthLen(
			self.spinY.get_value(),
			monthIndex + 1,
			self.mode,
		))








