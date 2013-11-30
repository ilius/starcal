#!/usr/bin/python

import os
from os import listdir
from os.path import join, isfile, isdir
from pprint import pprint, pformat
from collections import OrderedDict

try:
    import json
except ImportError:
    import simplejson as json

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=False, indent=4)
dataToCompactJson = lambda data: json.dumps(data, sort_keys=False, separators=(',', ':'))
jsonToData = json.loads

endObj = '' ## '' or None

infoDir = ['usr', 'share', 'zoneinfo']

groups = [
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
]

zoneTree = OrderedDict()
zoneNamesLevel = [[] for i in range(4)]

def addZoneNode(parentDict, zone):
    path = '/' + join(*tuple(infoDir + zone))
    name = zone[-1]
    zoneNamesLevel[len(zone)].append(name)
    if isfile(path):
        parentDict[name] = endObj
    elif isdir(path):
        parentDict[name] = OrderedDict()
        for chName in sorted(listdir(path)):
            addZoneNode(parentDict[name], zone + [chName])
    else:
        print('invalid path =', path)


for group in groups:
    addZoneNode(zoneTree, [group])

zoneNamesList = []
for levelNames in zoneNamesLevel:
    zoneNamesList += sorted(levelNames)

open('zoneinfo-tree.json', 'w').write(dataToPrettyJson(zoneTree).replace(' \n', '\n'))
#open('zoneinfo-names.json', 'w').write(dataToPrettyJson(zoneNamesList))


