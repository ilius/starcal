from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from collections.abc import Callable


def keeperCallable(obj: Any) -> Callable[[], Any]:
	def res():
		return obj

	return res


def moduleObjectInitializer(
	modulePath: str,
	className: str,
	*args,
	**kwargs,
) -> Callable[[], Any]:
	def res():
		module = __import__(
			modulePath,
			fromlist=[className],
		)
		cls = getattr(module, className)
		return cls(*args, **kwargs)

	return res
