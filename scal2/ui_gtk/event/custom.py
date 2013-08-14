# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2012 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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


from os.path import join, dirname

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir

from scal2 import event_lib
from scal2 import ui

from scal2.ui_gtk.event import common

import gtk
from gtk import gdk


class EventWidget(common.EventWidget):
    groups = [gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL), gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)]
    def __init__(self, event, autoCheck=True):
        common.EventWidget.__init__(self, event)
        ################
        self.autoCheck = autoCheck
        ######
        self.ruleAddBox = gtk.HBox()
        self.warnLabel = gtk.Label()
        self.warnLabel.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(-1, 0, 0))
        self.warnLabel.set_alignment(0, 0.5)
        #self.warnLabel.set_visible(False)## FIXME
        ###########
        self.rulesExp = gtk.Expander(_('Rules'))
        self.rulesExp.set_expanded(True)
        self.rulesBox = gtk.VBox()
        self.rulesExp.add(self.rulesBox)
        self.pack_start(self.rulesExp, 0, 0)
        ###
        self.pack_start(self.ruleAddBox, 0, 0)
        self.pack_start(self.warnLabel, 0, 0)
        ###
        self.notificationBox = common.NotificationBox(event)
        self.pack_start(self.notificationBox, 0, 0)
        ###########
        self.addRuleModel = gtk.ListStore(str, str)
        self.addRuleCombo = gtk.ComboBox(self.addRuleModel)
        ###
        cell = gtk.CellRendererText()
        self.addRuleCombo.pack_start(cell, True)
        self.addRuleCombo.add_attribute(cell, 'text', 1)
        ###
        self.ruleAddBox.pack_start(gtk.Label(_('Add Rule')+':'), 0, 0)
        self.ruleAddBox.pack_start(self.addRuleCombo, 0, 0)
        self.ruleAddBox.pack_start(gtk.Label(''), 1, 1)
        self.ruleAddButton = gtk.Button(stock=gtk.STOCK_ADD)
        if ui.autoLocale:
            self.ruleAddButton.set_label(_('_Add'))
            self.ruleAddButton.set_image(gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON))
        self.ruleAddBox.pack_start(self.ruleAddButton, 0, 0)
        #############
        #self.filesBox = common.FilesBox(self.event)
        #self.pack_start(self.filesBox, 0, 0)
        #############
        self.addRuleCombo.connect('changed', self.addRuleComboChanged)
        self.ruleAddButton.connect('clicked', self.addClicked)
    def makeRuleHbox(self, rule):
        hbox = gtk.HBox(spacing=5)
        lab = gtk.Label(rule.desc)
        lab.set_alignment(0, 0.5)
        hbox.pack_start(lab, 0, 0)
        self.groups[rule.sgroup].add_widget(lab)
        #hbox.pack_start(gtk.Label(''), 1, 1)
        inputWidget = rule.makeWidget()
        if rule.expand:
            hbox.pack_start(inputWidget, 1, 1)
        else:
            hbox.pack_start(inputWidget, 0, 0)
            hbox.pack_start(gtk.Label(''), 1, 1)
        ####
        removeButton = gtk.Button(stock=gtk.STOCK_REMOVE)
        if ui.autoLocale:
            removeButton.set_label(_('_Remove'))
            removeButton.set_image(gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_BUTTON))
        removeButton.connect('clicked', self.removeButtonClicked, hbox)## FIXME
        hbox.pack_start(removeButton, 0, 0)
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
            self.rulesBox.pack_start(hbox, 0, 0)
            #hbox.show_all()
            comboItems.remove(rule.name)
        self.rulesBox.show_all()
        for ruleName in comboItems:
            self.addRuleModel.append((ruleName, event_lib.classes.rule.byName[ruleName].desc))
        self.addRuleComboChanged()
    def updateRules(self):
        self.event.clearRules()
        for hbox in self.rulesBox.get_children():
            hbox.inputWidget.updateVars()
            self.event.addRule(hbox.inputWidget.rule)
    def updateWidget(self):
        common.EventWidget.updateWidget(self)
        self.addRuleModel.clear()
        self.updateRulesWidget()
        self.notificationBox.updateWidget()
    def updateVars(self):
        common.EventWidget.updateVars(self)
        self.updateRules()
        self.notificationBox.updateVars()
    def modeComboChanged(self, obj=None):## overwrite method from common.EventWidget
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
        if ci==None or ci<0:
            return
        newRuleName = self.addRuleModel[ci][0]
        newRule = event_lib.classes.rule.byName[newRuleName](self.event)
        ok, msg = self.event.checkRulesDependencies(newRule=newRule)
        self.warnLabel.set_label(msg)
    def addClicked(self, button):
        ci = self.addRuleCombo.get_active()
        if ci==None or ci<0:
            return
        ruleName = self.addRuleModel[ci][0]
        rule = event_lib.classes.rule.byName[ruleName](self.event)
        ok, msg = self.event.checkAndAddRule(rule)
        if not ok:
            return
        hbox = self.makeRuleHbox(rule)
        self.rulesBox.pack_start(hbox, 0, 0)
        del self.addRuleModel[ci]
        n = len(self.addRuleModel)
        if ci==n:
            self.addRuleCombo.set_active(ci-1)
        else:
            self.addRuleCombo.set_active(ci)
        hbox.show_all()


