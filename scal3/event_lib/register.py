from __future__ import annotations

from scal3.event_lib.pytypes import BaseClassType

__all__ = ["classes"]


class ClassGroup[T: BaseClassType](list):
	def __init__(self, tname: str) -> None:
		list.__init__(self)
		self.tname = tname
		self.names = []
		self.byName = {}
		self.byDesc = {}
		self.main = None

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
	rule = ClassGroup("rule")
	notifier = ClassGroup("notifier")
	event = ClassGroup("event")
	group = ClassGroup("group")
	account = ClassGroup("account")
