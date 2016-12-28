#!/usr/bin/python

import os
import os.path
from collections import OrderedDict
from .directory import infoDir

infoDirL = list(os.path.split(infoDir))


def _addZoneNode(parentDict, zone, zoneNamesLevel):
	path = '/' + os.path.join(*tuple(infoDirL + zone))
	name = zone[-1]
	zoneNamesLevel[len(zone)].append(name)
	if os.path.isfile(path):
		parentDict[name] = ''
	elif os.path.isdir(path):
		parentDict[name] = OrderedDict()
		for chName in sorted(os.listdir(path)):
			_addZoneNode(
				parentDict[name],
				zone + [chName],
				zoneNamesLevel,
			)
	else:
		print('invalid path =', path)


def getZoneInfoTree():
	zoneTree = OrderedDict()
	zoneNamesLevel = [[] for i in range(4)]
	for group in [
		'Etc',
		'Africa',
		'America',
		'Antarctica',
		'Arctic',
		'Asia',
		'Atlantic',
		'Australia',
		'Brazil',
		'Canada',
		'Chile',
		'Europe',
		'Indian',
		'Mexico',
		'Mideast',
		'Pacific',
	]:
		_addZoneNode(
			zoneTree,
			[group],
			zoneNamesLevel,
		)
	#zoneNamesList = []
	#for levelNames in zoneNamesLevel:
	#	zoneNamesList += sorted(levelNames)
	#from pprint import pprint ; pprint(zoneTree)
	return zoneTree
