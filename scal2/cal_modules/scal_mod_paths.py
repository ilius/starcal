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

import time
#print time.time(), __file__

import os
from os.path import dirname, join

APP_NAME = 'starcal2'

curDir = dirname(__file__)
if not curDir:
        curDir = os.getcwd()
srcDir = dirname(curDir)
rootDir = dirname(srcDir)

if os.sep=='/':## Unix-like OS
    homeDir = os.getenv('HOME')
    confDir = homeDir + '/.' + APP_NAME
    sysConfDir    = '/etc/' + APP_NAME
    #tmpDir    = '/tmp'
elif os.sep=='\\':## Dos/Windows OS
    homeDir = os.getenv('HOMEPATH')
    confDir = os.getenv('APPDATA') + '\\' + APP_NAME ##??????????
    sysConfDir    = rootDir
    #tmpDir    = os.getenv('TEMP')
else:
    raise RuntimeError('bad seperator (os.sep=="%s") !! What is your Operating System?!'%os.sep)


modDir = '%s/cal_modules'%srcDir
plugDirUser = os.path.join(confDir, 'plugins')

