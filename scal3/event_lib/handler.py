from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.event_notification_thread import EventNotificationManager

from . import state
from .accounts_holder import EventAccountsHolder
from .groups_holder import EventGroupsHolder
from .trash import EventTrash

if TYPE_CHECKING:
	from scal3.filesystem import FileSystem

	from .state import InfoWrapper, LastIdsWrapper

__all__ = ["Handler"]


class Handler:
	def __init__(self) -> None:
		self._fs: FileSystem | None = None
		self._accounts: EventAccountsHolder | None = None
		self._groups: EventGroupsHolder | None = None
		self._trash: EventTrash | None = None
		self._notif: EventNotificationManager | None = None

	def init(self, fs: FileSystem) -> None:
		self._fs = fs
		self._accounts = EventAccountsHolder.load(0, fs=fs)
		self._groups = EventGroupsHolder.load(0, fs=fs)
		assert self._groups is not None
		self._trash = EventTrash.s_load(0, fs=fs)
		assert self._trash is not None
		self._groups.setTrash(self._trash)
		self._notif = EventNotificationManager(self._groups)

	@property
	def fs(self) -> FileSystem:
		assert self._fs is not None
		return self._fs

	@property
	def accounts(self) -> EventAccountsHolder:
		assert self._accounts is not None
		return self._accounts

	@property
	def groups(self) -> EventGroupsHolder:
		assert self._groups is not None
		return self._groups

	@property
	def trash(self) -> EventTrash:
		assert self._trash is not None
		return self._trash

	@property
	def notif(self) -> EventNotificationManager:
		assert self._notif is not None
		return self._notif

	@property
	def info(self) -> InfoWrapper:
		info = state.info
		assert info is not None
		return info

	@property
	def lastIds(self) -> LastIdsWrapper:
		lastIds = state.lastIds
		assert lastIds is not None
		return lastIds

	@property
	def allReadOnly(self) -> bool:
		return state.allReadOnly
