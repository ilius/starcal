# -*- coding: utf-8 -*-

from scal3.utils import myRaise
from scal3.utils import toStr
from scal3.time_utils import getEpochFromJd

def encodeShortStat(files_changed, insertions, deletions):
	parts = []
	if files_changed == 1:
		parts.append('1 file changed')
	else:
		parts.append('%d files changed'%files_changed)
	if insertions > 0:
		parts.append('%d insertions(+)'%insertions)
	if deletions > 0:
		parts.append('%d deletions(-)'%deletions)
	return ', '.join(parts)

def getCommitListFromEst(obj, startJd, endJd, format_rev_id=None):
	'''
		returns a list of (epoch, rev_id) tuples
	'''
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	###
	data = []
	for t0, t1, rev_id, dt in obj.est.search(startEpoch, endEpoch):
		if format_rev_id:
			rev_id = format_rev_id(obj.repo, rev_id)
		data.append((t0, rev_id))
	data.sort(reverse=True)
	return data


vcsModuleNames = [
	'git',
	'hg',
	'bzr',
]






