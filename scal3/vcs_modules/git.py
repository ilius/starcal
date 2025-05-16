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

from typing import Any

from scal3 import logger

log = logger.get()


from pygit2 import (
	GIT_SORT_REVERSE,
	GIT_SORT_TIME,
	GIT_SORT_TOPOLOGICAL,
	Repository,
)

from scal3.time_utils import getEpochFromJd
from scal3.vcs_modules import encodeShortStat

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


def prepareObj(obj: Any) -> None:  # noqa: ARG001
	pass


def clearObj(obj: Any) -> None:  # noqa: ARG001
	pass


def getCommitList(
	obj: Any,
	startJd: int | None = None,
	endJd: int | None = None,
	branch: str = "",
) -> list[tuple[int, str]]:
	"""
	Returns a list of (epoch, commit_id) tuples.

	this function is optimized for recent commits
	i.e. endJd is either None or recent
	"""
	if not branch:
		branch = "main"
	startEpoch = None
	endEpoch = None
	if startJd is not None:
		startEpoch = getEpochFromJd(startJd)
	if endJd is not None:
		endEpoch = getEpochFromJd(endJd)
	repo = Repository(obj.vcsDir)
	data: list[tuple[int, str]] = []
	# items of data are (epochTime, commitHash)
	target = repo.branches[branch].target
	for commit in repo.walk(target, GIT_SORT_TIME):
		tm = commit.author.time
		if endEpoch is not None and tm > endEpoch:
			continue
		if startEpoch is not None and tm < startEpoch:
			break
		data.append(
			(
				tm,
				commit.id.hex,
			),
		)
	data.reverse()
	return data


def getCommitInfo(obj: Any, commid_id: str) -> dict[str, Any]:
	repo = Repository(obj.vcsDir)
	commit = repo.revparse_single(commid_id)
	msg = commit.message
	return {
		"epoch": commit.author.time,
		"author": f"{commit.author.name} <{commit.author.email}>",
		"shortHash": commit.id.hex[:8],  # or commit.short_id.hex
		"summary": msg.split("\n")[0],
		"description": msg,
	}


def getShortStatLine(obj: Any, prevId: str, thisId: str) -> str:
	"""Returns str."""
	return encodeShortStat(*getShortStat(obj, prevId, thisId))


def getShortStat(obj: Any, prevId: str, thisId: str) -> tuple[int, int, int]:
	"""Returns (files_changed, insertions, deletions)."""
	repo = Repository(obj.vcsDir)
	diff = repo.diff(
		a=repo.revparse_single(prevId).id.hex,
		b=repo.revparse_single(thisId).id.hex,
	)
	stats = diff.stats
	return (stats.files_changed, stats.insertions, stats.deletions)


def getCommitShortStatLine(obj: Any, commit_id: str) -> str:
	"""Returns str."""
	return encodeShortStat(*getCommitShortStat(obj, commit_id))


def getCommitShortStat(obj: Any, commit_id: str) -> tuple[int, int, int]:
	"""Returns (files_changed, insertions, deletions)."""
	repo = Repository(obj.vcsDir)
	commit = repo.revparse_single(commit_id)
	diff = repo.diff(
		a=commit.parent_ids[0].hex,
		b=commit.id.hex,
	)
	stats = diff.stats
	return (stats.files_changed, stats.insertions, stats.deletions)


def getTagList(obj: Any, startJd: int, endJd: int) -> list[tuple[int, str]]:
	"""Returns a list of (epoch, tag_name) tuples."""
	repo = Repository(obj.vcsDir)
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	data = []
	for refName in repo.references:
		if not refName.startswith("refs/tags/"):
			continue
		tagName = refName[len("refs/tags/") :]
		ref = repo.references[refName]
		tag = repo.get(ref.target)
		# in some cases, tag is instance of _pygit2.Tag, with tag.author
		# in other cases, tag is instance of _pygit2.Commit, with tag.author
		try:
			author = tag.author
		except AttributeError:
			author = tag.tagger
		epoch = author.time  # type: int
		if epoch < startEpoch:
			continue
		if epoch >= endEpoch:
			break
		data.append(
			(
				epoch,
				tagName,
			),
		)
	return data


def getTagShortStatLine(obj: Any, prevTag: str, tag: str) -> str:
	return getShortStatLine(obj, prevTag, tag)


def getFirstCommitEpoch(obj: Any) -> str:
	repo = Repository(obj.vcsDir)
	target = repo.branches[obj.vcsBranch].target
	commitIter = repo.walk(target, GIT_SORT_TIME | GIT_SORT_REVERSE)
	commit = next(commitIter)
	return commit.author.time


def getLastCommitEpoch(obj: Any) -> str:
	repo = Repository(obj.vcsDir)
	target = repo.branches[obj.vcsBranch].target
	commitIter = repo.walk(target, GIT_SORT_TIME)
	commit = next(commitIter)
	return commit.author.time


def getLatestParentBefore(obj: Any, commitId: str, beforeEpoch: float) -> str:
	repo = Repository(obj.vcsDir)

	def find(commitIdArg: str) -> str:
		for commit in repo.walk(commitIdArg, GIT_SORT_TOPOLOGICAL):
			if commit.author.time < beforeEpoch:
				return commit.id.hex
			if len(commit.parent_ids) > 1:
				nextId = find(commit.parent_ids[0])
				if nextId:
					return nextId
				return commit.id.hex
		return ""

	return find(commitId)


if __name__ == "__main__":
	import os
	import sys
	from dataclasses import dataclass

	from dateutil.parser import parse

	@dataclass
	class DummyObj:
		vcsDir: str

	vcsDir = os.getcwd()
	commitId = sys.argv[1]
	beforeStr = sys.argv[2]
	beforeEpoch = parse(beforeStr).timestamp()
	obj = DummyObj(vcsDir)
	parentCommitId = getLatestParentBefore(obj, commitId, beforeEpoch)
	log.info(parentCommitId)
