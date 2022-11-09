#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _
from scal3.vcs_modules import vcsModuleNames

from scal3.ui_gtk import *
from scal3.ui_gtk.event.group.group import WidgetClass as NormalWidgetClass


class VcsBaseWidgetClass(NormalWidgetClass):
	userCanAddEvents = False

	def __init__(self, group):
		NormalWidgetClass.__init__(self, group)
		######
		hbox = HBox()
		label = gtk.Label(label=_("VCS Type"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		self.vcsTypeCombo = gtk.ComboBoxText()
		for name in vcsModuleNames:
			self.vcsTypeCombo.append_text(name)## descriptive name FIXME
		pack(hbox, self.vcsTypeCombo)
		hbox.show_all()
		pack(self, hbox)
		######
		hbox = HBox()
		label = gtk.Label(label=_("Directory"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		self.dirEntry = gtk.Entry()
		hbox.show_all()
		pack(hbox, self.dirEntry)
		##
		#self.dirBrowse = gtk.Button(label=_("Browse"))
		hbox.show_all()
		pack(self, hbox)
		######
		hbox = HBox()
		label = gtk.Label(label=_("Branch"))
		label.set_xalign(0)
		self.sizeGroup.add_widget(label)
		pack(hbox, label)
		self.branchEntry = gtk.Entry()
		pack(hbox, self.branchEntry)
		hbox.show_all()
		pack(self, hbox)

	def updateWidget(self):
		NormalWidgetClass.updateWidget(self)
		self.vcsTypeCombo.set_active(vcsModuleNames.index(self.group.vcsType))
		self.dirEntry.set_text(self.group.vcsDir)
		self.branchEntry.set_text(self.group.vcsBranch)

	def updateVars(self):
		NormalWidgetClass.updateVars(self)
		self.group.vcsType = vcsModuleNames[self.vcsTypeCombo.get_active()]
		self.group.vcsDir = self.dirEntry.get_text()
		self.group.vcsBranch = self.branchEntry.get_text()
