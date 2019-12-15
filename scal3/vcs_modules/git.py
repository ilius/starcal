#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from scal3 import logger
log = logger.get()

from os.path import join
from subprocess import Popen, PIPE

from typing import List, Tuple

from pygit2 import (
	Repository,
	GIT_SORT_TIME,
	GIT_SORT_TOPOLOGICAL,
	GIT_SORT_REVERSE,
)

from scal3.utils import toStr, toBytes
from scal3.time_utils import getEpochFromJd, encodeJd
from scal3.vcs_modules import encodeShortStat


def prepareObj(obj):
	pass


def clearObj(obj):
	pass



def getCommitList(obj, startJd=None, endJd=None, branch="") -> List[Tuple[int, str]]:
	"""
	returns a list of (epoch, commit_id) tuples

	this function is optimized for recent commits
		i.e. endJd is either None or recent
	"""
	if not branch:
		branch = "master"
	startEpoch = None
	endEpoch = None
	if startJd is not None:
		startEpoch = getEpochFromJd(startJd)
	if endJd is not None:
		endEpoch = getEpochFromJd(endJd)
	repo = Repository(obj.vcsDir)
	data = []  # type: List[Tuple[int, str]]
	# items of data are (epochTime, commitHash)
	target = repo.branches[branch].target
	for commit in repo.walk(target, GIT_SORT_TIME):
		tm = commit.author.time
		if endEpoch is not None and tm > endEpoch:
			continue
		if startEpoch is not None and tm < startEpoch:
			break
		data.append((
			tm,
			commit.id.hex,
		))
	data.reverse()
	return data


def getCommitInfo(obj, commid_id):
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


def getShortStatLine(obj, prevId, thisId):
	"""
	returns str
	"""
	return encodeShortStat(*getShortStat(obj, prevId, thisId))


def getShortStat(obj, prevId, thisId):
	"""
	returns (files_changed, insertions, deletions)
	"""
	repo = Repository(obj.vcsDir)
	diff = repo.diff(
		a=repo.revparse_single(prevId).id.hex,
		b=repo.revparse_single(thisId).id.hex,
	)
	stats = diff.stats
	return (stats.files_changed, stats.insertions, stats.deletions)


def getCommitShortStatLine(obj, commit_id):
	"""
	returns str
	"""
	return encodeShortStat(*getCommitShortStat(obj, commit_id))


def getCommitShortStat(obj, commit_id):
	"""
	returns (files_changed, insertions, deletions)
	"""
	repo = Repository(obj.vcsDir)
	commit = repo.revparse_single(commit_id)
	diff = repo.diff(
		a=commit.parent_ids[0].hex,
		b=commit.id.hex,
	)
	stats = diff.stats
	return (stats.files_changed, stats.insertions, stats.deletions)


def getTagList(obj, startJd, endJd):
	"""
	returns a list of (epoch, tag_name) tuples
	"""
	repo = Repository(obj.vcsDir)
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	data = []
	for refName in repo.references:
		if not refName.startswith("refs/tags/"):
			continue
		tagName = refName[len("refs/tags/"):]
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
		data.append((
			epoch,
			tagName,
		))
	return data


def getTagShortStatLine(obj, prevTag, tag):
	return getShortStatLine(obj, prevTag, tag)


def getFirstCommitEpoch(obj):
	repo = Repository(obj.vcsDir)
	target = repo.branches["master"].target
	commitIter = repo.walk(target, GIT_SORT_TIME | GIT_SORT_REVERSE)
	commit = next(commitIter)
	return commit.author.time


def getLastCommitEpoch(obj):
	repo = Repository(obj.vcsDir)
	target = repo.branches["master"].target
	commitIter = repo.walk(target, GIT_SORT_TIME)
	commit = next(commitIter)
	return commit.author.time

def getLatestParentBefore(obj, commitId: str, beforeEpoch: float) -> str:
	repo = Repository(obj.vcsDir)

	def find(commitIdArg):
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
	import sys
	import os
	from dateutil.parser import parse
	
	class DummyObj:
		def __init__(self, vcsDir):
			self.vcsDir = vcsDir

	vcsDir = os.getcwd()
	commitId = sys.argv[1]
	beforeStr = sys.argv[2]
	beforeEpoch = parse(beforeStr).timestamp()
	obj = DummyObj(vcsDir)
	parentCommitId = getLatestParentBefore(obj, commitId, beforeEpoch)
	log.info(parentCommitId)
