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

from scal3.time_utils import getEpochFromJd
from scal3.vcs_modules import encodeShortStat, getCommitListFromEst
from scal3.event_search_tree import EventSearchTree

import mercurial.ui
from mercurial.localrepo import localrepository
from mercurial.patch import diff, diffstatdata, diffstatsum
from mercurial.util import iterlines


def prepareObj(obj):
	obj.repo = localrepository(mercurial.ui.ui(), obj.vcsDir)
	###
	obj.est = EventSearchTree()
	for rev_id in obj.repo.changelog:
		epoch = obj.repo[rev_id].date()[0]
		obj.est.add(epoch, epoch, rev_id)


def clearObj(obj):
	obj.repo = None
	obj.est = EventSearchTree()


def getCommitList(obj, startJd, endJd):
	"""
	return a list of (epoch, commit_id) tuples
	"""
	return getCommitListFromEst(
		obj,
		startJd,
		endJd,
		lambda repo, rev_id: str(repo[rev_id])
	)


def getCommitInfo(obj, commid_id):
	ctx = obj.repo[commid_id]
	lines = ctx.description().split('\n')
	return {
		'epoch': ctx.date()[0],
		'author': ctx.user(),
		'shortHash': str(ctx),
		'summary': lines[0],
		'description': '\n'.join(lines[1:]),
	}


def getShortStat(obj, node1, node2):## SLOW FIXME
	repo = obj.repo
	# if not node1 ## FIXME
	stats = diffstatdata(
		iterlines(
			diff(
				repo,
				str(node1),
				str(node2),
			)
		)
	)
	(
		maxname,
		maxtotal,
		insertions,
		deletions,
		hasbinary,
	) = diffstatsum(stats)
	return len(stats), insertions, deletions


def getCommitShortStat(obj, commit_id):
	"""
	returns (files_changed, insertions, deletions)
	"""
	ctx = obj.repo[commit_id]
	return getShortStat(
		obj,
		ctx.p1(),
		ctx,
	)


def getCommitShortStatLine(obj, commit_id):
	"""returns str"""
	return encodeShortStat(*getCommitShortStat(obj, commit_id))


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
	for tag, unkown in obj.repo.tagslist():
		if tag == 'tip':
			continue
		epoch = obj.repo[tag].date()[0]
		if startEpoch <= epoch < endEpoch:
			data.append((
				epoch,
				tag,
			))
	data.sort()
	return data


def getTagShortStat(obj, prevTag, tag):
	repo = obj.repo
	return getShortStat(
		obj,
		repo[prevTag if prevTag else 0],
		repo[tag],
	)


def getTagShortStatLine(obj, prevTag, tag):
	"""returns str"""
	return encodeShortStat(*getTagShortStat(obj, prevTag, tag))


def getFirstCommitEpoch(obj):
	return obj.repo[0].date()[0]


def getLastCommitEpoch(obj):
	return obj.repo[len(obj.repo) - 1].date()[0]


def getLastCommitIdUntilJd(obj, jd):
	untilEpoch = getEpochFromJd(jd)
	last = obj.est.getLastBefore(untilEpoch)
	if not last:
		return
	t0, t1, rev_id = last
	return str(obj.repo[rev_id])
