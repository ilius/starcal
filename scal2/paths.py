# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import os
from os.path import dirname, join
import platform

APP_NAME = 'starcal2'

psys = platform.system()## 'Linux', 'Windows', 'Darwin'

srcDir = dirname(__file__)
cwd = os.getcwd()
if srcDir in ('.', ''):
    srcDir = cwd
elif os.sep=='/':
    if srcDir.startswith('./'):
        srcDir = cwd + srcDir[1:]
    elif srcDir[0] != '/':
        srcDir = join(cwd, srcDir)
elif os.sep=='\\':
    if srcDir.startswith('.\\'):
        srcDir = cwd + srcDir[1:]
#print 'srcDir=%r'%srcDir

rootDir = dirname(srcDir)
pixDir = os.path.join(rootDir, 'pixmaps')
plugDir = os.path.join(rootDir, 'plugins')

if os.sep=='/':## Unix-like OS
    homeDir = os.getenv('HOME')
    #tmpDir = '/tmp'
    #user = os.getenv('USER')
    if psys=='Darwin':## MacOS X
        confPath = homeDir + '/Library/Preferences/' + APP_NAME ## OR '/Library/' + APP_NAME
        ## os.environ['OSTYPE'] == 'darwin10.0'
        ## os.environ['MACHTYPE'] == 'x86_64-apple-darwin10.0'
        ## platform.dist() == ('', '', '')
        ## platform.release() == '10.3.0'
    else:## GNU/Linux, ...
        confDir = homeDir + '/.' + APP_NAME
        sysConfDir = '/etc/' + APP_NAME
elif os.sep=='\\':## Dos/Windows OS
    #homeDrive = os.environ['HOMEDRIVE']
    homeDir = os.getenv('HOMEPATH')
    confDir = os.getenv('APPDATA') + '\\' + APP_NAME
    sysConfDir = join(rootDir, 'config')
    #tmpDir = os.getenv('TEMP')
    #user = os.getenv('USERNAME')
    ####
    winStartupRelPath = r'\Microsoft\Windows\Start Menu\Programs\Startup'
    winStartupDir = os.getenv('APPDATA') + winStartupRelPath
    #winStartupDirSys = os.getenv('ALLUSERSPROFILE') + winStartupRelPath
    winStartupFile = join(winStartupDir, APP_NAME+'.lnk')
else:
    raise RuntimeError('bad seperator (os.sep=="%s") !! What is your Operating System?!'%os.sep)

userPlugConf = join(confDir, 'plugin.conf')
modDir = '%s/cal_modules'%srcDir
plugDirUser = os.path.join(confDir, 'plugins')
plugConfDir = os.path.join(confDir, 'plugins.conf')




