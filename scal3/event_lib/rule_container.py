# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
#
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

if TYPE_CHECKING:
	from collections.abc import Iterator
	from typing import Any

	from .rules import EventRule

from collections import OrderedDict

import mytz
from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.time_utils import (
	getEpochFromJd,
	getEpochFromJhms,
	getJdFromEpoch,
	getJhmsFromEpoch,
)

from .register import classes

__all__ = ["RuleContainer"]


class RuleContainer:
	requiredRules = ()
	supportedRules = None  # None means all rules are supported
	params = (
		"timeZoneEnable",
		"timeZone",
	)
	paramsOrder = (
		"timeZoneEnable",
		"timeZone",
	)

	@staticmethod
	def copyRulesDict(rulesOd: dict[str, EventRule]) -> dict[str, EventRule]:
		newRulesOd = OrderedDict()
		for ruleName, rule in rulesOd.items():
			newRulesOd[ruleName] = rule.copy()
		return newRulesOd

	def __init__(self) -> None:
		self.timeZoneEnable = False
		self.timeZone = ""
		# ---
		self.clearRules()
		self.rulesHash = None

	def clearRules(self) -> None:
		self.rulesOd = OrderedDict()

	def getRule(self, key: str) -> EventRule:
		return self.rulesOd[key]

	def getRuleIfExists(self, key: str) -> EventRule | None:
		return self.rulesOd.get(key)

	def setRule(self, key: str, value: EventRule):
		self.rulesOd[key] = value

	def iterRulesData(self) -> Iterator[tuple[str, Any]]:
		for rule in self.rulesOd.values():
			yield rule.name, rule.getData()

	def getRulesData(self) -> list[tuple[str, Any]]:
		return list(self.iterRulesData())

	def getRulesHash(self) -> int:
		return hash(
			str(
				(
					self.getTimeZoneStr(),
					sorted(self.iterRulesData()),
				),
			),
		)

	def getRuleNames(self) -> list[str]:
		return list(self.rulesOd)

	def addRule(self, rule: EventRule) -> None:
		self.rulesOd[rule.name] = rule

	def addNewRule(self, ruleType: str) -> EventRule:
		rule = classes.rule.byName[ruleType](self)
		self.addRule(rule)
		return rule

	def getAddRule(self, ruleType: str) -> EventRule:
		rule = self.getRuleIfExists(ruleType)
		if rule is not None:
			return rule
		return self.addNewRule(ruleType)

	def removeRule(self, rule: EventRule) -> None:
		del self.rulesOd[rule.name]

	def __delitem__(self, key: str) -> None:
		self.rulesOd.__delitem__(key)

	# returns (rule, found) where found is boolean
	def __getitem__(self, key: str) -> tuple[EventRule | None, bool]:
		rule = self.getRuleIfExists(key)
		if rule is None:
			return None, False
		return rule, True

	def __setitem__(self, key: str, value: EventRule) -> None:
		self.setRule(key, value)

	def __iter__(self) -> Iterator[EventRule]:
		return iter(self.rulesOd.values())

	def setRulesData(self, rulesData: list[tuple[str, Any]]) -> None:
		self.clearRules()
		for ruleName, ruleData in rulesData:
			rule = classes.rule.byName[ruleName](self)
			rule.setData(ruleData)
			self.addRule(rule)

	def addRequirements(self) -> None:
		for name in self.requiredRules:
			if name not in self.rulesOd:
				self.addNewRule(name)

	def checkAndAddRule(self, rule: EventRule) -> tuple[bool, str]:
		ok, msg = self.checkRulesDependencies(newRule=rule)
		if ok:
			self.addRule(rule)
		return (ok, msg)

	def removeSomeRuleTypes(self, *rmTypes) -> None:
		for ruleType in rmTypes:
			if ruleType in self.rulesOd:
				del self.rulesOd[ruleType]

	def checkAndRemoveRule(self, rule: EventRule) -> tuple[bool, str]:
		ok, msg = self.checkRulesDependencies(disabledRule=rule)
		if ok:
			self.removeRule(rule)
		return (ok, msg)

	def checkRulesDependencies(
		self,
		newRule: EventRule | None = None,
		disabledRule: EventRule | None = None,
	) -> tuple[bool, str]:
		rulesOd = self.rulesOd.copy()
		if newRule:
			rulesOd[newRule.name] = newRule
		if disabledRule and disabledRule.name in rulesOd:
			del rulesOd[disabledRule.name]
		provideList = []
		for ruleName, rule in rulesOd.items():
			provideList.append(ruleName)
			provideList += rule.provide
		for rule in rulesOd.values():
			for conflictName in rule.conflict:
				if conflictName in provideList:
					return (
						False,
						_(
							'Conflict between "{rule1}" and "{rule2}"',
						).format(
							rule1=_(rule.desc),
							rule2=_(rulesOd[conflictName].desc),
						),
					)
			for needName in rule.need:
				if needName not in provideList:
					# TODO: find which rule(s) provide(s) `needName`
					return (
						False,
						_('"{rule1}" needs "{rule2}"').format(
							rule1=_(rule.desc),
							rule2=_(needName),
						),
					)
		return (True, "")

	def copyRulesFrom(self, other: EventRule) -> None:
		for ruleType, rule in other.rulesOd.items():
			if self.supportedRules is None or ruleType in self.supportedRules:
				self.getAddRule(ruleType).copyFrom(rule)

	def copySomeRuleTypesFrom(
		self,
		other: EventRule,
		*ruleTypes: tuple[str],
	) -> None:
		for ruleType in ruleTypes:
			if ruleType not in self.supportedRules:
				log.info(
					f"copySomeRuleTypesFrom: unsupported rule {ruleType}"
					f" for container {self!r}",
				)
				continue
			rule = other.getRuleIfExists(ruleType)
			if rule is None:
				continue
			self.getAddRule(ruleType).copyFrom(rule)

	def getTimeZoneObj(self):
		if self.timeZoneEnable and self.timeZone:
			# mytz.gettz does not raise exception, returns None if invalid
			tz = mytz.gettz(self.timeZone)
			if tz:
				return tz
		return locale_man.localTz

	def getTimeZoneStr(self):
		return str(self.getTimeZoneObj())

	def getEpochFromJd(self, jd):
		return getEpochFromJd(jd, tz=self.getTimeZoneObj())

	def getJdFromEpoch(self, jd):
		return getJdFromEpoch(jd, tz=self.getTimeZoneObj())

	def getJhmsFromEpoch(self, epoch):
		return getJhmsFromEpoch(epoch, tz=self.getTimeZoneObj())

	def getEpochFromJhms(self, jd, h, m, s):
		return getEpochFromJhms(jd, h, m, s, tz=self.getTimeZoneObj())
