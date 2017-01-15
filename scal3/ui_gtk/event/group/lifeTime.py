from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass


class WidgetClass(NormalWidgetClass):
	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		####
		hbox = gtk.HBox()
		self.showSeperatedYmdInputsCheck = gtk.CheckButton(_(
			"Show Seperated Inputs for Year, Month and Day"
		))
		pack(hbox, self.showSeperatedYmdInputsCheck)
		pack(hbox, gtk.Label(""), 1, 1)
		pack(self, hbox)

	def updateWidget(self):
		NormalWidgetClass.updateWidget(self)
		self.showSeperatedYmdInputsCheck.set_active(
			self.group.showSeperatedYmdInputs
		)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		self.group.showSeperatedYmdInputs = \
			self.showSeperatedYmdInputsCheck.get_active()
