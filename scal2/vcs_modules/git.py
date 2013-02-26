# -*- coding: utf-8 -*-

from os.path import join
from subprocess import Popen, PIPE
from scal2.time_utils import dateEncode, getEpochFromJd
from scal2.cal_modules import jd_to, to_jd, DATE_GREG

def getCommitList(direc, startJd=None, endJd=None):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    cmd = [
        'git',
        '--git-dir', join(direc, '.git'),
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


def getCommitInfo(direc, commid_id):
    cmd = [
        'git',
        '--git-dir', join(direc, '.git'),
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


def getCommitShortStatLine(direc, commit_id):
    '''
        returns str
    '''
    p = Popen([
        'git',
        '--git-dir', join(direc, '.git'),
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

def getCommitShortStat(direc, commit_id):
    '''
        returns (files_changed, insertions, deletions)
    '''
    statLine = getCommitShortStatLine(direc, commit_id)
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


"""
def getShortStatList(direc):
    '''
        returns a list of (epoch, files_changed, insertions, deletions) tuples
    '''
    stat = []
    commits = getCommitList(direc)
    n = len(commits) - 1
    for i in range(n):
        epoch, commit_id = commits[i]
        files_changed, insertions, deletions = getCommitShortStat(
            direc,
            commit_id,
        )
        stat.append((epoch, files_changed, insertions, deletions))
    return stat
"""


def getTagList(direc, startJd, endJd):
    '''
        returns a list of (epoch, tag_name) tuples
    '''
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    cmd = [
        'git',
        '--git-dir', join(direc, '.git'),
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
            '--git-dir', join(direc, '.git'),
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

def getTagShortStatLine(direc, prevTag, tag):
    '''
        returns str
    '''
    cmd = [
        'git',
        '--git-dir', join(direc, '.git'),
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

#def getLog(direc, startJd, endJd):
#    log = []
#    for epoch, commit_id in getCommitList(direc):

if __name__=='__main__':
    from pprint import pprint
    pprint(getTagList('/starcal2'))

