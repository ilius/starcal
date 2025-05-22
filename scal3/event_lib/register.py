from __future__ import annotations

from .pytypes import (
	AccountType,
	BaseClassType,
	EventGroupType,
	EventNotifierType,
	EventRuleType,
	EventType,
)

__all__ = ["classes"]


class ClassGroup[T: BaseClassType](list):
	def __init__(self, tname: str) -> None:
		list.__init__(self)
		self.tname = tname
		self.names: list[str] = []
		self.byName: dict[str, type[T]] = {}
		self.byDesc: dict[str, type[T]] = {}
		self.main: type[T] | None = None

	def register(self, cls: type[T]) -> type[T]:
		assert cls.name
		cls.tname = self.tname
		self.append(cls)
		self.names.append(cls.name)
		self.byName[cls.name] = cls
		self.byDesc[cls.desc] = cls
		nameAlias = getattr(cls, "nameAlias", None)
		if nameAlias:
			self.byName[nameAlias] = cls
		return cls

	def setMain(self, cls: type[T]) -> type[T]:
		self.main = cls
		return cls


class classes:
	# TODO: EventRuleType, EventNotifierType, EventType, EventGroupType, AccountType
	rule: ClassGroup[EventRuleType] = ClassGroup("rule")
	notifier: ClassGroup[EventNotifierType] = ClassGroup("notifier")
	event: ClassGroup[EventType] = ClassGroup("event")
	group: ClassGroup[EventGroupType] = ClassGroup("group")
	account: ClassGroup[AccountType] = ClassGroup("account")
