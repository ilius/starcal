from scal3.ui_gtk import gtk

__all__ = ["tree_path_split"]


def tree_path_split(path: str) -> list[int]:
	if isinstance(path, gtk.TreePath):
		return path.get_indices()
	if isinstance(path, str):
		return [int(x) for x in path.split(":")]
	if isinstance(path, int):
		return [path]
	raise TypeError(f"invalid path: {path!r}")
