#!/usr/bin/env python3
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from scal3.cal_types import convert
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	def __init__(self, event):
		common.WidgetClass.__init__(self, event)
		###
		hbox = HBox()
		pack(hbox, gtk.Label(label=_("Date")))
		self.dateInput = DateButton()
		pack(hbox, self.dateInput)
		pack(self, hbox)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)

	def updateWidget(self):
		common.WidgetClass.updateWidget(self)
		self.dateInput.set_value(self.event.getDate())

	def updateVars(self):
		common.WidgetClass.updateVars(self)
		self.event.setDate(*self.dateInput.get_value())

	def calTypeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		self.dateInput.changeCalType(self.event.calType, newCalType)
		self.event.calType = newCalType
