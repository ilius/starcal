#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

from scal3 import event_lib
from scal3.locale_man import tr as _
from scal3.ui_gtk import gdk, gtk, pack
from scal3.ui_gtk.event import common, makeWidget
from scal3.ui_gtk.utils import labelImageButton

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventRuleType, EventType
	from scal3.ui_gtk.event import EventWidgetType

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	groups = [
		gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL),
		gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL),
	]
	expandDescription = False

	def __init__(self, event: EventType, autoCheck: bool = True) -> None:
		common.WidgetClass.__init__(self, event)
		# ----------------
		self.autoCheck = autoCheck
		# ------
		self.ruleAddBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.warnLabel = gtk.Label()
		self.warnLabel.modify_fg(
			gtk.StateType.NORMAL,
			gdk.Color(65535, 0, 0),  # type: ignore[call-arg]
		)
		self.warnLabel.set_xalign(0)
		# self.warnLabel.set_visible(False)-- FIXME
		# -----------
		self.rulesFrame = gtk.Frame()
		self.rulesFrame.set_label(_("Rules"))
		self.rulesFrame.set_border_width(1)
		self.rulesSwin = gtk.ScrolledWindow()
		self.rulesBox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		self.rulesBox.set_border_width(5)
		self.rulesSwin.add(self.rulesBox)
		self.rulesFrame.add(self.rulesSwin)
		pack(self, self.rulesFrame, expand=True, fill=True)
		# ---
		pack(self, self.ruleAddBox)
		pack(self, self.warnLabel)
		# ---
		self.notificationBox = common.NotificationBox(event)
		pack(self, self.notificationBox)
		# -----------
		self.addRuleModel = gtk.ListStore(str, str)
		self.ruleAddCombo = gtk.ComboBox()
		self.ruleAddCombo.set_model(self.addRuleModel)
		# ---
		cell = gtk.CellRendererText()
		self.ruleAddCombo.pack_start(cell, expand=True)
		self.ruleAddCombo.add_attribute(cell, "text", 1)
		# ---
		pack(self.ruleAddBox, gtk.Label(label=_("Add Rule") + ":"))
		pack(self.ruleAddBox, self.ruleAddCombo)
		pack(self.ruleAddBox, gtk.Label(), 1, 1)
		self.ruleAddButton = labelImageButton(
			_("_Add"),
			"list-add.svg",
		)
		pack(self.ruleAddBox, self.ruleAddButton)
		# -------------
		# self.filesBox = common.FilesBox(self._event)
		# pack(self, self.filesBox)
		# -------------
		self.ruleAddCombo.connect("changed", self.onRuleAddComboChanged)
		self.ruleAddButton.connect("clicked", self.onRuleAddButtonClick)
		self.inputWidgets: dict[int, EventWidgetType] = {}
		self.removeButtons: dict[int, gtk.Button] = {}

	def makeRuleHbox(self, rule: EventRuleType) -> gtk.Box | None:
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=5)
		lab = gtk.Label(label=rule.desc)
		lab.set_xalign(0)
		pack(hbox, lab)
		self.groups[rule.sgroup].add_widget(lab)
		# pack(hbox, gtk.Label(), 1, 1)
		inputWidget = makeWidget(rule)
		if not inputWidget:
			log.error(f"failed to create inpout widget for rule {rule.name}")
			return None
		if rule.expand:
			pack(hbox, inputWidget.w, True, True)
		else:
			pack(hbox, inputWidget.w)
			pack(hbox, gtk.Label(), True, True)
		# ----
		removeButton = labelImageButton(
			label=_("_Remove"),
			imageName="list-remove.svg",
		)
		removeButton.connect("clicked", self.onRemoveButtonClick, hbox)
		# ^ FIXME
		pack(hbox, removeButton)
		# ----
		self.inputWidgets[id(hbox)] = inputWidget
		self.removeButtons[id(hbox)] = removeButton
		return hbox

	def updateRulesWidget(self) -> None:
		for child in self.rulesBox.get_children():
			child.destroy()
		comboItems = [ruleClass.name for ruleClass in event_lib.classes.rule]
		for rule in self._event.rulesDict.values():
			hbox = self.makeRuleHbox(rule)
			if not hbox:
				continue
			pack(self.rulesBox, hbox)
			# hbox.show_all()
			comboItems.remove(rule.name)
		self.rulesBox.show_all()
		for ruleName in comboItems:
			self.addRuleModel.append(
				(
					ruleName,
					event_lib.classes.rule.byName[ruleName].desc,
				),
			)
		self.onRuleAddComboChanged()

	def updateRules(self) -> None:
		self._event.clearRules()
		for hbox in self.rulesBox.get_children():
			inputWidget = self.inputWidgets[id(hbox)]
			inputWidget.updateVars()
			rule: EventRuleType = inputWidget.rule  # type: ignore[attr-defined]
			self._event.addRule(rule)

	def updateWidget(self) -> None:
		common.WidgetClass.updateWidget(self)
		self.addRuleModel.clear()
		self.updateRulesWidget()
		self.notificationBox.updateWidget()

	def updateVars(self) -> None:
		common.WidgetClass.updateVars(self)
		self.updateRules()
		self.notificationBox.updateVars()

	def calTypeComboChanged(self, _w: gtk.Widget | None = None) -> None:
		# overwrite method from common.WidgetClass
		newCalType = self.calTypeCombo.getActive()
		assert newCalType is not None
		for hbox in self.rulesBox.get_children():
			inputWidget = self.inputWidgets[id(hbox)]
			if hasattr(inputWidget, "changeRuleCalType"):
				inputWidget.changeRuleCalType(newCalType)
		self._event.calType = newCalType

	def onRemoveButtonClick(self, _b: gtk.Button, hbox: gtk.Box) -> None:
		inputWidget = self.inputWidgets[id(hbox)]
		rule: EventRuleType = inputWidget.rule  # type: ignore[attr-defined]
		ok, msg = self._event.checkRulesDependencies(disabledRule=rule)
		self.warnLabel.set_label(msg)
		if not ok:
			return
		self._event.checkAndRemoveRule(rule)
		# ----
		self.addRuleModel.append((rule.name, rule.desc))
		# ----
		hbox.destroy()
		# self.rulesBox.remove(hbox)
		self.onRuleAddComboChanged()

	def onRuleAddComboChanged(self, _combo: gtk.ComboBox | None = None) -> None:
		ci = self.ruleAddCombo.get_active()
		if ci is None or ci < 0:
			return
		newRuleName = self.addRuleModel[ci][0]
		newRule = self._event.create(newRuleName)
		_ok, msg = self._event.checkRulesDependencies(newRule=newRule)
		self.warnLabel.set_label(msg)

	def onRuleAddButtonClick(self, _b: gtk.ComboBox) -> None:
		ci = self.ruleAddCombo.get_active()
		if ci is None or ci < 0:
			return
		ruleName = self.addRuleModel[ci][0]
		rule = self._event.create(ruleName)
		ok, _msg = self._event.checkAndAddRule(rule)
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
