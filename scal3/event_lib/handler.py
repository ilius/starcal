from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.event_notification_thread import EventNotificationManager

from . import state
from .accounts_holder import EventAccountsHolder
from .groups_holder import (
	EventArchivedGroupsHolder,
	EventGroupsHolder,
)
from .trash import EventTrash

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem

	from .state import InfoWrapper, LastIdsWrapper

__all__ = ["Handler"]


class Handler:
	"""Facade providing access to all event subsystems."""

	def __init__(self) -> None:
		self._fs: FileSystem | None = None
		self._accounts: EventAccountsHolder | None = None
		self._groups: EventGroupsHolder | None = None
		self._archivedGroups: EventArchivedGroupsHolder | None = None
		self._trash: EventTrash | None = None
		self._notif: EventNotificationManager | None = None

	def init(self, fs: FileSystem) -> None:
		"""Initialize all subsystems from the given filesystem backend."""
		self._fs = fs
		self._accounts = EventAccountsHolder.load(0, fs=fs)
		self._groups = EventGroupsHolder.load(0, fs=fs)
		assert self._groups is not None
		self._archivedGroups = EventArchivedGroupsHolder.load(0, fs=fs)
		assert self._archivedGroups is not None
		self._trash = EventTrash.s_load(0, fs=fs)
		assert self._trash is not None
		self._groups.setTrash(self._trash)
		self._groups.setArchivedGroups(self._archivedGroups)
		self._notif = EventNotificationManager(self._groups)

	@property
	def fs(self) -> FileSystem:
		"""Return the initialized filesystem backend."""
		assert self._fs is not None
		return self._fs

	@property
	def accounts(self) -> EventAccountsHolder:
		"""Return the account holder subsystem."""
		assert self._accounts is not None
		return self._accounts

	@property
	def groups(self) -> EventGroupsHolder:
		"""Return the group holder subsystem."""
		assert self._groups is not None
		return self._groups

	@property
	def archivedGroups(self) -> EventArchivedGroupsHolder:
		"""Return the archived-groups holder subsystem."""
		assert self._archivedGroups is not None
		return self._archivedGroups

	@property
	def trash(self) -> EventTrash:
		"""Return the trash subsystem."""
		assert self._trash is not None
		return self._trash

	@property
	def notif(self) -> EventNotificationManager:
		"""Return the notification manager subsystem."""
		assert self._notif is not None
		return self._notif

	@property
	def info(self) -> InfoWrapper:
		"""Return the persistent info wrapper."""
		info = state.info
		assert info is not None
		return info

	@property
	def lastIds(self) -> LastIdsWrapper:
		"""Return the persistent last-IDs wrapper."""
		lastIds = state.lastIds
		assert lastIds is not None
		return lastIds

	@property
	def allReadOnly(self) -> bool:
		"""Return True if all event data is currently read-only."""
		return state.allReadOnly
