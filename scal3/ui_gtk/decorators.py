from __future__ import annotations

from scal3 import logger

log = logger.get()

from gi.repository import GObject

__all__ = [
	"registerSignals",
	"registerType",
]


def registerType[T: type[GObject]](cls: T) -> T:
	GObject.type_register(cls)
	return cls


def registerSignals[T: type[GObject]](cls: T) -> T:
	GObject.type_register(cls)
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
