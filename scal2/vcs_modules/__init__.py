# -*- coding: utf-8 -*-

vcsModuleNames = [
    'git',
    'hg',
    'bzr',
]

vcsModuleDict = {}

for name in vcsModuleNames:
    try:
        mod = __import__('scal2.vcs_modules', fromlist=[name])
    except ImportError:
        vcsModuleNames.remove(name)
        continue
    vcsModuleDict[name] = getattr(mod, name)


