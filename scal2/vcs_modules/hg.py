# -*- coding: utf-8 -*-


from subprocess import Popen, PIPE
from scal2.time_utils import dateEncodeDash, getEpochFromJd
from scal2.cal_modules import jd_to, to_jd, DATE_GREG

fixEpochStr = lambda epoch_str: int(epoch_str.split('.')[0])

def getCommitList(direc, startJd=None, endJd=None):
    '''
        returns a list of (epoch, commit_id) tuples
    '''
    cmd = [
        'hg',
        '-R', direc,
        'log',
        '--template',
        '{date} {node}\n',
    ]
    if startJd is not None:
        if endJd is not None:
            cmd += [
                '-d',
                '%s to %s'%(
                    dateEncodeDash(jd_to(startJd, DATE_GREG)),
                    dateEncodeDash(jd_to(endJd, DATE_GREG)),
                )
            ]
        else:
            cmd += [
                '-d',
                '>%s'%dateEncodeDash(jd_to(startJd, DATE_GREG)),
            ]
    elif endJd is not None:
        cmd += [
            '-d',
            '<%s'%dateEncodeDash(jd_to(endJd, DATE_GREG)),
        ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        parts = line.strip().split(' ')
        data.append((
            fixEpochStr(parts[0]),
            parts[1],
        ))
    return data


def getCommitInfo(direc, commid_id):
    cmd = [
        'hg',
        '-R', direc,
        'log',
        '-r', commid_id,
        '--template', '{date}\n{author}\n{node|short}\n{desc}',
    ]
    parts = Popen(cmd, stdout=PIPE).stdout.read().split('\n')
    if not parts:
        return
    return {
        'epoch': fixEpochStr(parts[0]),
        'author': parts[1],
        'shortHash': parts[2],
        'summary': parts[3],
        'description': '\n'.join(parts[4:]),
    }

def getCommitShortStat(direc, commit_id):
    '''
        returns (files_changed, insertions, deletions)
    '''
    p = Popen([
        'hg',
        '-R', direc,
        'log',
        '-r', commit_id,
        '--template',
        '{diffstat}',
    ], stdout=PIPE)
    p.wait()
    parts = p.stdout.read().strip().split(' ')
    files_changed = int(parts[0].split(':')[0])
    insertions, deletions = parts[1].split('/')
    insertions = int(insertions)
    deletions = -int(deletions)
    return files_changed, insertions, deletions

def getCommitShortStatLine(direc, commit_id):
    '''
        returns str
    '''
    files_changed, insertions, deletions = getCommitShortStat(direc, commit_id)
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

"""
def getShortStatList(direc):
    '''
        returns a list of (epoch, files_changed, insertions, deletions) tuples
    '''
    p = Popen([
        'hg',
        '-R', direc,
        'log',
        '--template',
        '{date} {diffstat}\n',
    ], stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        parts = line.strip().split(' ')
        epoch = fixEpochStr(parts[0])
        files_changed = int(parts[1].split(':')[0])
        insertions, deletions = parts[2].split('/')
        insertions = int(insertions)
        deletions = -int(deletions)
        data.append((epoch, files_changed, insertions, deletions))
    return data
"""

def getTagList(direc, startJd, endJd):
    '''
        returns a list of (epoch, tag_name) tuples
    '''
    startEpoch = getEpochFromJd(startJd)
    endEpoch = getEpochFromJd(endJd)
    cmd = [
        'hg',
        '-R', direc,
        'tags',
    ]
    p = Popen(cmd, stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        line = line.strip()
        if not line:
            continue
        parts = line.split(' ')
        tag = ' '.join(parts[:-1]).strip()
        if not tag:
            continue
        shortHash = parts[-1]
        line = Popen([
            'hg',
            '-R', direc,
            'log',
            '-r', shortHash,
            '--template', '{date}',
        ], stdout=PIPE).stdout.read().strip()
        epoch = fixEpochStr(line)
        if epoch < startEpoch:
            continue
        if epoch >= endEpoch:
            break
        data.append((
            epoch,
            tag,
        ))
    return data


def getTagShortStatLine(direc, prevTag, tag):## FIXME
    '''
        returns str
    '''
    cmd = [
        'hg',
        '-R', direc,
        'diff',
        '--stat',
        '-r',
    ]
    if prevTag:
        cmd += [
            "tag('%s'):tag('%s')"%(prevTag, tag),
        ]
    else:
        cmd += [
            "tag('%s')"%tag,
        ]
    p = Popen(cmd, stdout=PIPE)
    return p.stdout.readlines()[-1].strip()


