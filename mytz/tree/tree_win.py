from collections import OrderedDict

from dateutil.tz.win import tzwin

__all__ = ["getZoneInfoTree"]


def getZoneInfoTree():
	zoneTree = OrderedDict()
	for name in tzwin.list():
		zoneTree[name] = ""
	# FIXME: this is long list, find a way to group them
	# even group by the first word if you have to
	return zoneTree
