# -*- coding: utf-8 -*-

from scal3.core import jd_to
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets import MyColorButton
from scal3.ui_gtk.mywidgets.multi_spin.date import DateButton
from scal3.ui_gtk.event import common
from scal3.ui_gtk.event.group.base import BaseWidgetClass
from scal3.ui_gtk.event.account import AccountCombo, AccountGroupBox


class WidgetClass(BaseWidgetClass):
	def __init__(self, group):
		BaseWidgetClass.__init__(self, group)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_("Start"))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.startDateInput = DateButton()
		pack(hbox, self.startDateInput)
		pack(self, hbox)
		###
		hbox = gtk.HBox()
		label = gtk.Label(_("End"))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		self.sizeGroup.add_widget(label)
		self.endDateInput = DateButton()
		pack(hbox, self.endDateInput)
		pack(self, hbox)
		######
		exp = gtk.Expander()
		exp.set_label(_("Online Service"))
		vbox = gtk.VBox()
		exp.add(vbox)
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		##
		hbox = gtk.HBox()
		label = gtk.Label(_("Account"))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		sizeGroup.add_widget(label) ## FIXME
		self.accountCombo = AccountCombo()
		pack(hbox, self.accountCombo)
		pack(vbox, hbox)
		##
		hbox = gtk.HBox()
		label = gtk.Label(_("Remote Group"))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		sizeGroup.add_widget(label) ## FIXME
		accountGroupBox = AccountGroupBox(self.accountCombo)
		pack(hbox, accountGroupBox, 1, 1)
		pack(vbox, hbox)
		self.accountGroupCombo = accountGroupBox.combo
		##
		hbox = gtk.HBox()
		self.syncCheck = gtk.CheckButton(_("Synchronization Interval"))
		pack(hbox, self.syncCheck)
		sizeGroup.add_widget(self.syncCheck)
		self.syncIntervalInput = common.DurationInputBox()
		pack(hbox, self.syncIntervalInput)
		pack(hbox, gtk.Label(""), 1, 1)
		pack(vbox, hbox)
		self.syncCheck.connect(
			"clicked",
			lambda check: self.syncIntervalInput.set_sensitive(check.get_active()),
		)
		##
		pack(self, exp)

	def updateWidget(self):
		BaseWidgetClass.updateWidget(self)
		self.startDateInput.set_value(jd_to(
			self.group.startJd,
			self.group.mode,
		))
		self.endDateInput.set_value(jd_to(
			self.group.endJd,
			self.group.mode,
		))
		###
		if self.group.remoteIds:
			aid, gid = self.group.remoteIds
		else:
			aid, gid = None, None
		self.accountCombo.set_active(aid)
		self.accountGroupCombo.set_active(gid)
		self.syncCheck.set_active(self.group.remoteSyncEnable)
		self.syncIntervalInput.set_sensitive(self.group.remoteSyncEnable)

		value, unit = self.group.remoteSyncDuration
		self.syncIntervalInput.setDuration(value, unit)

	def updateVars(self):
		BaseWidgetClass.updateVars(self)
		self.group.startJd = self.startDateInput.get_jd(self.group.mode)
		self.group.endJd = self.endDateInput.get_jd(self.group.mode)
		###
		aid = self.accountCombo.get_active()
		if aid:
			gid = self.accountGroupCombo.get_active()
			self.group.remoteIds = aid, gid
		else:
			self.group.remoteIds = None
		self.group.remoteSyncEnable = self.syncCheck.get_active()
		self.group.remoteSyncDuration = self.syncIntervalInput.getDuration()

	def modeComboChanged(self, obj=None):
		newMode = self.modeCombo.get_active()
		self.startDateInput.changeMode(self.group.mode, newMode)
		self.endDateInput.changeMode(self.group.mode, newMode)
		self.group.mode = newMode
