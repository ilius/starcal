#!/usr/bin/env python3
import os

__all__ = [
	"getZoneInfoTree",
]

if os.sep == "\\":
	from .tree_win import getZoneInfoTree
else:
	from .tree_unix import getZoneInfoTree
