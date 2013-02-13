# -*- coding: utf-8 -*-

from os.path import join
from subprocess import Popen, PIPE
from scal2.time_utils import dateEncode
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
        '--pretty=%at\n%s\n%cn <%ce>\n%h',
        commid_id,
    ]
    parts = Popen(cmd, stdout=PIPE).stdout.read().split('\n')
    if not parts:
        return
    return {
        'epoch': int(parts[0]),
        'summary': parts[1],
        'author': parts[2],
        'shortHash': parts[3],
    }

#def getLog(direc, startJd, endJd):
#    log = []
#    for epoch, commit_id in getCommitList(direc):



def getStat(direc):
    '''
        returns a list of (epoch, files_changed, insertions, deletions) tuples
    '''
    stat = []
    commits = getCommitList(direc)
    n = len(commits) - 1
    for i in range(n):
        epoch = commits[i][0]
        p = Popen([
            'git',
            'diff',
            '--shortstat',
            commits[i][1],
            commits[i+1][1],
        ], stdout=PIPE)
        p.wait()
        nums = []
        output = p.stdout.read().strip()
        if not output:
            continue
        for section in output.split(','):
            try:
                num = int(section.strip().split(' ')[0])
            except:
                print 'bad section: %r, output=%r'%(section, output)
            else:
                nums.append(num)
        ## nums == (files_changed, insertions, deletions)
        stat.append((epoch, nums[0], nums[1], nums[2]))
    return stat


