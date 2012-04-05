#!/usr/bin/python2
from subprocess import Popen, PIPE
from os import chdir

fixEpochStr = lambda epoch_str: int(epoch_str.split('.')[0])

def getCommitList(direc):
    '''
        returns a list of (epoch_time, long_commit_id) tuples
    '''
    chdir(direc)
    p = Popen([
        'hg',
        'log',
        '--template',
        '{date} {node}\n',
    ], stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        parts = line.strip().split(' ')
        data.append((
            fixEpochStr(parts[0]),
            parts[1],
        ))
    return data


def getStat(direc):
    '''
        returns a list of (epoch, files_changed, insertions, deletions) tuples
    '''
    chdir(direc)
    p = Popen([
        'hg',
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


if __name__=='__main__':
    for item in  getStat('/data/documents/reStructuredText/bidirest'):
        print item

