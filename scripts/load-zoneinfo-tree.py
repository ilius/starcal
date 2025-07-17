#!/usr/bin/env python3
# mypy: ignore-errors

from __future__ import annotations

import json


def dataToPrettyJson(data):
	return json.dumps(data, sort_keys=False, indent=4)


if __name__ == "__main__":
	from mytz.tree import getZoneInfoTree

	zoneTree = getZoneInfoTree()
	# open("data/zoneinfo-tree.json", "w").write(
	# 	dataToPrettyJson(zoneTree).replace(" \n", "\n")
	# )
