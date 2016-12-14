tree_path_split = lambda p: [int(x) for x in p.split(':')]

def getTreeviewPathStr(path):
	if not path:
		return None
	return '/'.join([str(x) for x in path])

