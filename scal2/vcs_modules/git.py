#!/usr/bin/python2
from subprocess import Popen, PIPE
from os import chdir


def getCommitList(direc):
    '''
        returns a list of (epoch_time, long_commit_id) tuples
    '''
    chdir(direc)
    p = Popen([
        'git',
        'log',
        '--pretty=format:%ct %H',
        #'--git-dir', '%s/.git'%direc,
    ], stdout=PIPE)
    p.wait()
    data = []
    for line in p.stdout:
        parts = line.strip().split(' ')
        data.append((
            int(parts[0]),
            parts[1],
        ))
    return data

def getShortStat(direc):
    '''
        returns a list of (epoch, files_changed, insertions, deletions) tuples
    '''
    chdir(direc)
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


if __name__=='__main__':
    for item in  getStat('/starcal2'):
        print item




