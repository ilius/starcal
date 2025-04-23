from scal3.time_utils import getEpochFromJd

__all__ = ["encodeShortStat", "getCommitListFromEst", "vcsModuleNames"]


def encodeShortStat(files_changed, insertions, deletions):
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


def getCommitListFromEst(obj, startJd, endJd, format_rev_id=None):
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
