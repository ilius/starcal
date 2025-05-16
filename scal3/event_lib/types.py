from typing import Protocol


class BaseClassType(Protocol):
	name: str
	tname: str
	desc: str
	nameAlias: str


# TODO: EventRuleType, EventNotifierType, EventType, EventGroupType, AccountType
