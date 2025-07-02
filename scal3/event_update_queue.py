from __future__ import annotations

from queue import Queue
from threading import Thread
from time import sleep

from scal3 import logger
from scal3.event_lib.groups import EventGroup
from scal3.event_lib.pytypes import EventGroupType

log = logger.get()

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from scal3.event_lib.trash import EventTrash

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.ui_gtk.gtk_ud import CalObjType

__all__ = ["EventUpdateQueue", "EventUpdateRecord"]


"""
Usage:
	ui.eventUpdateQueue.put(action, event, self)
"""


@dataclass(slots=True)
class EventUpdateRecord:
	action: str
	obj: EventType | EventGroupType | EventTrash
	sender: CalObjType | None


class ConsumerType(Protocol):
	def onEventUpdate(self, record: EventUpdateRecord) -> None: ...


class EventUpdateQueue:
	def __init__(self) -> None:
		self.q: Queue[EventUpdateRecord | None] = Queue()
		self._consumers: list[ConsumerType] = []
		self._thread: Thread | None = None
		self._paused: bool = False

	def registerConsumer(self, consumer: ConsumerType) -> None:
		log.debug(f"registerConsumer: {consumer.__class__.__name__}")
		if not hasattr(consumer, "onEventUpdate"):
			raise TypeError(
				f"type {consumer.__class__.__name__} has no method onEventUpdate",
			)
		self._consumers.append(consumer)

	def put(
		self,
		action: str,
		obj: EventType | EventGroupType | EventTrash,
		sender: CalObjType | None,
	) -> None:
		if action not in {
			"+",  # add/create event
			"-",  # delete/remove event
			"e",  # edit event
			"v",  # move event
			"r",  # reload group or trash
			"eg",  # edit group, including enable/disable
			"+g",  # new group with events inside it (imported)
			"-g",  # delete/remove group with all its events
		}:
			raise ValueError(f"invalid {action=}")
		if action not in {"r", "eg", "+g", "-g"} and obj.parent is None:
			raise ValueError("obj.parent is None")
		if action == "r":
			if not isinstance(obj, EventGroup | EventTrash):
				raise TypeError(
					f"invalid obj type {obj.__class__.__name__} for {action=}",
				)
		elif action == "eg":  # noqa: SIM102
			if not isinstance(obj, EventGroup):
				raise TypeError(
					f"invalid obj type {obj.__class__.__name__} for {action=}",
				)
		log.info(f"EventUpdateQueue: add: {action=}, {obj=}")
		record = EventUpdateRecord(action, obj, sender)
		self.q.put(record)

	def startLoop(self) -> None:
		if self._thread is not None:
			raise RuntimeError("startLoop: self._thread is not None")
		self._thread = Thread(
			target=self.runLoop,
		)
		self._thread.start()

	def stopLoop(self) -> None:
		self.q.put(None)
		if self._thread is None:
			return
		# should we wait here until it's stopped?
		self._thread.join()
		self._thread = None

	def pauseLoop(self) -> None:
		self._paused = True

	def resumeLoop(self) -> None:
		self._paused = False

	def runLoop(self) -> None:
		while True:  # OK
			if self._paused:
				sleep(0.2)
				continue
			# Queue.get: Remove and return an item from the queue.
			# If queue is empty, wait until an item is available.
			record = self.q.get()
			if record is None:
				return
			for consumer in self._consumers:
				if consumer is record.sender:
					continue
				consumer.onEventUpdate(record)


def testEventUpdateQueue() -> None:
	import time

	class MockGroup:
		pass

	class MockEvent:
		def __init__(
			self,
			ident: int,
			parent: object,  # FIXME
		) -> None:
			self.id = ident
			self.parent = parent

		def getPath(self) -> tuple[int, int]:
			return (0, self.id)

	class MockConsumer:
		def onEventUpdate(self, record: EventUpdateRecord) -> None:  # noqa: PLR6301
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
		queue.put(action, MockEvent(eid, group), sender)  # type: ignore[arg-type]
	queue.startLoop()
	time.sleep(2)
	queue.stopLoop()


if __name__ == "__main__":
	testEventUpdateQueue()
