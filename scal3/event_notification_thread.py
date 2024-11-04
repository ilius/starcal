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

import sched
from heapq import heappop
from threading import Thread
from time import perf_counter, sleep
from time import time as now


class EventNotificationManager:
	def __init__(self, eventGroups):
		self.byGroup = {}
		for group in eventGroups:
			self.runGroup(group)

	def checkGroup(self, group):
		if not group.enable:
			return
		if not group.notificationEnabled:
			return

		thread = self.byGroup.get(group.id)
		if thread is not None and thread.is_alive():
			return

		thread = EventGroupNotificationThread(group)
		self.byGroup[group.id] = thread
		thread.start()


class EventGroupNotificationThread(Thread):
	interval = 30 * 60  # seconds
	maxTimerCount = 100

	def __init__(self, group):
		self.group = group
		# self.sch: sched.scheduler | None = None
		self.queues = {}
		# type: dict[int, list[int]]
		# the values should be a (min) heap
		# use heappush and heappop
		# 	epoch = self.queues[eid][0]			# to get the smallest without pop
		# 	epoch = heappop(self.queues[eid])	# to get and remove the smallest
		# heappush(self.queues[eid], epoch)

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

	def mainLoop(self):
		# time.perf_counter() is resistant to change of system time
		interval = self.interval
		while True:
			t0 = perf_counter()
			self.run()
			dt = perf_counter() - t0
			sleep(interval - dt)

	def finishFunc(self):
		pass  # FIXME: what to do here?

	def notify(self, eid: int):
		self.group[eid].checkNotify(self.finishFunc)

	def run(self):
		if not self.group.enable:
			return
		if not self.group.notificationEnabled:
			return

		interval = self.interval
		queues = self.queues

		# if self.sch is not None and not self.sch.empty():
		# 	print(f"EventGroupNotificationThread: run: last scheduler is not done yet")

		sch = sched.scheduler(now, sleep)
		tm = now()

		for eid in queues:
			if queues[eid][0] > tm + interval:
				continue
			sch.enterabs(
				heappop(queues[eid]),
				self.notify,
				argument=(eid,),
			)

		# self.sch = sch
		sch.run(blocking=True)
