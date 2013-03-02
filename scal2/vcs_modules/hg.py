# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import mercurial.ui
from mercurial.localrepo import localrepository
from mercurial.patch import diff, diffstatdata, diffstatsum
from mercurial.util import iterlines

def getCommitList(direc, startJd, endJd):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    ###
    repo = localrepository(mercurial.ui.ui(), direc)
    data = []
    for rev in repo.changelog:
        ctx = repo[rev]
        epoch = ctx.date()[0]
        if epoch < startEpoch:
            continue
        if epoch >= endEpoch:
            break
        data.append((epoch, str(ctx)))
    return data


def getCommitInfo(direc, commid_id):
    repo = localrepository(mercurial.ui.ui(), direc)
    ctx = repo[commid_id]
    lines = ctx.description().split('\n')
    return {
        'epoch': ctx.date()[0],
        'author': ctx.user(),
        'shortHash': str(ctx),
        'summary': lines[0],
        'description': '\n'.join(lines[1:]),
    }


def getShortStat(repo, node1, node2):
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


def getCommitShortStat(direc, commit_id):
    '''
        returns (files_changed, insertions, deletions)
    '''
    repo = localrepository(mercurial.ui.ui(), direc)
    ctx = repo[commit_id]
    return getShortStat(
        repo,
        ctx.p1(),
        ctx,
    )

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

def getCommitShortStatLine(direc, commit_id):
    '''
        returns str
    '''
    return encodeShortStat(*getCommitShortStat(direc, commit_id))


def getTagList(direc, startJd, endJd):
    '''
        returns a list of (epoch, tag_name) tuples
    '''
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    ###
    repo = localrepository(mercurial.ui.ui(), direc)
    data = []
    for tag, unkown in repo.tagslist():
        if tag == 'tip':
            continue
        epoch = repo[tag].date()[0]
        if epoch < startEpoch:
            continue
        if epoch >= endEpoch:
            break
        data.append((
            epoch,
            tag,
        ))
    return data

def getTagShortStat(direc, prevTag, tag):
    repo = localrepository(mercurial.ui.ui(), direc)
    return getShortStat(
        repo,
        repo[prevTag if prevTag else 0],
        repo[tag],
    )


def getTagShortStatLine(direc, prevTag, tag):
    '''
        returns str
    '''
    return encodeShortStat(*getTagShortStat(direc, prevTag, tag))




