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

from os.path import join
from subprocess import Popen, PIPE
from scal2.time_utils import getEpochFromJd
from scal2.date_utils import dateEncode
from scal2.cal_types import jd_to, to_jd, DATE_GREG

def prepareObj(obj):
    pass

def clearObj(obj):
    pass

def getCommitList(obj, startJd=None, endJd=None):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '--pretty=format:%ct %H',
    ]
    if startJd is not None:
        cmd += [
            '--since',
            dateEncode(jd_to(startJd, DATE_GREG)),
        ]
    if endJd is not None:
        cmd += [
            '--until',
            dateEncode(jd_to(endJd, DATE_GREG)),
        ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        parts = line.strip().split(' ')
        data.append((
            int(parts[0]),
            parts[1],
        ))
    return data


def getCommitInfo(obj, commid_id):
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '-1',
        '--pretty=%at\n%cn <%ce>\n%h\n%s',
        commid_id,
    ]
    parts = Popen(cmd, stdout=PIPE).stdout.read().strip().split('\n')
    if not parts:
        return
    return {
        'epoch': int(parts[0]),
        'author': parts[1],
        'shortHash': parts[2],
        'summary': parts[3],
        'description': '\n'.join(parts[4:]),
    }


def getCommitShortStatLine(obj, commit_id):
    '''
        returns str
    '''
    p = Popen([
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '--shortstat',
        '-1',
        '--pretty=%%',
        commit_id,
    ], stdout=PIPE)
    p.wait()
    nums = []
    for line in p.stdout.readlines():
        if line.startswith(' '):
            return line.strip()
    return ''

def getCommitShortStat(obj, commit_id):
    '''
        returns (files_changed, insertions, deletions)
    '''
    statLine = getCommitShortStatLine(obj.vcsDir, commit_id)
    if not statLine:
        return 0, 0, 0
    for section in statLine.split(','):
        try:
            num = int(section.strip().split(' ')[0])
        except:
            print 'bad section: %r, statLine=%r'%(section, statLine)
        else:
            nums.append(num)
    return nums[:3]


def getTagList(obj, startJd, endJd):
    '''
        returns a list of (epoch, tag_name) tuples
    '''
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'tag',
    ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        tag = line.strip()
        if not tag:
            continue
        line = Popen([
            'git',
            '--git-dir', join(obj.vcsDir, '.git'),
            'log',
            '-1',
            tag,
            '--pretty=%ct',
        ], stdout=PIPE).stdout.read().strip()
        epoch = int(line)
        if epoch < startEpoch:
            continue
        if epoch >= endEpoch:
            break
        data.append((
            epoch,
            tag,
        ))
    return data

def getTagShortStatLine(obj, prevTag, tag):
    '''
        returns str
    '''
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'diff',
        '--shortstat',
    ]
    if prevTag:
        cmd += [
            prevTag,
            tag,
        ]
    else:
        cmd += [
            tag,
        ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    return p.stdout.read().strip()


