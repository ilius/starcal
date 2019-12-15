#!/usr/bin/env python3
from scal3 import cal_types
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.year import YearSpinButton
from scal3.ui_gtk.mywidgets.multi_spin.day import DaySpinButton


class YearMonthDayBox(gtk.Box):
	def __init__(self):
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL, spacing=4)
		self.calType = calTypes.primary
		####
		pack(self, gtk.Label(label=_("Year")))
		self.spinY = YearSpinButton()
		pack(self, self.spinY)
		####
		pack(self, gtk.Label(label=_("Month")))
		comboMonth = gtk.ComboBoxText()
		module, ok = calTypes[self.calType]
		if not ok:
			raise RuntimeError(f"cal type {self.calType!r} not found")
		for i in range(12):
			comboMonth.append_text(_(module.getMonthName(
				i + 1,
				None,  # year=None means all months
			)))
		comboMonth.set_active(0)
		pack(self, comboMonth)
		self.comboMonth = comboMonth
		####
		pack(self, gtk.Label(label=_("Day")))
		self.spinD = DaySpinButton()
		pack(self, self.spinD)
		self.comboMonthConn = comboMonth.connect(
			"changed",
			self.comboMonthChanged,
		)
		self.spinY.connect("changed", self.comboMonthChanged)

	def setCalType(self, calType):
		self.comboMonth.disconnect(self.comboMonthConn)
		self.calType = calType
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError(f"cal type '{calType}' not found")
		combo = self.comboMonth
		combo.remove_all()
		for i in range(12):
			combo.append_text(_(module.getMonthName(i + 1)))
		self.spinD.set_range(1, module.maxMonthLen)
		self.comboMonthConn = self.comboMonth.connect(
			"changed",
			self.comboMonthChanged,
		)

	def changeCalType(self, calType, newCalType):## FIXME naming standard?
		self.setCalType(newCalType)

	def set_value(self, date):
		y, m, d = date
		self.spinY.set_value(y)
		self.comboMonth.set_active(m - 1)
		self.spinD.set_value(d)

	def get_value(self):
		return (
			self.spinY.get_value(),
			self.comboMonth.get_active() + 1,
			self.spinD.get_value(),
		)

	def comboMonthChanged(self, widget=None):
		monthIndex = self.comboMonth.get_active()
		if monthIndex == -1:
			return
		self.spinD.set_range(1, cal_types.getMonthLen(
			self.spinY.get_value(),
			monthIndex + 1,
			self.calType,
		))
