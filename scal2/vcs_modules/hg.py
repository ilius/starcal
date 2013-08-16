# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Saeed Rasooli <saeed.gnu@gmail.com>
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

from scal2.time_utils import getEpochFromJd
from scal2.vcs_modules.common import encodeShortStat

import mercurial.ui
from mercurial.localrepo import localrepository
from mercurial.patch import diff, diffstatdata, diffstatsum
from mercurial.util import iterlines

def prepareObj(obj):
    obj.repo = localrepository(mercurial.ui.ui(), obj.vcsDir)

def clearObj(obj):
    obj.repo = None

def getCommitList(obj, startJd, endJd):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    if not obj.repo:
        return []
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    ###
    data = []
    for rev in obj.repo.changelog:
        ctx = obj.repo[rev]
        epoch = ctx.date()[0]
        if epoch < startEpoch:
            continue
        if epoch >= endEpoch:
            break
        data.append((epoch, str(ctx)))
    return data


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


def getShortStat(repo, node1, node2):## SLOW FIXME
    stats = diffstatdata(
        iterlines(
            diff(
                repo,
                str(node1),
                str(node2),
            )
        )
    )
    maxname, maxtotal, insertions, deletions, hasbinary = diffstatsum(stats)
    return len(stats), insertions, deletions


def getCommitShortStat(obj, commit_id):
    '''
        returns (files_changed, insertions, deletions)
    '''
    ctx = obj.repo[commit_id]
    return getShortStat(
        obj.repo,
        ctx.p1(),
        ctx,
    )


def getCommitShortStatLine(obj, commit_id):
    '''
        returns str
    '''
    return encodeShortStat(*getCommitShortStat(obj, commit_id))


def getTagList(obj, startJd, endJd):
    '''
        returns a list of (epoch, tag_name) tuples
    '''
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
        repo,
        repo[prevTag if prevTag else 0],
        repo[tag],
    )


def getTagShortStatLine(obj, prevTag, tag):
    '''
        returns str
    '''
    return encodeShortStat(*getTagShortStat(obj, prevTag, tag))




