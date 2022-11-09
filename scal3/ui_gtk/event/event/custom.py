#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import labelImageButton
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	groups = [
		gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL),
		gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL),
	]
	expandDescription = False

	def __init__(self, event, autoCheck=True):
		common.WidgetClass.__init__(self, event)
		################
		self.autoCheck = autoCheck
		######
		self.ruleAddBox = HBox()
		self.warnLabel = gtk.Label()
		self.warnLabel.modify_fg(gtk.StateType.NORMAL, gdk.Color(65535, 0, 0))
		self.warnLabel.set_xalign(0)
		#self.warnLabel.set_visible(False)## FIXME
		###########
		self.rulesFrame = gtk.Frame()
		self.rulesFrame.set_label(_("Rules"))
		self.rulesFrame.set_border_width(1)
		self.rulesSwin = gtk.ScrolledWindow()
		self.rulesBox = VBox()
		self.rulesBox.set_border_width(5)
		self.rulesSwin.add(self.rulesBox)
		self.rulesFrame.add(self.rulesSwin)
		pack(self, self.rulesFrame, expand=True, fill=True)
		###
		pack(self, self.ruleAddBox)
		pack(self, self.warnLabel)
		###
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		###########
		self.addRuleModel = gtk.ListStore(str, str)
		self.ruleAddCombo = gtk.ComboBox()
		self.ruleAddCombo.set_model(self.addRuleModel)
		###
		cell = gtk.CellRendererText()
		pack(self.ruleAddCombo, cell, True)
		self.ruleAddCombo.add_attribute(cell, "text", 1)
		###
		pack(self.ruleAddBox, gtk.Label(label=_("Add Rule") + ":"))
		pack(self.ruleAddBox, self.ruleAddCombo)
		pack(self.ruleAddBox, gtk.Label(), 1, 1)
		self.ruleAddButton = labelImageButton(
			_("_Add"),
			"list-add.svg",
		)
		pack(self.ruleAddBox, self.ruleAddButton)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)
		#############
		self.ruleAddCombo.connect("changed", self.onRuleAddComboChanged)
		self.ruleAddButton.connect("clicked", self.onRuleAddButtonClick)

	def makeRuleHbox(self, rule):
		hbox = HBox(spacing=5)
		lab = gtk.Label(label=rule.desc)
		lab.set_xalign(0)
		pack(hbox, lab)
		self.groups[rule.sgroup].add_widget(lab)
		#pack(hbox, gtk.Label(), 1, 1)
		inputWidget = makeWidget(rule)
		if not inputWidget:
			log.error(f"failed to create inpout widget for rule {rule.name}")
			return
		if rule.expand:
			pack(hbox, inputWidget, 1, 1)
		else:
			pack(hbox, inputWidget)
			pack(hbox, gtk.Label(), 1, 1)
		####
		removeButton = labelImageButton(
			label=_("_Remove"),
			imageName="list-remove.svg",
		)
		removeButton.connect("clicked", self.onRemoveButtonClick, hbox)
		# ^ FIXME
		pack(hbox, removeButton)
		####
		hbox.inputWidget = inputWidget
		hbox.removeButton = removeButton
		return hbox

	def updateRulesWidget(self):
		for hbox in self.rulesBox.get_children():
			hbox.destroy()
		comboItems = [ruleClass.name for ruleClass in event_lib.classes.rule]
		for rule in self.event:
			hbox = self.makeRuleHbox(rule)
			if not hbox:
				continue
			pack(self.rulesBox, hbox)
			#hbox.show_all()
			comboItems.remove(rule.name)
		self.rulesBox.show_all()
		for ruleName in comboItems:
			self.addRuleModel.append((
				ruleName,
				event_lib.classes.rule.byName[ruleName].desc,
			))
		self.onRuleAddComboChanged()

	def updateRules(self):
		self.event.clearRules()
		for hbox in self.rulesBox.get_children():
			hbox.inputWidget.updateVars()
			self.event.addRule(hbox.inputWidget.rule)

	def updateWidget(self):
		common.WidgetClass.updateWidget(self)
		self.addRuleModel.clear()
		self.updateRulesWidget()
		self.notificationBox.updateWidget()

	def updateVars(self):
		common.WidgetClass.updateVars(self)
		self.updateRules()
		self.notificationBox.updateVars()

	def calTypeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.get_active()
		for hbox in self.rulesBox.get_children():
			widget = hbox.inputWidget
			if hasattr(widget, "changeCalType"):
				widget.changeCalType(newCalType)
		self.event.calType = newCalType

	def onRemoveButtonClick(self, button, hbox):
		rule = hbox.inputWidget.rule
		ok, msg = self.event.checkRulesDependencies(disabledRule=rule)
		self.warnLabel.set_label(msg)
		if not ok:
			return
		self.event.checkAndRemoveRule(rule)
		####
		self.addRuleModel.append((rule.name, rule.desc))
		####
		hbox.destroy()
		#self.rulesBox.remove(hbox)
		self.onRuleAddComboChanged()

	def onRuleAddComboChanged(self, combo=None):
		ci = self.ruleAddCombo.get_active()
		if ci is None or ci < 0:
			return
		newRuleName = self.addRuleModel[ci][0]
		newRule = self.event.create(newRuleName)
		ok, msg = self.event.checkRulesDependencies(newRule=newRule)
		self.warnLabel.set_label(msg)

	def onRuleAddButtonClick(self, button):
		ci = self.ruleAddCombo.get_active()
		if ci is None or ci < 0:
			return
		ruleName = self.addRuleModel[ci][0]
		rule = self.event.create(ruleName)
		ok, msg = self.event.checkAndAddRule(rule)
		if not ok:
			return
		hbox = self.makeRuleHbox(rule)
		if not hbox:
			return
		pack(self.rulesBox, hbox)
		del self.addRuleModel[ci]
		n = len(self.addRuleModel)
		if ci == n:
			self.ruleAddCombo.set_active(ci - 1)
		else:
			self.ruleAddCombo.set_active(ci)
		hbox.show_all()
