import logging

log = logging.getLogger("root")

import os
import os.path
from collections import OrderedDict


def findZoneInfoDir():
	for dir_ in (
		"/usr/share/zoneinfo",
		"/usr/lib/zoneinfo",
		"/usr/share/lib/zoneinfo",
		"/etc/zoneinfo",
	):
		if os.path.isdir(dir_):
			return dir_

	try:
		import pytz
	except ImportError:
		pass
	else:
		dir_ = os.path.join(os.path.dirname(pytz.__file__), "zoneinfo")
		if os.path.isdir(dir_):
			return dir_

	raise OSError("zoneinfo directory not found")


infoDir = findZoneInfoDir()

infoDirL = list(os.path.split(infoDir))


def _addZoneNode(parentDict, zone, zoneNamesLevel):
	path = os.path.join(*tuple(infoDirL + zone))
	name = zone[-1]
	zoneNamesLevel[len(zone)].append(name)
	if os.path.isfile(path):
		parentDict[name] = ""
	elif os.path.isdir(path):
		parentDict[name] = OrderedDict()
		for chName in sorted(os.listdir(path)):
			_addZoneNode(
				parentDict[name],
				zone + [chName],
				zoneNamesLevel,
			)
	else:
		log.error(f"invalid {path=}")


def getZoneInfoTree():
	zoneTree = OrderedDict()
	zoneNamesLevel = [[] for i in range(4)]
	for group in (
		"Etc",
		"Africa",
		"America",
		"Antarctica",
		"Arctic",
		"Asia",
		"Atlantic",
		"Australia",
		"Brazil",
		"Canada",
		"Chile",
		"Europe",
		"Indian",
		"Mexico",
		"Pacific",
		"US",
	):
		_addZoneNode(
			zoneTree,
			[group],
			zoneNamesLevel,
		)
	# zoneNamesList = []
	# for levelNames in zoneNamesLevel:
	# 	zoneNamesList += sorted(levelNames)
	# from pprint import pprint ; log.info(pprint(zoneTree))
	return zoneTree
