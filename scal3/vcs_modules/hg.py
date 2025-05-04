#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

import mercurial.ui
from mercurial.localrepo import localrepository
from mercurial.patch import diff, diffstatdata, diffstatsum
from mercurial.util import iterlines

from scal3.event_search_tree import EventSearchTree
from scal3.time_utils import getEpochFromJd
from scal3.vcs_modules import encodeShortStat, getCommitListFromEst

__all__ = [
	"clearObj",
	"getCommitInfo",
	"getCommitList",
	"getCommitShortStatLine",
	"getFirstCommitEpoch",
	"getLastCommitEpoch",
	"getLatestParentBefore",
	"getShortStat",
	"getTagList",
	"getTagShortStatLine",
	"prepareObj",
]


def getLatestParentBefore(obj, commitId: str, beforeEpoch: float) -> str:
	raise NotImplementedError


def prepareObj(obj) -> None:
	obj.repo = localrepository(mercurial.ui.ui(), obj.vcsDir)
	# ---
	obj.est = EventSearchTree()
	for rev_id in obj.repo.changelog:
		epoch = obj.repo[rev_id].date()[0]
		obj.est.add(epoch, epoch, rev_id)


def clearObj(obj) -> None:
	obj.repo = None
	obj.est = EventSearchTree()


def getCommitList(obj, startJd, endJd):
	"""Return a list of (epoch, commit_id) tuples."""
	return getCommitListFromEst(
		obj,
		startJd,
		endJd,
		lambda repo, rev_id: str(repo[rev_id]),
	)


def getCommitInfo(obj, commid_id):
	ctx = obj.repo[commid_id]
	lines = ctx.description().split("\n")
	return {
		"epoch": ctx.date()[0],
		"author": ctx.user(),
		"shortHash": str(ctx),
		"summary": lines[0],
		"description": "\n".join(lines[1:]),
	}


# FIXME: SLOW
def getShortStat(obj, node1, node2):
	repo = obj.repo
	# if not node1 # FIXME
	stats = diffstatdata(
		iterlines(
			diff(
				repo,
				str(node1),
				str(node2),
			),
		),
	)
	(
		_maxname,
		_maxtotal,
		insertions,
		deletions,
		_hasbinary,
	) = diffstatsum(stats)
	return len(stats), insertions, deletions


def getCommitShortStat(obj, commit_id):
	"""Returns (files_changed, insertions, deletions)."""
	ctx = obj.repo[commit_id]
	return getShortStat(
		obj,
		ctx.p1(),
		ctx,
	)


def getCommitShortStatLine(obj, commit_id):
	"""Returns str."""
	return encodeShortStat(*getCommitShortStat(obj, commit_id))


def getTagList(obj, startJd, endJd):
	"""Returns a list of (epoch, tag_name) tuples."""
	if not obj.repo:
		return []
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	# ---
	data = []
	for tag, _unknown in obj.repo.tagslist():
		if tag == "tip":
			continue
		epoch = obj.repo[tag].date()[0]
		if startEpoch <= epoch < endEpoch:
			data.append(
				(
					epoch,
					tag,
				),
			)
	data.sort()
	return data


def getTagShortStat(obj, prevTag, tag):
	repo = obj.repo
	return getShortStat(
		obj,
		repo[prevTag or 0],
		repo[tag],
	)


def getTagShortStatLine(obj, prevTag, tag):
	"""Returns str."""
	return encodeShortStat(*getTagShortStat(obj, prevTag, tag))


def getFirstCommitEpoch(obj):
	return obj.repo[0].date()[0]


def getLastCommitEpoch(obj):
	return obj.repo[len(obj.repo) - 1].date()[0]
