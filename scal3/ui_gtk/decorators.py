from __future__ import annotations

from typing import Any, Protocol

from scal3 import logger

log = logger.get()

from gi.repository import GObject

__all__ = [
	"registerSignals",
]


class ObjectType(Protocol):
	signals: list[tuple[str, list[Any]]]


def registerSignals[T: ObjectType](cls: type[T]) -> type[T]:
	for name, args in cls.signals:
		try:
			GObject.signal_new(
				name,
				cls,
				GObject.SignalFlags.RUN_LAST,
				None,
				args,
			)
		except Exception:  # noqa: PERF203
			log.error(
				f"Failed to create signal {name} "
				f"for class {cls.__name__} in {cls.__module__}",
			)
	return cls
