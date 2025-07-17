from __future__ import annotations

from typing import TYPE_CHECKING

from .pytypes import (
	BaseClassType,
)

if TYPE_CHECKING:
	from collections.abc import Iterator

	from .pytypes import (
		AccountType,
		EventGroupType,
		EventNotifierType,
		EventRuleType,
		EventType,
	)

__all__ = ["classes"]


class ClassGroup[T: BaseClassType]:
	def __init__(self, tname: str) -> None:
		self.lst: list[type[T]] = []
		self.tname = tname
		self.names: list[str] = []
		self.byName: dict[str, type[T]] = {}
		self.byDesc: dict[str, type[T]] = {}
		self.main: type[T] | None = None

	def __iter__(self) -> Iterator[type[T]]:
		return iter(self.lst)

	def __getitem__(self, i: int) -> type[T]:
		return self.lst[i]

	def index(self, x: type[T]) -> int:
		return self.lst.index(x)

	def register(
		self,
		cls: type[T],
	) -> type[T]:
		assert cls.name
		cls.tname = self.tname
		self.lst.append(cls)
		self.names.append(cls.name)
		self.byName[cls.name] = cls
		self.byDesc[cls.desc] = cls
		nameAlias = cls.nameAlias
		if nameAlias:
			self.byName[nameAlias] = cls
		return cls

	def setMain(
		self,
		cls: type[T],
	) -> type[T]:
		self.main = cls
		return cls


class classes:
	# TODO: EventRuleType, EventNotifierType, EventType, EventGroupType, AccountType
	rule: ClassGroup[EventRuleType] = ClassGroup("rule")
	notifier: ClassGroup[EventNotifierType] = ClassGroup("notifier")
	event: ClassGroup[EventType] = ClassGroup("event")
	group: ClassGroup[EventGroupType] = ClassGroup("group")
	account: ClassGroup[AccountType] = ClassGroup("account")
