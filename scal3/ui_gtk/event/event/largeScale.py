#!/usr/bin/env python
# -*- coding: utf-8 -*-
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.multi_spin.integer import IntSpinButton
from scal3.ui_gtk.event import common

maxStart = 999999
maxDur = 99999

class WidgetClass(common.WidgetClass):
	def __init__(self, event):## FIXME
		common.WidgetClass.__init__(self, event)
		######
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		######
		hbox = gtk.HBox()
		label = gtk.Label(_('Scale'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.scaleCombo = common.Scale10PowerComboBox()
		pack(hbox, self.scaleCombo)
		pack(self, hbox)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_('Start'))
		label.set_alignment(0, 0.5)
		sizeGroup.add_widget(label)
		pack(hbox, label)
		self.startSpin = IntSpinButton(-maxStart, maxStart)
		self.startSpin.connect('changed', self.startSpinChanged)
		pack(hbox, self.startSpin)
		pack(self, hbox)
		####
		hbox = gtk.HBox()
		self.endRelCombo = gtk.ComboBoxText()
		for item in ('Duration', 'End'):
			self.endRelCombo.append_text(_(item))
		self.endRelCombo.connect('changed', self.endRelComboChanged)
		sizeGroup.add_widget(self.endRelCombo)
		pack(hbox, self.endRelCombo)
		self.endSpin = IntSpinButton(-maxDur, maxDur)
		pack(hbox, self.endSpin)
		pack(self, hbox)
		####
		self.endRelComboChanged()
	def endRelComboChanged(self, combo=None):
		rel = self.endRelCombo.get_active()
		start = self.startSpin.get_value()
		end = self.endSpin.get_value()
		if rel==0:## reletive(duration)
			self.endSpin.set_range(1, maxStart)
			self.endSpin.set_value(max(1, end-start))
		elif rel==1:## absolute(end)
			self.endSpin.set_range(start+1, maxStart)
			self.endSpin.set_value(max(start+1, start+end))
	def startSpinChanged(self, spin=None):
		if self.endRelCombo.get_active() == 1:## absolute(end)
			self.endSpin.set_range(self.startSpin.get_value()+1, maxStart)
	def updateWidget(self):
		common.WidgetClass.updateWidget(self)
		self.scaleCombo.set_value(self.event.scale)
		self.startSpin.set_value(self.event.start)
		self.endRelCombo.set_active(0 if self.event.endRel else 1)
		self.endSpin.set_value(self.event.end)
	def updateVars(self):## FIXME
		common.WidgetClass.updateVars(self)
		self.event.scale = self.scaleCombo.get_value()
		self.event.start = self.startSpin.get_value()
		self.event.endRel = (self.endRelCombo.get_active()==0)
		self.event.end = self.endSpin.get_value()



if __name__=='__main__':
	combo = Scale10PowerComboBox()
	combo.set_value(200)
	win = gtk.Dialog(parent=None)
	pack(win.vbox, combo)
	win.vbox.show_all()
	win.run()
	print(combo.get_value())




