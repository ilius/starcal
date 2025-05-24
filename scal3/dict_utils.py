from __future__ import annotations

from scal3 import logger

log = logger.get()

from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Sequence
	from typing import Any

	from scal3.utils import Comparable

__all__ = ["makeOrderedData", "sortDict"]


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

	return OrderedDict(sorted(data.items(), key=lambda x: paramIndex(x[0])))


def makeOrderedData(
	data: dict[str, Any] | Sequence,
	params: Sequence[str],
) -> dict[str, Any] | list:
	if isinstance(data, dict) and params:
		data = list(data.items())

		def paramIndex(key: str) -> int:
			try:
				return params.index(key)
			except ValueError:
				return len(params)

		data.sort(key=lambda x: paramIndex(x[0]))
		data = OrderedDict(data)

	return data
