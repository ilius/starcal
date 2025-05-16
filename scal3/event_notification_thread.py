# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from __future__ import annotations

from scal3 import event_lib, logger

log = logger.get()

import os
import threading
from queue import Empty, Queue

# from sched import scheduler
from threading import Thread
from time import perf_counter, sleep
from time import time as now
from typing import TYPE_CHECKING

from .simple_sched import scheduler

if TYPE_CHECKING:
	from collections.abc import Iterable

	from scal3.event_lib.groups import EventGroup

__all__ = ["EventNotificationManager"]


DISABLE = False


class EventNotificationManager:
	def __init__(self, eventGroups: Iterable[EventGroup]) -> None:
		self.byGroup: dict[int, EventGroupNotificationThread] = {}
		if DISABLE:
			return
		for group in eventGroups:
			self.checkGroup(group)

	def stop(self) -> None:
		for thread in self.byGroup.values():
			thread.cancel()

	def _startGroup(self, group: event_lib.EventGroup) -> None:
		log.info(f"EventNotificationManager: {group=}: creating thread")
		thread = EventGroupNotificationThread(group)
		self.byGroup[group.id] = thread
		thread.start()

	def checkGroup(self, group: event_lib.EventGroup) -> None:
		# log.debug(f"EventNotificationManager.checkGroup: {group=}")
		if not (group.enable and group.notificationEnabled):
			return

		log.info(f"EventNotificationManager.checkGroup: {group=}")

		thread = self.byGroup.get(group.id)
		if thread is not None and thread.is_alive():
			return

		self._startGroup(group)

	def checkEvent(self, group: event_lib.EventGroup, event: event_lib.Event) -> None:
		if not (group.enable and group.notificationEnabled):
			log.info("EventNotificationManager.checkEvent: not enabled")
			return

		log.info(f"EventNotificationManager.checkEvent: {group=}, {event=}")

		thread = self.byGroup.get(group.id)
		if thread is not None and thread.is_alive():
			thread.checkEvent(event)
			return

		self._startGroup(group)


class EventGroupNotificationThread(Thread):
	sleepSeconds = 1  # seconds
	interval = int(os.getenv("STARCAL_NOTIFICATION_CHECK_INTERVAL") or "1800")
	# ^ seconds
	# TODO: get from group.notificationCheckInterval

	def __init__(self, group: EventGroup) -> None:
		self.group = group

		self.sent = set()
		self._stop_event = threading.Event()
		self._new_events = Queue()

		# self.sch: sched.scheduler | None = None
		# threading.Timer is a subclass of threading.Thread
		# so probably too expensive to create a timer for each occurance or even event!
		# try using sched.scheduler
		# https://docs.python.org/3/library/sched.html#sched.scheduler
		# Changed in Python 3.3: scheduler class can be safely used in multi-threaded
		# environments.

		Thread.__init__(
			self,
			target=self.mainLoop,
		)

	def cancel(self) -> None:
		log.debug("EventGroupNotificationThread.cancel")
		self._stop_event.set()

	def stopped(self) -> bool:
		return self._stop_event.is_set()

	def checkEvent(self, event: event_lib.Event) -> None:
		self._new_events.put_nowait(event)

	def sleep(self, seconds: float) -> None:
		step = self.sleepSeconds
		sleepUntil = perf_counter() + seconds
		while not self.stopped() and perf_counter() < sleepUntil:
			sleep(step)

	def mainLoop(self) -> None:
		log.info("EventGroupNotificationThread.mainLoop ---------------")
		# time.perf_counter() is resistant to change of system time
		interval = self.interval
		sleepSeconds = self.sleepSeconds
		while not self._stop_event.is_set():
			sleepUntil = perf_counter() + interval
			log.debug(f"EventGroupNotificationThread: run: {self.group=}")
			self._runStep()
			log.debug(f"EventGroupNotificationThread: finished run: {self.group=}")
			while not self._stop_event.is_set() and perf_counter() < sleepUntil:
				try:
					event = self._new_events.get(block=True, timeout=sleepSeconds)
				except Empty:  # noqa: PERF203
					continue
				else:
					event.checkNotify(self.finishFunc)

	def finishFunc(self) -> None:
		pass  # FIXME: what to do here?

	def notify(self, eid: int) -> None:
		log.info(f"EventGroupNotificationThread: notify: {eid=}")
		for _ in range(10):
			try:
				event = self.group[eid]
			except ValueError as e:
				log.error(str(e))
				sleep(2)
				continue
			event.checkNotify(self.finishFunc)
			break

	def _runStep(self) -> None:
		log.info("EventGroupNotificationThread: _runStep")
		if not self.group.enable:
			return
		if not self.group.notificationEnabled:
			return

		interval = self.interval
		group = self.group

		tm = now()
		items = list(group.notifyOccur.search(tm, tm + interval))
		log.info(f"{tm=}, {tm + interval=}, {items=}")

		if not items:
			return

		sch = scheduler(
			timefunc=now,
			delayfunc=self.sleep,
			stopped=self.stopped,
		)

		for item in items:
			if item.oid in self.sent:
				log.info(f"EventGroupNotificationThread: skipping {item}")
				continue
			log.info(f"EventGroupNotificationThread: adding {item}")
			self.sent.add(item.oid)
			sch.enterabs(
				item.start,  # max(now(), item.start),
				1,  # priority
				self.notify,
				argument=(item.eid,),
			)

		# self.sch = sch
		log.info(f"EventGroupNotificationThread: run: starting sch.run, {len(items)=}")
		sch.run()
		log.info("EventGroupNotificationThread: run: finished sch.run")
