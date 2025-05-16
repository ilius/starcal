from collections.abc import Callable
from typing import Any

from scal3.time_utils import getEpochFromJd

__all__ = ["encodeShortStat", "getCommitListFromEst", "vcsModuleNames"]


def encodeShortStat(files_changed: int, insertions: int, deletions: int) -> str:
	parts = []
	if files_changed == 1:
		parts.append("1 file changed")
	else:
		parts.append(f"{files_changed:d} files changed")
	if insertions > 0:
		parts.append(f"{insertions:d} insertions(+)")
	if deletions > 0:
		parts.append(f"{deletions:d} deletions(-)")
	return ", ".join(parts)


def getCommitListFromEst(
	obj: Any,
	startJd: int,
	endJd: int,
	format_rev_id: Callable | None = None,
) -> list[tuple[int, int | str]]:
	"""Returns a list of (epoch, rev_id) tuples."""
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	# ---
	data = []
	for t0, _t1, rev_id, _dt in obj.est.search(startEpoch, endEpoch):
		if format_rev_id:
			rev_id = format_rev_id(obj.repo, rev_id)  # noqa: PLW2901
		data.append((t0, rev_id))
	data.sort(reverse=True)
	return data


vcsModuleNames = [
	"git",
	"hg",
]
