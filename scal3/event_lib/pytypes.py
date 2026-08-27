from __future__ import annotations

from typing import (
	IO,
	TYPE_CHECKING,
	Any,
	NotRequired,
	Protocol,
	Self,
	TypedDict,
	runtime_checkable,
)

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator, Sequence
	from datetime import tzinfo

	from scal3.color_utils import ColorType
	from scal3.event_search_tree import EventSearchTree
	from scal3.filesystem import FileSystem
	from scal3.s_object import ParentSObj
	from scal3.time_utils import HMS

	from .groups_import import EventGroupsImportResult


__all__ = [
	"AccountType",
	"BaseClassType",
	"EventContainerType",
	"EventGroupType",
	"EventNotifierType",
	"EventRuleType",
	"EventSearchConditionDict",
	"EventType",
	"OccurSetType",
	"RuleContainerType",
]


class BaseClassType(Protocol):
	"""Common attributes shared by all registrable classes."""

	name: str
	tname: str
	desc: str
	nameAlias: str
	WidgetClass: Any
	fs: FileSystem


class BaseTextModelType(Protocol):
	"""Common attributes for event entities backed by a text model."""

	name: str
	tname: str
	desc: str
	nameAlias: str
	WidgetClass: Any
	fs: FileSystem


class OccurSetType(Protocol):
	"""The set of times at which an event occurs."""

	event: EventType | None

	def intersection(self, other: OccurSetType) -> OccurSetType:
		"""Return a new set containing only times present in both sets."""

	# def getDaysJdList(self) -> list[int]: ...
	def getTimeRangeList(self) -> list[tuple[int, int]]:
		"""Return a list of (startEpoch, endEpoch) time ranges."""

	def getStartJd(self) -> int | None:
		"""Return the first Julian day of this set, or None if empty."""

	def getEndJd(self) -> int | None:
		"""Return the exclusive end Julian day of this set, or None if empty."""


class RuleContainerType(BaseClassType, Protocol):
	"""Common interface for containers that hold event rules."""

	calType: int
	rulesDict: dict[str, EventRuleType]

	def __getitem__(self, key: str) -> EventRuleType | None: ...

	def getTimeZoneObj(self) -> tzinfo:
		"""Return the time zone used by this container."""

	def getJhmsFromEpoch(self, epoch: int) -> tuple[int, HMS]:
		"""Return the (jd, hms) for an epoch in the container's time zone."""

	def getEpochFromJhms(self, jd: int, h: int, m: int, s: int) -> int:
		"""Return the epoch for a Julian day and time in the container's time zone."""

	def getRule(self, key: str) -> EventRuleType | None:
		"""Return the rule with the given name, or None."""

	def getAddRule(self, ruleType: str) -> EventRuleType:
		"""Return the rule of the given type, creating it if absent."""

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the container from a serialized dictionary."""

	def getDict(self) -> dict[str, Any]:
		"""Serialize the container to a dictionary."""

	def getRulesHash(self) -> int:
		"""Return a hash of the event's rules for change detection."""


class EventRuleType(BaseClassType, Protocol):
	"""Interface for rules that define how events recur or appear."""

	provide: Sequence[str]
	need: Sequence[str]
	conflict: Sequence[str]
	sgroup: int
	expand: bool

	def __init__(self, parent: RuleContainerType) -> None: ...
	def getEpoch(self) -> int:
		"""Return the epoch timestamp for this rule's primary time point."""

	def getRuleValue(self) -> Any:
		"""Return the rule's value for serialization."""

	def setRuleValue(self, data: Any) -> None:
		"""Set the rule's value from serialized data."""

	def calcOccurrence(
		self,
		startJd: int,
		endJd: int,
		event: EventType,
	) -> OccurSetType:
		"""Calculate the set of occurrences within the given Julian day range."""

	def changeCalType(self, calType: int) -> bool:
		"""Convert dates to a new calendar type, returning success."""

	def getJd(self) -> int:
		"""Return the Julian day number for this rule's date."""

	def getInfo(self) -> str:
		"""Return a human-readable description of this rule."""

	def getServerString(self) -> str:
		"""Return a server-compatible string representation of this rule."""

	@classmethod
	def getFrom(cls, container: RuleContainerType) -> Self | None:
		"""Return the rule of this type from the container, or None if absent."""

	@classmethod
	def addOrGetFrom(cls, container: RuleContainerType) -> Self:
		"""Return the rule of this type from the container, creating it if absent."""


