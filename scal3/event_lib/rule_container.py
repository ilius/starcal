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

from copy import copy

from scal3 import logger
from scal3.s_object import SObj, copyParams

log = logger.get()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator, Sequence
	from datetime import tzinfo
	from typing import Any

	from scal3.filesystem import FileSystem
	from scal3.time_utils import (
		HMS,
	)

	from .pytypes import EventRuleType, RuleContainerType


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


class RuleContainer(SObj):
	"""Container that manages a dictionary of event rules with dependency checking."""

	requiredRules: list[str] = []
	supportedRules: Sequence[str] | None = None  # None means all rules are supported
	params: list[str] = [
		"timeZoneEnable",
		"timeZone",
	]
	paramsOrder: list[str] = [
		"timeZoneEnable",
		"timeZone",
	]
	WidgetClass: Any
	fs: FileSystem

	@staticmethod
	def copyRulesDict(rulesDict: dict[str, EventRuleType]) -> dict[str, EventRuleType]:
		"""Return a shallow copy of the rules dictionary."""
		newRulesOd = {}
		for ruleName, rule in rulesDict.items():
			newRulesOd[ruleName] = copy(rule)
		return newRulesOd

	def __init__(self) -> None:
		self.timeZoneEnable = False
		self.timeZone = ""
		# ---
		self.clearRules()
		self.rulesHash: int | None = None
		self.calType = 0

	def clearRules(self) -> None:
		"""Remove all rules from this container."""
		self.rulesDict: dict[str, EventRuleType] = {}

	def getRule(self, key: str) -> EventRuleType | None:
		"""Return the rule with the given name, or None if absent."""
		return self.rulesDict.get(key)

	def setRule(self, key: str, value: EventRuleType) -> None:
		"""Store the given rule under its key in the rules dictionary."""
		self.rulesDict[key] = value

	def iterRulesData(self) -> Iterator[tuple[str, Any]]:
		"""Yield (ruleName, ruleValue) pairs for all rules."""
		for rule in self.rulesDict.values():
			yield rule.name, rule.getRuleValue()

	def getRulesData(self) -> list[tuple[str, Any]]:
		"""Return all rules as a list of (name, value) tuples."""
		return list(self.iterRulesData())

	def getRulesHash(self) -> int:
		"""Return a hash of the time zone and all rules for change detection."""
		return hash(
			str(
				(
					self.getTimeZoneStr(),
					sorted(self.iterRulesData()),
				),
			),
		)

	def getRuleNames(self) -> list[str]:
		"""Return the names of all rules in this container."""
		return list(self.rulesDict)

	def addRule(self, rule: EventRuleType) -> None:
		"""Attach the given rule to this container."""
		self.rulesDict[rule.name] = rule

	def addNewRule(self, ruleType: str) -> EventRuleType:
		"""Create a new rule of the given type, attach it, and return it."""
		# if TYPE_CHECKING:
		# 	_container: RuleContainerType = self
		rule = classes.rule.byName[ruleType](self)  # type: ignore[arg-type]
		self.addRule(rule)
		return rule

	def getAddRule(self, ruleType: str) -> EventRuleType:
		"""Return an existing rule of the given type, or create and return a new one."""
		rule = self.getRule(ruleType)
		if rule is not None:
			return rule
		return self.addNewRule(ruleType)

	def removeRule(self, rule: EventRuleType) -> None:
		"""Remove the given rule from this container."""
		del self.rulesDict[rule.name]

	def __delitem__(self, key: str) -> None:
		self.rulesDict.__delitem__(key)

	def __getitem__(self, key: str) -> EventRuleType | None:
		return self.getRule(key)

	def __setitem__(self, key: str, value: EventRuleType) -> None:
		self.setRule(key, value)

	def __iter__(self) -> Iterator[EventRuleType]:
		return iter(self.rulesDict.values())

	def setRulesData(self, rulesData: list[tuple[str, Any]]) -> None:
		"""Replace all rules with those from the given serialized data."""
		self.clearRules()
		for ruleName, ruleData in rulesData:
			rule = classes.rule.byName[ruleName](self)  # type: ignore[arg-type]
			rule.setRuleValue(ruleData)
			self.addRule(rule)

	def addRequirements(self) -> None:
		"""Add any required rules that are not already present."""
		for name in self.requiredRules:
			if name not in self.rulesDict:
				self.addNewRule(name)

	def checkAndAddRule(self, rule: EventRuleType) -> tuple[bool, str]:
		"""Validate rule dependencies and add it if valid."""
		ok, msg = self.checkRulesDependencies(newRule=rule)
		if ok:
			self.addRule(rule)
		return (ok, msg)

	def removeSomeRuleTypes(
		self,
		*typesToRemove: str,
	) -> None:
		"""Remove rules matching the given type names if present."""
		for ruleType in typesToRemove:
			if ruleType in self.rulesDict:
				del self.rulesDict[ruleType]

	def checkAndRemoveRule(self, rule: EventRuleType) -> tuple[bool, str]:
		"""Validate that removing a rule won't break dependencies, then remove it."""
		ok, msg = self.checkRulesDependencies(disabledRule=rule)
		if ok:
			self.removeRule(rule)
		return (ok, msg)

	def checkRulesDependencies(
		self,
		newRule: EventRuleType | None = None,
		disabledRule: EventRuleType | None = None,
	) -> tuple[bool, str]:
		"""Check whether rule changes cause conflicts or missing dependencies."""
		rulesDict = self.rulesDict.copy()
		if newRule:
			rulesDict[newRule.name] = newRule
		if disabledRule and disabledRule.name in rulesDict:
			del rulesDict[disabledRule.name]
		provideList = []
		for ruleName, rule in rulesDict.items():
			provideList.append(ruleName)
			provideList += rule.provide
		for rule in rulesDict.values():
			for conflictName in rule.conflict:
				if conflictName in provideList:
					return (
						False,
						_(
							'Conflict between "{rule1}" and "{rule2}"',
						).format(
							rule1=_(rule.desc),
							rule2=_(rulesDict[conflictName].desc),
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

	def copyRulesFrom(self, other: RuleContainerType) -> None:
		"""Copy all supported rules from another container."""
		for ruleType, rule in other.rulesDict.items():
			if self.supportedRules is None or ruleType in self.supportedRules:
				rule2 = self.getAddRule(ruleType)
				copyParams(rule2, rule)

	def copySomeRuleTypesFrom(
		self,
		other: RuleContainerType,
		*ruleTypes: str,
	) -> None:
		"""Copy only the specified rule types from another container."""
		assert self.supportedRules is not None
		for ruleType in ruleTypes:
			if ruleType not in self.supportedRules:
				log.info(
					f"copySomeRuleTypesFrom: unsupported rule {ruleType}"
					f" for container {self!r}",
				)
				continue
			rule = other.getRule(ruleType)
			if rule is None:
				continue
			rule2 = self.getAddRule(ruleType)
			copyParams(rule2, rule)

	def getTimeZoneObj(self) -> tzinfo:
		"""Return the configured time zone, or the local time zone."""
		if self.timeZoneEnable and self.timeZone:
			# mytz.gettz does not raise exception, returns None if invalid
			tz = mytz.gettz(self.timeZone)
			if tz:
				return tz
		assert locale_man.localTz is not None
		return locale_man.localTz

	def getTimeZoneStr(self) -> str:
		"""Return the time zone name string."""
		return str(self.getTimeZoneObj())

	def getEpochFromJd(self, jd: int) -> int:
		"""Convert a Julian day to an epoch timestamp in the container's time zone."""
		return getEpochFromJd(jd, tz=self.getTimeZoneObj())

	def getJdFromEpoch(self, jd: int) -> int:
		"""Convert an epoch timestamp to a Julian day in the container's time zone."""
		return getJdFromEpoch(jd, tz=self.getTimeZoneObj())

	def getJhmsFromEpoch(self, epoch: int) -> tuple[int, HMS]:
		"""Return the (jd, hms) for an epoch in the container's time zone."""
		return getJhmsFromEpoch(epoch, tz=self.getTimeZoneObj())

	def getEpochFromJhms(self, jd: int, h: int, m: int, s: int) -> int:
		"""Return the epoch for a Julian day and time in the container's time zone."""
		return getEpochFromJhms(jd, h, m, s, tz=self.getTimeZoneObj())
