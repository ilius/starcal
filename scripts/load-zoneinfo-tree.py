#!/usr/bin/env python3

import os

try:
	import json
except ImportError:
	import simplejson as json

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=False, indent=4)


if __name__ == "__main__":
	zoneTree = getZoneInfoTree(
		["usr", "share", "zoneinfo"]
	)
	#open("zoneinfo-tree.json", "w").write(
	#	dataToPrettyJson(zoneTree).replace(" \n", "\n")
	#)