class EventNotifierType(BaseClassType, Protocol):
	"""Interface for event notification mechanisms."""

	extraMessage: str
	event: EventType

	def __init__(self, event: EventType) -> None: ...
	def notify(self, finishFunc: Callable[[], None]) -> None:
		"""Trigger the notification, calling finishFunc when done."""

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the notifier from a serialized dictionary."""

	def getDict(self) -> dict[str, Any]:
		"""Serialize the notifier to a dictionary."""


class EventType(RuleContainerType, Protocol):
	"""Interface for all calendar event types."""

	id: int | None
	uuid: str | None
	parent: EventContainerType | None
	calType: int
	timeZone: str
	timeZoneEnable: bool
	lastHash: str | None
	modified: float
	rulesHash: int | None
	isSingleOccur: bool
	remoteIds: tuple[int, str, str, str] | None
	notifiers: list[EventNotifierType]
	notifyBefore: tuple[float, int]
	icon: str | None
	summary: str
	description: str
	isAllDay: bool
	readOnly: bool

	def __init__(
		self,
		ident: int | None = None,
		parent: EventContainerType | None = None,
	) -> None: ...

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the event from a serialized dictionary."""

	def getDict(self) -> dict[str, Any]:
		"""Serialize the event to a dictionary for JSON storage."""

	def getV4Dict(self) -> dict[str, Any]:
		"""Return a v4-format dictionary representation."""

	@classmethod
	def getDefaultIcon(cls) -> str:
		"""Return the default icon path for this event type."""

	def save(self) -> None:
		"""Save the event to disk."""

	def copyFrom(self, other: EventType) -> None:
		"""Copy rules and properties from another event."""

	def copyFromExact(self, other: EventType) -> None:
		"""Copy rules and properties, using exact JD conversion."""

	def getStartJd(self) -> int:
		"""Return the Julian day of the event's start."""

	def getStartEpoch(self) -> int:
		"""Return the epoch timestamp of the event's start."""

	def checkNotify(self, finishFunc: Callable[[], None]) -> None:
		"""Check whether notification time has been reached and notify if so."""

	def getTextParts(self, showDesc: bool = True) -> list[str]:
		"""Return summary and optional description as text parts."""

	def getIconRel(self) -> str | None:
		"""Return the icon path relative to the application data directories."""

	def getInfo(self) -> str:
		"""Return a multi-line human-readable summary of this event."""

	def afterModify(self) -> None:
		"""Handle post-modification tasks for the event."""

	def afterModifyBasic(self) -> None:
		"""Assign an ID if needed and update the modification timestamp."""

	def afterModifyInGroup(self) -> None:
		"""Notify the parent group about occurrence changes."""

	def changeCalType(self, calType: int) -> bool:
		"""Change the calendar type, returning success."""

	def setId(self, ident: int | None = None) -> None:
		"""Assign a numeric ID to this event."""

	def calcEventOccurrenceIn(self, startJd: int, endJd: int) -> OccurSetType:
		"""Calculate the occurrence set within the given Julian day range."""

	def calcEventOccurrence(self) -> OccurSetType:
		"""Calculate the occurrence set within the parent's date range."""

	def getNotifyBeforeSec(self) -> float:
		"""Return the notification lead time in seconds."""

	def getSummary(self) -> str:
		"""Return the event summary text."""

	def getDescription(self) -> str:
		"""Return the event description text."""

	def getText(self, showDesc: bool = True) -> str:
		"""Return the full display text for this event."""

	def icsUID(self) -> str:
		"""Generate a unique ICS UID string for this event."""

	def getIcsData(
		self,
		prettyDateTime: bool = False,
	) -> list[tuple[str, str]] | None:
		"""Return ICS fields for this event, or None if not supported."""

	def getDictOrdered(self) -> dict[str, Any]:
		"""Serialize the event to an ordered dictionary."""

	def setDictOverride(self, data: dict[str, Any]) -> None:
		"""Populate the event from a dictionary, overriding existing data."""

	def loadHistory(self) -> list[tuple[int, str]]:
		"""Return the event's modification history as (epoch, hash) pairs."""

	def createPatchByHash(self, oldHash: str) -> dict[str, Any]:
		"""Generate a diff patch between this event and a previous revision."""

	def getEndEpoch(self) -> int:
		"""Return the epoch timestamp of the event's end."""

	def getJd(self) -> int:
		"""Return the Julian day of the event's start."""

	def getEndJd(self) -> int:
		"""Return the Julian day of the event's end."""

	def updateSummary(self) -> None:
		"""Update the summary from other event properties."""

	def getRevision(self, revHash: str, ident: int = 0) -> Self:
		"""Return a historical revision of this event by hash."""

	def setJd(self, jd: int) -> None:
		"""Set the event date from a Julian day."""

	def invalidate(self) -> None:
		"""Invalidate the event so it can no longer be saved."""

	def clearRules(self) -> None:
		"""Remove all rules from this event."""

	def addRule(self, rule: EventRuleType) -> None:
		"""Add a rule to this event."""

	def checkRulesDependencies(
		self,
		newRule: EventRuleType | None = None,
		disabledRule: EventRuleType | None = None,
	) -> tuple[bool, str]:
		"""Check whether rule changes cause conflicts or missing dependencies."""

	def checkAndRemoveRule(self, rule: EventRuleType) -> tuple[bool, str]:
		"""Validate that removing a rule won't break dependencies, then remove it."""

	def create(self, ruleName: str) -> EventRuleType:
		"""Create and attach a new rule of the given type."""

	def checkAndAddRule(self, rule: EventRuleType) -> tuple[bool, str]:
		"""Validate rule dependencies and add it if valid."""

	def getIcon(self) -> str | None:
		"""Return the absolute icon path, or None if unset."""

	def getShownDescription(self) -> str:
		"""Return the description to display for this event."""

	def getNotifyBeforeMin(self) -> int:
		"""Return the notification lead time in whole minutes."""

	def setIcsData(self, data: dict[str, str]) -> bool:
		"""Import event data from an iCalendar dictionary."""


