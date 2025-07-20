# mypy: ignore-errors

from typing import Any

from dateutil.tz.win import tzwin

__all__ = ["getZoneInfoTree"]


def getZoneInfoTree() -> dict[str, Any]:
	zoneTree = {}
	name: str
	for name in tzwin.list():
		zoneTree[name] = ""
	# FIXME: this is long list, find a way to group them
	# even group by the first word if you have to
	return zoneTree
