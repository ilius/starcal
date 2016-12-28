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


from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event import common


class WidgetClass(common.WidgetClass):
	groups = [
		gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL),
		gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL),
	]

	def __init__(self, event, autoCheck=True):
		common.WidgetClass.__init__(self, event)
		################
		self.autoCheck = autoCheck
		######
		self.ruleAddBox = gtk.HBox()
		self.warnLabel = gtk.Label()
		self.warnLabel.modify_fg(gtk.StateType.NORMAL, gdk.Color(65535, 0, 0))
		self.warnLabel.set_alignment(0, 0.5)
		#self.warnLabel.set_visible(False)## FIXME
		###########
		self.rulesExp = gtk.Expander()
		self.rulesExp.set_label(_('Rules'))
		self.rulesExp.set_expanded(True)
		self.rulesBox = gtk.VBox()
		self.rulesExp.add(self.rulesBox)
		pack(self, self.rulesExp)
		###
		pack(self, self.ruleAddBox)
		pack(self, self.warnLabel)
		###
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		###########
		self.addRuleModel = gtk.ListStore(str, str)
		self.addRuleCombo = gtk.ComboBox()
		self.addRuleCombo.set_model(self.addRuleModel)
		###
		cell = gtk.CellRendererText()
		pack(self.addRuleCombo, cell, True)
		self.addRuleCombo.add_attribute(cell, 'text', 1)
		###
		pack(self.ruleAddBox, gtk.Label(_('Add Rule') + ':'))
		pack(self.ruleAddBox, self.addRuleCombo)
		pack(self.ruleAddBox, gtk.Label(''), 1, 1)
		self.ruleAddButton = gtk.Button(stock=gtk.STOCK_ADD)
		if ui.autoLocale:
			self.ruleAddButton.set_label(_('_Add'))
			self.ruleAddButton.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_ADD,
				gtk.IconSize.BUTTON,
			))
		pack(self.ruleAddBox, self.ruleAddButton)
		#############
		#self.filesBox = common.FilesBox(self.event)
		#pack(self, self.filesBox)
		#############
		self.addRuleCombo.connect('changed', self.addRuleComboChanged)
		self.ruleAddButton.connect('clicked', self.addClicked)

	def makeRuleHbox(self, rule):
		hbox = gtk.HBox(spacing=5)
		lab = gtk.Label(rule.desc)
		lab.set_alignment(0, 0.5)
		pack(hbox, lab)
		self.groups[rule.sgroup].add_widget(lab)
		#pack(hbox, gtk.Label(''), 1, 1)
		inputWidget = makeWidget(rule)
		if not inputWidget:
			print('failed to create inpout widget for rule %s' % rule.name)
			return
		if rule.expand:
			pack(hbox, inputWidget, 1, 1)
		else:
			pack(hbox, inputWidget)
			pack(hbox, gtk.Label(''), 1, 1)
		####
		removeButton = gtk.Button(stock=gtk.STOCK_REMOVE)
		if ui.autoLocale:
			removeButton.set_label(_('_Remove'))
			removeButton.set_image(gtk.Image.new_from_stock(
				gtk.STOCK_REMOVE,
				gtk.IconSize.BUTTON,
			))
		removeButton.connect('clicked', self.removeButtonClicked, hbox)## FIXME
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
		self.addRuleComboChanged()

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

	def modeComboChanged(self, obj=None):
		# overwrite method from common.WidgetClass
		newMode = self.modeCombo.get_active()
		for hbox in self.rulesBox.get_children():
			widget = hbox.inputWidget
			if hasattr(widget, 'changeMode'):
				widget.changeMode(newMode)
		self.event.mode = newMode

	def removeButtonClicked(self, button, hbox):
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
		self.addRuleComboChanged()

	def addRuleComboChanged(self, combo=None):
		ci = self.addRuleCombo.get_active()
		if ci is None or ci < 0:
			return
		newRuleName = self.addRuleModel[ci][0]
		newRule = event_lib.classes.rule.byName[newRuleName](self.event)
		ok, msg = self.event.checkRulesDependencies(newRule=newRule)
		self.warnLabel.set_label(msg)

	def addClicked(self, button):
		ci = self.addRuleCombo.get_active()
		if ci is None or ci < 0:
			return
		ruleName = self.addRuleModel[ci][0]
		rule = event_lib.classes.rule.byName[ruleName](self.event)
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
			self.addRuleCombo.set_active(ci - 1)
		else:
			self.addRuleCombo.set_active(ci)
		hbox.show_all()
