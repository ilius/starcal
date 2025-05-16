from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = ["moduleObjectInitializer"]


def keeperCallable[T](obj: T) -> Callable[[], T]:
	def res() -> T:
		return obj

	return res


def moduleObjectInitializer(
	modulePath: str,
	className: str,
	*args,
	**kwargs,
) -> Callable[[], Any]:
	def res() -> Any:
		module = __import__(
			modulePath,
			fromlist=[className],
		)
		cls = getattr(module, className)
		return cls(*args, **kwargs)

	return res
