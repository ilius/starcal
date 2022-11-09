#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.event.group.base import BaseWidgetClass
from scal3.ui_gtk.event import common


maxStartEnd = 999999


class WidgetClass(BaseWidgetClass):
	def addStartEndWidgets(self):
		group = self.group
		######
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = HBox()
		label = gtk.Label(label=_("Scale"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.scaleCombo = common.Scale10PowerComboBox()
		pack(hbox, self.scaleCombo)
		pack(self, hbox)
		hbox.show_all()
		####
		hbox = HBox()
		label = gtk.Label(label=_("Start"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.startSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
		pack(hbox, self.startSpin)
		pack(self, hbox)
		hbox.show_all()
		####
		hbox = HBox()
		label = gtk.Label(label=_("End"))
		label.set_xalign(0)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.endSpin = IntSpinButton(-maxStartEnd, maxStartEnd)
		pack(hbox, self.endSpin)
		pack(self, hbox)
		hbox.show_all()

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
