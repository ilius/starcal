#!/usr/bin/env python3

from scal3.ui_gtk import gtk


def tree_path_split(path):
	if isinstance(path, gtk.TreePath):
		return path.get_indices()
	elif isinstance(path, str):
		return [
			int(x)
			for x in path.split(":")
		]
	elif isinstance(path, int):
		return [path]
	else:
		raise TypeError(f"invalid path: {path!r}")


def getTreeviewPathStr(path):
	if not path:
		return None
	return "/".join([str(x) for x in path])
