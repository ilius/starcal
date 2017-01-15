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

from difflib import SequenceMatcher

from scal3.utils import NullObj
from scal3.time_utils import getEpochFromJd
from scal3.vcs_modules import encodeShortStat, getCommitListFromEst
from scal3.event_search_tree import EventSearchTree

from bzrlib.bzrdir import BzrDir
from bzrlib.diff import DiffText
from bzrlib import revision as _mod_revision
from bzrlib.osutils import split_lines


def prepareObj(obj):
	(
		tree,
		branch,
		repo,
		relpath,
	) = BzrDir.open_containing_tree_branch_or_repository(obj.vcsDir)
	obj.branch = branch
	obj.repo = repo
	###
	obj.est = EventSearchTree()
	obj.firstRev = None
	obj.lastRev = None
	for (
		rev_id,
		depth,
		revno,
		end_of_merge,
	) in branch.iter_merge_sorted_revisions(direction="forward"):
		rev = obj.repo.get_revision(rev_id)
		epoch = rev.timestamp
		obj.est.add(epoch, epoch, rev_id)
		if not obj.firstRev:
			obj.firstRev = rev
		obj.lastRev = rev


def clearObj(obj):
	obj.branch = None
	obj.repo = None
	obj.est = EventSearchTree()


def getCommitList(obj, startJd, endJd):
	"""
		returns a list of (epoch, rev_id) tuples
	"""
	return getCommitListFromEst(
		obj,
		startJd,
		endJd,
	)


def getCommitInfo(obj, rev_id):
	rev = obj.repo.get_revision(rev_id)
	lines = rev.message.split("\n")
	return {
		"epoch": rev.timestamp,
		"author": rev.committer,
		"shortHash": rev_id,
		"summary": lines[0],
		"description": "\n".join(lines[1:]),
	}


def getShortStat(obj, old_rev_id, rev_id):
	repo = obj.repo
	return getShortStatByTrees(
		repo,
		repo.revision_tree(old_rev_id),
		repo.revision_tree(rev_id),
	)


def getShortStatByTrees(repo, old_tree, tree):
	files_changed = 0
	insertions = 0
	deletions = 0
	####
	tree.lock_read()
	for (
		file_id,
		(old_path, new_path),
		changed_content,
		versioned,
		parent,
		name,
		(old_kind, new_kind),
		executable,
	) in tree.iter_changes(old_tree):
		if changed_content:
			#for kind in (old_kind, new_kind):
			#	if not kind in (None, "file", "symlink", "directory"):
			#		print("kind", old_kind, new_kind)
			if new_kind in ("file", "symlink"):
				files_changed += 1
				text = tree.get_file_text(file_id)
				if "\x00" not in text[:1024]:## FIXME
					if old_kind is None:
						insertions += len(split_lines(text))
					elif old_kind in ("file", "symlink"):
						old_text = old_tree.get_file_text(file_id)
						seq = SequenceMatcher(
							None,
							split_lines(old_text),
							split_lines(text),
						)
						for op, i1, i2, j1, j2 in seq.get_opcodes():
							if op == "equal":
								continue
							#if not op in ("insert", "delete", "replace"):
							#	print("op", op)
							insertions += (j2 - j1)
							deletions += (i2 - i1)
			elif new_kind is None:
				if old_kind in ("file", "symlink"):
					files_changed += 1
					old_text = old_tree.get_file_text(file_id)
					if "\x00" not in old_text[:1024]:## FIXME
						deletions += len(split_lines(old_text))
	return files_changed, insertions, deletions


def getCommitShortStat(obj, rev_id):
	"""
		returns (files_changed, insertions, deletions)
	"""
	repo = obj.repo
	rev = repo.get_revision(rev_id)
	tree = repo.revision_tree(rev_id)
	try:
		old_rev_id = rev.parent_ids[0]
	except IndexError:
		old_rev_id = _mod_revision.NULL_REVISION
	return getShortStatByTrees(
		repo,
		repo.revision_tree(old_rev_id),
		tree,
	)


def getCommitShortStatLine(obj, rev_id):
	"""returns str"""
	return encodeShortStat(*getCommitShortStat(obj, rev_id))


def getTagList(obj, startJd, endJd):
	"""
		returns a list of (epoch, tag_name) tuples
	"""
	if not obj.repo:
		return []
	startEpoch = getEpochFromJd(startJd)
	endEpoch = getEpochFromJd(endJd)
	###
	data = []
	for tag, rev_id in obj.branch.tags.get_tag_dict().items():
		rev = obj.repo.get_revision(rev_id)
		epoch = rev.timestamp
		if startEpoch <= epoch < endEpoch:
			data.append((
				epoch,
				tag,
			))
	data.sort()
	return data


def getTagShortStat(obj, prevTag, tag):
	"""
		returns (files_changed, insertions, deletions)
	"""
	repo = obj.repo
	td = obj.branch.tags.get_tag_dict()
	return getShortStatByTrees(
		repo,
		repo.revision_tree(td[prevTag] if prevTag else None),
		repo.revision_tree(td[tag]),
	)


def getTagShortStatLine(obj, prevTag, tag):
	"""returns str"""
	return encodeShortStat(*getTagShortStat(obj, prevTag, tag))


def getFirstCommitEpoch(obj):
	return obj.firstRev.timestamp


def getLastCommitEpoch(obj):
	return obj.lastRev.timestamp


def getLastCommitIdUntilJd(obj, jd):
	untilEpoch = getEpochFromJd(jd)
	last = obj.est.getLastBefore(untilEpoch)
	if not last:
		return
	t0, t1, rev_id = last
	return str(obj.repo.get_revision(rev_id))
