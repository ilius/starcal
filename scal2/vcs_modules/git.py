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
from scal2.time_utils import getEpochFromJd, epochGregDateTimeEncode

def prepareObj(obj):
    pass

def clearObj(obj):
    pass

encodeJd = lambda jd: epochGregDateTimeEncode(getEpochFromJd(jd))

def getCommitList(obj, startJd=None, endJd=None):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '--format=%ct %H',## or '--format=%ct %H'
    ]
    if startJd is not None:
        cmd += [
            '--since',
            encodeJd(startJd),
        ]
    if endJd is not None:
        cmd += [
            '--until',
            encodeJd(endJd),
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

def getFirstCommitEpoch(obj):
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'rev-list',
        '--max-parents=0',
        'HEAD',
        '--format=%ct',
    ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    lines = p.stdout.read().split('\n')
    return int(lines[1].strip())


def getLastCommitEpoch(obj):
    cmd = [
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '-1',
        '--format=%ct',
    ]
    return int(Popen(cmd, stdout=PIPE).stdout.read().strip())


def getLastCommitIdUntil(obj, jd):
    return Popen([
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'log',
        '--until', encodeJd(jd),
        '-1',
        '--format=%H',
    ], stdout=PIPE).stdout.read().strip()

def getDailyStatLine(obj, jd):
    '''
        returns str
    '''
    return Popen([
        'git',
        '--git-dir', join(obj.vcsDir, '.git'),
        'diff',
        '--shortstat',
        getLastCommitIdUntil(obj, jd),
        getLastCommitIdUntil(obj, jd+1),
    ], stdout=PIPE).stdout.read().strip()


