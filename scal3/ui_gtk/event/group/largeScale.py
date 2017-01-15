from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.event.group.base import BaseWidgetClass
from scal3.ui_gtk.event import common


maxStartEnd = 999999


class WidgetClass(BaseWidgetClass):
	def __init__(self, group):
		BaseWidgetClass.__init__(self, group)
		######
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_("Scale"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.scaleCombo = common.Scale10PowerComboBox()
		pack(hbox, self.scaleCombo)
		pack(self, hbox)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_("Start"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.startSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
		pack(hbox, self.startSpin)
		pack(self, hbox)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_("End"))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.endSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
		pack(hbox, self.endSpin)
		pack(self, hbox)

	def updateWidget(self):
		BaseWidgetClass.updateWidget(self)
		self.scaleCombo.set_value(self.group.scale)
		self.startSpin.set_value(self.group.getStartValue())
		self.endSpin.set_value(self.group.getEndValue())

	def updateVars(self):
		BaseWidgetClass.updateVars(self)
		self.group.scale = self.scaleCombo.get_value()
		self.group.setStartValue(self.startSpin.get_value())
		self.group.setEndValue(self.endSpin.get_value())
