# -*- coding: utf-8 -*-


from subprocess import Popen, PIPE
from scal2.time_utils import dateEncodeDash
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
        '--template', '{date}\n{desc}\n{author}\n{node|short}',
    ]
    parts = Popen(cmd, stdout=PIPE).stdout.read().split('\n')
    if not parts:
        return
    return {
        'epoch': fixEpochStr(parts[0]),
        'summary': parts[1],
        'author': parts[2],
        'shortHash': parts[3],
    }



def getStat(direc):
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


