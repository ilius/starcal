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

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import mercurial.ui
from mercurial.localrepo import localrepository
from mercurial.patch import diff, diffstatdata, diffstatsum
from mercurial.util import iterlines

from scal3.event_search_tree import EventSearchTree
from scal3.time_utils import getEpochFromJd
from scal3.vcs_modules import encodeShortStat, getCommitListFromEst

if TYPE_CHECKING:
	from scal3.event_lib.vcs_base import VcsBaseEventGroup

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

# TODO: obj: VcsBaseEventGroup


def getLatestParentBefore(
	obj: VcsBaseEventGroup,
	commitId: str,
	beforeEpoch: float,
) -> str:
	raise NotImplementedError


def prepareObj(obj: VcsBaseEventGroup) -> None:
	repo = obj.repo = localrepository(mercurial.ui.ui(), obj.vcsDir)  # type: ignore[attr-defined]
	est = obj.est = EventSearchTree()  # type: ignore[attr-defined]
	for rev_id in repo.changelog:
		epoch = repo[rev_id].date()[0]
		est.add(epoch, epoch, rev_id)


def clearObj(obj: VcsBaseEventGroup) -> None:
	obj.repo = None  # type: ignore[attr-defined]
	obj.est = EventSearchTree()  # type: ignore[attr-defined]


def getCommitList(
	obj: VcsBaseEventGroup,
	startJd: int,
	endJd: int,
) -> list[tuple[int, int | str]]:
	"""Return a list of (epoch, commit_id) tuples."""
	return getCommitListFromEst(
		obj,
		startJd,
		endJd,
		format_rev_id=lambda repo, rev_id: str(repo[rev_id]),
	)


def getCommitInfo(obj: VcsBaseEventGroup, commid_id: int) -> dict[str, Any]:
	ctx = obj.repo[commid_id]  # type: ignore[attr-defined]
	lines = ctx.description().split("\n")
	return {
		"epoch": ctx.date()[0],
		"author": ctx.user(),
		"shortHash": str(ctx),
		"summary": lines[0],
		"description": "\n".join(lines[1:]),
	}


# FIXME: SLOW
def getShortStat(
	obj: VcsBaseEventGroup,
	node1: str,
	node2: str,
) -> tuple[int, int, int]:
	repo = obj.repo  # type: ignore[attr-defined]
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


def getCommitShortStat(
	obj: VcsBaseEventGroup,
	commit_id: str,
) -> tuple[int, int, int]:
	"""Returns (files_changed, insertions, deletions)."""
	ctx = obj.repo[commit_id]  # type: ignore[attr-defined]
	return getShortStat(
		obj,
		ctx.p1(),
		ctx,
	)


def getCommitShortStatLine(
	obj: VcsBaseEventGroup,
	commit_id: str,
) -> str:
	"""Returns str."""
	return encodeShortStat(*getCommitShortStat(obj, commit_id))


def getTagList(
	obj: VcsBaseEventGroup,
	startJd: int,
	endJd: int,
) -> list[tuple[int, str]]:
	"""Returns a list of (epoch, tag_name) tuples."""
	repo = obj.repo  # type: ignore[attr-defined]
	if not repo:
		return []
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	# ---
	data = []
	for tag, _unknown in repo.tagslist():
		if tag == "tip":
			continue
		epoch = repo[tag].date()[0]
		if startEpoch <= epoch < endEpoch:
			data.append(
				(
					epoch,
					tag,
				),
			)
	data.sort()
	return data


def getTagShortStat(
	obj: VcsBaseEventGroup,
	prevTag: str,
	tag: str,
) -> tuple[int, int, int]:
	repo = obj.repo  # type: ignore[attr-defined]
	return getShortStat(
		obj,
		repo[prevTag or 0],
		repo[tag],
	)


def getTagShortStatLine(obj: VcsBaseEventGroup, prevTag: str, tag: str) -> str:
	"""Returns str."""
	return encodeShortStat(*getTagShortStat(obj, prevTag, tag))


def getFirstCommitEpoch(obj: VcsBaseEventGroup) -> int:
	return obj.repo[0].date()[0]  # type: ignore[attr-defined]


def getLastCommitEpoch(obj: VcsBaseEventGroup) -> int:
	return obj.repo[len(obj.repo) - 1].date()[0]  # type: ignore[attr-defined]