class EventContainerType(BaseTextModelType, Protocol):
	"""Interface for containers that hold a list of events."""

	title: str
	calType: int
	showFullEventDesc: bool
	idList: list[int]
	eventTextSep: str
	startJd: int
	endJd: int
	occur: EventSearchTree | None

	def __len__(self) -> int: ...
	def __iter__(self) -> Iterator[EventType]: ...
	def index(self, ident: int) -> int:
		"""Return the positional index of an event ID in the list."""

	def getIdPath(self) -> list[int]:
		"""Return the ID path from the root object to this container."""

	def getPath(self) -> list[int]:
		"""Return the index path from the root object to this container."""

	def updateOccurrenceEvent(self, event: EventType) -> None:
		"""Update the occurrence tree for a single event."""

	def getStartEpoch(self) -> int:
		"""Return the epoch timestamp of the container's start date."""

	def getEndEpoch(self) -> int:
		"""Return the epoch timestamp of the container's end date."""

	def getTimeZoneStr(self) -> str:
		"""Return the container's time zone string, or empty if disabled."""


class EventGroupType(EventContainerType, Protocol):
	"""Interface for event groups."""

	id: int | None
	uuid: str | None
	file: str
	enable: bool
	parent: ParentSObj | None
	color: ColorType
	icon: str | None
	modified: float
	actions: list[tuple[str, str]]
	acceptsEventTypes: Sequence[str]
	canConvertTo: list[str]
	notificationEnabled: bool
	notifyOccur: EventSearchTree | None = None
	remoteIds: tuple[int, str] | None
	occurCount: int
	showInDCal: bool
	showInWCal: bool
	showInMCal: bool
	showInStatusIcon: bool
	showInTimeLine: bool
	deletedRemoteEvents: dict[int, tuple[float, int, str, str]]
	addEventsToBeginning: bool

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> EventGroupType | None:
		"""Load a group from disk by ID."""

	@property
	def mustId(self) -> int:
		"""Return the group ID, asserting it has been assigned."""

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the group from a serialized dictionary."""

	def getDict(self) -> dict[str, Any]:
		"""Serialize the group to a dictionary for JSON storage."""

	def save(self) -> None:
		"""Save the group to disk."""

	def getEvent(self, ident: int) -> EventType:
		"""Return the event with the given ID."""

	def setId(self, ident: int | None = None) -> None:
		"""Assign a numeric ID to this group."""

	def afterModify(self) -> None:
		"""Handle post-modification tasks for the group."""

	def create(self, eventType: str) -> EventType:
		"""Create a new event of the given type in this group."""

	def append(self, event: EventType) -> None:
		"""Append an event to the end of the group's list."""

	def removeAll(self) -> None:
		"""Remove all events from the group and clear occurrence data."""

	def remove(self, event: EventType) -> int:
		"""Remove an event from the group and return its previous index."""

	def setRandomColor(self) -> None:
		"""Assign a random color to this group."""

	def setTitle(self, title: str) -> None:
		"""Set the group title."""

	def deepConvertTo(self, newGroupType: str) -> EventGroupType:
		"""Convert this group to a different type, migrating all events."""

	def exportData(self) -> dict[str, Any]:
		"""Export the group and all its events as a serializable dictionary."""

	def getLastSync(self) -> tuple[float, float] | None:
		"""Return the last sync time range, or None."""

	def getStartEpoch(self) -> int:
		"""Return the epoch timestamp of the group's start date."""

	def setReadOnly(self, readOnly: bool) -> None:
		"""Set this group's read-only flag."""

	def afterSync(self, startEpoch: int | float | None = None) -> None:
		"""Record the sync completion time range."""

	def getSortBys(self) -> tuple[str, list[tuple[str, str, bool]]]:
		"""Return the default sort attribute and available sort options."""

	def sort(self, attr: str = "summary", reverse: bool = False) -> None:
		"""Sort the id list by the given attribute."""

	def __iter__(self) -> Iterator[EventType]: ...
	def updateOccurrence(self) -> None:
		"""Rebuild the entire occurrence search tree for all events."""

	def importData(
		self,
		data: dict[str, Any],
		importMode: int,
	) -> EventGroupsImportResult:
		"""Import events from data dict into group, creating or updating as needed."""

	def exportToIcsFp(self, fp: IO[str]) -> None:
		"""Write all events in this group to an ICS file object."""

	def __getitem__(self, ident: int) -> EventType: ...
	def showInCal(self) -> bool:
		"""Return True if the group is shown in any calendar view."""

	def index(self, ident: int) -> int:
		"""Return the positional index of an event ID in the list."""

	def search(self, conds: EventSearchConditionDict) -> Iterator[EventType]:
		"""Yield events matching the given search conditions."""

	def __len__(self) -> int: ...
	def checkEventToAdd(self, event: EventType) -> bool:
		"""Return True if the event type is accepted by this group."""

	def isReadOnly(self) -> bool:
		"""Return True if the group is read-only."""

	def deepCopy(self) -> EventGroupType:
		"""Create a full copy of this group including all its events."""

	def moveUp(self, index: int) -> None:
		"""Move the event at the given index one position earlier."""

	def moveDown(self, index: int) -> None:
		"""Move the event at the given index one position later."""

	def insert(self, index: int, event: EventType) -> None:
		"""Insert an event at the given position in the id list."""

	def updateCache(self, event: EventType) -> None:
		"""Update the cached event entry and notify of modification."""


