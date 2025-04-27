from __future__ import annotations

from scal3 import logger

log = logger.get()

import json
from json import JSONEncoder

__all__ = ["dataToCompactJson", "dataToPrettyJson"]


def _default(_self, obj):
	return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default


def dataToPrettyJson(
	data: dict | list,
	ensure_ascii: bool = False,
	sort_keys: bool = False,
) -> str:
	try:
		return json.dumps(
			data,
			indent="\t",
			ensure_ascii=ensure_ascii,
			sort_keys=sort_keys,
		)
	except Exception:
		log.exception(f"{data =}")


def dataToCompactJson(
	data: dict | list,
	ensure_ascii: bool = False,
	sort_keys: bool = False,
) -> str:
	return json.dumps(
		data,
		separators=(",", ":"),
		ensure_ascii=ensure_ascii,
		sort_keys=sort_keys,
	)
