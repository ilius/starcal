#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join, dirname

from scal2 import core
from scal2.locale_man import tr as _
from scal2.core import pixDir

from scal2 import event_man
from scal2 import ui

from scal2.ui_gtk.event_extenders.common import buffer_get_text, IconSelectButton, TagsListBox

import gtk
from gtk import gdk



class CustomEventWidget(gtk.VBox):
    groups = [gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL), gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)]
    def __init__(self, event, autoCheck=True):
        gtk.VBox.__init__(self)
        ################
        self.event = event
        self.autoCheck = autoCheck
        ######
        self.ruleAddBox = gtk.HBox()
        self.warnLabel = gtk.Label()
        self.warnLabel.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(-1, 0, 0))
        self.warnLabel.set_alignment(0, 0.5)
        #self.warnLabel.set_visible(False)## FIXME
        ###########
        self.notifiersHboxDict = {}
        notifiersBox = gtk.VBox()
        for cls in event_man.eventNotifiersClassList:
            notifier = cls(self.event)
            inputWidget = notifier.makeWidget()
            hbox = gtk.HBox()
            cb = gtk.CheckButton(notifier.desc)
            cb.inputWidget = inputWidget
            cb.connect('clicked', lambda check: check.inputWidget.set_sensitive(check.get_active()))
            cb.set_active(False)
            hbox.pack_start(cb, 0, 0)
            hbox.cb = cb
            #hbox.pack_start(gtk.Label(''), 1, 1)
            hbox.pack_start(inputWidget, 1, 1)
            hbox.inputWidget = inputWidget
            self.notifiersHboxDict[notifier.name] = hbox
            notifiersBox.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        ###
        self.enableCheck = gtk.CheckButton(_('Enable'))
        self.enableCheck.set_active(True)
        hbox.pack_start(self.enableCheck, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        hbox.pack_start(gtk.Label(_('Calendar Type')+':'), 0, 0)
        combo = gtk.combo_box_new_text()
        for module in core.modules:
            combo.append_text(_(module.desc))
        combo.set_active(core.primaryMode)
        hbox.pack_start(combo, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        self.modeCombo = combo
        ###
        hbox.pack_start(gtk.Label(_('Icon')+':'), 0, 0)
        self.iconSelect = IconSelectButton()
        #print join(pixDir, self.defaultIcon)
        hbox.pack_start(self.iconSelect, 0, 0)
        hbox.pack_start(gtk.Label(''), 1, 1)
        ###
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Summary')), 0, 0)
        self.summuryEntry = gtk.Entry()
        hbox.pack_start(self.summuryEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_('Description')), 0, 0)
        textview = gtk.TextView()
        textview.set_wrap_mode(gtk.WRAP_WORD)
        self.descriptionBuff = textview.get_buffer()
        hbox.pack_start(textview, 1, 1)
        self.pack_start(hbox, 0, 0)
        ###########
        '''
        hbox = gtk.HBox()
        hbox.set_tooltip_text(_('Seperate tags using character |'))
        hbox.pack_start(gtk.Label(_('Tags')), 0, 0)
        self.tagsEntry = gtk.Entry()
        hbox.pack_start(self.tagsEntry, 1, 1)
        self.pack_start(hbox, 0, 0)
        '''
        exp = gtk.Expander(_('Tags'))
        exp.set_expanded(True)
        self.tagsBox = TagsListBox()
        exp.add(self.tagsBox)
        self.pack_start(exp, 1, 1)
        ###########
        self.rulesFrame = gtk.Expander(_('Rules'))
        self.rulesFrame.set_expanded(True)
        self.pack_start(self.rulesFrame, 0, 0)
        ###
        self.pack_start(self.ruleAddBox, 0, 0)
        self.pack_start(self.warnLabel, 0, 0)
        ###
        notifiersFrame = gtk.Expander(_('Notifiers'))
        notifiersFrame.add(notifiersBox)
        notifiersFrame.set_expanded(True)
        self.pack_start(notifiersFrame, 0, 0)
        ###########
        self.rulesModel = gtk.ListStore(str, str)
        self.addRuleCombo = gtk.ComboBox(self.rulesModel)
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
        self.updateWidget()
        #############
        self.modeCombo.connect('changed', self.modeComboChanged)
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
        self.rulesBox = gtk.VBox()
        comboItems = [ruleClass.name for ruleClass in event_man.eventRulesClassList]
        for rule in self.event.rules:
            hbox = self.makeRuleHbox(rule)
            self.rulesBox.pack_start(hbox, 0, 0)
            comboItems.remove(rule.name)
        self.rulesFrame.add(self.rulesBox)
        for ruleName in comboItems:
            self.rulesModel.append((ruleName, event_man.eventRulesClassDict[ruleName].desc))
    def updateRules(self):
        self.event.rules = []
        for hbox in self.rulesBox.get_children():
            hbox.inputWidget.updateVars()
            self.event.rules.append(hbox.inputWidget.rule)
    def updateNotifiersWidget(self):
        for hbox in self.notifiersHboxDict.values():
            hbox.cb.set_active(False)
            hbox.inputWidget.set_sensitive(False)
        for notifier in self.event.notifiers:
            hbox = self.notifiersHboxDict[notifier.name]
            hbox.cb.set_active(True)
            hbox.inputWidget.set_sensitive(True)
            hbox.inputWidget.notifier = notifier
            hbox.inputWidget.updateWidget()
    def updateNotifiers(self):
        self.event.notifiers = []
        for hbox in self.notifiersHboxDict.values():
            if hbox.cb.get_active():
                hbox.inputWidget.updateVars()
                self.event.notifiers.append(hbox.inputWidget.notifier)
    def updateWidget(self):
        ## self.enableCheck  self.modeCombo  self.iconSelect  self.summuryEntry  self.descriptionBuff
        self.enableCheck.set_active(self.event.enable)
        self.modeCombo.set_active(self.event.mode)
        self.iconSelect.set_filename(self.event.icon)
        self.summuryEntry.set_text(self.event.summary)
        self.descriptionBuff.set_text(self.event.description)
        ####
        if hasattr(self, 'rulesBox'):
            self.rulesBox.destroy()
        self.rulesModel.clear()
        self.updateRulesWidget()
        ####
        self.updateNotifiersWidget()
    def updateVars(self):
        self.event.enable = self.enableCheck.get_active()
        self.event.mode = self.modeCombo.get_active()
        self.event.icon = self.iconSelect.get_filename()
        self.event.summary = self.summuryEntry.get_text()
        self.event.description = buffer_get_text(self.descriptionBuff)
        ####
        self.updateRules()
        self.updateNotifiers()
    def modeComboChanged(self, combo):## FIXME
        newMode = combo.get_active()
        for hbox in self.rulesBox.get_children():
            widget = hbox.inputWidget
            if hasattr(widget, 'changeMode'):
                widget.changeMode(newMode)
        self.event.mode = newMode
    def removeButtonClicked(self, button, hbox):
        rule = hbox.inputWidget.rule
        (ok, msg) = self.event.checkRulesDependencies(disabledRule=rule)
        self.warnLabel.set_label(msg)
        if not ok:
            return
        self.event.rules.remove(rule)
        ####
        self.rulesModel.append((rule.name, rule.desc))
        ####
        hbox.destroy()
        #self.rulesBox.remove(hbox)
        self.addRuleComboChanged()
    def addRuleComboChanged(self, combo=None):
        ci = self.addRuleCombo.get_active()
        if ci==None or ci<0:
            return
        newRuleName = self.rulesModel[ci][0]
        newRule = event_man.eventRulesClassDict[newRuleName](self.event)
        (ok, msg) = self.event.checkRulesDependencies(newRule=newRule)
        self.warnLabel.set_label(msg)
    def addClicked(self, button):
        ci = self.addRuleCombo.get_active()
        if ci==None or ci<0:
            return
        ruleName = self.rulesModel[ci][0]
        rule = event_man.eventRulesClassDict[ruleName](self.event)
        (ok, msg) = self.event.addRule(rule)
        if not ok:
            return
        hbox = self.makeRuleHbox(rule)
        self.rulesBox.pack_start(hbox, 0, 0)
        del self.rulesModel[ci]
        n = len(self.rulesModel)
        if ci==n:
            self.addRuleCombo.set_active(ci-1)
        else:
            self.addRuleCombo.set_active(ci)
        hbox.show_all()


event_man.Event.WidgetClass = CustomEventWidget