@runtime_checkable
class AccountType(BaseTextModelType, Protocol):
	"""Interface for remote calendar accounts."""

	id: int | None
	uuid: str | None
	file: str
	enable: bool
	title: str
	loaded: bool
	remoteGroups: list[dict[str, Any]]

	@classmethod
	def load(
		cls,
		ident: int,
		fs: FileSystem,
	) -> AccountType | None:
		"""Load an account from disk by ID."""

	def __init__(self, ident: int | None = None) -> None: ...
	def setId(self, ident: int | None = None) -> None:
		"""Assign a numeric ID to this account."""

	def setDict(self, data: dict[str, Any]) -> None:
		"""Populate the account from a serialized dictionary."""

	def getDict(self) -> dict[str, Any]:
		"""Serialize the account to a dictionary for JSON storage."""

	def save(self) -> None:
		"""Save the account to disk."""

	def fetchGroups(self) -> None:
		"""Fetch the list of remote groups."""

	def sync(
		self,
		group: EventGroupType,
		remoteGroupId: str,
	) -> None:
		"""Synchronize a local group with a remote group."""


class EventSearchConditionDict(TypedDict):
	"""Search conditions that can be passed to EventGroup.search."""

	text: NotRequired[str]
	text_lower: NotRequired[str]
	time_from: NotRequired[int]
	time_to: NotRequired[int]
	modified_from: NotRequired[int]
	type: NotRequired[str]
	timezone: NotRequired[str]
