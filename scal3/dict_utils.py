from __future__ import annotations

from scal3 import logger

log = logger.get()

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence
	from typing import Any

	from scal3.utils import Comparable

__all__ = ["makeOrderedDict", "sortDict"]


def sortDict[T](
	data: dict[str, T],
	keyFunc: Callable[[T], Comparable],
) -> dict[str, T]:
	return dict(
		sorted(
			data.items(),
			key=lambda item: keyFunc(item[1]),
		),
	)


def makeOrderedDict(
	data: dict[str, Any],
	params: Sequence[str],
) -> dict[str, Any]:
	if not params:
		return data

	def paramIndex(key: str) -> int:
		try:
			return params.index(key)
		except ValueError:
			return len(params)

	return dict(sorted(data.items(), key=lambda x: paramIndex(x[0])))
