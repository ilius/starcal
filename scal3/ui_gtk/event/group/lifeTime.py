#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass

class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		####
		hbox = HBox()
		self.showSeparatedYmdInputsCheck = gtk.CheckButton(label=_(
			"Show Separated Inputs for Year, Month and Day"
		))
		pack(hbox, self.showSeparatedYmdInputsCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self, hbox)
		hbox.show_all()

	def updateWidget(self):
		NormalWidgetClass.updateWidget(self)
		self.showSeparatedYmdInputsCheck.set_active(
			self.group.showSeparatedYmdInputs,
		)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		self.group.showSeparatedYmdInputs = \
			self.showSeparatedYmdInputsCheck.get_active()
