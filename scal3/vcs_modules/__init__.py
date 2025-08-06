from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3.time_utils import getEpochFromJd

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.event_lib.vcs_base import VcsBaseEventGroup
	from scal3.event_search_tree import EventSearchTree

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
	obj: VcsBaseEventGroup,
	startJd: int,
	endJd: int,
	format_rev_id: Callable[[Any, tuple[int, float, float]], Any] | None = None,
) -> list[tuple[int, int | str]]:
	"""Returns a list of (epoch, rev_id) tuples."""
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	# ---
	data = []
	est: EventSearchTree = obj.est  # type: ignore[attr-defined]
	repo: Any = obj.repo  # type: ignore[attr-defined]
	for occur in est.search(startEpoch, endEpoch):
		if format_rev_id:
			data.append((occur.start, format_rev_id(repo, occur.oid)))
		else:
			data.append((occur.start, occur.oid))
	data.sort(reverse=True)
	return data


vcsModuleNames = [
	"git",
	"hg",
]
