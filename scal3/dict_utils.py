from __future__ import annotations

from scal3 import logger

log = logger.get()

from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Sequence
	from typing import Any

__all__ = ["makeOrderedData", "sortDict"]


def sortDict(data: dict[str, Any], keyFunc: str) -> dict[str, Any]:
	return dict(
		sorted(
			data.items(),
			key=lambda item: keyFunc(item[1]),
		),
	)


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
