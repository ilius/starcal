# -*- coding: utf-8 -*-

vcsModuleNames = [
    'git',
    #'hg',
]

vcsModuleDict = dict([
    (name, getattr(__import__('scal2.vcs_modules', fromlist=[name]), name))
    for name in vcsModuleNames
])

#print dir(vcsModuleDict['git'])

