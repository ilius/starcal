#!/usr/bin/env python3

from queue import Queue
from threading import Thread

from typing import Union

from scal3 import logger
log = logger.get()


"""
Usage:
	ui.eventUpdateQueue.put(action, event, self)
"""


class EventUpdateRecord:
	def __init__(
		self,
		action: str,
		obj: Union["event_lib.Event", "event_lib.EventGroup"],
		sender: "BaseCalObj",
	):
		self.action = action
		self.obj = obj
		self.sender = sender


class EventUpdateQueue(Queue):
	def __init__(self):
		Queue.__init__(self)
		self._consumers = []
		self._thread = None

	def registerConsumer(self, consumer) -> None:
		log.info(f"registerConsumer: {consumer.__class__.__name__}")
		if not hasattr(consumer, "onEventUpdate"):
			raise TypeError(f"type {consumer.__class__.__name__} has no method onEventUpdate")
		self._consumers.append(consumer)

	def put(self, action, obj, sender):
		if action not in (
			"+",  # add/create event
			"-",  # delete/remove event
			"e",  # edit event
			"v",  # move event
			"r",  # reload group or trash
			"eg",  # edit group, including enable/disable
			"+g",  # new group with events inside it (imported)
			"-g",  # delete/remove group with all its events
		):
			raise ValueError(f"invalid action={action}")
		if action not in ("r", "eg", "+g", "-g") and obj.parent is None:
			raise ValueError("obj.parent is None")
		if action == "r":
			if obj.__class__.__name__ not in ("EventGroup", "EventTrash"):
				raise TypeError(f"invalid obj type {obj.__class__.__name__} for action={action!r}")
		elif action == "eg":
			if obj.__class__.__name__ != "EventGroup":
				raise TypeError(f"invalid obj type {obj.__class__.__name__} for action={action!r}")
		log.info(f"EventUpdateQueue: add: obj={obj}")
		record = EventUpdateRecord(action, obj, sender)
		Queue.put(self, record)

	def startLoop(self):
		if self._thread is not None:
			raise RuntimeError("startLoop: self._thread is not None")
		self._thread = Thread(
			target=self.runLoop,
		)
		self._thread.start()

	def stopLoop(self):
		Queue.put(self, None)
		if self._thread is None:
			return
		# should we wait here until it's stopped?
		self._thread.join()
		self._thread = None

	def runLoop(self):
		while True:
			# Queue.get: Remove and return an item from the queue.
			# If queue is empty, wait until an item is available.
			record = self.get()
			if record is None:
				return
			for consumer in self._consumers:
				if consumer is record.sender:
					continue
				consumer.onEventUpdate(record)


def testEventUpdateQueue():
	import time

	class MockGroup:
		pass

	class MockEvent:
		def __init__(self, _id, parent):
			self.id = _id
			self.parent = parent
		def getPath(self):
			return (0, self.id)

	class MockConsumer:
		def onEventUpdate(self, record: "EventUpdateRecord") -> None:
			log.info(f"{record.action} {record.obj.id}")

	queue = EventUpdateQueue()
	queue.registerConsumer(MockConsumer())
	items = [
		("+", 1),
		("+", 2),
		("+", 3),
		("-", 4),
		("e", 5),
		("-", 2),
		("e", 3),
		("e", 6),
		("e", 5),
	]
	sender = None
	group = MockGroup()
	for action, eid in items:
		queue.put(action, MockEvent(eid, group), sender)
	group.startLoop()
	time.sleep(2)
	queue.stopLoop()


if __name__ == "__main__":
	testEventUpdateQueue()
