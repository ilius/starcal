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

from scal3 import logger

log = logger.get()

import os
import threading

# from sched import scheduler
from threading import Thread
from time import perf_counter, sleep
from time import time as now

from .simple_sched import scheduler

DISABLE = False


class EventNotificationManager:
	def __init__(self, eventGroups):
		self.byGroup: dict[int, EventGroupNotificationThread] = {}
		if DISABLE:
			return
		for group in eventGroups:
			self.checkGroup(group)

	def stop(self):
		for thread in self.byGroup.values():
			thread.cancel()

	def checkGroup(self, group):
		# log.debug(f"EventNotificationManager.checkGroup: {group=}")
		if not group.enable:
			return
		if not group.notificationEnabled:
			return

		thread = self.byGroup.get(group.id)
		if thread is not None and thread.is_alive():
			thread.reCalc()
			return

		log.info(f"EventNotificationManager.checkGroup: {group=}: creating thread")
		thread = EventGroupNotificationThread(group)
		self.byGroup[group.id] = thread
		thread.start()


class EventGroupNotificationThread(Thread):
	sleepSeconds = 1  # seconds
	interval = int(os.getenv("STARCAL_NOTIFICATION_CHECK_INTERVAL") or "1800")
	# ^ seconds
	# TODO: get from group.notificationCheckInterval

	def __init__(self, group):
		self.group = group

		self.sent = set()

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

		self._stop_event = threading.Event()
		self._recalc_event = threading.Event()

	def cancel(self):
		log.debug("EventGroupNotificationThread.cancel")
		self._stop_event.set()

	def stopped(self):
		return self._stop_event.is_set()

	def reCalc(self):
		log.info("EventGroupNotificationThread.reCalc ----------------")
		self.sent = set()
		self._recalc_event.set()

	def sleep(self, seconds: float):
		step = self.sleepSeconds
		sleepUntil = perf_counter() + seconds
		while not self.stopped() and perf_counter() < sleepUntil:
			sleep(step)

	def mainLoop(self):
		log.info("EventGroupNotificationThread.mainLoop ---------------")
		# time.perf_counter() is resistant to change of system time
		interval = self.interval
		sleepSeconds = self.sleepSeconds
		while not self._stop_event.is_set():
			self._recalc_event.clear()
			sleepUntil = perf_counter() + interval
			log.debug(f"EventGroupNotificationThread: run: {self.group=}")
			self._runStep()
			log.debug(f"EventGroupNotificationThread: finished run: {self.group=}")
			while not (
				self._stop_event.is_set() or self._recalc_event.is_set()
			) and perf_counter() < sleepUntil:
				sleep(sleepSeconds)

	def finishFunc(self):
		pass  # FIXME: what to do here?

	def notify(self, eid: int):
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

	def _runStep(self):
		log.info("EventGroupNotificationThread: _runStep")
		if not self.group.enable:
			return
		if not self.group.notificationEnabled:
			return

		interval = self.interval
		group = self.group

		tm = now()
		items = list(group.notifyOccur.search(tm, tm + interval))
		print(items)

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
