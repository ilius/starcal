from __future__ import annotations

from typing import Protocol

__all__ = ["BaseClassType"]


class BaseClassType(Protocol):
	name: str
	tname: str
	desc: str
	nameAlias: str


class EventRuleType(BaseClassType, Protocol):
	pass


class EventNotifierType(BaseClassType, Protocol):
	pass


class EventType(BaseClassType, Protocol):
	pass


class EventGroupType(BaseClassType, Protocol):
	pass


class AccountType(BaseClassType, Protocol):
	pass
