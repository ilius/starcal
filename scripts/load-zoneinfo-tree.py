#!/usr/bin/env python3


try:
	import json
except ImportError:
	import simplejson as json


def dataToPrettyJson(data):
	return json.dumps(data, sort_keys=False, indent=4)


if __name__ == "__main__":
	from natz.tree import getZoneInfoTree
	zoneTree = getZoneInfoTree(["usr", "share", "zoneinfo"])
	# open("data/zoneinfo-tree.json", "w").write(
	# 	dataToPrettyJson(zoneTree).replace(" \n", "\n")
	# )
