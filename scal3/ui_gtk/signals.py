from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from scal3 import logger

log = logger.get()

from gi.repository import GObject

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"EmptySignalHandler",
	"SignalHandlerBase",
	"SignalHandlerType",
	"registerSignals",
]


class SignalHandlerType(Protocol):
	signals: ClassVar[list[tuple[str, list[Any]]]]

	def emit(self, signal_name: str, *args: Any) -> Any: ...

	def connect(
		self,
		signal_name: str,
		handler: Callable[..., Any],
		*args: Any,
	) -> int: ...


class SignalHandlerBase(GObject.Object):
	signals: ClassVar[list[tuple[str, list[Any]]]]


def registerSignals[T: type[SignalHandlerType]](cls: T) -> T:
	GObject.type_register(cls)  # type: ignore[no-untyped-call]
	# log.error(f"\nregisterSignals: {cls.__module__}.{cls.__name__}")
	for name, args in cls.signals:
		try:
			GObject.signal_new(  # type: ignore[no-untyped-call]
				name,
				cls,
				GObject.SignalFlags.RUN_LAST,
				None,
				args,
			)
		except Exception:  # noqa: PERF203
			log.error(
				f"Failed to create signal {name} for {cls.__module__}.{cls.__name__}",
			)
	return cls


@registerSignals
class EmptySignalHandler(SignalHandlerBase):
	signals = []
