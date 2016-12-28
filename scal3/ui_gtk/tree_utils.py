def tree_path_split(p):
	return [
		int(x)
		for x in p.split(':')
	]


def getTreeviewPathStr(path):
	if not path:
		return None
	return '/'.join([str(x) for x in path])
